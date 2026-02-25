"""Event Grid + Storage Queue pipeline messaging helper.

Provides a convenient combined wrapper for the pattern:
  - Publish: events via Event Grid topic
  - Receive: messages from Azure Storage Queues
    (Event Grid subscriptions route events to Storage Queues)

Responsibility: Message publish/receive coordination for multi-stage pipelines.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from azure.eventgrid import EventGridEvent
from azure.eventgrid.aio import EventGridPublisherClient
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueClient

logger = structlog.get_logger(__name__)

# Polling interval for queue receive operations
_POLL_INTERVAL_SECONDS = 1.0


class EventGridPipelineMessaging:
    """Wraps Event Grid publish + Storage Queue receive for multi-agent pipelines."""

    def __init__(
        self,
        eventgrid_endpoint: str,
        storage_account_name: str,
    ) -> None:
        self._eg_endpoint = eventgrid_endpoint
        self._storage_account = storage_account_name
        self._credential: DefaultAzureCredential | None = None
        self._eg_client: EventGridPublisherClient | None = None
        self._queue_clients: dict[str, QueueClient] = {}

    async def _get_credential(self) -> DefaultAzureCredential:
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    async def _get_eg_client(self) -> EventGridPublisherClient:
        if self._eg_client is None:
            credential = await self._get_credential()
            self._eg_client = EventGridPublisherClient(
                endpoint=self._eg_endpoint,
                credential=credential,
            )
        return self._eg_client

    async def _get_queue_client(self, queue_name: str) -> QueueClient:
        if queue_name not in self._queue_clients:
            credential = await self._get_credential()
            account_url = f"https://{self._storage_account}.queue.core.windows.net"
            self._queue_clients[queue_name] = QueueClient(
                account_url=account_url,
                queue_name=queue_name,
                credential=credential,
            )
        return self._queue_clients[queue_name]

    async def publish(
        self,
        event_type: str,
        subject: str,
        data: dict[str, Any],
    ) -> None:
        """Publish an event to the Event Grid topic."""
        client = await self._get_eg_client()
        event = EventGridEvent(
            event_type=event_type,
            subject=subject,
            data=data,
            data_version="1.0",
        )
        await client.send([event])
        logger.info("eventgrid.published", event_type=event_type, subject=subject)

    async def receive_one(
        self,
        queue_name: str,
        max_wait_time: float = 30.0,
        visibility_timeout: int = 60,
    ) -> dict[str, Any] | None:
        """Receive and delete a single message from a Storage Queue.

        Polls the queue until a message arrives or *max_wait_time* elapses.
        """
        queue = await self._get_queue_client(queue_name)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max_wait_time
        while loop.time() < deadline:
            messages: list[Any] = []
            async for msg in queue.receive_messages(
                max_messages=1,
                visibility_timeout=visibility_timeout,
            ):
                messages.append(msg)
            if messages:
                raw = messages[0].content
                await queue.delete_message(messages[0])
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    body = {"raw": raw}
                # Event Grid wraps the payload in an event envelope
                if "data" in body and isinstance(body["data"], dict):
                    body = body["data"]
                logger.info("queue.received", queue=queue_name)
                return body
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        logger.warning("queue.timeout", queue=queue_name)
        return None

    async def close(self) -> None:
        for qc in self._queue_clients.values():
            await qc.close()
        self._queue_clients.clear()
        if self._eg_client:
            await self._eg_client.close()
            self._eg_client = None
        if self._credential:
            await self._credential.close()
            self._credential = None
