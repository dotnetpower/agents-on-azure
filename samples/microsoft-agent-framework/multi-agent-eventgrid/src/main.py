"""MS Agent Framework multi-agent Event Grid pipeline.

Three Azure AI Agents communicating via Event Grid + Storage Queues.
Events are published to Event Grid topics and received from Storage Queues.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import DefaultAzureCredential
from azure_clients import EventGridPipelineMessaging
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
    messaging = EventGridPipelineMessaging(
        eventgrid_endpoint=settings.azure_eventgrid_endpoint,
        storage_account_name=settings.azure_storage_account_name,
    )
    credential = DefaultAzureCredential()
    cid = str(uuid.uuid4())

    logger.info("pipeline.start", framework="microsoft-agent-framework", pattern="multi-agent-eventgrid")

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
            analysis = await _call_ai_agent(
                client, analyzer.id, ANALYZE_PROMPT.format(document=msg.get("document", "")),
            )

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
            summary = await _call_ai_agent(
                client, summarizer.id, SUMMARIZE_PROMPT.format(analysis=msg.get("analysis", "")),
            )

            # Stage 3: Publish summary for review
            await messaging.publish(
                event_type="Pipeline.ReviewRequest",
                subject=f"/pipeline/{cid}/review",
                data={
                    "correlation_id": cid, "analysis": analysis,
                    "summary": summary, "stage": "summarized",
                },
            )

            msg = await messaging.receive_one(settings.eventgrid_queue_reviewer)
            if not msg:
                logger.error("pipeline.timeout", stage="review-receive")
                return
            review = await _call_ai_agent(
                client, reviewer.id,
                REVIEW_PROMPT.format(analysis=msg.get("analysis", ""), summary=msg.get("summary", "")),
            )

            print_pipeline_results(analysis, summary, review)
            logger.info("pipeline.complete", correlation_id=cid)

        finally:
            await client.delete_agent(analyzer.id)
            await client.delete_agent(summarizer.id)
            await client.delete_agent(reviewer.id)

    await messaging.close()
    await credential.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
