# Semantic Kernel — Single Agent

A single Semantic Kernel agent that performs the full **document analysis → summary → review** pipeline without any messaging service.

## Architecture

```
┌──────────────────────────────────────────────┐
│            Semantic Kernel Agent              │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Analyze  │→ │Summarize │→ │  Review  │   │
│  │ Plugin   │  │ Plugin   │  │ Plugin   │   │
│  └──────────┘  └──────────┘  └──────────┘   │
│                                              │
│          Azure OpenAI (gpt-4o)               │
└──────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Azure OpenAI resource with `gpt-4o` deployed
- `az login` completed (DefaultAzureCredential)

## Quick Start

```bash
# 1. Set up environment
cp ../../../.env.example .env
# Edit .env with your Azure OpenAI endpoint

# 2. Install dependencies
uv sync

# 3. Run
uv run python src/main.py
```

## Customization

- Modify prompts in `src/agents/prompts.py`
- Add new plugins in `src/tools/`
- Adjust model parameters in `src/main.py`
