"""Tests for benchmarks.ttft module."""

import time

from benchmarks.ttft import TTFTResult, TTFTTracker


class TestTTFTResult:
    """Test TTFTResult dataclass."""

    def test_defaults(self) -> None:
        r = TTFTResult()
        assert r.ttft_ms == 0.0
        assert r.total_latency_ms == 0.0
        assert r.output_tokens == 0
        assert r.tokens_per_second == 0.0


class TestTTFTTracker:
    """Test TTFTTracker."""

    def test_basic_flow(self) -> None:
        tracker = TTFTTracker()
        tracker.start()
        time.sleep(0.01)
        tracker.on_token("Hello")
        tracker.on_token(" world")
        time.sleep(0.01)
        result = tracker.finish()

        assert result.ttft_ms >= 5  # Should be ~10ms
        assert result.total_latency_ms >= result.ttft_ms
        assert result.output_tokens == 2

    def test_tokens_per_second(self) -> None:
        tracker = TTFTTracker()
        tracker.start()
        time.sleep(0.005)
        for i in range(10):
            tracker.on_token(f"token{i}")
        time.sleep(0.02)
        result = tracker.finish()

        assert result.output_tokens == 10
        assert result.tokens_per_second > 0

    def test_no_tokens(self) -> None:
        """Edge case: LLM returns no tokens."""
        tracker = TTFTTracker()
        tracker.start()
        time.sleep(0.005)
        result = tracker.finish()

        assert result.ttft_ms == 0.0  # No first token
        assert result.output_tokens == 0
        assert result.tokens_per_second == 0.0
        assert result.total_latency_ms > 0

    def test_single_token(self) -> None:
        tracker = TTFTTracker()
        tracker.start()
        tracker.on_token("only")
        result = tracker.finish()

        assert result.output_tokens == 1
        assert result.ttft_ms >= 0

    def test_reset_on_start(self) -> None:
        """Calling start() again resets internal state."""
        tracker = TTFTTracker()

        # First measurement
        tracker.start()
        tracker.on_token("a")
        r1 = tracker.finish()

        # Second measurement
        tracker.start()
        time.sleep(0.01)
        tracker.on_token("b")
        r2 = tracker.finish()

        assert r2.output_tokens == 1  # Reset, not accumulated
        assert r2.ttft_ms >= 5  # Should reflect the sleep

    def test_multiple_tokens_first_token_recorded_once(self) -> None:
        tracker = TTFTTracker()
        tracker.start()
        time.sleep(0.01)
        tracker.on_token("first")
        time.sleep(0.01)
        tracker.on_token("second")
        result = tracker.finish()

        # TTFT should capture the delay to the FIRST token only
        assert result.ttft_ms >= 5
        assert result.ttft_ms < result.total_latency_ms
