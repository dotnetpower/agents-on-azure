"""Core message dataclasses for inter-agent communication.

All agents exchange messages conforming to these standard schemas,
regardless of the underlying Azure messaging service.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Types of messages exchanged between agents."""

    TASK_REQUEST = "TaskRequest"
    TASK_RESPONSE = "TaskResponse"
    EVENT = "Event"
    HEARTBEAT = "Heartbeat"


class TaskStatus(str, Enum):
    """Status of a task response."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass(frozen=True)
class AgentIdentity:
    """Identifies the source agent."""

    agent_id: str
    framework: str
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class Destination:
    """Target destination for a message."""

    agent_id: str
    queue: str = ""


@dataclass(frozen=True)
class TaskConstraints:
    """Constraints applied to a task request."""

    timeout_seconds: int = 300
    max_retries: int = 3
    priority: str = "medium"  # high | medium | low


@dataclass(frozen=True)
class MessageMetadata:
    """Distributed tracing and versioning metadata."""

    trace_id: str = ""
    span_id: str = ""
    version: str = "1.0"


@dataclass
class TaskRequest:
    """Request message sent from one agent to another to perform a task."""

    source: AgentIdentity
    destination: Destination
    task_type: str  # analyze | summarize | review
    input_data: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    constraints: TaskConstraints = field(default_factory=TaskConstraints)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_type: str = MessageType.TASK_REQUEST.value
    metadata: MessageMetadata = field(default_factory=MessageMetadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskRequest:
        return cls(
            source=AgentIdentity(**data["source"]),
            destination=Destination(**data["destination"]),
            task_type=data["task_type"],
            input_data=data.get("input_data", {}),
            context=data.get("context", {}),
            constraints=TaskConstraints(**data.get("constraints", {})),
            message_id=data.get("message_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            message_type=data.get("message_type", MessageType.TASK_REQUEST.value),
            metadata=MessageMetadata(**data.get("metadata", {})),
        )


@dataclass
class TaskResponse:
    """Response message returned after a task completes."""

    source: AgentIdentity
    destination: Destination
    task_type: str
    status: str = TaskStatus.SUCCESS.value
    output_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_type: str = MessageType.TASK_RESPONSE.value
    metadata: MessageMetadata = field(default_factory=MessageMetadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskResponse:
        return cls(
            source=AgentIdentity(**data["source"]),
            destination=Destination(**data["destination"]),
            task_type=data["task_type"],
            status=data.get("status", TaskStatus.SUCCESS.value),
            output_data=data.get("output_data", {}),
            error=data.get("error"),
            message_id=data.get("message_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            message_type=data.get("message_type", MessageType.TASK_RESPONSE.value),
            metadata=MessageMetadata(**data.get("metadata", {})),
        )


@dataclass
class Event:
    """Event notification message for choreography patterns."""

    source: AgentIdentity
    event_type: str  # e.g., AnalysisCompleted, SummaryCompleted
    data: dict[str, Any] = field(default_factory=dict)
    subject: str = ""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_type: str = MessageType.EVENT.value
    metadata: MessageMetadata = field(default_factory=MessageMetadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            source=AgentIdentity(**data["source"]),
            event_type=data["event_type"],
            data=data.get("data", {}),
            subject=data.get("subject", ""),
            message_id=data.get("message_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            message_type=data.get("message_type", MessageType.EVENT.value),
            metadata=MessageMetadata(**data.get("metadata", {})),
        )


@dataclass
class Heartbeat:
    """Health check message from an agent."""

    source: AgentIdentity
    status: str = "alive"  # alive | degraded | shutting_down
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_type: str = MessageType.HEARTBEAT.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Heartbeat:
        """Deserialize from dictionary."""
        return cls(
            source=AgentIdentity(**data["source"]),
            status=data.get("status", "alive"),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            message_type=data.get("message_type", MessageType.HEARTBEAT.value),
        )
