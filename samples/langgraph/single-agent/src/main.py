"""LangGraph single-agent: document analysis-summary-review pipeline.

Uses a StateGraph with three sequential nodes, each calling Azure OpenAI.
"""

from __future__ import annotations

import asyncio

import structlog
from agents.graph import PipelineState, create_pipeline_graph
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from contracts.sample_document import SAMPLE_DOCUMENT
from langchain_openai import AzureChatOpenAI
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


def _build_llm(settings: Settings) -> AzureChatOpenAI:
    """Create an AzureChatOpenAI instance with DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_model,
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview",
        temperature=0.7,
        max_tokens=2048,
    )


async def run_pipeline(document: str, settings: Settings) -> PipelineState:
    """Execute the LangGraph pipeline."""
    llm = _build_llm(settings)
    graph = create_pipeline_graph(llm)
    app = graph.compile()

    logger.info("pipeline.start", framework="langgraph", pattern="single-agent")

    initial_state: PipelineState = {
        "document": document,
        "analysis": "",
        "summary": "",
        "review": "",
    }

    result = await app.ainvoke(initial_state)
    logger.info("pipeline.done", framework="langgraph", pattern="single-agent")
    return result


async def main() -> None:
    settings = load_settings()
    result = await run_pipeline(SAMPLE_DOCUMENT, settings)
    print_pipeline_results(result["analysis"], result["summary"], result["review"])


if __name__ == "__main__":
    asyncio.run(main())
