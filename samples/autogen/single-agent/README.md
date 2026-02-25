# AutoGen — Single Agent

A single AutoGen `AssistantAgent` that performs the full **document analysis → summary → review** pipeline.

## Architecture

```
┌──────────────────────────────────────────────┐
│         AutoGen AssistantAgent               │
│                                              │
│  Step 1: Analyze document                    │
│  Step 2: Summarize analysis                  │
│  Step 3: Review summary                      │
│                                              │
│     AzureOpenAIChatCompletionClient          │
│            Azure OpenAI (gpt-4o)             │
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

# 2. Install dependencies
uv sync

# 3. Run
uv run python src/main.py
```

## Customization

- Modify prompts in `src/agents/prompts.py`
- Add tool functions in `src/tools/`
- Adjust agent behavior in `src/agents/pipeline_agent.py`
