"""Microsoft Agent Framework single-agent: document analysis-summary-review pipeline.

Uses Azure AI Agent Service (AgentsClient) with a single agent
performing three sequential tasks via thread messages.
"""

from __future__ import annotations

import asyncio

import structlog
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import DefaultAzureCredential
from contracts.prompts import AGENT_INSTRUCTIONS, ANALYZE_PROMPT, REVIEW_PROMPT, SUMMARIZE_PROMPT
from contracts.sample_document import SAMPLE_DOCUMENT
from utils.config import Settings, load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


async def _send_and_get_response(client: AgentsClient, agent_id: str, thread_id: str, content: str) -> str:
    """Send a message to a thread and run the agent to get a response."""
    await client.messages.create(thread_id=thread_id, role="user", content=content)

    run = await client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
    if run.status != "completed":
        raise RuntimeError(f"Agent run failed with status: {run.status}")

    messages = await client.messages.list(thread_id=thread_id)
    for msg in messages.data:
        if msg.role == "assistant":
            return msg.content[0].text.value if msg.content else ""
    return ""


async def run_pipeline(document: str, settings: Settings) -> dict[str, str]:
    """Execute the three-step pipeline using Azure AI Agent Service."""
    credential = DefaultAzureCredential()
    results: dict[str, str] = {}

    # Use AI Foundry endpoint if available, otherwise fall back to OpenAI endpoint
    endpoint = settings.azure_ai_foundry_endpoint or settings.azure_openai_endpoint

    async with AgentsClient(endpoint=endpoint, credential=credential) as client:
        agent = await client.create_agent(
            model=settings.azure_openai_model,
            name="document-processor",
            instructions=AGENT_INSTRUCTIONS,
        )
        logger.info("agent.created", agent_id=agent.id)

        thread = await client.threads.create()
        logger.info("thread.created", thread_id=thread.id)

        try:
            # Step 1 - Analyze
            logger.info("pipeline.step", step="analyze")
            analysis = await _send_and_get_response(
                client, agent.id, thread.id, ANALYZE_PROMPT.format(document=document),
            )
            results["analysis"] = analysis
            logger.info("pipeline.step.done", step="analyze", length=len(analysis))

            # Step 2 - Summarize
            logger.info("pipeline.step", step="summarize")
            summary = await _send_and_get_response(
                client, agent.id, thread.id, SUMMARIZE_PROMPT.format(analysis=analysis),
            )
            results["summary"] = summary
            logger.info("pipeline.step.done", step="summarize", length=len(summary))

            # Step 3 - Review
            logger.info("pipeline.step", step="review")
            review = await _send_and_get_response(
                client, agent.id, thread.id,
                REVIEW_PROMPT.format(analysis=analysis, summary=summary),
            )
            results["review"] = review
            logger.info("pipeline.step.done", step="review", length=len(review))

        finally:
            await client.threads.delete(thread.id)
            await client.delete_agent(agent.id)
            logger.info("cleanup.done")

    await credential.close()
    return results


async def main() -> None:
    settings = load_settings()
    logger.info("pipeline.start", framework="microsoft-agent-framework", pattern="single-agent")

    results = await run_pipeline(SAMPLE_DOCUMENT, settings)
    print_pipeline_results(results["analysis"], results["summary"], results["review"])

    logger.info("pipeline.done", framework="microsoft-agent-framework", pattern="single-agent")


if __name__ == "__main__":
    asyncio.run(main())
