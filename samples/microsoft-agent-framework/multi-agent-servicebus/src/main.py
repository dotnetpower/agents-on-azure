"""MS Agent Framework multi-agent Service Bus pipeline.

Three Azure AI Agents communicating via Service Bus queues.
Each agent has its own thread and processes messages from its input queue.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import DefaultAzureCredential
from azure_clients import PipelineMessaging
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
    messaging = PipelineMessaging(settings.azure_servicebus_namespace)
    credential = DefaultAzureCredential()

    logger.info("pipeline.start", framework="microsoft-agent-framework", pattern="multi-agent-servicebus")

    async with AgentsClient(endpoint=settings.azure_openai_endpoint, credential=credential) as client:
        analyzer_agent = await client.create_agent(
            model=settings.azure_openai_model, name="analyzer", instructions=ANALYZER_INSTRUCTIONS,
        )
        summarizer_agent = await client.create_agent(
            model=settings.azure_openai_model, name="summarizer", instructions=SUMMARIZER_INSTRUCTIONS,
        )
        reviewer_agent = await client.create_agent(
            model=settings.azure_openai_model, name="reviewer", instructions=REVIEWER_INSTRUCTIONS,
        )

        try:
            correlation_id = str(uuid.uuid4())
            await messaging.send(settings.servicebus_queue_analyzer, {
                "correlation_id": correlation_id, "document": SAMPLE_DOCUMENT,
            })

            # Analyzer: read -> process -> forward
            msg = await messaging.receive_one(settings.servicebus_queue_analyzer, max_wait_time=30)
            if msg:
                analysis = await _call_ai_agent(
                    client, analyzer_agent.id,
                    ANALYZE_PROMPT.format(document=msg.get("document", "")),
                )
                await messaging.send(settings.servicebus_queue_summarizer, {
                    "correlation_id": msg.get("correlation_id", ""), "analysis": analysis,
                })

            # Summarizer: read -> process -> forward
            msg = await messaging.receive_one(settings.servicebus_queue_summarizer, max_wait_time=30)
            if msg:
                summary = await _call_ai_agent(
                    client, summarizer_agent.id,
                    SUMMARIZE_PROMPT.format(analysis=msg.get("analysis", "")),
                )
                await messaging.send(settings.servicebus_queue_reviewer, {
                    "correlation_id": msg.get("correlation_id", ""),
                    "analysis": msg.get("analysis", ""), "summary": summary,
                })

            # Reviewer: read -> process -> forward to results
            msg = await messaging.receive_one(settings.servicebus_queue_reviewer, max_wait_time=30)
            if msg:
                review = await _call_ai_agent(
                    client, reviewer_agent.id,
                    REVIEW_PROMPT.format(analysis=msg.get("analysis", ""), summary=msg.get("summary", "")),
                )
                await messaging.send(settings.servicebus_queue_results, {
                    "correlation_id": msg.get("correlation_id", ""),
                    "analysis": msg.get("analysis", ""),
                    "summary": msg.get("summary", ""),
                    "review": review,
                })

            # Collect result
            result = await messaging.receive_one(settings.servicebus_queue_results, max_wait_time=30)
            if result:
                print_pipeline_results(result.get("analysis", ""), result.get("summary", ""), result.get("review", ""))

        finally:
            await client.delete_agent(analyzer_agent.id)
            await client.delete_agent(summarizer_agent.id)
            await client.delete_agent(reviewer_agent.id)

    await messaging.close()
    await credential.close()
    logger.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
