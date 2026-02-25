"""
TTFT (Time To First Token) tracker.

Captures the latency from LLM API call initiation to the first streamed token,
total response time, and token generation rate. Works with any framework's
streaming interface through a simple start/on_token/finish protocol.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TTFTResult:
    """Result of a TTFT measurement."""

    ttft_ms: float = 0.0
    total_latency_ms: float = 0.0
    output_tokens: int = 0
    tokens_per_second: float = 0.0


class TTFTTracker:
    """Streaming callback that captures TTFT and token generation rate.

    Usage (Azure OpenAI direct)::

        tracker = TTFTTracker()
        tracker.start()
        async for chunk in client.chat.completions.create(..., stream=True):
            if chunk.choices[0].delta.content:
                tracker.on_token(chunk.choices[0].delta.content)
        result = tracker.finish()
        print(f"TTFT: {result.ttft_ms:.1f}ms")

    Usage (LangGraph / LangChain)::

        tracker = TTFTTracker()
        tracker.start()
        async for event in graph.astream_events(input, version="v2"):
            if event["event"] == "on_chat_model_stream":
                tracker.on_token(event["data"]["chunk"].content)
        result = tracker.finish()
    """

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._first_token_time: float | None = None
        self._token_count: int = 0
        self._finished: bool = False

    def start(self) -> None:
        """Mark the start of the LLM API call."""
        self._start_time = time.perf_counter()
        self._first_token_time = None
        self._token_count = 0
        self._finished = False

    def on_token(self, token: str) -> None:
        """Call for each streamed token."""
        if self._first_token_time is None:
            self._first_token_time = time.perf_counter()
        self._token_count += 1

    def finish(self) -> TTFTResult:
        """Finalize measurement and return results."""
        end = time.perf_counter()
        self._finished = True

        ttft = (
            (self._first_token_time - self._start_time) * 1000
            if self._first_token_time
            else 0.0
        )
        total = (end - self._start_time) * 1000
        gen_time = (
            (end - self._first_token_time) if self._first_token_time else 0.0
        )
        tps = self._token_count / gen_time if gen_time > 0 else 0.0

        return TTFTResult(
            ttft_ms=ttft,
            total_latency_ms=total,
            output_tokens=self._token_count,
            tokens_per_second=tps,
        )
