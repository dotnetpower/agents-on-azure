"""
Fan-out delivery tracker for pub/sub patterns.

Measures delivery latency across multiple subscribers when a single
publisher sends to a topic/hub, tracking spread and per-subscriber timing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class FanOutDeliveryResult:
    """Delivery result for a single subscriber."""

    subscriber_id: str = ""
    delivery_ms: float = 0.0
    receive_ms: float = 0.0


class FanOutTracker:
    """Track delivery times across multiple subscribers in a pub/sub fan-out.

    Usage::

        tracker = FanOutTracker()
        send_ts = tracker.mark_published()

        # Embed send_ts in message properties:
        #   msg.application_properties["bench_send_ts"] = str(send_ts)

        # In each subscriber process:
        tracker.mark_received("summarizer", send_ts_ns=int(props["bench_send_ts"]))
        tracker.mark_received("translator", send_ts_ns=int(props["bench_send_ts"]))

        spread = tracker.fan_out_spread_ms()
    """

    def __init__(self) -> None:
        self._publish_time_ns: int = 0
        self._deliveries: dict[str, int] = {}

    def mark_published(self) -> int:
        """Mark the publish time. Returns nanosecond timestamp to embed in message."""
        self._publish_time_ns = time.time_ns()
        return self._publish_time_ns

    def mark_received(self, subscriber_id: str, send_ts_ns: int | None = None) -> float:
        """Mark a subscriber's receive time.

        Args:
            subscriber_id: Unique identifier for this subscriber.
            send_ts_ns: Original send timestamp from message headers.
                        Falls back to self._publish_time_ns if not provided.

        Returns:
            Delivery latency in milliseconds.
        """
        receive_ns = time.time_ns()
        self._deliveries[subscriber_id] = receive_ns
        origin = send_ts_ns if send_ts_ns is not None else self._publish_time_ns
        return (receive_ns - origin) / 1_000_000

    def fan_out_spread_ms(self) -> float:
        """Difference between first and last subscriber delivery (ms)."""
        if len(self._deliveries) < 2:
            return 0.0
        times = list(self._deliveries.values())
        return (max(times) - min(times)) / 1_000_000

    def results(self) -> list[FanOutDeliveryResult]:
        """Get per-subscriber delivery results."""
        out: list[FanOutDeliveryResult] = []
        for sub_id, recv_ns in self._deliveries.items():
            delivery = (recv_ns - self._publish_time_ns) / 1_000_000
            out.append(FanOutDeliveryResult(subscriber_id=sub_id, delivery_ms=delivery))
        return out
