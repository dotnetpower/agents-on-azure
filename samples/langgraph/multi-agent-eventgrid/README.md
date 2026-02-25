# LangGraph — Multi-Agent Event Grid Pipeline

## Overview

Demonstrates a **three-agent document analysis pipeline** built with
[LangGraph](https://github.com/langchain-ai/langgraph) where agents
communicate through **Azure Event Grid** (publish) and **Azure Storage Queues**
(subscribe/receive).

## Architecture

```mermaid
sequenceDiagram
    participant Main
    participant EG as Event Grid
    participant Q1 as Queue: analyzer-events
    participant Q2 as Queue: summarizer-events
    participant Q3 as Queue: reviewer-events
    participant A as Analyzer (LG)
    participant S as Summarizer (LG)
    participant R as Reviewer (LG)

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
uv venv --python 3.11 && source .venv/bin/activate
uv sync
uv run python src/main.py
```
