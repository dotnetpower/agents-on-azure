"""Semantic Kernel multi-agent Service Bus pipeline.

Orchestrator mode: sends a document to the analyzer queue, then
each agent picks up from its input queue, processes with SK, and
forwards to the next queue. Final results land in pipeline-results.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure_clients import PipelineMessaging
from contracts.prompts import (
    ANALYZE_PROMPT,
    ANALYZER_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
)
from contracts.sample_document import SAMPLE_DOCUMENT
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_kernel(settings: Settings) -> Kernel:
    kernel = Kernel()
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    chat_service = AzureChatCompletion(
        deployment_name=settings.azure_openai_model,
        endpoint=settings.azure_openai_endpoint,
        ad_token_provider=token_provider,
        service_id="azure-openai",
    )
    kernel.add_service(chat_service)
    return kernel


async def _call_llm(kernel: Kernel, system_prompt: str, user_prompt: str) -> str:
    chat = kernel.get_service("azure-openai")
    execution_settings = AzureChatPromptExecutionSettings(temperature=0.7, max_tokens=2048)
    history = ChatHistory()
    history.add_system_message(system_prompt)
    history.add_user_message(user_prompt)
    response = await chat.get_chat_message_contents(history, execution_settings, kernel=kernel)
    return str(response[0])


async def run_analyzer(settings: Settings, messaging: PipelineMessaging) -> None:
    """Listen on analyzer-tasks, process, forward to summarizer-tasks."""
    kernel = _build_kernel(settings)
    logger.info("agent.start", agent="analyzer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_analyzer, max_wait_time=30)
        if msg is None:
            logger.info("agent.idle", agent="analyzer")
            break
        document = msg.get("document", "")
        correlation_id = msg.get("correlation_id", str(uuid.uuid4()))
        analysis = await _call_llm(kernel, ANALYZER_SYSTEM_PROMPT, ANALYZE_PROMPT.format(document=document))
        await messaging.send(settings.servicebus_queue_summarizer, {
            "correlation_id": correlation_id,
            "analysis": analysis,
        })
        logger.info("agent.forwarded", agent="analyzer", target="summarizer")


async def run_summarizer(settings: Settings, messaging: PipelineMessaging) -> None:
    """Listen on summarizer-tasks, process, forward to reviewer-tasks."""
    kernel = _build_kernel(settings)
    logger.info("agent.start", agent="summarizer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_summarizer, max_wait_time=30)
        if msg is None:
            logger.info("agent.idle", agent="summarizer")
            break
        analysis = msg.get("analysis", "")
        correlation_id = msg.get("correlation_id", "")
        summary = await _call_llm(kernel, SUMMARIZER_SYSTEM_PROMPT, SUMMARIZE_PROMPT.format(analysis=analysis))
        await messaging.send(settings.servicebus_queue_reviewer, {
            "correlation_id": correlation_id,
            "analysis": analysis,
            "summary": summary,
        })
        logger.info("agent.forwarded", agent="summarizer", target="reviewer")


async def run_reviewer(settings: Settings, messaging: PipelineMessaging) -> None:
    """Listen on reviewer-tasks, process, forward to pipeline-results."""
    kernel = _build_kernel(settings)
    logger.info("agent.start", agent="reviewer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_reviewer, max_wait_time=30)
        if msg is None:
            logger.info("agent.idle", agent="reviewer")
            break
        analysis = msg.get("analysis", "")
        summary = msg.get("summary", "")
        correlation_id = msg.get("correlation_id", "")
        review = await _call_llm(
            kernel, REVIEWER_SYSTEM_PROMPT,
            REVIEW_PROMPT.format(analysis=analysis, summary=summary),
        )
        await messaging.send(settings.servicebus_queue_results, {
            "correlation_id": correlation_id,
            "analysis": analysis,
            "summary": summary,
            "review": review,
        })
        logger.info("agent.forwarded", agent="reviewer", target="results")


async def main() -> None:
    settings = load_settings()
    messaging = PipelineMessaging(settings.azure_servicebus_namespace)

    logger.info("pipeline.start", framework="semantic-kernel", pattern="multi-agent-servicebus")

    # 1) Send document to analyzer queue
    correlation_id = str(uuid.uuid4())
    await messaging.send(settings.servicebus_queue_analyzer, {
        "correlation_id": correlation_id,
        "document": SAMPLE_DOCUMENT,
    })

    # 2) Run all three agents concurrently
    await asyncio.gather(
        run_analyzer(settings, messaging),
        run_summarizer(settings, messaging),
        run_reviewer(settings, messaging),
    )

    # 3) Collect result
    result = await messaging.receive_one(settings.servicebus_queue_results, max_wait_time=30)
    if result:
        print_pipeline_results(
            result.get("analysis", ""),
            result.get("summary", ""),
            result.get("review", ""),
        )
    else:
        logger.warning("pipeline.no_result")

    await messaging.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
