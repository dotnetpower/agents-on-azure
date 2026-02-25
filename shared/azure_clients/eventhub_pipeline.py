"""Event Hubs pipeline messaging helper.

Provides a convenient wrapper for multi-hub pipelines where each stage
publishes to / consumes from a different Event Hub.

Responsibility: Message send/receive coordination across multiple hubs.
Authentication is delegated to DefaultAzureCredential.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubConsumerClient, EventHubProducerClient
from azure.identity.aio import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class EventHubPipelineMessaging:
    """Wraps Event Hubs operations for a multi-stage agent pipeline.

    Unlike :class:`EventHubProducer`/:class:`EventHubConsumer` (single-hub),
    this class manages multiple hubs behind a single interface with
    ``send(hub_name, body)`` and ``receive_one(hub_name)`` semantics.
    """

    def __init__(self, namespace: str) -> None:
        self._namespace = namespace
        self._credential: DefaultAzureCredential | None = None
        self._producers: dict[str, EventHubProducerClient] = {}

    async def _get_credential(self) -> DefaultAzureCredential:
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    async def _get_producer(self, hub_name: str) -> EventHubProducerClient:
        if hub_name not in self._producers:
            credential = await self._get_credential()
            self._producers[hub_name] = EventHubProducerClient(
                fully_qualified_namespace=self._namespace,
                eventhub_name=hub_name,
                credential=credential,
            )
        return self._producers[hub_name]

    async def send(
        self,
        hub_name: str,
        body: dict[str, Any],
        partition_key: str | None = None,
    ) -> None:
        """Send a single JSON event to *hub_name*."""
        producer = await self._get_producer(hub_name)
        batch = await producer.create_batch(partition_key=partition_key)
        batch.add(EventData(json.dumps(body)))
        await producer.send_batch(batch)
        logger.info("eventhub.sent", hub=hub_name)

    async def receive_one(
        self,
        hub_name: str,
        consumer_group: str = "$Default",
        max_wait_time: float = 30.0,
    ) -> dict[str, Any] | None:
        """Receive a single event from partition 0 (simplified for demo)."""
        credential = await self._get_credential()
        consumer = EventHubConsumerClient(
            fully_qualified_namespace=self._namespace,
            eventhub_name=hub_name,
            consumer_group=consumer_group,
            credential=credential,
        )
        try:
            events = await consumer.receive_batch(
                partition_id="0",
                max_batch_size=1,
                max_wait_time=max_wait_time,
            )
            if events:
                body = json.loads(events[0].body_as_str())
                logger.info("eventhub.received", hub=hub_name)
                return body
            return None
        finally:
            await consumer.close()

    async def close(self) -> None:
        for producer in self._producers.values():
            await producer.close()
        self._producers.clear()
        if self._credential:
            await self._credential.close()
            self._credential = None
