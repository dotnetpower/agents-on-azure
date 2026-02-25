"""Tests for benchmarks.choreography_tracker module."""

import time

from benchmarks.choreography_tracker import ChoreographyTracker, HopResult


class TestHopResult:
    """Test HopResult dataclass."""

    def test_defaults(self) -> None:
        h = HopResult()
        assert h.hop_index == 0
        assert h.event_type == ""
        assert h.routing_ms == 0.0
        assert h.total_hop_ms == 0.0


class TestChoreographyTracker:
    """Test ChoreographyTracker."""

    def test_single_hop(self) -> None:
        ct = ChoreographyTracker()
        ct.start_hop("TaskSubmitted")
        ct.mark_event_published()
        time.sleep(0.005)
        ct.mark_event_received()
        ct.mark_agent_activated()
        hop = ct.finish_hop(processing_ms=100.0, ttft_ms=50.0)

        assert hop.event_type == "TaskSubmitted"
        assert hop.hop_index == 0
        assert hop.routing_ms >= 3  # ~5ms sleep
        assert hop.processing_ms == 100.0
        assert hop.ttft_ms == 50.0
        assert hop.total_hop_ms > 100.0  # routing + activation + processing

    def test_multiple_hops(self) -> None:
        ct = ChoreographyTracker()

        # Hop 0
        ct.start_hop("TaskSubmitted")
        ct.mark_event_published()
        time.sleep(0.005)
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=200.0)

        # Hop 1
        ct.start_hop("AnalysisDone")
        ct.mark_event_published()
        time.sleep(0.003)
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=150.0)

        # Hop 2
        ct.start_hop("SummaryDone")
        ct.mark_event_published()
        time.sleep(0.002)
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=100.0)

        hops = ct.hops
        assert len(hops) == 3
        assert hops[0].hop_index == 0
        assert hops[1].hop_index == 1
        assert hops[2].hop_index == 2
        assert hops[0].event_type == "TaskSubmitted"
        assert hops[2].event_type == "SummaryDone"

    def test_cumulative_routing(self) -> None:
        ct = ChoreographyTracker()

        ct.start_hop("A")
        ct.mark_event_published()
        time.sleep(0.005)
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=50.0)

        ct.start_hop("B")
        ct.mark_event_published()
        time.sleep(0.005)
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=50.0)

        assert ct.cumulative_routing_ms >= 6  # ~10ms total routing

    def test_total_choreography(self) -> None:
        ct = ChoreographyTracker()

        ct.start_hop("X")
        ct.mark_event_published()
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=100.0)

        ct.start_hop("Y")
        ct.mark_event_published()
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=200.0)

        total = ct.total_choreography_ms
        assert total >= 300.0  # At minimum the processing times

    def test_hops_returns_copy(self) -> None:
        ct = ChoreographyTracker()
        ct.start_hop("A")
        ct.mark_event_published()
        ct.mark_event_received()
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=100.0)

        hops_a = ct.hops
        hops_b = ct.hops
        assert hops_a is not hops_b  # Different list instances
        assert hops_a[0].event_type == hops_b[0].event_type

    def test_external_publish_ts(self) -> None:
        """Simulate receiving external publish timestamp (from CloudEvent extension)."""
        ct = ChoreographyTracker()
        ct.start_hop("External")
        external_ts = time.time_ns()
        time.sleep(0.01)
        routing = ct.mark_event_received(publish_ts_ns=external_ts)
        assert routing >= 5  # ~10ms
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=50.0)
        assert ct.hops[0].routing_ms >= 5

    def test_activation_latency(self) -> None:
        ct = ChoreographyTracker()
        ct.start_hop("Activate")
        ct.mark_event_published()
        ct.mark_event_received()
        time.sleep(0.01)  # Simulate activation delay
        ct.mark_agent_activated()
        ct.finish_hop(processing_ms=50.0)

        assert ct.hops[0].activation_ms >= 5  # ~10ms
