"""AutoGen multi-agent pipeline using Azure Event Grid.

Pipeline: Analyzer -> Summarizer -> Reviewer
Messaging: Event Grid (publish) + Storage Queue (subscribe)
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
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
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_model_client(settings: Settings) -> AzureOpenAIChatCompletionClient:
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    return AzureOpenAIChatCompletionClient(
        azure_deployment=settings.azure_openai_model,
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        model=settings.azure_openai_model,
        api_version="2024-12-01-preview",
    )


async def _invoke_agent(agent: AssistantAgent, message: str) -> str:
    response = await agent.on_messages(
        [TextMessage(content=message, source="user")],
        cancellation_token=CancellationToken(),
    )
    return response.chat_message.content if response.chat_message else ""


async def main() -> None:
    settings = load_settings()
    model_client = _build_model_client(settings)
    messaging = EventGridPipelineMessaging(
        eventgrid_endpoint=settings.azure_eventgrid_endpoint,
        storage_account_name=settings.azure_storage_account_name,
    )
    cid = str(uuid.uuid4())

    analyzer = AssistantAgent("analyzer", model_client=model_client, system_message=ANALYZER_SYSTEM_PROMPT)
    summarizer = AssistantAgent("summarizer", model_client=model_client, system_message=SUMMARIZER_SYSTEM_PROMPT)
    reviewer = AssistantAgent("reviewer", model_client=model_client, system_message=REVIEWER_SYSTEM_PROMPT)

    logger.info("pipeline.start", framework="autogen", pattern="multi-agent-eventgrid", correlation_id=cid)

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
        analysis = await _invoke_agent(analyzer, ANALYZE_PROMPT.format(document=msg.get("document", "")))

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
        summary = await _invoke_agent(summarizer, SUMMARIZE_PROMPT.format(analysis=msg.get("analysis", "")))

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
        review = await _invoke_agent(reviewer, REVIEW_PROMPT.format(analysis=msg.get("analysis", ""), summary=msg.get("summary", "")))

        print_pipeline_results(analysis, summary, review)
        logger.info("pipeline.complete", correlation_id=cid)

    finally:
        await messaging.close()


if __name__ == "__main__":
    asyncio.run(main())
