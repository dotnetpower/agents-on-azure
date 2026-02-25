"""
Benchmark results collector.

Responsible for collecting BenchmarkRun records, persisting them as JSONL,
and computing aggregate statistics (mean, median, P50/P95/P99, std dev).
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from benchmarks.run import BenchmarkRun


@dataclass
class AggregateStats:
    """Statistical summary of a metric across multiple runs."""

    metric_name: str = ""
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min: float = 0.0
    max: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

    @classmethod
    def from_values(cls, name: str, values: list[float]) -> AggregateStats:
        """Compute aggregate statistics from a list of values."""
        if not values:
            return cls(metric_name=name)

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        return cls(
            metric_name=name,
            count=n,
            mean=statistics.mean(sorted_vals),
            median=statistics.median(sorted_vals),
            std_dev=statistics.stdev(sorted_vals) if n > 1 else 0.0,
            min=sorted_vals[0],
            max=sorted_vals[-1],
            p50=sorted_vals[int(n * 0.50)],
            p95=sorted_vals[min(int(n * 0.95), n - 1)],
            p99=sorted_vals[min(int(n * 0.99), n - 1)],
        )


class BenchmarkCollector:
    """Collect benchmark runs and persist/aggregate results.

    Usage::

        collector = BenchmarkCollector(output_dir="benchmarks/results/raw")

        for i in range(30):
            run = BenchmarkRun(framework=Framework.LANGGRAPH, ...)
            # ... populate segments ...
            run.compute_derived()
            collector.add(run)

        collector.flush()  # write all runs to JSONL

        stats = collector.aggregate("segments.s3_analyzer_ttft_ms")
        print(f"TTFT P95: {stats.p95:.1f}ms")
    """

    def __init__(self, output_dir: str | Path = "benchmarks/results/raw") -> None:
        self._output_dir = Path(output_dir)
        self._runs: list[BenchmarkRun] = []

    def add(self, run: BenchmarkRun) -> None:
        """Add a completed benchmark run."""
        self._runs.append(run)

    @property
    def runs(self) -> list[BenchmarkRun]:
        """All collected runs."""
        return list(self._runs)

    def flush(self, filename: str | None = None) -> Path:
        """Write all collected runs to a JSONL file.

        Args:
            filename: Output filename. Auto-generated if not provided.

        Returns:
            Path to the written file.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None and self._runs:
            first = self._runs[0]
            filename = f"{first.framework.value}-{first.messaging.value}-{first.topology.value}.jsonl"
        elif filename is None:
            filename = "benchmark-results.jsonl"

        filepath = self._output_dir / filename
        with open(filepath, "a", encoding="utf-8") as f:
            for run in self._runs:
                f.write(json.dumps(run.to_dict(), default=str, ensure_ascii=False) + "\n")

        written_count = len(self._runs)
        self._runs.clear()
        return filepath

    def aggregate(self, metric_path: str) -> AggregateStats:
        """Compute aggregate statistics for a specific metric.

        Args:
            metric_path: Dot-separated path to the metric field.
                         e.g., "segments.s3_analyzer_ttft_ms" or "derived.e2e_pipeline_ms"

        Returns:
            AggregateStats for the specified metric.
        """
        values = self._extract_metric(metric_path)
        return AggregateStats.from_values(metric_path, values)

    def aggregate_all_segments(self) -> dict[str, AggregateStats]:
        """Compute aggregate statistics for all PipelineSegments fields."""
        if not self._runs:
            return {}

        segment_fields = [
            f"segments.{f}" for f in vars(self._runs[0].segments) if not f.startswith("_")
        ]
        return {field: self.aggregate(field) for field in segment_fields}

    def _extract_metric(self, metric_path: str) -> list[float]:
        """Extract numeric values from all runs for a given metric path."""
        parts = metric_path.split(".")
        values: list[float] = []

        for run in self._runs:
            obj: Any = run
            try:
                for part in parts:
                    obj = getattr(obj, part)
                if isinstance(obj, (int, float)):
                    values.append(float(obj))
            except (AttributeError, TypeError):
                continue

        return values

    def to_summary_dict(self) -> dict[str, Any]:
        """Generate a summary dictionary of all segment aggregations."""
        stats = self.aggregate_all_segments()
        return {name: asdict(s) for name, s in stats.items()}
