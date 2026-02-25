"""Tests for benchmarks.run module (BenchmarkRun)."""

import json
import uuid

import pytest
from benchmarks.enums import Framework, Messaging, Scenario, Topology
from benchmarks.metrics import SubscriberMetrics
from benchmarks.run import BenchmarkRun
from benchmarks.segments import ChoreographySegments, FanInSegments


class TestBenchmarkRunDefaults:
    """Tests for BenchmarkRun default values."""

    def test_auto_generated_ids(self) -> None:
        run = BenchmarkRun()
        uuid.UUID(run.run_id)  # raises if invalid
        uuid.UUID(run.correlation_id)

    def test_unique_ids(self) -> None:
        a = BenchmarkRun()
        b = BenchmarkRun()
        assert a.run_id != b.run_id
        assert a.correlation_id != b.correlation_id

    def test_timestamp_is_iso_format(self) -> None:
        run = BenchmarkRun()
        from datetime import datetime

        datetime.fromisoformat(run.timestamp)  # raises if invalid

    def test_default_enums(self) -> None:
        run = BenchmarkRun()
        assert run.framework == Framework.SEMANTIC_KERNEL
        assert run.messaging == Messaging.NONE
        assert run.scenario == Scenario.SINGLE_AGENT
        assert run.topology == Topology.LINEAR

    def test_default_segments_and_derived(self) -> None:
        run = BenchmarkRun()
        assert run.segments.s3_analyzer_ttft_ms == 0.0
        assert run.derived.e2e_pipeline_ms == 0.0

    def test_pubsub_segments_default_none(self) -> None:
        run = BenchmarkRun()
        assert run.fan_out is None
        assert run.fan_in is None
        assert run.choreography is None


class TestComputeDerived:
    """Tests for the compute_derived() method."""

    def test_total_llm_time(self, sample_pipeline_run: BenchmarkRun) -> None:
        run = sample_pipeline_run
        expected = 800.0 + 600.0 + 400.0  # analyzer + summarizer + reviewer
        assert run.derived.total_llm_time_ms == pytest.approx(expected)

    def test_total_messaging_overhead(self, sample_pipeline_run: BenchmarkRun) -> None:
        run = sample_pipeline_run
        expected = 12.0 + 45.0 + 8.0 + 10.0 + 7.0  # s5+s6+s7+s9+s10
        assert run.derived.total_messaging_overhead_ms == pytest.approx(expected)

    def test_percentages(self, sample_pipeline_run: BenchmarkRun) -> None:
        run = sample_pipeline_run
        assert run.derived.e2e_pipeline_ms == 1900.0
        assert run.derived.messaging_overhead_pct > 0
        assert run.derived.llm_time_pct > 0
        assert run.derived.messaging_overhead_pct + run.derived.llm_time_pct < 100.0

    def test_framework_overhead(self, sample_pipeline_run: BenchmarkRun) -> None:
        run = sample_pipeline_run
        total = (
            run.derived.total_llm_time_ms
            + run.derived.total_messaging_overhead_ms
            + run.derived.total_framework_overhead_ms
        )
        assert total == pytest.approx(run.derived.e2e_pipeline_ms)

    def test_zero_e2e_no_percentages(self) -> None:
        """When e2e_pipeline_ms is 0, percentages stay 0 (no division by zero)."""
        run = BenchmarkRun()
        run.segments.s4_analyzer_llm_total_ms = 100.0
        run.compute_derived()
        assert run.derived.messaging_overhead_pct == 0.0
        assert run.derived.llm_time_pct == 0.0

    def test_fan_out_compute_triggered(self, sample_fanout_run: BenchmarkRun) -> None:
        run = sample_fanout_run
        run.compute_derived()
        assert run.fan_out is not None
        assert run.fan_out.fan_out_spread_ms > 0
        assert run.fan_out.parallel_efficiency > 0

    def test_fan_in_compute_triggered(self) -> None:
        run = BenchmarkRun()
        run.fan_in = FanInSegments(
            publishers=[
                SubscriberMetrics(subscriber_id="p1", total_ms=100.0),
                SubscriberMetrics(subscriber_id="p2", total_ms=200.0),
            ],
            first_message_received_ms=10.0,
            last_message_received_ms=50.0,
        )
        run.compute_derived()
        assert run.fan_in.fan_in_wait_ms == pytest.approx(40.0)

    def test_choreography_compute_triggered(self) -> None:
        run = BenchmarkRun()
        run.choreography = ChoreographySegments(
            hops=[{"routing_ms": 5.0}, {"routing_ms": 8.0}]
        )
        run.compute_derived()
        assert run.choreography.total_hops == 2
        assert run.choreography.cumulative_routing_ms == pytest.approx(13.0)


class TestToDict:
    """Tests for the to_dict() serialization method."""

    def test_returns_dict(self, sample_pipeline_run: BenchmarkRun) -> None:
        d = sample_pipeline_run.to_dict()
        assert isinstance(d, dict)

    def test_json_serializable(self, sample_pipeline_run: BenchmarkRun) -> None:
        d = sample_pipeline_run.to_dict()
        json_str = json.dumps(d, default=str)
        assert isinstance(json_str, str)

    def test_contains_expected_keys(self, sample_pipeline_run: BenchmarkRun) -> None:
        d = sample_pipeline_run.to_dict()
        assert "run_id" in d
        assert "framework" in d
        assert "messaging" in d
        assert "segments" in d
        assert "derived" in d
        assert "correlation_id" in d

    def test_segments_nested(self, sample_pipeline_run: BenchmarkRun) -> None:
        d = sample_pipeline_run.to_dict()
        assert d["segments"]["s3_analyzer_ttft_ms"] == 150.0
        assert d["segments"]["s4_analyzer_output_tokens"] == 200

    def test_roundtrip_preserves_values(self, sample_pipeline_run: BenchmarkRun) -> None:
        d = sample_pipeline_run.to_dict()
        json_str = json.dumps(d, default=str)
        loaded = json.loads(json_str)
        assert loaded["segments"]["s3_analyzer_ttft_ms"] == 150.0
