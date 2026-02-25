"""Tests for benchmarks.segments module."""

import pytest
from benchmarks.metrics import SubscriberMetrics
from benchmarks.segments import (
    ChoreographySegments,
    FanInSegments,
    FanOutSegments,
    PipelineSegments,
)


class TestPipelineSegments:
    """Tests for the PipelineSegments dataclass."""

    def test_all_defaults_are_zero(self) -> None:
        s = PipelineSegments()
        # All float fields should default to 0.0
        for attr_name in vars(s):
            val = getattr(s, attr_name)
            if isinstance(val, float):
                assert val == 0.0, f"{attr_name} should default to 0.0"
            elif isinstance(val, int):
                assert val == 0, f"{attr_name} should default to 0"

    def test_has_all_12_segment_groups(self) -> None:
        s = PipelineSegments()
        # Check key segment fields exist
        assert hasattr(s, "s1_request_submit_ms")
        assert hasattr(s, "s3_analyzer_ttft_ms")
        assert hasattr(s, "s5_msg_send_ms")
        assert hasattr(s, "s8_summarizer_ttft_ms")
        assert hasattr(s, "s11_reviewer_ttft_ms")
        assert hasattr(s, "s12_result_delivery_ms")

    def test_mutation(self) -> None:
        s = PipelineSegments()
        s.s3_analyzer_ttft_ms = 150.0
        s.s4_analyzer_output_tokens = 200
        assert s.s3_analyzer_ttft_ms == 150.0
        assert s.s4_analyzer_output_tokens == 200


class TestFanOutSegments:
    """Tests for the FanOutSegments dataclass."""

    def test_empty_subscribers(self) -> None:
        f = FanOutSegments()
        assert f.subscribers == []
        f.compute()
        assert f.fan_out_spread_ms == 0.0

    def test_compute_with_subscribers(self) -> None:
        subs = [
            SubscriberMetrics(subscriber_id="a", delivery_ms=10.0, total_ms=100.0),
            SubscriberMetrics(subscriber_id="b", delivery_ms=20.0, total_ms=200.0),
            SubscriberMetrics(subscriber_id="c", delivery_ms=15.0, total_ms=150.0),
        ]
        f = FanOutSegments(subscribers=subs, wall_clock_ms=250.0)
        f.compute()

        assert f.fan_out_spread_ms == pytest.approx(10.0)  # 20 - 10
        assert f.subscriber_skew_ms > 0  # std dev of deliveries
        assert 0 < f.parallel_efficiency <= 1.0  # wall_clock / sum(individual)

    def test_compute_parallel_efficiency(self) -> None:
        subs = [
            SubscriberMetrics(subscriber_id="a", delivery_ms=10.0, total_ms=500.0),
            SubscriberMetrics(subscriber_id="b", delivery_ms=12.0, total_ms=500.0),
        ]
        f = FanOutSegments(subscribers=subs, wall_clock_ms=500.0)
        f.compute()

        # wall_clock / total_individual = 500 / 1000 = 0.5
        assert f.parallel_efficiency == pytest.approx(0.5)

    def test_compute_single_subscriber_no_skew(self) -> None:
        subs = [SubscriberMetrics(subscriber_id="only", delivery_ms=10.0, total_ms=100.0)]
        f = FanOutSegments(subscribers=subs, wall_clock_ms=100.0)
        f.compute()

        assert f.fan_out_spread_ms == 0.0
        assert f.subscriber_skew_ms == 0.0


class TestFanInSegments:
    """Tests for the FanInSegments dataclass."""

    def test_defaults(self) -> None:
        fi = FanInSegments()
        assert fi.publishers == []
        assert fi.fan_in_wait_ms == 0.0

    def test_compute(self) -> None:
        pubs = [
            SubscriberMetrics(subscriber_id="p1", total_ms=100.0),
            SubscriberMetrics(subscriber_id="p2", total_ms=200.0),
            SubscriberMetrics(subscriber_id="p3", total_ms=150.0),
        ]
        fi = FanInSegments(
            publishers=pubs,
            first_message_received_ms=10.0,
            last_message_received_ms=50.0,
        )
        fi.compute()

        assert fi.fan_in_wait_ms == pytest.approx(40.0)  # 50 - 10
        mean_total = 150.0  # (100+200+150)/3
        assert fi.straggler_penalty_ms == pytest.approx(200.0 - mean_total)

    def test_compute_empty(self) -> None:
        fi = FanInSegments(first_message_received_ms=10.0, last_message_received_ms=10.0)
        fi.compute()
        assert fi.fan_in_wait_ms == 0.0
        assert fi.straggler_penalty_ms == 0.0


class TestChoreographySegments:
    """Tests for the ChoreographySegments dataclass."""

    def test_defaults(self) -> None:
        c = ChoreographySegments()
        assert c.hops == []
        assert c.total_hops == 0

    def test_compute(self) -> None:
        hops = [
            {"routing_ms": 5.0, "processing_ms": 100.0},
            {"routing_ms": 8.0, "processing_ms": 80.0},
            {"routing_ms": 3.0, "processing_ms": 120.0},
        ]
        c = ChoreographySegments(hops=hops)
        c.compute()

        assert c.total_hops == 3
        assert c.cumulative_routing_ms == pytest.approx(16.0)  # 5+8+3

    def test_compute_empty(self) -> None:
        c = ChoreographySegments()
        c.compute()
        assert c.total_hops == 0
        assert c.cumulative_routing_ms == 0.0
