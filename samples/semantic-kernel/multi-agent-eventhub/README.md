# Semantic Kernel — Multi-Agent with Azure Event Hubs

Three Semantic Kernel agents communicating via Azure Event Hubs for real-time event streaming.

## Architecture

```
┌──────────┐  Event Hub     ┌──────────┐  Event Hub     ┌──────────┐
│ Analyzer │──────────────→ │Summarizer│──────────────→ │ Reviewer │
│  Agent   │ analysis-      │  Agent   │ summary-       │  Agent   │
│          │ results        │          │ results        │          │
└──────────┘                └──────────┘                └────┬─────┘
                                                             │
                                                      Event Hub
                                                      review-results
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
