"""LangGraph multi-agent Service Bus pipeline.

Three independent LangGraph agents communicate via Service Bus queues.
Each agent has a single-node graph that processes its task.
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
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_llm(settings: Settings) -> AzureChatOpenAI:
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_model,
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview",
    )


async def _call_llm(llm: AzureChatOpenAI, system: str, user: str) -> str:
    response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
    return response.content


async def run_analyzer(settings: Settings, messaging: PipelineMessaging) -> None:
    llm = _build_llm(settings)
    logger.info("agent.start", agent="analyzer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_analyzer, max_wait_time=30)
        if msg is None:
            break
        document = msg.get("document", "")
        correlation_id = msg.get("correlation_id", "")
        analysis = await _call_llm(llm, ANALYZER_SYSTEM_PROMPT, ANALYZE_PROMPT.format(document=document))
        await messaging.send(settings.servicebus_queue_summarizer, {
            "correlation_id": correlation_id, "analysis": analysis,
        })
        logger.info("agent.forwarded", agent="analyzer", target="summarizer")


async def run_summarizer(settings: Settings, messaging: PipelineMessaging) -> None:
    llm = _build_llm(settings)
    logger.info("agent.start", agent="summarizer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_summarizer, max_wait_time=30)
        if msg is None:
            break
        analysis = msg.get("analysis", "")
        correlation_id = msg.get("correlation_id", "")
        summary = await _call_llm(llm, SUMMARIZER_SYSTEM_PROMPT, SUMMARIZE_PROMPT.format(analysis=analysis))
        await messaging.send(settings.servicebus_queue_reviewer, {
            "correlation_id": correlation_id, "analysis": analysis, "summary": summary,
        })
        logger.info("agent.forwarded", agent="summarizer", target="reviewer")


async def run_reviewer(settings: Settings, messaging: PipelineMessaging) -> None:
    llm = _build_llm(settings)
    logger.info("agent.start", agent="reviewer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_reviewer, max_wait_time=30)
        if msg is None:
            break
        analysis = msg.get("analysis", "")
        summary = msg.get("summary", "")
        correlation_id = msg.get("correlation_id", "")
        review = await _call_llm(llm, REVIEWER_SYSTEM_PROMPT, REVIEW_PROMPT.format(analysis=analysis, summary=summary))
        await messaging.send(settings.servicebus_queue_results, {
            "correlation_id": correlation_id, "analysis": analysis, "summary": summary, "review": review,
        })
        logger.info("agent.forwarded", agent="reviewer", target="results")


async def main() -> None:
    settings = load_settings()
    messaging = PipelineMessaging(settings.azure_servicebus_namespace)

    logger.info("pipeline.start", framework="langgraph", pattern="multi-agent-servicebus")

    correlation_id = str(uuid.uuid4())
    await messaging.send(settings.servicebus_queue_analyzer, {
        "correlation_id": correlation_id, "document": SAMPLE_DOCUMENT,
    })

    await asyncio.gather(
        run_analyzer(settings, messaging),
        run_summarizer(settings, messaging),
        run_reviewer(settings, messaging),
    )

    result = await messaging.receive_one(settings.servicebus_queue_results, max_wait_time=30)
    if result:
        print_pipeline_results(result.get("analysis", ""), result.get("summary", ""), result.get("review", ""))

    await messaging.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
