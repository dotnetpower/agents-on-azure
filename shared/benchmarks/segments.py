"""
Segment data structures for each topology pattern.

Each dataclass holds the timing segments for one topology:
- PipelineSegments: linear point-to-point (S1–S12)
- FanOutSegments: pub/sub 1→N
- FanInSegments: pub/sub N→1
- ChoreographySegments: event-driven chain
"""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.metrics import SubscriberMetrics


@dataclass
class PipelineSegments:
    """All 12 measurable segments of a linear pipeline run."""

    # S1: Client request submission
    s1_request_submit_ms: float = 0.0

    # Analyzer stage
    s2_analyzer_prompt_build_ms: float = 0.0
    s3_analyzer_ttft_ms: float = 0.0
    s4_analyzer_llm_total_ms: float = 0.0
    s4_analyzer_output_tokens: int = 0
    s4_analyzer_tokens_per_sec: float = 0.0

    # Messaging: Analyzer → Summarizer
    s5_msg_send_ms: float = 0.0
    s6_msg_delivery_ms: float = 0.0
    s7_msg_receive_ms: float = 0.0

    # Summarizer stage
    s8_summarizer_ttft_ms: float = 0.0
    s8_summarizer_llm_total_ms: float = 0.0
    s8_summarizer_output_tokens: int = 0
    s8_summarizer_tokens_per_sec: float = 0.0

    # Messaging: Summarizer → Reviewer
    s9_msg_send_ms: float = 0.0
    s10_msg_receive_ms: float = 0.0

    # Reviewer stage
    s11_reviewer_ttft_ms: float = 0.0
    s11_reviewer_llm_total_ms: float = 0.0
    s11_reviewer_output_tokens: int = 0
    s11_reviewer_tokens_per_sec: float = 0.0

    # S12: Final result delivery
    s12_result_delivery_ms: float = 0.0


@dataclass
class FanOutSegments:
    """Segments for pub/sub fan-out pattern (1 publisher → N subscribers)."""

    # Publisher side
    pf1_publisher_prepare_ms: float = 0.0
    pf2_publish_latency_ms: float = 0.0

    # Per-subscriber delivery & processing
    subscribers: list[SubscriberMetrics] = field(default_factory=list)

    # Derived (populated by compute())
    fan_out_spread_ms: float = 0.0
    subscriber_skew_ms: float = 0.0
    wall_clock_ms: float = 0.0
    parallel_efficiency: float = 0.0

    def compute(self) -> None:
        """Calculate derived fan-out metrics from subscriber data."""
        if not self.subscribers:
            return
        deliveries = [s.delivery_ms for s in self.subscribers]
        self.fan_out_spread_ms = max(deliveries) - min(deliveries)
        if len(deliveries) > 1:
            mean = sum(deliveries) / len(deliveries)
            variance = sum((d - mean) ** 2 for d in deliveries) / len(deliveries)
            self.subscriber_skew_ms = variance ** 0.5
        total_individual = sum(s.total_ms for s in self.subscribers)
        if total_individual > 0:
            self.parallel_efficiency = self.wall_clock_ms / total_individual


@dataclass
class FanInSegments:
    """Segments for pub/sub fan-in pattern (N publishers → 1 collector)."""

    publishers: list[SubscriberMetrics] = field(default_factory=list)

    # Collector side
    first_message_received_ms: float = 0.0
    last_message_received_ms: float = 0.0
    fan_in_wait_ms: float = 0.0
    aggregation_processing_ms: float = 0.0
    straggler_penalty_ms: float = 0.0

    def compute(self) -> None:
        """Calculate derived fan-in metrics from publisher data."""
        self.fan_in_wait_ms = self.last_message_received_ms - self.first_message_received_ms
        if self.publishers:
            totals = [p.total_ms for p in self.publishers]
            mean_total = sum(totals) / len(totals)
            self.straggler_penalty_ms = max(totals) - mean_total


@dataclass
class ChoreographySegments:
    """Segments for event-driven choreography pattern (event chain)."""

    hops: list[dict[str, float]] = field(default_factory=list)

    cumulative_routing_ms: float = 0.0
    total_hops: int = 0
    e2e_choreography_ms: float = 0.0

    def compute(self) -> None:
        """Calculate derived choreography metrics from hop data."""
        self.total_hops = len(self.hops)
        self.cumulative_routing_ms = sum(h.get("routing_ms", 0) for h in self.hops)
