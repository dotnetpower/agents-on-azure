# Microsoft Agent Framework — Single Agent

A single Azure AI Agent that performs the full **document analysis → summary → review** pipeline using the Azure AI Agent Service.

## Architecture

```
┌──────────────────────────────────────────────┐
│      Azure AI Agent Service (Foundry)        │
│                                              │
│  ┌─────────────────────────────────────┐     │
│  │        AIProjectClient              │     │
│  │  Agent → Thread → Run (3 steps)     │     │
│  └─────────────────────────────────────┘     │
│                                              │
│          Azure OpenAI (gpt-4o)               │
└──────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Azure AI Foundry project with `gpt-4o` deployed
- `az login` completed (DefaultAzureCredential)

## Quick Start

```bash
# 1. Set up environment
cp ../../../.env.example .env
# Edit .env with your Azure AI Foundry project endpoint

# 2. Install dependencies
uv sync

# 3. Run
uv run python src/main.py
```

## Customization

- Modify prompts in `src/agents/prompts.py`
- Add tool definitions in `src/tools/`
- Adjust agent instructions in `src/main.py`
