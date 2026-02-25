# LangGraph — Multi-Agent with Azure Event Hubs

Three LangGraph agents streaming events through Azure Event Hubs.

## Architecture

```
┌──────────┐  Event Hub     ┌──────────┐  Event Hub     ┌──────────┐
│ Analyzer │──────────────→ │Summarizer│──────────────→ │ Reviewer │
│ (Graph)  │ analysis-      │ (Graph)  │ summary-       │ (Graph)  │
│          │ results        │          │ results        │          │
└──────────┘                └──────────┘                └──────────┘
```

## Quick Start

```bash
cp ../../../.env.example .env
uv sync
uv run python src/main.py
```
