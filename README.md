# Agents on Azure

A collection of practical examples combining various AI Agent frameworks with Azure messaging services to build **loosely coupled, resilient multi-agent systems**.

[![CI](https://github.com/dotnetpower/agents-on-azure/workflows/CI/badge.svg)](https://github.com/dotnetpower/agents-on-azure/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project demonstrates how to build **production-ready multi-agent AI systems** using Azure cloud services. Each sample implements the same document analysis pipeline, making it easy to compare frameworks and messaging patterns.

### Key Features

- **4 Agent Frameworks**: Semantic Kernel, LangGraph, AutoGen, MS Agent Framework
- **3 Messaging Patterns**: Service Bus (queues), Event Hubs (streaming), Event Grid (pub/sub)
- **16 Complete Samples**: Every framework × every pattern combination
- **Resilience Built-in**: Message persistence, automatic retry, dead letter handling
- **Security First**: Managed Identity only, no API keys or connection strings

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Document Analysis Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐         ┌───────────┐         ┌──────────┐        │
│  │ Analyzer │────────▶│ Summarizer│────────▶│ Reviewer │        │
│  │  Agent   │         │   Agent   │         │  Agent   │        │
│  └──────────┘         └───────────┘         └──────────┘        │
│        │                    │                    │               │
│        └────────────────────┴────────────────────┘               │
│                             │                                    │
│              Azure Messaging (Service Bus / Event Hubs / Grid)   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Sample Matrix

| Framework | Single Agent | Service Bus | Event Hubs | Event Grid |
|-----------|:------------:|:-----------:|:----------:|:----------:|
| **Semantic Kernel** | ✅ | ✅ | ✅ | ✅ |
| **LangGraph** | ✅ | ✅ | ✅ | ✅ |
| **AutoGen** | ✅ | ✅ | ✅ | ✅ |
| **MS Agent Framework** | ✅ | ✅ | ✅ | ✅ |

## Benchmark Results

Performance benchmarks for the document analysis pipeline (analyzed 2026-02-25).

### Single-Agent Pattern

| Framework | Time | Tokens/sec | Notes |
|-----------|:----:|:----------:|-------|
| **AutoGen** | 14.3s | ~280 | Fastest single-agent execution |
| **Semantic Kernel** | 15.9s | ~250 | Consistent, enterprise-ready |
| **LangGraph** | 18.2s | ~220 | State management overhead |

### Multi-Agent Service Bus Pattern

| Framework | Time | Latency (avg) | Notes |
|-----------|:----:|:-------------:|-------|
| **LangGraph** | 65.8s | ~22s/step | Best async orchestration |
| **AutoGen** | 67.4s | ~22s/step | Excellent group chat coordination |
| **Semantic Kernel** | 69.5s | ~23s/step | Most verbose logging |

### Key Findings

- **Single-agent**: All frameworks perform similarly (~14-18s for 3-step pipeline)
- **Multi-agent**: Service Bus adds ~50s overhead for message passing between agents
- **Network impact**: Azure Service Bus message delivery: ~100-200ms per hop
- **Token efficiency**: All frameworks optimize for streaming; TTFT ~500-800ms

> **Note**: Benchmarks run on Azure OpenAI gpt-4o (GlobalStandard SKU, 10 TPM). Results may vary based on region, load, and model availability.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Azure CLI
- Azure subscription with Contributor access

### 1. Clone & Setup

```bash
git clone https://github.com/dotnetpower/agents-on-azure.git
cd agents-on-azure

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Deploy Azure Resources

```bash
az login
./infra/scripts/deploy.sh dev eastus
```

### 3. Run a Sample

```bash
cd samples/semantic-kernel/single-agent
uv run python src/main.py
```

## Documentation

- [Getting Started](docs/getting-started.md) — Quick start guide
- [Azure Setup](docs/azure-setup.md) — Manual resource provisioning
- [Architecture Overview](docs/architecture/overview.md) — System design
- [Messaging Patterns](docs/architecture/messaging-patterns.md) — When to use each pattern

## Project Structure

```
agents-on-azure/
├── docs/                           # Documentation
│   ├── architecture/               # Architecture docs & diagrams
│   ├── getting-started.md          # Quick start guide
│   └── azure-setup.md              # Azure provisioning guide
├── infra/
│   ├── bicep/                      # Infrastructure as Code
│   │   ├── main.bicep              # Main deployment
│   │   ├── modules/                # Resource modules
│   │   └── parameters/             # Environment params
│   └── scripts/                    # Deployment scripts
├── samples/
│   ├── semantic-kernel/            # 4 samples
│   ├── langgraph/                  # 4 samples
│   ├── autogen/                    # 4 samples
│   └── microsoft-agent-framework/  # 4 samples
├── shared/                         # Shared packages
│   ├── contracts/                  # Message schemas
│   ├── azure_clients/              # Azure SDK wrappers
│   ├── utils/                      # Configuration & logging
│   └── benchmarks/                 # Performance measurement
├── tests/
│   ├── integration/                # Azure integration tests
│   └── e2e/                        # End-to-end pipeline tests
└── pyproject.toml                  # uv workspace config
```

## Security

All samples follow Azure security best practices:

- ✅ **Managed Identity** for all Azure service authentication
- ✅ **No API keys** or connection strings in code
- ✅ **Local auth disabled** on all Azure resources
- ✅ **RBAC roles** with minimum privileges

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding conventions in `.github/copilot-instructions.md`
4. Submit a pull request

## License

MIT