"""AutoGen multi-agent Event Hubs pipeline."""

from __future__ import annotations

import asyncio
import uuid

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
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


async def _call_agent(mc: AzureOpenAIChatCompletionClient, name: str, system: str, user: str) -> str:
    agent = AssistantAgent(name=name, model_client=mc, system_message=system)
    resp = await agent.on_messages([TextMessage(content=user, source="user")], CancellationToken())
    return resp.chat_message.content


async def main() -> None:
    settings = load_settings()
    messaging = EventHubPipelineMessaging(settings.azure_eventhub_namespace)
    mc = _build_model_client(settings)
    cid = str(uuid.uuid4())

    logger.info("pipeline.start", framework="autogen", pattern="multi-agent-eventhub")

    await messaging.send(settings.eventhub_analysis, {"correlation_id": cid, "document": SAMPLE_DOCUMENT, "stage": "input"})
    msg = await messaging.receive_one(settings.eventhub_analysis)
    if msg:
        analysis = await _call_agent(mc, "analyzer", ANALYZER_SYSTEM_PROMPT, ANALYZE_PROMPT.format(document=msg["document"]))
        await messaging.send(settings.eventhub_summary, {"correlation_id": cid, "analysis": analysis, "stage": "analyzed"})

    msg = await messaging.receive_one(settings.eventhub_summary)
    if msg:
        summary = await _call_agent(mc, "summarizer", SUMMARIZER_SYSTEM_PROMPT, SUMMARIZE_PROMPT.format(analysis=msg["analysis"]))
        await messaging.send(settings.eventhub_review, {"correlation_id": cid, "analysis": msg["analysis"], "summary": summary, "stage": "summarized"})

    msg = await messaging.receive_one(settings.eventhub_review)
    if msg:
        review = await _call_agent(mc, "reviewer", REVIEWER_SYSTEM_PROMPT, REVIEW_PROMPT.format(analysis=msg["analysis"], summary=msg["summary"]))
        print_pipeline_results(msg["analysis"], msg["summary"], review)

    await messaging.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
