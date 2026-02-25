"""
Enumeration types for benchmark configuration.

Defines the categorical dimensions of each benchmark run:
framework, messaging service, topology, and scenario.
"""

from enum import Enum


class Framework(str, Enum):
    """Supported AI agent frameworks."""

    MICROSOFT_AGENT_FRAMEWORK = "microsoft-agent-framework"
    LANGGRAPH = "langgraph"
    SEMANTIC_KERNEL = "semantic-kernel"
    AUTOGEN = "autogen"


class Messaging(str, Enum):
    """Azure messaging services used for inter-agent communication."""

    NONE = "none"  # single-agent baseline
    SERVICE_BUS = "servicebus"
    EVENT_HUBS = "eventhubs"
    EVENT_GRID = "eventgrid"


class Topology(str, Enum):
    """Communication topology between agents."""

    LINEAR = "linear"  # point-to-point pipeline
    FAN_OUT = "fan-out"  # pub/sub: 1 publisher → N subscribers
    FAN_IN = "fan-in"  # pub/sub: N publishers → 1 collector
    CHOREOGRAPHY = "choreography"  # event-driven chain (no orchestrator)


class Scenario(str, Enum):
    """Test scenario type."""

    SINGLE_AGENT = "single-agent"
    MULTI_AGENT_PIPELINE = "multi-agent-pipeline"
    PUBSUB_FAN_OUT = "pubsub-fan-out"
    PUBSUB_FAN_IN = "pubsub-fan-in"
    CHOREOGRAPHY = "choreography"
    CONCURRENT_LOAD = "concurrent-load"
    RESILIENCY = "resiliency"
