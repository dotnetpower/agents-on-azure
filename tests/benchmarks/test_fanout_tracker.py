"""Tests for benchmarks.fanout_tracker module."""

import time

from benchmarks.fanout_tracker import FanOutDeliveryResult, FanOutTracker


class TestFanOutDeliveryResult:
    """Test FanOutDeliveryResult dataclass."""

    def test_defaults(self) -> None:
        r = FanOutDeliveryResult()
        assert r.subscriber_id == ""
        assert r.delivery_ms == 0.0


class TestFanOutTracker:
    """Test FanOutTracker."""

    def test_publish_returns_timestamp(self) -> None:
        tracker = FanOutTracker()
        ts = tracker.mark_published()
        assert isinstance(ts, int)
        assert ts > 0

    def test_single_subscriber(self) -> None:
        tracker = FanOutTracker()
        send_ts = tracker.mark_published()
        time.sleep(0.01)
        latency = tracker.mark_received("sub-1", send_ts_ns=send_ts)

        assert latency >= 5
        results = tracker.results()
        assert len(results) == 1
        assert results[0].subscriber_id == "sub-1"
        assert results[0].delivery_ms >= 5

    def test_multiple_subscribers(self) -> None:
        tracker = FanOutTracker()
        send_ts = tracker.mark_published()
        time.sleep(0.005)
        tracker.mark_received("sub-1", send_ts_ns=send_ts)
        time.sleep(0.01)
        tracker.mark_received("sub-2", send_ts_ns=send_ts)
        time.sleep(0.005)
        tracker.mark_received("sub-3", send_ts_ns=send_ts)

        results = tracker.results()
        assert len(results) == 3
        ids = {r.subscriber_id for r in results}
        assert ids == {"sub-1", "sub-2", "sub-3"}

    def test_fan_out_spread(self) -> None:
        tracker = FanOutTracker()
        tracker.mark_published()
        time.sleep(0.005)
        tracker.mark_received("fast")
        time.sleep(0.015)
        tracker.mark_received("slow")

        spread = tracker.fan_out_spread_ms()
        assert spread >= 10  # At least ~15ms gap

    def test_spread_single_subscriber_is_zero(self) -> None:
        tracker = FanOutTracker()
        tracker.mark_published()
        tracker.mark_received("only")
        assert tracker.fan_out_spread_ms() == 0.0

    def test_spread_no_subscribers_is_zero(self) -> None:
        tracker = FanOutTracker()
        tracker.mark_published()
        assert tracker.fan_out_spread_ms() == 0.0

    def test_fallback_to_internal_publish_time(self) -> None:
        """When send_ts_ns is not provided, falls back to mark_published() time."""
        tracker = FanOutTracker()
        tracker.mark_published()
        time.sleep(0.01)
        latency = tracker.mark_received("sub-1")  # No explicit send_ts_ns
        assert latency >= 5

    def test_external_send_ts(self) -> None:
        """Simulate cross-process: manually provide a nanosecond send timestamp."""
        tracker = FanOutTracker()
        external_ts = time.time_ns()
        time.sleep(0.01)
        latency = tracker.mark_received("sub-1", send_ts_ns=external_ts)
        assert latency >= 5
