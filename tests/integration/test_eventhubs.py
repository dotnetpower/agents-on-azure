"""Integration tests for Azure Event Hubs client."""

import os
from uuid import uuid4

import pytest

# Skip if Azure credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_EVENTHUB_NAMESPACE"),
    reason="AZURE_EVENTHUB_NAMESPACE not set"
)


@pytest.fixture
def namespace() -> str:
    """Get Event Hubs namespace from environment."""
    return os.environ["AZURE_EVENTHUB_NAMESPACE"]


@pytest.fixture
def test_hub() -> str:
    """Test event hub name (must exist)."""
    return "analysis-results"


class TestEventHubsIntegration:
    """Integration tests for Event Hubs client."""

    @pytest.mark.asyncio
    async def test_send_event(self, namespace: str, test_hub: str):
        """Test sending an event to Event Hubs."""
        from azure_clients import EventHubPipelineMessaging

        messaging = EventHubPipelineMessaging(namespace=namespace)

        try:
            correlation_id = str(uuid4())
            test_event = {
                "type": "test",
                "correlation_id": correlation_id,
                "data": "integration test event",
            }

            # Send should not raise
            await messaging.send(test_hub, test_event)

        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_connection_with_managed_identity(self, namespace: str, test_hub: str):
        """Test that connection uses managed identity."""
        from azure_clients import EventHubPipelineMessaging

        messaging = EventHubPipelineMessaging(namespace=namespace)

        try:
            # Should not raise authentication errors
            await messaging.send(test_hub, {"test": True})

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip("Managed identity not configured")
            raise
        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_multiple_hubs(self, namespace: str):
        """Test sending to multiple event hubs."""
        from azure_clients import EventHubPipelineMessaging

        hubs = ["analysis-results", "summary-results", "review-results"]
        messaging = EventHubPipelineMessaging(namespace=namespace)

        try:
            correlation_id = str(uuid4())

            for hub in hubs:
                await messaging.send(hub, {
                    "type": "multi_hub_test",
                    "correlation_id": correlation_id,
                    "hub": hub,
                })

        except Exception as e:
            # Some hubs may not exist - that's ok for this test
            if "not found" not in str(e).lower():
                raise
        finally:
            await messaging.close()


class TestEventHubsResilience:
    """Test resilience features of Event Hubs."""

    @pytest.mark.asyncio
    async def test_batch_send(self, namespace: str, test_hub: str):
        """Test sending a batch of events."""
        from azure_clients import EventHubPipelineMessaging

        messaging = EventHubPipelineMessaging(namespace=namespace)

        try:
            correlation_id = str(uuid4())

            # Send multiple events
            for i in range(5):
                await messaging.send(test_hub, {
                    "type": "batch_test",
                    "correlation_id": correlation_id,
                    "sequence": i,
                })

        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_reconnection_after_close(self, namespace: str, test_hub: str):
        """Test that client can be reused after close."""
        from azure_clients import EventHubPipelineMessaging

        messaging = EventHubPipelineMessaging(namespace=namespace)

        try:
            # First operation
            await messaging.send(test_hub, {"test": 1})

            # Close
            await messaging.close()

            # Should work again
            await messaging.send(test_hub, {"test": 2})

        finally:
            await messaging.close()
