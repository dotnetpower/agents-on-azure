"""AutoGen multi-agent Service Bus pipeline.

Three AutoGen AssistantAgents communicating via Service Bus queues.
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


async def _call_agent(model_client: AzureOpenAIChatCompletionClient, name: str, system: str, user: str) -> str:
    agent = AssistantAgent(name=name, model_client=model_client, system_message=system)
    response = await agent.on_messages([TextMessage(content=user, source="user")], CancellationToken())
    return response.chat_message.content


async def run_analyzer(settings: Settings, messaging: PipelineMessaging) -> None:
    model_client = _build_model_client(settings)
    logger.info("agent.start", agent="analyzer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_analyzer, max_wait_time=30)
        if msg is None:
            break
        analysis = await _call_agent(
            model_client, "analyzer", ANALYZER_SYSTEM_PROMPT,
            ANALYZE_PROMPT.format(document=msg.get("document", "")),
        )
        await messaging.send(settings.servicebus_queue_summarizer, {
            "correlation_id": msg.get("correlation_id", ""), "analysis": analysis,
        })


async def run_summarizer(settings: Settings, messaging: PipelineMessaging) -> None:
    model_client = _build_model_client(settings)
    logger.info("agent.start", agent="summarizer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_summarizer, max_wait_time=30)
        if msg is None:
            break
        summary = await _call_agent(
            model_client, "summarizer", SUMMARIZER_SYSTEM_PROMPT,
            SUMMARIZE_PROMPT.format(analysis=msg.get("analysis", "")),
        )
        await messaging.send(settings.servicebus_queue_reviewer, {
            "correlation_id": msg.get("correlation_id", ""),
            "analysis": msg.get("analysis", ""), "summary": summary,
        })


async def run_reviewer(settings: Settings, messaging: PipelineMessaging) -> None:
    model_client = _build_model_client(settings)
    logger.info("agent.start", agent="reviewer")
    while True:
        msg = await messaging.receive_one(settings.servicebus_queue_reviewer, max_wait_time=30)
        if msg is None:
            break
        review = await _call_agent(
            model_client, "reviewer", REVIEWER_SYSTEM_PROMPT,
            REVIEW_PROMPT.format(analysis=msg.get("analysis", ""), summary=msg.get("summary", "")),
        )
        await messaging.send(settings.servicebus_queue_results, {
            "correlation_id": msg.get("correlation_id", ""),
            "analysis": msg.get("analysis", ""),
            "summary": msg.get("summary", ""),
            "review": review,
        })


async def main() -> None:
    settings = load_settings()
    messaging = PipelineMessaging(settings.azure_servicebus_namespace)
    logger.info("pipeline.start", framework="autogen", pattern="multi-agent-servicebus")

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
