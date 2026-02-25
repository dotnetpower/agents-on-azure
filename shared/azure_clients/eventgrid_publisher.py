"""Azure Event Grid publisher for the pipeline.

Responsibility: Publish events to an Event Grid topic only.
Does NOT handle receiving — that is StorageQueueReceiver's job.
"""

from __future__ import annotations

from typing import Any

import structlog
from azure.eventgrid import EventGridEvent
from azure.eventgrid.aio import EventGridPublisherClient
from azure.identity.aio import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class PipelineEventGridPublisher:
    """Publish pipeline events to an Event Grid topic."""

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._credential: DefaultAzureCredential | None = None
        self._client: EventGridPublisherClient | None = None

    async def _get_client(self) -> EventGridPublisherClient:
        if self._client is None:
            self._credential = DefaultAzureCredential()
            self._client = EventGridPublisherClient(
                endpoint=self._endpoint,
                credential=self._credential,
            )
        return self._client

    async def publish(
        self,
        event_type: str,
        subject: str,
        data: dict[str, Any],
        data_version: str = "1.0",
    ) -> None:
        """Publish a single EventGridEvent."""
        client = await self._get_client()
        event = EventGridEvent(
            event_type=event_type,
            subject=subject,
            data=data,
            data_version=data_version,
        )
        await client.send([event])
        logger.info("eventgrid.published", event_type=event_type, subject=subject)

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        if self._credential:
            await self._credential.close()
            self._credential = None
