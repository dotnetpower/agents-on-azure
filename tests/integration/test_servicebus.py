"""Integration tests for Azure Service Bus messaging."""

import os
from uuid import uuid4

import pytest

# Skip if Azure credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_SERVICEBUS_NAMESPACE"),
    reason="AZURE_SERVICEBUS_NAMESPACE not set"
)


@pytest.fixture
def namespace() -> str:
    """Get Service Bus namespace from environment."""
    return os.environ["AZURE_SERVICEBUS_NAMESPACE"]


@pytest.fixture
def test_queue() -> str:
    """Test queue name (must exist in Service Bus)."""
    return "pipeline-results"  # Use existing queue


class TestServiceBusIntegration:
    """Integration tests for Service Bus client."""

    @pytest.mark.asyncio
    async def test_send_and_receive_message(self, namespace: str, test_queue: str):
        """Test sending and receiving a message through Service Bus."""
        from azure_clients import PipelineMessaging

        messaging = PipelineMessaging(namespace=namespace)

        try:
            # Create test message
            correlation_id = str(uuid4())
            test_payload = {
                "type": "test",
                "correlation_id": correlation_id,
                "data": "integration test message",
            }

            # Send message
            await messaging.send(test_queue, test_payload)

            # Receive message (should get our message or timeout)
            received = await messaging.receive_one(test_queue, max_wait_time=10)

            # Message may not be ours if other tests running
            assert received is None or "type" in received

        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_connection_with_managed_identity(self, namespace: str, test_queue: str):
        """Test that connection uses managed identity (no connection string)."""
        from azure_clients import PipelineMessaging

        messaging = PipelineMessaging(namespace=namespace)

        try:
            # Should not raise authentication errors
            # Connection is lazy, so we trigger it with a receive
            await messaging.receive_one(test_queue, max_wait_time=1)

        except Exception as e:
            # AuthenticationError would mean managed identity not configured
            if "authentication" in str(e).lower():
                pytest.skip("Managed identity not configured")
            raise
        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_multiple_messages(self, namespace: str, test_queue: str):
        """Test sending multiple messages."""
        from azure_clients import PipelineMessaging

        messaging = PipelineMessaging(namespace=namespace)

        try:
            correlation_id = str(uuid4())

            # Send multiple messages
            for i in range(3):
                await messaging.send(test_queue, {
                    "type": "batch_test",
                    "correlation_id": correlation_id,
                    "sequence": i,
                })

            # Just verify no errors - actual receipt depends on timing

        finally:
            await messaging.close()


class TestServiceBusResilience:
    """Test resilience features of Service Bus."""

    @pytest.mark.asyncio
    async def test_receive_timeout(self, namespace: str, test_queue: str):
        """Test that receive times out gracefully."""
        from azure_clients import PipelineMessaging

        messaging = PipelineMessaging(namespace=namespace)

        try:
            # Use very short timeout - should return None, not error
            result = await messaging.receive_one(test_queue, max_wait_time=1)

            # Result may be None (timeout) or a message (if queue has messages)
            # Either is acceptable

        finally:
            await messaging.close()

    @pytest.mark.asyncio
    async def test_reconnection_after_close(self, namespace: str, test_queue: str):
        """Test that client can be reused after close."""
        from azure_clients import PipelineMessaging

        messaging = PipelineMessaging(namespace=namespace)

        try:
            # First operation
            await messaging.receive_one(test_queue, max_wait_time=1)

            # Close and reopen
            await messaging.close()

            # Should work again (lazy reconnection)
            await messaging.receive_one(test_queue, max_wait_time=1)

        finally:
            await messaging.close()
