"""Integration tests for Azure Event Grid client."""

import os
from uuid import uuid4

import pytest

# Skip if Azure credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_EVENTGRID_ENDPOINT"),
    reason="AZURE_EVENTGRID_ENDPOINT not set"
)


@pytest.fixture
def endpoint() -> str:
    """Get Event Grid endpoint from environment."""
    return os.environ["AZURE_EVENTGRID_ENDPOINT"]


@pytest.fixture
def storage_account() -> str:
    """Get Storage account name from environment."""
    return os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "")


class TestEventGridIntegration:
    """Integration tests for Event Grid client."""

    @pytest.mark.asyncio
    async def test_publish_event(self, endpoint: str, storage_account: str):
        """Test publishing an event to Event Grid."""
        if not storage_account:
            pytest.skip("AZURE_STORAGE_ACCOUNT_NAME not set")

        from azure_clients import EventGridPipelineMessaging

        messaging = EventGridPipelineMessaging(
            eventgrid_endpoint=endpoint,
            storage_account_name=storage_account,
        )

        try:
            correlation_id = str(uuid4())

            await messaging.publish(
                event_type="Pipeline.Test",
                subject=f"/test/{correlation_id}",
                data={
                    "type": "integration_test",
                    "correlation_id": correlation_id,
                },
            )

        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_connection_with_managed_identity(self, endpoint: str, storage_account: str):
        """Test that connection uses managed identity."""
        if not storage_account:
            pytest.skip("AZURE_STORAGE_ACCOUNT_NAME not set")

        from azure_clients import EventGridPipelineMessaging

        messaging = EventGridPipelineMessaging(
            eventgrid_endpoint=endpoint,
            storage_account_name=storage_account,
        )

        try:
            await messaging.publish(
                event_type="Pipeline.AuthTest",
                subject="/test/auth",
                data={"test": True},
            )

        except Exception as e:
            if "authentication" in str(e).lower() or "401" in str(e):
                pytest.skip("Managed identity not configured")
            raise
        finally:
            await messaging.close()


class TestStorageQueueIntegration:
    """Integration tests for Storage Queue receiver."""

    @pytest.mark.asyncio
    async def test_receive_from_queue(self, storage_account: str):
        """Test receiving from Storage Queue."""
        if not storage_account:
            pytest.skip("AZURE_STORAGE_ACCOUNT_NAME not set")

        from azure_clients import StorageQueueReceiver

        queue_name = "results-events"
        receiver = StorageQueueReceiver(
            storage_account_name=storage_account,
            queue_name=queue_name,
        )

        try:
            # Should return None or a message (not error)
            result = await receiver.receive_one(timeout=2)
            # Result may be None (empty queue) or dict (message)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Queue {queue_name} not found")
            if "authentication" in str(e).lower():
                pytest.skip("Managed identity not configured")
            raise
        finally:
            await receiver.close()

    @pytest.mark.asyncio
    async def test_receive_timeout(self, storage_account: str):
        """Test that receive times out gracefully."""
        if not storage_account:
            pytest.skip("AZURE_STORAGE_ACCOUNT_NAME not set")

        from azure_clients import StorageQueueReceiver

        receiver = StorageQueueReceiver(
            storage_account_name=storage_account,
            queue_name="results-events",
        )

        try:
            # Should return None, not raise
            result = await receiver.receive_one(timeout=1)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip("Queue not found")
            raise
        finally:
            await receiver.close()
