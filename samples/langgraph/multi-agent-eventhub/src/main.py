"""LangGraph multi-agent Event Hubs pipeline."""

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


async def main() -> None:
    settings = load_settings()
    messaging = EventHubPipelineMessaging(settings.azure_eventhub_namespace)
    llm = _build_llm(settings)
    correlation_id = str(uuid.uuid4())

    logger.info("pipeline.start", framework="langgraph", pattern="multi-agent-eventhub")

    # Analyzer
    await messaging.send(settings.eventhub_analysis, {"correlation_id": correlation_id, "document": SAMPLE_DOCUMENT, "stage": "input"})
    msg = await messaging.receive_one(settings.eventhub_analysis)
    analysis = ""
    if msg:
        analysis = await _call_llm(llm, ANALYZER_SYSTEM_PROMPT, ANALYZE_PROMPT.format(document=msg["document"]))
        await messaging.send(settings.eventhub_summary, {"correlation_id": correlation_id, "analysis": analysis, "stage": "analyzed"})

    # Summarizer
    summary = ""
    msg = await messaging.receive_one(settings.eventhub_summary)
    if msg:
        summary = await _call_llm(llm, SUMMARIZER_SYSTEM_PROMPT, SUMMARIZE_PROMPT.format(analysis=msg["analysis"]))
        await messaging.send(settings.eventhub_review, {"correlation_id": correlation_id, "analysis": msg["analysis"], "summary": summary, "stage": "summarized"})

    # Reviewer
    msg = await messaging.receive_one(settings.eventhub_review)
    if msg:
        review = await _call_llm(llm, REVIEWER_SYSTEM_PROMPT, REVIEW_PROMPT.format(analysis=msg["analysis"], summary=msg["summary"]))
        print_pipeline_results(msg["analysis"], msg["summary"], review)

    await messaging.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
