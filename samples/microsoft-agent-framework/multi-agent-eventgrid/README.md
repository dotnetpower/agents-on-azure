# Microsoft Agent Framework — Multi-Agent Event Grid Pipeline

## Overview

Demonstrates a **three-agent document analysis pipeline** built with the
[Microsoft Agent Framework](https://learn.microsoft.com/azure/ai-services/agents/)
(Azure AI Agent Service) where agents communicate through **Azure Event Grid**
(publish) and **Azure Storage Queues** (subscribe/receive).

## Architecture

```mermaid
sequenceDiagram
    participant Main
    participant EG as Event Grid
    participant Q1 as Queue: analyzer-events
    participant Q2 as Queue: summarizer-events
    participant Q3 as Queue: reviewer-events
    participant A as Analyzer (MAF)
    participant S as Summarizer (MAF)
    participant R as Reviewer (MAF)

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
| Azure AI Foundry Project | Agent hosting |
| Azure Event Grid | Event routing |
| Azure Storage Account | Storage Queues for subscriptions |

## Quick Start

```bash
uv venv --python 3.11 && source .venv/bin/activate
uv sync
uv run python src/main.py
```
