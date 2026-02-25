"""Shared message contracts for inter-agent communication.

Modules:
- messages.py        — Core message dataclasses (TaskRequest, TaskResponse, Event, Heartbeat)
- prompts.py         — Shared prompt templates for all pipeline agents
- sample_document.py — Sample document fixture for demonstrations
"""

from contracts.messages import (
    AgentIdentity,
    Destination,
    Event,
    Heartbeat,
    MessageMetadata,
    MessageType,
    TaskConstraints,
    TaskRequest,
    TaskResponse,
    TaskStatus,
)
from contracts.prompts import (
    AGENT_INSTRUCTIONS,
    ANALYZE_PROMPT,
    ANALYZER_INSTRUCTIONS,
    ANALYZER_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    REVIEWER_INSTRUCTIONS,
    REVIEWER_SYSTEM_PROMPT,
    SINGLE_AGENT_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT,
    SUMMARIZER_INSTRUCTIONS,
    SUMMARIZER_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)
from contracts.sample_document import SAMPLE_DOCUMENT

__all__ = [
    "AGENT_INSTRUCTIONS",
    "ANALYZE_PROMPT",
    "ANALYZER_INSTRUCTIONS",
    "ANALYZER_SYSTEM_PROMPT",
    "AgentIdentity",
    "Destination",
    "Event",
    "Heartbeat",
    "MessageMetadata",
    "MessageType",
    "REVIEW_PROMPT",
    "REVIEWER_INSTRUCTIONS",
    "REVIEWER_SYSTEM_PROMPT",
    "SAMPLE_DOCUMENT",
    "SINGLE_AGENT_SYSTEM_PROMPT",
    "SUMMARIZE_PROMPT",
    "SUMMARIZER_INSTRUCTIONS",
    "SUMMARIZER_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "TaskConstraints",
    "TaskRequest",
    "TaskResponse",
    "TaskStatus",
]
