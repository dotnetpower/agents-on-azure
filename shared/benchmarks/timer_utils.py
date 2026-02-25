"""
High-resolution timer and timestamp utilities.

Provides a context manager for precise elapsed-time measurement
and nanosecond-precision helpers for cross-process latency calculation.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


@dataclass
class TimerResult:
    """Result holder for the timer context manager."""

    elapsed_ms: float = 0.0
    label: str = ""


@contextmanager
def timer(label: str = "") -> Generator[TimerResult, None, None]:
    """Context manager for high-resolution timing.

    Usage::

        with timer("analyzer_llm") as t:
            result = await llm.invoke(prompt)
        print(f"{t.label}: {t.elapsed_ms:.2f}ms")
    """
    result = TimerResult(label=label)
    start = time.perf_counter()
    try:
        yield result
    finally:
        result.elapsed_ms = (time.perf_counter() - start) * 1000


def stamp_ns() -> int:
    """Return current time as nanoseconds since epoch.

    Embed this value in messaging headers for cross-process latency calculation.
    """
    return time.time_ns()


def delivery_latency_ms(send_ts_ns: int) -> float:
    """Calculate delivery latency from a nanosecond send timestamp.

    Args:
        send_ts_ns: Nanosecond epoch timestamp recorded at send time.

    Returns:
        Latency in milliseconds.
    """
    return (time.time_ns() - send_ts_ns) / 1_000_000
