"""
BenchmarkRun — the top-level record for a single benchmark execution.

Composes metrics, segments, and enums into one serializable record.
Holds the compute_derived() logic for calculating summary metrics
from the raw segments of a linear pipeline run.
"""

from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from benchmarks.enums import Framework, Messaging, Scenario, Topology
from benchmarks.metrics import AgentStageMetrics, DerivedMetrics, MessagingMetrics
from benchmarks.segments import (
    ChoreographySegments,
    FanInSegments,
    FanOutSegments,
    PipelineSegments,
)


@dataclass
class BenchmarkRun:
    """Complete record of a single benchmark run."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    framework: Framework = Framework.SEMANTIC_KERNEL
    messaging: Messaging = Messaging.NONE
    scenario: Scenario = Scenario.SINGLE_AGENT
    topology: Topology = Topology.LINEAR
    concurrency: int = 1
    input_doc_hash: str = ""

    # Detailed stage metrics
    stages: list[AgentStageMetrics] = field(default_factory=list)

    # Messaging hop metrics
    messaging_hops: list[MessagingMetrics] = field(default_factory=list)

    # Linear pipeline segments
    segments: PipelineSegments = field(default_factory=PipelineSegments)

    # Pub/Sub and choreography segment views
    fan_out: FanOutSegments | None = None
    fan_in: FanInSegments | None = None
    choreography: ChoreographySegments | None = None

    # Calculated
    derived: DerivedMetrics = field(default_factory=DerivedMetrics)

    # Tracing
    trace_id: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error: str | None = None

    def compute_derived(self) -> None:
        """Calculate derived metrics from raw segments.

        For linear pipelines, aggregates from PipelineSegments.
        For pub/sub and choreography, delegates to the respective segment's compute().
        """
        # Linear pipeline derived metrics
        s = self.segments
        self.derived.total_llm_time_ms = (
            s.s4_analyzer_llm_total_ms
            + s.s8_summarizer_llm_total_ms
            + s.s11_reviewer_llm_total_ms
        )
        self.derived.total_messaging_overhead_ms = (
            s.s5_msg_send_ms
            + s.s6_msg_delivery_ms
            + s.s7_msg_receive_ms
            + s.s9_msg_send_ms
            + s.s10_msg_receive_ms
        )

        if self.derived.e2e_pipeline_ms > 0:
            self.derived.messaging_overhead_pct = (
                self.derived.total_messaging_overhead_ms
                / self.derived.e2e_pipeline_ms
                * 100
            )
            self.derived.llm_time_pct = (
                self.derived.total_llm_time_ms
                / self.derived.e2e_pipeline_ms
                * 100
            )
            self.derived.total_framework_overhead_ms = (
                self.derived.e2e_pipeline_ms
                - self.derived.total_llm_time_ms
                - self.derived.total_messaging_overhead_ms
            )

        # Pub/Sub and choreography derived metrics
        if self.fan_out is not None:
            self.fan_out.compute()
        if self.fan_in is not None:
            self.fan_in.compute()
        if self.choreography is not None:
            self.choreography.compute()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return dataclasses.asdict(self)
