"""Azure Storage Queue receiver for the pipeline.

Responsibility: Receive messages from Azure Storage Queues only.
Used as the subscription endpoint for Event Grid → Storage Queue routing.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueClient

logger = structlog.get_logger(__name__)

# Polling interval for queue receive operations
_POLL_INTERVAL_SECONDS = 1.0


class StorageQueueReceiver:
    """Poll an Azure Storage Queue for messages (Event Grid subscription target)."""

    def __init__(self, storage_account_name: str) -> None:
        self._storage_account = storage_account_name
        self._credential: DefaultAzureCredential | None = None
        self._queue_clients: dict[str, QueueClient] = {}

    async def _get_credential(self) -> DefaultAzureCredential:
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

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

    async def receive_one(
        self,
        queue_name: str,
        max_wait_time: float = 30.0,
        visibility_timeout: int = 60,
    ) -> dict[str, Any] | None:
        """Receive and delete a single message from a Storage Queue.

        Polls until a message arrives or max_wait_time is exceeded.
        """
        queue = await self._get_queue_client(queue_name)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max_wait_time

        while loop.time() < deadline:
            messages = []
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
                # Event Grid wraps payload in an event envelope
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
        if self._credential:
            await self._credential.close()
            self._credential = None
