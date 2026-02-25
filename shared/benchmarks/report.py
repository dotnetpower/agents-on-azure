"""
Benchmark comparison report generator.

Reads aggregated benchmark results and produces comparison tables
in Markdown format, organized by framework, messaging service, and topology.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmarks.collector import BenchmarkCollector
from benchmarks.enums import Framework, Messaging, Topology
from benchmarks.run import BenchmarkRun


class ReportGenerator:
    """Generate comparison reports from benchmark runs.

    Usage::

        generator = ReportGenerator()

        # Load runs from multiple collectors or JSONL files
        generator.load_jsonl("benchmarks/results/raw/langgraph-servicebus-linear.jsonl")
        generator.load_jsonl("benchmarks/results/raw/semantic-kernel-servicebus-linear.jsonl")

        # Generate comparison report
        report = generator.framework_comparison_report(
            metric="segments.s3_analyzer_ttft_ms",
            label="Analyzer TTFT",
        )
        print(report)

        # Save all reports
        generator.save_all_reports("benchmarks/results/reports/")
    """

    def __init__(self) -> None:
        self._runs: list[BenchmarkRun] = []

    def add_runs(self, runs: list[BenchmarkRun]) -> None:
        """Add pre-loaded runs."""
        self._runs.extend(runs)

    def load_jsonl(self, filepath: str | Path) -> int:
        """Load benchmark runs from a JSONL file.

        Returns:
            Number of runs loaded.
        """
        path = Path(filepath)
        count = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                run = self._dict_to_run(data)
                self._runs.append(run)
                count += 1
        return count

    def filter_runs(
        self,
        framework: Framework | None = None,
        messaging: Messaging | None = None,
        topology: Topology | None = None,
    ) -> list[BenchmarkRun]:
        """Filter runs by dimensions."""
        result = self._runs
        if framework is not None:
            result = [r for r in result if r.framework == framework]
        if messaging is not None:
            result = [r for r in result if r.messaging == messaging]
        if topology is not None:
            result = [r for r in result if r.topology == topology]
        return result

    def framework_comparison_report(
        self,
        metric: str,
        label: str = "",
        messaging: Messaging | None = None,
        topology: Topology | None = None,
    ) -> str:
        """Generate a Markdown table comparing a metric across frameworks.

        Args:
            metric: Dot-separated metric path (e.g., "segments.s3_analyzer_ttft_ms").
            label: Human-readable label for the metric.
            messaging: Filter to specific messaging service.
            topology: Filter to specific topology.
        """
        label = label or metric
        lines = [
            f"## {label} — Framework Comparison",
            "",
            "| Framework | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Std Dev |",
            "|---|---:|---:|---:|---:|---:|",
        ]

        for fw in Framework:
            runs = self.filter_runs(framework=fw, messaging=messaging, topology=topology)
            if not runs:
                continue
            collector = BenchmarkCollector()
            for r in runs:
                collector.add(r)
            stats = collector.aggregate(metric)
            lines.append(
                f"| {fw.value} | {stats.mean:.1f} | {stats.median:.1f} "
                f"| {stats.p95:.1f} | {stats.p99:.1f} | {stats.std_dev:.1f} |"
            )

        return "\n".join(lines)

    def messaging_comparison_report(
        self,
        metric: str,
        label: str = "",
        framework: Framework | None = None,
        topology: Topology | None = None,
    ) -> str:
        """Generate a Markdown table comparing a metric across messaging services."""
        label = label or metric
        lines = [
            f"## {label} — Messaging Comparison",
            "",
            "| Messaging | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Std Dev |",
            "|---|---:|---:|---:|---:|---:|",
        ]

        for msg in Messaging:
            if msg == Messaging.NONE:
                continue
            runs = self.filter_runs(framework=framework, messaging=msg, topology=topology)
            if not runs:
                continue
            collector = BenchmarkCollector()
            for r in runs:
                collector.add(r)
            stats = collector.aggregate(metric)
            lines.append(
                f"| {msg.value} | {stats.mean:.1f} | {stats.median:.1f} "
                f"| {stats.p95:.1f} | {stats.p99:.1f} | {stats.std_dev:.1f} |"
            )

        return "\n".join(lines)

    def topology_comparison_report(
        self,
        metric: str,
        label: str = "",
        framework: Framework | None = None,
        messaging: Messaging | None = None,
    ) -> str:
        """Generate a Markdown table comparing a metric across topologies."""
        label = label or metric
        lines = [
            f"## {label} — Topology Comparison",
            "",
            "| Topology | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Std Dev |",
            "|---|---:|---:|---:|---:|---:|",
        ]

        for topo in Topology:
            runs = self.filter_runs(framework=framework, messaging=messaging, topology=topo)
            if not runs:
                continue
            collector = BenchmarkCollector()
            for r in runs:
                collector.add(r)
            stats = collector.aggregate(metric)
            lines.append(
                f"| {topo.value} | {stats.mean:.1f} | {stats.median:.1f} "
                f"| {stats.p95:.1f} | {stats.p99:.1f} | {stats.std_dev:.1f} |"
            )

        return "\n".join(lines)

    def e2e_heatmap_data(self) -> dict[str, dict[str, float]]:
        """Generate Framework × Messaging E2E latency matrix data.

        Returns:
            Nested dict: {framework: {messaging: mean_e2e_ms}}
        """
        matrix: dict[str, dict[str, float]] = {}
        for fw in Framework:
            matrix[fw.value] = {}
            for msg in Messaging:
                runs = self.filter_runs(framework=fw, messaging=msg)
                if not runs:
                    continue
                collector = BenchmarkCollector()
                for r in runs:
                    collector.add(r)
                stats = collector.aggregate("derived.e2e_pipeline_ms")
                matrix[fw.value][msg.value] = stats.mean
        return matrix

    def save_all_reports(self, output_dir: str | Path) -> list[Path]:
        """Generate and save all standard comparison reports.

        Returns:
            List of paths to generated report files.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        saved: list[Path] = []

        # Framework comparison for key metrics
        key_metrics = [
            ("segments.s3_analyzer_ttft_ms", "Analyzer TTFT"),
            ("derived.e2e_pipeline_ms", "End-to-End Pipeline Latency"),
            ("derived.total_messaging_overhead_ms", "Total Messaging Overhead"),
            ("derived.total_llm_time_ms", "Total LLM Time"),
        ]

        report_lines = ["# Benchmark Comparison Report\n"]
        for metric, label in key_metrics:
            report_lines.append(self.framework_comparison_report(metric, label))
            report_lines.append("")
            report_lines.append(self.messaging_comparison_report(metric, label))
            report_lines.append("")
            report_lines.append(self.topology_comparison_report(metric, label))
            report_lines.append("\n---\n")

        # E2E heatmap data
        heatmap = self.e2e_heatmap_data()
        report_lines.append("## E2E Latency Heatmap Data\n")
        report_lines.append("```json")
        report_lines.append(json.dumps(heatmap, indent=2))
        report_lines.append("```\n")

        report_path = out / "comparison-report.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        saved.append(report_path)

        # Raw heatmap JSON
        heatmap_path = out / "e2e-heatmap.json"
        heatmap_path.write_text(json.dumps(heatmap, indent=2), encoding="utf-8")
        saved.append(heatmap_path)

        return saved

    @staticmethod
    def _dict_to_run(data: dict[str, Any]) -> BenchmarkRun:
        """Reconstruct a BenchmarkRun from a dictionary (basic deserialization)."""
        run = BenchmarkRun()
        run.run_id = data.get("run_id", run.run_id)
        run.timestamp = data.get("timestamp", run.timestamp)
        run.concurrency = data.get("concurrency", 1)
        run.input_doc_hash = data.get("input_doc_hash", "")
        run.trace_id = data.get("trace_id", "")
        run.correlation_id = data.get("correlation_id", run.correlation_id)
        run.error = data.get("error")

        # Enums
        if "framework" in data:
            run.framework = Framework(data["framework"])
        if "messaging" in data:
            run.messaging = Messaging(data["messaging"])
        if "topology" in data:
            run.topology = Topology(data["topology"])

        # Segments (flat copy)
        if "segments" in data and isinstance(data["segments"], dict):
            for k, v in data["segments"].items():
                if hasattr(run.segments, k):
                    setattr(run.segments, k, v)

        # Derived
        if "derived" in data and isinstance(data["derived"], dict):
            for k, v in data["derived"].items():
                if hasattr(run.derived, k):
                    setattr(run.derived, k, v)

        return run
