"""Azure Service Bus send/receive helpers.

Uses DefaultAzureCredential for authentication.
Provides simple async send/receive operations for inter-agent messaging.
"""

from __future__ import annotations

import json
import os
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver, ServiceBusSender

logger = structlog.get_logger(__name__)


class ServiceBusHelper:
    """Async helper for sending/receiving messages on Azure Service Bus queues."""

    def __init__(
        self,
        namespace: str | None = None,
    ) -> None:
        self._namespace = namespace or os.environ["AZURE_SERVICEBUS_NAMESPACE"]
        self._credential: DefaultAzureCredential | None = None
        self._client: ServiceBusClient | None = None

    async def _get_client(self) -> ServiceBusClient:
        if self._client is None:
            self._credential = DefaultAzureCredential()
            self._client = ServiceBusClient(
                fully_qualified_namespace=self._namespace,
                credential=self._credential,
            )
        return self._client

    async def send(self, queue_name: str, body: dict[str, Any]) -> None:
        """Send a JSON message to a queue."""
        client = await self._get_client()
        sender: ServiceBusSender
        async with client.get_queue_sender(queue_name=queue_name) as sender:
            message = ServiceBusMessage(
                body=json.dumps(body),
                content_type="application/json",
            )
            await sender.send_messages(message)
            logger.info("servicebus.sent", queue=queue_name, message_id=body.get("message_id"))

    async def receive_one(
        self,
        queue_name: str,
        max_wait_time: float = 30.0,
    ) -> dict[str, Any] | None:
        """Receive and complete a single message from a queue. Returns None on timeout."""
        client = await self._get_client()
        receiver: ServiceBusReceiver
        async with client.get_queue_receiver(
            queue_name=queue_name,
            max_wait_time=max_wait_time,
        ) as receiver:
            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=max_wait_time)
            if not messages:
                return None
            msg = messages[0]
            body = json.loads(str(msg))
            await receiver.complete_message(msg)
            logger.info("servicebus.received", queue=queue_name, message_id=body.get("message_id"))
            return body

    async def receive_batch(
        self,
        queue_name: str,
        max_count: int = 10,
        max_wait_time: float = 30.0,
    ) -> list[dict[str, Any]]:
        """Receive and complete a batch of messages."""
        client = await self._get_client()
        results: list[dict[str, Any]] = []
        async with client.get_queue_receiver(
            queue_name=queue_name,
            max_wait_time=max_wait_time,
        ) as receiver:
            messages = await receiver.receive_messages(
                max_message_count=max_count,
                max_wait_time=max_wait_time,
            )
            for msg in messages:
                body = json.loads(str(msg))
                await receiver.complete_message(msg)
                results.append(body)
        return results

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        if self._credential:
            await self._credential.close()
            self._credential = None
