"""Tests for benchmarks.timer_utils module."""

import time

import pytest
from benchmarks.timer_utils import TimerResult, delivery_latency_ms, stamp_ns, timer


class TestTimerResult:
    """Tests for the TimerResult dataclass."""

    def test_defaults(self) -> None:
        r = TimerResult()
        assert r.elapsed_ms == 0.0
        assert r.label == ""

    def test_custom(self) -> None:
        r = TimerResult(elapsed_ms=42.5, label="test")
        assert r.elapsed_ms == 42.5
        assert r.label == "test"


class TestTimer:
    """Tests for the timer() context manager."""

    def test_measures_elapsed_time(self) -> None:
        with timer("sleep") as t:
            time.sleep(0.02)
        assert t.elapsed_ms >= 15.0  # at least 15ms (allowing some tolerance)
        assert t.elapsed_ms < 200.0  # but not absurdly long

    def test_label_preserved(self) -> None:
        with timer("my_label") as t:
            pass
        assert t.label == "my_label"

    def test_empty_label(self) -> None:
        with timer() as t:
            pass
        assert t.label == ""

    def test_elapsed_set_after_exit(self) -> None:
        with timer("op") as t:
            assert t.elapsed_ms == 0.0  # not set yet inside
        assert t.elapsed_ms > 0.0  # set after exiting

    def test_exception_still_records_time(self) -> None:
        with pytest.raises(ValueError):
            with timer("fail") as t:
                time.sleep(0.01)
                raise ValueError("boom")
        # Timer should still have recorded time despite exception
        assert t.elapsed_ms >= 5.0

    def test_nested_timers(self) -> None:
        with timer("outer") as outer:
            with timer("inner") as inner:
                time.sleep(0.01)
        assert inner.elapsed_ms > 0
        assert outer.elapsed_ms >= inner.elapsed_ms


class TestStampNs:
    """Tests for the stamp_ns() function."""

    def test_returns_int(self) -> None:
        ts = stamp_ns()
        assert isinstance(ts, int)

    def test_is_nanosecond_epoch(self) -> None:
        ts = stamp_ns()
        # Should be a reasonable epoch time (after 2020, before 2100)
        seconds = ts / 1_000_000_000
        assert 1577836800 < seconds < 4102444800  # 2020 to 2100

    def test_monotonically_increasing(self) -> None:
        a = stamp_ns()
        time.sleep(0.001)
        b = stamp_ns()
        assert b > a


class TestDeliveryLatencyMs:
    """Tests for the delivery_latency_ms() function."""

    def test_positive_latency(self) -> None:
        ts = stamp_ns()
        time.sleep(0.01)
        latency = delivery_latency_ms(ts)
        assert latency >= 5.0  # at least ~10ms with tolerance

    def test_near_zero_latency(self) -> None:
        ts = stamp_ns()
        latency = delivery_latency_ms(ts)
        assert 0.0 <= latency < 5.0  # should be very small

    def test_returns_float(self) -> None:
        ts = stamp_ns()
        latency = delivery_latency_ms(ts)
        assert isinstance(latency, float)
