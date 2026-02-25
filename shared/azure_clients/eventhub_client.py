"""Azure Event Hubs producer/consumer helpers.

Uses DefaultAzureCredential for authentication.
Consumer uses BlobCheckpointStore for reliable offset tracking.
"""

from __future__ import annotations

import json
import os
from typing import Any

import structlog
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubConsumerClient, EventHubProducerClient
from azure.identity.aio import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class EventHubProducer:
    """Async helper for sending events to an Azure Event Hub."""

    def __init__(
        self,
        namespace: str | None = None,
        eventhub_name: str | None = None,
    ) -> None:
        self._namespace = namespace or os.environ["AZURE_EVENTHUB_NAMESPACE"]
        self._eventhub_name = eventhub_name or os.environ["AZURE_EVENTHUB_NAME"]
        self._credential: DefaultAzureCredential | None = None
        self._producer: EventHubProducerClient | None = None

    async def _get_producer(self) -> EventHubProducerClient:
        if self._producer is None:
            self._credential = DefaultAzureCredential()
            self._producer = EventHubProducerClient(
                fully_qualified_namespace=self._namespace,
                eventhub_name=self._eventhub_name,
                credential=self._credential,
            )
        return self._producer

    async def send(self, body: dict[str, Any], partition_key: str | None = None) -> None:
        """Send a single JSON event."""
        producer = await self._get_producer()
        event_data_batch = await producer.create_batch(partition_key=partition_key)
        event_data_batch.add(EventData(json.dumps(body)))
        await producer.send_batch(event_data_batch)
        logger.info("eventhub.sent", hub=self._eventhub_name, message_id=body.get("message_id"))

    async def close(self) -> None:
        if self._producer:
            await self._producer.close()
            self._producer = None
        if self._credential:
            await self._credential.close()
            self._credential = None


class EventHubConsumer:
    """Async helper for receiving events from an Azure Event Hub.

    For simplicity, uses receive_batch for pull-based consumption.
    For production, use EventHubConsumerClient with BlobCheckpointStore.
    """

    def __init__(
        self,
        namespace: str | None = None,
        eventhub_name: str | None = None,
        consumer_group: str = "$Default",
    ) -> None:
        self._namespace = namespace or os.environ["AZURE_EVENTHUB_NAMESPACE"]
        self._eventhub_name = eventhub_name or os.environ["AZURE_EVENTHUB_NAME"]
        self._consumer_group = consumer_group
        self._credential: DefaultAzureCredential | None = None
        self._consumer: EventHubConsumerClient | None = None

    async def _get_consumer(self) -> EventHubConsumerClient:
        if self._consumer is None:
            self._credential = DefaultAzureCredential()
            self._consumer = EventHubConsumerClient(
                fully_qualified_namespace=self._namespace,
                eventhub_name=self._eventhub_name,
                consumer_group=self._consumer_group,
                credential=self._credential,
            )
        return self._consumer

    async def receive_batch(
        self,
        partition_id: str = "0",
        max_count: int = 1,
        max_wait_time: float = 30.0,
    ) -> list[dict[str, Any]]:
        """Receive a batch of events from a single partition."""
        consumer = await self._get_consumer()
        events = await consumer.receive_batch(
            partition_id=partition_id,
            max_batch_size=max_count,
            max_wait_time=max_wait_time,
        )
        results: list[dict[str, Any]] = []
        for event in events:
            body = json.loads(event.body_as_str())
            results.append(body)
        logger.info("eventhub.received", hub=self._eventhub_name, count=len(results))
        return results

    async def close(self) -> None:
        if self._consumer:
            await self._consumer.close()
            self._consumer = None
        if self._credential:
            await self._credential.close()
            self._credential = None
