"""LangGraph multi-agent pipeline using Azure Event Grid.

Pipeline: Analyzer -> Summarizer -> Reviewer
Messaging: Event Grid (publish) + Storage Queue (subscribe)
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure_clients import EventGridPipelineMessaging
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


async def _invoke_agent(llm: AzureChatOpenAI, system_prompt: str, user_message: str) -> str:
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    return str(response.content)


async def main() -> None:
    settings = load_settings()
    llm = _build_llm(settings)
    messaging = EventGridPipelineMessaging(
        eventgrid_endpoint=settings.azure_eventgrid_endpoint,
        storage_account_name=settings.azure_storage_account_name,
    )
    cid = str(uuid.uuid4())

    logger.info("pipeline.start", framework="langgraph", pattern="multi-agent-eventgrid", correlation_id=cid)

    try:
        # Stage 1: Publish document for analysis
        await messaging.publish(
            event_type="Pipeline.AnalyzeRequest",
            subject=f"/pipeline/{cid}/analyze",
            data={"correlation_id": cid, "document": SAMPLE_DOCUMENT, "stage": "input"},
        )

        msg = await messaging.receive_one(settings.eventgrid_queue_analyzer)
        if not msg:
            logger.error("pipeline.timeout", stage="analyze-receive")
            return
        analysis = await _invoke_agent(llm, ANALYZER_SYSTEM_PROMPT, ANALYZE_PROMPT.format(document=msg.get("document", "")))

        # Stage 2: Publish analysis for summarization
        await messaging.publish(
            event_type="Pipeline.SummarizeRequest",
            subject=f"/pipeline/{cid}/summarize",
            data={"correlation_id": cid, "analysis": analysis, "stage": "analyzed"},
        )

        msg = await messaging.receive_one(settings.eventgrid_queue_summarizer)
        if not msg:
            logger.error("pipeline.timeout", stage="summarize-receive")
            return
        summary = await _invoke_agent(llm, SUMMARIZER_SYSTEM_PROMPT, SUMMARIZE_PROMPT.format(analysis=msg.get("analysis", "")))

        # Stage 3: Publish summary for review
        await messaging.publish(
            event_type="Pipeline.ReviewRequest",
            subject=f"/pipeline/{cid}/review",
            data={"correlation_id": cid, "analysis": analysis, "summary": summary, "stage": "summarized"},
        )

        msg = await messaging.receive_one(settings.eventgrid_queue_reviewer)
        if not msg:
            logger.error("pipeline.timeout", stage="review-receive")
            return
        review = await _invoke_agent(llm, REVIEWER_SYSTEM_PROMPT, REVIEW_PROMPT.format(analysis=msg.get("analysis", ""), summary=msg.get("summary", "")))

        print_pipeline_results(analysis, summary, review)
        logger.info("pipeline.complete", correlation_id=cid)

    finally:
        await messaging.close()


if __name__ == "__main__":
    asyncio.run(main())
