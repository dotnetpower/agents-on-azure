"""Semantic Kernel multi-agent Event Hubs pipeline.

Three SK agents communicate via Event Hubs: each reads from its input hub,
processes with the LLM, and publishes to the next hub.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure_clients import EventHubPipelineMessaging
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
    kernel.add_service(AzureChatCompletion(
        deployment_name=settings.azure_openai_model,
        endpoint=settings.azure_openai_endpoint,
        ad_token_provider=token_provider,
        service_id="azure-openai",
    ))
    return kernel


async def _call_llm(kernel: Kernel, system: str, user: str) -> str:
    chat = kernel.get_service("azure-openai")
    execution_settings = AzureChatPromptExecutionSettings(temperature=0.7, max_tokens=2048)
    history = ChatHistory()
    history.add_system_message(system)
    history.add_user_message(user)
    response = await chat.get_chat_message_contents(history, execution_settings, kernel=kernel)
    return str(response[0])


async def main() -> None:
    settings = load_settings()
    messaging = EventHubPipelineMessaging(settings.azure_eventhub_namespace)
    kernel = _build_kernel(settings)

    logger.info("pipeline.start", framework="semantic-kernel", pattern="multi-agent-eventhub")

    correlation_id = str(uuid.uuid4())

    # Step 1: Analyze — publish document, read from analysis hub
    await messaging.send(settings.eventhub_analysis, {
        "correlation_id": correlation_id, "document": SAMPLE_DOCUMENT, "stage": "input",
    })

    msg = await messaging.receive_one(settings.eventhub_analysis)
    analysis = ""
    if msg and msg.get("stage") == "input":
        analysis = await _call_llm(kernel, ANALYZER_SYSTEM_PROMPT,
                                   ANALYZE_PROMPT.format(document=msg["document"]))
        await messaging.send(settings.eventhub_summary, {
            "correlation_id": correlation_id, "analysis": analysis, "stage": "analyzed",
        })
        logger.info("agent.done", agent="analyzer")

    # Step 2: Summarize
    summary = ""
    msg = await messaging.receive_one(settings.eventhub_summary)
    if msg and msg.get("stage") == "analyzed":
        summary = await _call_llm(kernel, SUMMARIZER_SYSTEM_PROMPT,
                                  SUMMARIZE_PROMPT.format(analysis=msg["analysis"]))
        await messaging.send(settings.eventhub_review, {
            "correlation_id": correlation_id,
            "analysis": msg["analysis"], "summary": summary, "stage": "summarized",
        })
        logger.info("agent.done", agent="summarizer")

    # Step 3: Review
    msg = await messaging.receive_one(settings.eventhub_review)
    if msg and msg.get("stage") == "summarized":
        review = await _call_llm(kernel, REVIEWER_SYSTEM_PROMPT,
                                 REVIEW_PROMPT.format(analysis=msg["analysis"], summary=msg["summary"]))
        logger.info("agent.done", agent="reviewer")
        print_pipeline_results(msg["analysis"], msg["summary"], review)

    await messaging.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
