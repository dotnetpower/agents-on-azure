"""Configuration loader — .env file discovery, parsing, and mapping.

Responsibility: Read .env files and populate Settings from environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from utils.settings import Settings


def _find_env_file() -> Path | None:
    """Walk up from CWD to find a .env file."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        env_path = parent / ".env"
        if env_path.exists():
            return env_path
    return None


def _load_dotenv(path: Path) -> None:
    """Minimal .env file loader (no external dependency)."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_ENV_MAP: dict[str, str] = {
    "AZURE_OPENAI_ENDPOINT": "azure_openai_endpoint",
    "AZURE_OPENAI_MODEL": "azure_openai_model",
    "AZURE_AI_FOUNDRY_ENDPOINT": "azure_ai_foundry_endpoint",
    "AZURE_SERVICEBUS_NAMESPACE": "azure_servicebus_namespace",
    "AZURE_SERVICEBUS_QUEUE_ANALYZER": "servicebus_queue_analyzer",
    "AZURE_SERVICEBUS_QUEUE_SUMMARIZER": "servicebus_queue_summarizer",
    "AZURE_SERVICEBUS_QUEUE_REVIEWER": "servicebus_queue_reviewer",
    "AZURE_SERVICEBUS_QUEUE_RESULTS": "servicebus_queue_results",
    "AZURE_EVENTHUB_NAMESPACE": "azure_eventhub_namespace",
    "AZURE_EVENTHUB_NAME": "azure_eventhub_name",
    "AZURE_EVENTHUB_ANALYSIS": "eventhub_analysis",
    "AZURE_EVENTHUB_SUMMARY": "eventhub_summary",
    "AZURE_EVENTHUB_REVIEW": "eventhub_review",
    "AZURE_EVENTGRID_ENDPOINT": "azure_eventgrid_endpoint",
    "AZURE_STORAGE_ACCOUNT_NAME": "azure_storage_account_name",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "applicationinsights_connection_string",
    "AZURE_EVENTGRID_QUEUE_ANALYZER": "eventgrid_queue_analyzer",
    "AZURE_EVENTGRID_QUEUE_SUMMARIZER": "eventgrid_queue_summarizer",
    "AZURE_EVENTGRID_QUEUE_REVIEWER": "eventgrid_queue_reviewer",
    "AZURE_EVENTGRID_QUEUE_RESULTS": "eventgrid_queue_results",
}


def load_settings() -> Settings:
    """Load settings from environment variables (with .env fallback)."""
    env_file = _find_env_file()
    if env_file:
        _load_dotenv(env_file)

    settings = Settings()
    for env_key, attr_name in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value:
            setattr(settings, attr_name, value)
    return settings
