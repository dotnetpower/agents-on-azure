"""Azure OpenAI chat completion wrapper with streaming and TTFT measurement."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import structlog
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

logger = structlog.get_logger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # system | user | assistant
    content: str


@dataclass
class ChatResponse:
    """Response from a chat completion call."""

    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


@dataclass
class AzureOpenAIClient:
    """Thin wrapper around Azure OpenAI async client.

    Uses DefaultAzureCredential for authentication (no API keys).
    """

    endpoint: str = field(default_factory=lambda: os.environ["AZURE_OPENAI_ENDPOINT"])
    model: str = field(default_factory=lambda: os.environ.get("AZURE_OPENAI_MODEL", "gpt-4o"))
    _client: AsyncAzureOpenAI | None = field(default=None, init=False, repr=False)
    _credential: DefaultAzureCredential | None = field(default=None, init=False, repr=False)

    async def _get_client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            self._credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                self._credential, "https://cognitiveservices.azure.com/.default"
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-12-01-preview",
            )
        return self._client

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """Non-streaming chat completion."""
        client = await self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage
        return ChatResponse(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=response.model or self.model,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Streaming chat completion — yields content chunks."""
        client = await self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def close(self) -> None:
        """Release resources."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._credential:
            await self._credential.close()
            self._credential = None
