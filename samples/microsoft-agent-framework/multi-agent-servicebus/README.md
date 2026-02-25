# Microsoft Agent Framework — Multi-Agent with Azure Service Bus

Three Azure AI agents communicating via Azure Service Bus queues.

## Architecture

```
┌──────────┐   SB Queue    ┌──────────┐   SB Queue    ┌──────────┐
│ Analyzer │──────────────→│Summarizer│──────────────→│ Reviewer │
│ (Agent)  │ summarizer-   │ (Agent)  │ reviewer-     │ (Agent)  │
└──────────┘ tasks         └──────────┘ tasks         └────┬─────┘
                                                           │
                                                    pipeline-results
```

## Quick Start

```bash
cp ../../../.env.example .env
uv sync
uv run python src/main.py
```
