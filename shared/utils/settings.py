"""Application settings schema.

Responsibility: Define the Settings dataclass only. No I/O or parsing logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    """Typed settings loaded from environment variables."""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_model: str = "gpt-4o"

    # Azure AI Foundry (for Microsoft Agent Framework)
    azure_ai_foundry_endpoint: str = ""

    # Azure Service Bus
    azure_servicebus_namespace: str = ""
    servicebus_queue_analyzer: str = "analyzer-tasks"
    servicebus_queue_summarizer: str = "summarizer-tasks"
    servicebus_queue_reviewer: str = "reviewer-tasks"
    servicebus_queue_results: str = "pipeline-results"

    # Azure Event Hubs
    azure_eventhub_namespace: str = ""
    azure_eventhub_name: str = "agent-events"
    eventhub_analysis: str = "analysis-results"
    eventhub_summary: str = "summary-results"
    eventhub_review: str = "review-results"

    # Azure Event Grid
    azure_eventgrid_endpoint: str = ""

    # Storage
    azure_storage_account_name: str = ""

    # Observability
    applicationinsights_connection_string: str = ""

    # Event Grid queue destinations
    eventgrid_queue_analyzer: str = "analyzer-events"
    eventgrid_queue_summarizer: str = "summarizer-events"
    eventgrid_queue_reviewer: str = "reviewer-events"
    eventgrid_queue_results: str = "results-events"
