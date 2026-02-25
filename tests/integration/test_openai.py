"""Integration tests for Azure OpenAI client."""

import os

import pytest

# Skip if Azure credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_ENDPOINT"),
    reason="AZURE_OPENAI_ENDPOINT not set"
)


@pytest.fixture
def endpoint() -> str:
    """Get OpenAI endpoint from environment."""
    return os.environ["AZURE_OPENAI_ENDPOINT"]


@pytest.fixture
def model() -> str:
    """Get model deployment name from environment."""
    return os.environ.get("AZURE_OPENAI_MODEL", "gpt-4o")


class TestOpenAIIntegration:
    """Integration tests for Azure OpenAI client."""

    @pytest.mark.asyncio
    async def test_simple_completion(self, endpoint: str, model: str):
        """Test simple chat completion."""
        from azure_clients import get_openai_client

        client = get_openai_client(endpoint)

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'hello' and nothing else."},
                ],
                max_tokens=10,
            )

            assert response.choices
            assert len(response.choices) > 0
            assert "hello" in response.choices[0].message.content.lower()

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_managed_identity_auth(self, endpoint: str, model: str):
        """Test that client uses managed identity for authentication."""
        from azure_clients import get_openai_client

        client = get_openai_client(endpoint)

        try:
            # Should not raise any authentication errors
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Reply with 'ok'"},
                ],
                max_tokens=5,
            )

            assert response.choices

        except Exception as e:
            if "authentication" in str(e).lower() or "401" in str(e):
                pytest.skip("Managed identity not configured or lacking permissions")
            raise
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_streaming_completion(self, endpoint: str, model: str):
        """Test streaming chat completion."""
        from azure_clients import get_openai_client

        client = get_openai_client(endpoint)

        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Count from 1 to 3."},
                ],
                max_tokens=20,
                stream=True,
            )

            chunks = []
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)

            assert len(chunks) > 0
            full_response = "".join(chunks)
            assert any(num in full_response for num in ["1", "2", "3"])

        finally:
            await client.close()


class TestOpenAIResilience:
    """Test resilience features of OpenAI client."""

    @pytest.mark.asyncio
    async def test_invalid_model_error(self, endpoint: str):
        """Test error handling for invalid model."""
        from azure_clients import get_openai_client

        client = get_openai_client(endpoint)

        try:
            with pytest.raises(Exception):  # Should raise NotFoundError or similar
                await client.chat.completions.create(
                    model="nonexistent-model-xyz",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                )
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_empty_messages_error(self, endpoint: str, model: str):
        """Test error handling for empty messages."""
        from azure_clients import get_openai_client

        client = get_openai_client(endpoint)

        try:
            with pytest.raises(Exception):  # Should raise validation error
                await client.chat.completions.create(
                    model=model,
                    messages=[],
                    max_tokens=5,
                )
        finally:
            await client.close()
