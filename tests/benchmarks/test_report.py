"""Tests for benchmarks.report module."""

import json
import tempfile
from pathlib import Path

import pytest
from benchmarks.enums import Framework, Messaging, Topology
from benchmarks.report import ReportGenerator
from benchmarks.run import BenchmarkRun


def _make_run(
    framework: Framework,
    messaging: Messaging,
    topology: Topology = Topology.LINEAR,
    ttft: float = 100.0,
    e2e: float = 1500.0,
) -> BenchmarkRun:
    """Helper to create a BenchmarkRun with specific values."""
    run = BenchmarkRun()
    run.framework = framework
    run.messaging = messaging
    run.topology = topology
    run.segments.s3_analyzer_ttft_ms = ttft
    run.derived.e2e_pipeline_ms = e2e
    run.compute_derived()
    return run


class TestReportGenerator:
    """Test ReportGenerator."""

    @pytest.fixture
    def populated_generator(self) -> ReportGenerator:
        """Generator with runs across multiple frameworks and messaging services."""
        gen = ReportGenerator()
        runs = [
            _make_run(Framework.LANGGRAPH, Messaging.SERVICE_BUS, ttft=120.0, e2e=1800.0),
            _make_run(Framework.LANGGRAPH, Messaging.SERVICE_BUS, ttft=130.0, e2e=1900.0),
            _make_run(Framework.LANGGRAPH, Messaging.SERVICE_BUS, ttft=125.0, e2e=1850.0),
            _make_run(Framework.SEMANTIC_KERNEL, Messaging.SERVICE_BUS, ttft=140.0, e2e=2000.0),
            _make_run(Framework.SEMANTIC_KERNEL, Messaging.SERVICE_BUS, ttft=145.0, e2e=2100.0),
            _make_run(Framework.LANGGRAPH, Messaging.EVENT_HUBS, ttft=135.0, e2e=1950.0),
            _make_run(Framework.LANGGRAPH, Messaging.EVENT_HUBS, ttft=128.0, e2e=1880.0),
            _make_run(Framework.AUTOGEN, Messaging.EVENT_GRID, ttft=110.0, e2e=1700.0),
            _make_run(Framework.AUTOGEN, Messaging.EVENT_GRID, ttft=115.0, e2e=1750.0),
        ]
        gen.add_runs(runs)
        return gen

    def test_add_runs(self) -> None:
        gen = ReportGenerator()
        runs = [BenchmarkRun(), BenchmarkRun()]
        gen.add_runs(runs)
        assert len(gen.filter_runs()) == 2

    def test_filter_by_framework(self, populated_generator: ReportGenerator) -> None:
        runs = populated_generator.filter_runs(framework=Framework.LANGGRAPH)
        assert len(runs) == 5  # 3 SB + 2 EH
        assert all(r.framework == Framework.LANGGRAPH for r in runs)

    def test_filter_by_messaging(self, populated_generator: ReportGenerator) -> None:
        runs = populated_generator.filter_runs(messaging=Messaging.SERVICE_BUS)
        assert len(runs) == 5  # 3 LG + 2 SK
        assert all(r.messaging == Messaging.SERVICE_BUS for r in runs)

    def test_filter_combined(self, populated_generator: ReportGenerator) -> None:
        runs = populated_generator.filter_runs(
            framework=Framework.LANGGRAPH, messaging=Messaging.SERVICE_BUS
        )
        assert len(runs) == 3

    def test_filter_no_match(self, populated_generator: ReportGenerator) -> None:
        runs = populated_generator.filter_runs(
            framework=Framework.MICROSOFT_AGENT_FRAMEWORK
        )
        assert len(runs) == 0

    def test_framework_comparison_report(self, populated_generator: ReportGenerator) -> None:
        report = populated_generator.framework_comparison_report(
            metric="segments.s3_analyzer_ttft_ms",
            label="Analyzer TTFT",
        )
        assert "## Analyzer TTFT — Framework Comparison" in report
        assert "| Framework |" in report
        assert "langgraph" in report
        assert "semantic-kernel" in report
        assert "autogen" in report

    def test_framework_comparison_with_filter(self, populated_generator: ReportGenerator) -> None:
        report = populated_generator.framework_comparison_report(
            metric="segments.s3_analyzer_ttft_ms",
            label="TTFT (SB only)",
            messaging=Messaging.SERVICE_BUS,
        )
        assert "langgraph" in report
        assert "semantic-kernel" in report
        # autogen uses Event Grid, not Service Bus
        assert "autogen" not in report

    def test_messaging_comparison_report(self, populated_generator: ReportGenerator) -> None:
        report = populated_generator.messaging_comparison_report(
            metric="segments.s3_analyzer_ttft_ms",
            label="TTFT by Messaging",
        )
        assert "## TTFT by Messaging — Messaging Comparison" in report
        assert "servicebus" in report
        assert "eventhubs" in report
        assert "eventgrid" in report
        # 'none' should be excluded
        assert "| none |" not in report

    def test_topology_comparison_report(self, populated_generator: ReportGenerator) -> None:
        report = populated_generator.topology_comparison_report(
            metric="segments.s3_analyzer_ttft_ms",
            label="TTFT by Topology",
        )
        assert "## TTFT by Topology — Topology Comparison" in report
        assert "linear" in report  # All test runs are LINEAR

    def test_e2e_heatmap_data(self, populated_generator: ReportGenerator) -> None:
        heatmap = populated_generator.e2e_heatmap_data()
        assert isinstance(heatmap, dict)
        assert "langgraph" in heatmap
        assert "servicebus" in heatmap["langgraph"]
        assert heatmap["langgraph"]["servicebus"] > 0

    def test_save_all_reports(self, populated_generator: ReportGenerator) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            saved = populated_generator.save_all_reports(tmpdir)
            assert len(saved) == 2  # comparison-report.md + e2e-heatmap.json

            report_path = Path(tmpdir) / "comparison-report.md"
            assert report_path.exists()
            content = report_path.read_text()
            assert "# Benchmark Comparison Report" in content
            assert "Framework Comparison" in content

            heatmap_path = Path(tmpdir) / "e2e-heatmap.json"
            assert heatmap_path.exists()
            heatmap = json.loads(heatmap_path.read_text())
            assert isinstance(heatmap, dict)


class TestLoadJsonl:
    """Test JSONL load/roundtrip."""

    def test_roundtrip(self) -> None:
        """Flush runs to JSONL, then load them back via ReportGenerator."""
        from benchmarks.collector import BenchmarkCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write
            collector = BenchmarkCollector(output_dir=tmpdir)
            run = _make_run(Framework.LANGGRAPH, Messaging.SERVICE_BUS, ttft=142.0, e2e=1850.0)
            collector.add(run)
            path = collector.flush()

            # Read
            gen = ReportGenerator()
            count = gen.load_jsonl(path)
            assert count == 1

            loaded = gen.filter_runs()
            assert len(loaded) == 1
            assert loaded[0].framework == Framework.LANGGRAPH
            assert loaded[0].segments.s3_analyzer_ttft_ms == pytest.approx(142.0)

    def test_roundtrip_multiple(self) -> None:
        from benchmarks.collector import BenchmarkCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            for i in range(5):
                collector.add(_make_run(Framework.AUTOGEN, Messaging.EVENT_GRID, ttft=100.0 + i))
            path = collector.flush()

            gen = ReportGenerator()
            count = gen.load_jsonl(path)
            assert count == 5

    def test_load_preserves_enums(self) -> None:
        from benchmarks.collector import BenchmarkCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = BenchmarkCollector(output_dir=tmpdir)
            collector.add(_make_run(Framework.SEMANTIC_KERNEL, Messaging.EVENT_HUBS))
            path = collector.flush()

            gen = ReportGenerator()
            gen.load_jsonl(path)
            loaded = gen.filter_runs()
            assert loaded[0].framework == Framework.SEMANTIC_KERNEL
            assert loaded[0].messaging == Messaging.EVENT_HUBS
            assert loaded[0].topology == Topology.LINEAR
