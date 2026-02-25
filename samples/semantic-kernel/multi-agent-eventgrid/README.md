# Semantic Kernel — Multi-Agent Event Grid Pipeline

## Overview

Demonstrates a **three-agent document analysis pipeline** built with
[Semantic Kernel](https://github.com/microsoft/semantic-kernel) where agents
communicate through **Azure Event Grid** (publish) and **Azure Storage Queues**
(subscribe/receive).

```
Event Grid Topic
  ├─► Storage Queue (analyzer-events)  → Analyzer Agent
  ├─► Storage Queue (summarizer-events) → Summarizer Agent
  └─► Storage Queue (reviewer-events)  → Reviewer Agent
```

## Architecture

```mermaid
sequenceDiagram
    participant Main
    participant EG as Event Grid
    participant Q1 as Queue: analyzer-events
    participant Q2 as Queue: summarizer-events
    participant Q3 as Queue: reviewer-events
    participant A as Analyzer (SK)
    participant S as Summarizer (SK)
    participant R as Reviewer (SK)

    Main->>EG: Publish (analyze request)
    EG->>Q1: Route event
    Q1->>A: Receive
    A->>EG: Publish (analysis result)
    EG->>Q2: Route event
    Q2->>S: Receive
    S->>EG: Publish (summary result)
    EG->>Q3: Route event
    Q3->>R: Receive
    R->>Main: Final review
```

## Prerequisites

| Resource | Purpose |
|---|---|
| Azure OpenAI | LLM inference (gpt-4o) |
| Azure Event Grid | Event routing |
| Azure Storage Account | Storage Queues for subscriptions |

## Quick Start

```bash
# 1. Create virtual environment
uv venv --python 3.11 && source .venv/bin/activate

# 2. Install dependencies
uv sync

# 3. Set environment variables (see .env.example at project root)

# 4. Run
uv run python src/main.py
```

## Resiliency

- Events are delivered to durable Storage Queues — survives consumer downtime
- Failed events route to Dead Letter storage for inspection
- Retry policies configurable on Event Grid subscriptions
