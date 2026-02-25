# Semantic Kernel — Multi-Agent with Azure Service Bus

Three Semantic Kernel agents communicating via Azure Service Bus queues to implement the **document analysis → summary → review** pipeline.

## Architecture

```
┌──────────┐   SB Queue    ┌──────────┐   SB Queue    ┌──────────┐
│ Analyzer │──────────────→│Summarizer│──────────────→│ Reviewer │
│  Agent   │ summarizer-   │  Agent   │ reviewer-     │  Agent   │
│          │ tasks         │          │ tasks         │          │
└──────────┘               └──────────┘               └────┬─────┘
                                                           │
                                                    SB Queue│
                                                    pipeline-results
                                                           │
                                                     ┌─────▼─────┐
                                                     │ Collector  │
                                                     └───────────┘
```

## Resiliency Demo

- Stop the Summarizer agent → Analyzer sends messages to the queue
- Messages persist in Service Bus queue (no loss)
- Restart Summarizer → Messages automatically processed
- Dead Letter Queue captures failed messages after retry exhaustion

## Prerequisites

- Python 3.11+
- Azure OpenAI with `gpt-4o`
- Azure Service Bus namespace with queues: `analyzer-tasks`, `summarizer-tasks`, `reviewer-tasks`, `pipeline-results`
- `az login` completed

## Quick Start

```bash
# 1. Set up environment
cp ../../../.env.example .env

# 2. Install dependencies
uv sync

# 3. Run orchestrator (sends document, collects results)
uv run python src/main.py

# Or run agents individually in separate terminals:
uv run python src/agents/analyzer.py
uv run python src/agents/summarizer.py
uv run python src/agents/reviewer.py
```
