"""Semantic Kernel single-agent: document analysis-summary-review pipeline.

Runs a single agent with three sequential steps using Azure OpenAI.
"""

from __future__ import annotations

import asyncio

import structlog
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from contracts.prompts import ANALYZE_PROMPT, REVIEW_PROMPT, SINGLE_AGENT_SYSTEM_PROMPT, SUMMARIZE_PROMPT
from contracts.sample_document import SAMPLE_DOCUMENT
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_kernel(settings: Settings) -> Kernel:
    """Create a Kernel with AzureChatCompletion service."""
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


async def run_pipeline(document: str, settings: Settings) -> dict[str, str]:
    """Execute the three-step document pipeline with a single Semantic Kernel agent."""
    kernel = _build_kernel(settings)
    chat = kernel.get_service("azure-openai")
    execution_settings = AzureChatPromptExecutionSettings(
        temperature=0.7,
        max_tokens=2048,
    )
    results: dict[str, str] = {}

    # Step 1 — Analyze
    logger.info("pipeline.step", step="analyze")
    history = ChatHistory()
    history.add_system_message(SINGLE_AGENT_SYSTEM_PROMPT)
    history.add_user_message(ANALYZE_PROMPT.format(document=document))
    response = await chat.get_chat_message_contents(history, execution_settings, kernel=kernel)
    analysis = str(response[0])
    results["analysis"] = analysis
    logger.info("pipeline.step.done", step="analyze", length=len(analysis))

    # Step 2 — Summarize
    logger.info("pipeline.step", step="summarize")
    history.add_assistant_message(analysis)
    history.add_user_message(SUMMARIZE_PROMPT.format(analysis=analysis))
    response = await chat.get_chat_message_contents(history, execution_settings, kernel=kernel)
    summary = str(response[0])
    results["summary"] = summary
    logger.info("pipeline.step.done", step="summarize", length=len(summary))

    # Step 3 — Review
    logger.info("pipeline.step", step="review")
    history.add_assistant_message(summary)
    history.add_user_message(REVIEW_PROMPT.format(analysis=analysis, summary=summary))
    response = await chat.get_chat_message_contents(history, execution_settings, kernel=kernel)
    review = str(response[0])
    results["review"] = review
    logger.info("pipeline.step.done", step="review", length=len(review))

    return results


async def main() -> None:
    settings = load_settings()
    logger.info("pipeline.start", framework="semantic-kernel", pattern="single-agent")

    results = await run_pipeline(SAMPLE_DOCUMENT, settings)
    print_pipeline_results(results["analysis"], results["summary"], results["review"])

    logger.info("pipeline.done", framework="semantic-kernel", pattern="single-agent")


if __name__ == "__main__":
    asyncio.run(main())
