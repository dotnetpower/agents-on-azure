"""MS Agent Framework multi-agent Event Hubs pipeline.

Three Azure AI Agents communicating via Event Hubs.
Each pipeline stage publishes results to a dedicated hub.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import DefaultAzureCredential
from azure_clients import EventHubPipelineMessaging
from contracts.prompts import (
    ANALYZE_PROMPT,
    ANALYZER_INSTRUCTIONS,
    REVIEW_PROMPT,
    REVIEWER_INSTRUCTIONS,
    SUMMARIZE_PROMPT,
    SUMMARIZER_INSTRUCTIONS,
)
from contracts.sample_document import SAMPLE_DOCUMENT
from utils.config import load_settings
from utils.output import print_pipeline_results

logger = structlog.get_logger(__name__)


async def _call_ai_agent(client: AgentsClient, agent_id: str, content: str) -> str:
    """Create a thread, send a message, run the agent, and return the response."""
    thread = await client.threads.create()
    await client.messages.create(thread_id=thread.id, role="user", content=content)
    run = await client.runs.create_and_process(thread_id=thread.id, agent_id=agent_id)
    if run.status != "completed":
        raise RuntimeError(f"Agent run failed: {run.status}")
    messages = await client.messages.list(thread_id=thread.id)
    for msg in messages.data:
        if msg.role == "assistant":
            result = msg.content[0].text.value if msg.content else ""
            await client.threads.delete(thread.id)
            return result
    await client.threads.delete(thread.id)
    return ""


async def main() -> None:
    settings = load_settings()
    messaging = EventHubPipelineMessaging(settings.azure_eventhub_namespace)
    credential = DefaultAzureCredential()
    cid = str(uuid.uuid4())

    logger.info("pipeline.start", framework="microsoft-agent-framework", pattern="multi-agent-eventhub")

    async with AgentsClient(endpoint=settings.azure_openai_endpoint, credential=credential) as client:
        analyzer = await client.create_agent(
            model=settings.azure_openai_model, name="analyzer", instructions=ANALYZER_INSTRUCTIONS,
        )
        summarizer = await client.create_agent(
            model=settings.azure_openai_model, name="summarizer", instructions=SUMMARIZER_INSTRUCTIONS,
        )
        reviewer = await client.create_agent(
            model=settings.azure_openai_model, name="reviewer", instructions=REVIEWER_INSTRUCTIONS,
        )

        try:
            # Stage 1: Analyzer
            await messaging.send(settings.eventhub_analysis, {
                "correlation_id": cid, "document": SAMPLE_DOCUMENT, "stage": "input",
            })
            msg = await messaging.receive_one(settings.eventhub_analysis)
            if msg:
                analysis = await _call_ai_agent(
                    client, analyzer.id, ANALYZE_PROMPT.format(document=msg["document"]),
                )
                # Stage 2: Summarizer
                await messaging.send(settings.eventhub_summary, {
                    "correlation_id": cid, "analysis": analysis, "stage": "analyzed",
                })

            msg = await messaging.receive_one(settings.eventhub_summary)
            if msg:
                summary = await _call_ai_agent(
                    client, summarizer.id, SUMMARIZE_PROMPT.format(analysis=msg["analysis"]),
                )
                # Stage 3: Reviewer
                await messaging.send(settings.eventhub_review, {
                    "correlation_id": cid, "analysis": msg["analysis"], "summary": summary, "stage": "summarized",
                })

            msg = await messaging.receive_one(settings.eventhub_review)
            if msg:
                review = await _call_ai_agent(
                    client, reviewer.id,
                    REVIEW_PROMPT.format(analysis=msg["analysis"], summary=msg["summary"]),
                )
                print_pipeline_results(msg["analysis"], msg["summary"], review)

        finally:
            await client.delete_agent(analyzer.id)
            await client.delete_agent(summarizer.id)
            await client.delete_agent(reviewer.id)

    await messaging.close()
    await credential.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
