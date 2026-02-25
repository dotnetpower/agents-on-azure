# AutoGen — Multi-Agent with Azure Service Bus

Three AutoGen agents communicating via Azure Service Bus queues.

## Architecture

```
┌──────────┐   SB Queue    ┌──────────┐   SB Queue    ┌──────────┐
│ Analyzer │──────────────→│Summarizer│──────────────→│ Reviewer │
│  Agent   │ summarizer-   │  Agent   │ reviewer-     │  Agent   │
└──────────┘ tasks         └──────────┘ tasks         └────┬─────┘
                                                           │
                                                    pipeline-results
                                                           ▼
                                                     ┌───────────┐
                                                     │ Collector  │
                                                     └───────────┘
```

## Quick Start

```bash
cp ../../../.env.example .env
uv sync
uv run python src/main.py
```
