"""AutoGen single-agent: document analysis-summary-review pipeline.

Uses a single AssistantAgent with AzureOpenAIChatCompletionClient
to perform three sequential tasks.
"""

from __future__ import annotations

import asyncio

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from contracts.prompts import ANALYZE_PROMPT, REVIEW_PROMPT, SINGLE_AGENT_SYSTEM_PROMPT, SUMMARIZE_PROMPT
from contracts.sample_document import SAMPLE_DOCUMENT
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_model_client(settings: Settings) -> AzureOpenAIChatCompletionClient:
    """Create an AzureOpenAIChatCompletionClient with DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    return AzureOpenAIChatCompletionClient(
        azure_deployment=settings.azure_openai_model,
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        model=settings.azure_openai_model,
        api_version="2024-12-01-preview",
    )


async def run_pipeline(document: str, settings: Settings) -> dict[str, str]:
    """Execute the three-step pipeline using a single AutoGen AssistantAgent."""
    model_client = _build_model_client(settings)
    results: dict[str, str] = {}

    agent = AssistantAgent(
        name="document_processor",
        model_client=model_client,
        system_message=SINGLE_AGENT_SYSTEM_PROMPT,
    )

    cancellation_token = CancellationToken()

    # Step 1 - Analyze
    logger.info("pipeline.step", step="analyze")
    analyze_msg = TextMessage(content=ANALYZE_PROMPT.format(document=document), source="user")
    response = await agent.on_messages([analyze_msg], cancellation_token)
    analysis = response.chat_message.content
    results["analysis"] = analysis
    logger.info("pipeline.step.done", step="analyze", length=len(analysis))

    # Step 2 - Summarize
    logger.info("pipeline.step", step="summarize")
    summarize_msg = TextMessage(content=SUMMARIZE_PROMPT.format(analysis=analysis), source="user")
    response = await agent.on_messages([summarize_msg], cancellation_token)
    summary = response.chat_message.content
    results["summary"] = summary
    logger.info("pipeline.step.done", step="summarize", length=len(summary))

    # Step 3 - Review
    logger.info("pipeline.step", step="review")
    review_msg = TextMessage(content=REVIEW_PROMPT.format(analysis=analysis, summary=summary), source="user")
    response = await agent.on_messages([review_msg], cancellation_token)
    review = response.chat_message.content
    results["review"] = review
    logger.info("pipeline.step.done", step="review", length=len(review))

    return results


async def main() -> None:
    settings = load_settings()
    logger.info("pipeline.start", framework="autogen", pattern="single-agent")

    results = await run_pipeline(SAMPLE_DOCUMENT, settings)
    print_pipeline_results(results["analysis"], results["summary"], results["review"])

    logger.info("pipeline.done", framework="autogen", pattern="single-agent")


if __name__ == "__main__":
    asyncio.run(main())
