"""
Choreography hop tracker for event-driven chain patterns.

Tracks latency at each hop in an event-driven choreography where
agents are activated by events (e.g., Event Grid → Storage Queue polling).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class HopResult:
    """Timing result for a single choreography hop."""

    hop_index: int = 0
    event_type: str = ""
    publish_ms: float = 0.0
    routing_ms: float = 0.0
    activation_ms: float = 0.0
    processing_ms: float = 0.0
    ttft_ms: float = 0.0
    total_hop_ms: float = 0.0


class ChoreographyTracker:
    """Track latency across event-driven choreography hops.

    Usage::

        tracker = ChoreographyTracker()

        # Hop 1: TaskSubmitted → Analyzer
        tracker.start_hop("TaskSubmitted")
        publish_ts = tracker.mark_event_published()
        # ... event is routed through Event Grid ...
        tracker.mark_event_received(publish_ts_ns=publish_ts)
        tracker.mark_agent_activated()
        with timer("analyzer") as t:
            result = await analyzer.run(...)
        tracker.finish_hop(processing_ms=t.elapsed_ms, ttft_ms=ttft_result.ttft_ms)

        # Hop 2: AnalysisCompleted → Summarizer
        tracker.start_hop("AnalysisCompleted")
        ...
    """

    def __init__(self) -> None:
        self._hops: list[HopResult] = []
        self._current_hop: int = -1
        self._publish_ns: int = 0
        self._receive_ns: int = 0
        self._activate_ns: int = 0

    def start_hop(self, event_type: str) -> None:
        """Begin tracking a new hop."""
        self._current_hop += 1
        self._hops.append(HopResult(hop_index=self._current_hop, event_type=event_type))

    def mark_event_published(self) -> int:
        """Mark event publish time. Returns nanosecond timestamp for CloudEvent extensions."""
        self._publish_ns = time.time_ns()
        return self._publish_ns

    def mark_event_received(self, publish_ts_ns: int | None = None) -> float:
        """Mark when subscriber received the event.

        Args:
            publish_ts_ns: Original publish timestamp (from CloudEvent extension).
                           Falls back to internally tracked publish time.

        Returns:
            Routing latency in milliseconds.
        """
        self._receive_ns = time.time_ns()
        origin = publish_ts_ns if publish_ts_ns is not None else self._publish_ns
        routing = (self._receive_ns - origin) / 1_000_000
        if 0 <= self._current_hop < len(self._hops):
            self._hops[self._current_hop].routing_ms = routing
        return routing

    def mark_agent_activated(self) -> None:
        """Mark when the agent starts processing after receiving the event."""
        self._activate_ns = time.time_ns()
        if 0 <= self._current_hop < len(self._hops):
            self._hops[self._current_hop].activation_ms = (
                (self._activate_ns - self._receive_ns) / 1_000_000
            )

    def finish_hop(self, processing_ms: float, ttft_ms: float = 0.0) -> HopResult:
        """Finalize the current hop with processing time.

        Args:
            processing_ms: Total agent processing time (including LLM).
            ttft_ms: Time to first token for the LLM call in this hop.

        Returns:
            Completed HopResult.
        """
        hop = self._hops[self._current_hop]
        hop.processing_ms = processing_ms
        hop.ttft_ms = ttft_ms
        hop.total_hop_ms = hop.routing_ms + hop.activation_ms + hop.processing_ms
        return hop

    @property
    def hops(self) -> list[HopResult]:
        """All completed hops."""
        return list(self._hops)

    @property
    def cumulative_routing_ms(self) -> float:
        """Sum of all Event Grid routing latencies."""
        return sum(h.routing_ms for h in self._hops)

    @property
    def total_choreography_ms(self) -> float:
        """Total time across all hops."""
        return sum(h.total_hop_ms for h in self._hops)
