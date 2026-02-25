"""
Atomic metric data structures.

Each dataclass represents metrics for a single concern:
LLM invocation, messaging hop, subscriber delivery, or agent stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LLMMetrics:
    """Metrics captured per LLM invocation (per agent stage)."""

    ttft_ms: float = 0.0  # Time to first token
    total_latency_ms: float = 0.0  # API call to full response
    output_tokens: int = 0
    input_tokens: int = 0
    tokens_per_second: float = 0.0  # Output tokens / generation time (after TTFT)
    prompt_build_ms: float = 0.0  # Time to construct the prompt


@dataclass
class MessagingMetrics:
    """Metrics captured per messaging hop between agents."""

    send_ms: float = 0.0  # Time to publish message
    delivery_ms: float = 0.0  # In-transit time (send timestamp → receive timestamp)
    receive_ms: float = 0.0  # Time to dequeue/pull message
    total_ms: float = 0.0  # send + delivery + receive
    retry_count: int = 0
    subscriber_id: str = ""  # Identifier for fan-out subscriber (empty for P2P)


@dataclass
class SubscriberMetrics:
    """Metrics for a single subscriber in a fan-out or publisher in a fan-in pattern."""

    subscriber_id: str = ""  # e.g., "summarizer", "translator", "sentiment"
    delivery_ms: float = 0.0  # Time from publish to this subscriber receiving
    receive_ms: float = 0.0  # Dequeue time
    agent_processing_ms: float = 0.0  # Agent total (including LLM)
    llm: LLMMetrics = field(default_factory=LLMMetrics)
    total_ms: float = 0.0  # delivery + receive + processing


@dataclass
class AgentStageMetrics:
    """Combined metrics for a single agent stage (e.g., Analyzer)."""

    stage_name: str = ""  # "analyzer", "summarizer", "reviewer"
    agent_total_ms: float = 0.0  # Total stage processing time
    llm: LLMMetrics = field(default_factory=LLMMetrics)
    framework_overhead_ms: float = 0.0  # agent_total - llm.total_latency


@dataclass
class DerivedMetrics:
    """Calculated summary metrics derived from raw segments."""

    e2e_pipeline_ms: float = 0.0
    total_messaging_overhead_ms: float = 0.0
    total_llm_time_ms: float = 0.0
    total_framework_overhead_ms: float = 0.0
    messaging_overhead_pct: float = 0.0  # messaging / e2e * 100
    llm_time_pct: float = 0.0  # llm / e2e * 100
