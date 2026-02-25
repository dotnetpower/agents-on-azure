# LangGraph — Multi-Agent with Azure Service Bus

Three LangGraph agents communicating via Azure Service Bus queues.

## Architecture

```
┌──────────┐   SB Queue    ┌──────────┐   SB Queue    ┌──────────┐
│ Analyzer │──────────────→│Summarizer│──────────────→│ Reviewer │
│ (Graph)  │ summarizer-   │ (Graph)  │ reviewer-     │ (Graph)  │
│          │ tasks         │          │ tasks         │          │
└──────────┘               └──────────┘               └────┬─────┘
                                                           │
                                                    pipeline-results
                                                           ▼
                                                     ┌───────────┐
                                                     │ Collector  │
                                                     └───────────┘
```

Each agent is a compiled LangGraph that reads from its input queue and writes to the next queue.

## Quick Start

```bash
cp ../../../.env.example .env
uv sync
uv run python src/main.py
```
