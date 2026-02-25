# LangGraph — Single Agent

A single LangGraph agent that performs the full **document analysis → summary → review** pipeline using a state graph.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              LangGraph StateGraph                │
│                                                 │
│  [START] → [analyze] → [summarize] → [review]  │
│                                        ↓         │
│                                     [END]        │
│                                                 │
│            Azure OpenAI (gpt-4o)                │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Azure OpenAI resource with `gpt-4o` deployed
- `az login` completed (DefaultAzureCredential)

## Quick Start

```bash
# 1. Set up environment
cp ../../../.env.example .env

# 2. Install dependencies
uv sync

# 3. Run
uv run python src/main.py
```

## Customization

- Modify graph structure in `src/agents/graph.py`
- Edit prompts in `src/agents/prompts.py`
- Add new tools in `src/tools/`
