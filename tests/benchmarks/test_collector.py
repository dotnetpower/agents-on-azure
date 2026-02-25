"""Tests for benchmarks.collector module."""

import json
import tempfile

import pytest
from benchmarks.collector import AggregateStats, BenchmarkCollector
from benchmarks.enums import Framework, Messaging, Topology
from benchmarks.run import BenchmarkRun


class TestAggregateStats:
    """Test AggregateStats."""

    def test_from_empty_values(self) -> None:
        stats = AggregateStats.from_values("empty", [])
        assert stats.count == 0
        assert stats.mean == 0.0
        assert stats.metric_name == "empty"

    def test_from_single_value(self) -> None:
        stats = AggregateStats.from_values("single", [42.0])
        assert stats.count == 1
        assert stats.mean == 42.0
        assert stats.median == 42.0
        assert stats.min == 42.0
        assert stats.max == 42.0
        assert stats.std_dev == 0.0  # stdev of 1 element

    def test_from_multiple_values(self) -> None:
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = AggregateStats.from_values("multi", values)
        assert stats.count == 5
        assert stats.mean == pytest.approx(30.0)
        assert stats.median == pytest.approx(30.0)
        assert stats.min == 10.0
        assert stats.max == 50.0
        assert stats.std_dev > 0

    def test_percentiles(self) -> None:
        values = list(range(1, 101))  # 1..100
        stats = AggregateStats.from_values("pct", [float(v) for v in values])
        assert stats.count == 100
        assert stats.p50 == pytest.approx(51.0)  # index 50
        assert stats.p95 == pytest.approx(96.0)  # index 95
        assert stats.p99 == pytest.approx(100.0)  # index 99

    def test_percentiles_small_set(self) -> None:
        """P95/P99 should not go out of bounds for small datasets."""
        stats = AggregateStats.from_values("small", [1.0, 2.0, 3.0])
        assert stats.p95 == 3.0
        assert stats.p99 == 3.0


class TestBenchmarkCollector:
    """Test BenchmarkCollector."""

    def test_add_and_runs(self) -> None:
        collector = BenchmarkCollector()
        run = BenchmarkRun()
        collector.add(run)
        assert len(collector.runs) == 1

    def test_runs_returns_copy(self) -> None:
        collector = BenchmarkCollector()
        collector.add(BenchmarkRun())
        runs_a = collector.runs
        runs_b = collector.runs
        assert runs_a is not runs_b

    def test_aggregate_single_metric(self) -> None:
        collector = BenchmarkCollector()
        for v in [100.0, 150.0, 200.0]:
            run = BenchmarkRun()
            run.segments.s3_analyzer_ttft_ms = v
            collector.add(run)

        stats = collector.aggregate("segments.s3_analyzer_ttft_ms")
        assert stats.count == 3
        assert stats.mean == pytest.approx(150.0)
        assert stats.min == 100.0
        assert stats.max == 200.0

    def test_aggregate_derived_metric(self, sample_pipeline_run: BenchmarkRun) -> None:
        collector = BenchmarkCollector()
        collector.add(sample_pipeline_run)
        stats = collector.aggregate("derived.total_llm_time_ms")
        assert stats.count == 1
        assert stats.mean == pytest.approx(1800.0)  # 800+600+400

    def test_aggregate_nonexistent_metric(self) -> None:
        collector = BenchmarkCollector()
        collector.add(BenchmarkRun())
        stats = collector.aggregate("segments.nonexistent_field")
        assert stats.count == 0

    def test_aggregate_all_segments(self, sample_pipeline_run: BenchmarkRun) -> None:
        collector = BenchmarkCollector()
        collector.add(sample_pipeline_run)
        all_stats = collector.aggregate_all_segments()

        assert "segments.s3_analyzer_ttft_ms" in all_stats
        assert "segments.s4_analyzer_llm_total_ms" in all_stats
        assert all_stats["segments.s3_analyzer_ttft_ms"].mean == pytest.approx(150.0)

    def test_aggregate_all_segments_empty(self) -> None:
        collector = BenchmarkCollector()
        assert collector.aggregate_all_segments() == {}

    def test_flush_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            run = BenchmarkRun()
            run.framework = Framework.AUTOGEN
            run.messaging = Messaging.EVENT_GRID
            run.topology = Topology.CHOREOGRAPHY
            collector.add(run)

            path = collector.flush()
            assert path.exists()
            assert path.suffix == ".jsonl"

            # Verify JSONL content
            lines = path.read_text().strip().split("\n")
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["framework"] == "autogen"
            assert data["messaging"] == "eventgrid"

    def test_flush_clears_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            collector.add(BenchmarkRun())
            assert len(collector.runs) == 1
            collector.flush()
            assert len(collector.runs) == 0

    def test_flush_auto_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            run = BenchmarkRun()
            run.framework = Framework.LANGGRAPH
            run.messaging = Messaging.SERVICE_BUS
            run.topology = Topology.LINEAR
            collector.add(run)
            path = collector.flush()
            assert path.name == "langgraph-servicebus-linear.jsonl"

    def test_flush_custom_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            collector.add(BenchmarkRun())
            path = collector.flush(filename="custom.jsonl")
            assert path.name == "custom.jsonl"

    def test_flush_empty_collector(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            path = collector.flush()
            assert path.name == "benchmark-results.jsonl"

    def test_flush_appends(self) -> None:
        """Multiple flushes should append to the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)

            run1 = BenchmarkRun()
            run1.framework = Framework.LANGGRAPH
            run1.messaging = Messaging.SERVICE_BUS
            run1.topology = Topology.LINEAR
            collector.add(run1)
            path = collector.flush()

            run2 = BenchmarkRun()
            run2.framework = Framework.LANGGRAPH
            run2.messaging = Messaging.SERVICE_BUS
            run2.topology = Topology.LINEAR
            collector.add(run2)
            collector.flush()

            lines = path.read_text().strip().split("\n")
            assert len(lines) == 2

    def test_to_summary_dict(self, sample_pipeline_run: BenchmarkRun) -> None:
        collector = BenchmarkCollector()
        collector.add(sample_pipeline_run)
        summary = collector.to_summary_dict()
        assert isinstance(summary, dict)
        assert len(summary) > 0
        for name, stats in summary.items():
            assert "mean" in stats
            assert "count" in stats

    def test_multiple_runs_aggregation(self, multiple_runs: list[BenchmarkRun]) -> None:
        collector = BenchmarkCollector()
        for run in multiple_runs:
            collector.add(run)

        stats = collector.aggregate("segments.s3_analyzer_ttft_ms")
        assert stats.count == 30
        assert stats.mean > 0
        assert stats.std_dev > 0
        assert stats.p95 >= stats.median
        assert stats.p99 >= stats.p95
        assert stats.min <= stats.mean <= stats.max
