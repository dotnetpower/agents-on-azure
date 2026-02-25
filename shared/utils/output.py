"""Pipeline result output formatter.

Responsibility: Format and display pipeline results only.
"""

from __future__ import annotations


def print_pipeline_results(
    analysis: str,
    summary: str,
    review: str,
    separator: str = "=",
    width: int = 80,
) -> None:
    """Print pipeline stage results with section headers."""
    for label, content in [("ANALYSIS", analysis), ("SUMMARY", summary), ("REVIEW", review)]:
        print(f"\n{separator * width}")
        print(label)
        print(separator * width)
        print(content)
