"""Shared benchmarks package for performance measurement.

Module structure (SRP):
- enums.py           — Framework, Messaging, Topology, Scenario enums
- metrics.py         — LLMMetrics, MessagingMetrics, SubscriberMetrics, AgentStageMetrics, DerivedMetrics
- segments.py        — PipelineSegments, FanOutSegments, FanInSegments, ChoreographySegments
- run.py             — BenchmarkRun (top-level record)
- timer_utils.py     — High-resolution timer, stamp_ns, delivery_latency_ms
- ttft.py            — TTFTTracker, TTFTResult
- fanout_tracker.py  — FanOutTracker, FanOutDeliveryResult
- choreography_tracker.py — ChoreographyTracker, HopResult
- collector.py       — Results aggregation & JSON export
- report.py          — Comparison report generator
"""

# Enums
# Choreography tracker
from benchmarks.choreography_tracker import ChoreographyTracker, HopResult

# Collector
from benchmarks.collector import AggregateStats, BenchmarkCollector
from benchmarks.enums import Framework, Messaging, Scenario, Topology

# Fan-out tracker
from benchmarks.fanout_tracker import FanOutDeliveryResult, FanOutTracker

# Metric data structures
from benchmarks.metrics import (
    AgentStageMetrics,
    DerivedMetrics,
    LLMMetrics,
    MessagingMetrics,
    SubscriberMetrics,
)

# Report
from benchmarks.report import ReportGenerator

# Top-level run record
from benchmarks.run import BenchmarkRun

# Segment data structures
from benchmarks.segments import (
    ChoreographySegments,
    FanInSegments,
    FanOutSegments,
    PipelineSegments,
)

# Timer utilities
from benchmarks.timer_utils import TimerResult, delivery_latency_ms, stamp_ns, timer

# TTFT tracker
from benchmarks.ttft import TTFTResult, TTFTTracker

__all__ = [
    # Enums
    "Framework",
    "Messaging",
    "Scenario",
    "Topology",
    # Metrics
    "AgentStageMetrics",
    "DerivedMetrics",
    "LLMMetrics",
    "MessagingMetrics",
    "SubscriberMetrics",
    # Segments
    "ChoreographySegments",
    "FanInSegments",
    "FanOutSegments",
    "PipelineSegments",
    # Run
    "BenchmarkRun",
    # Timer
    "TimerResult",
    "delivery_latency_ms",
    "stamp_ns",
    "timer",
    # TTFT
    "TTFTResult",
    "TTFTTracker",
    # Fan-out
    "FanOutDeliveryResult",
    "FanOutTracker",
    # Choreography
    "ChoreographyTracker",
    "HopResult",
    # Collector
    "AggregateStats",
    "BenchmarkCollector",
    # Report
    "ReportGenerator",
]
