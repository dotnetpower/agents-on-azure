# Architecture Overview

This document describes the high-level architecture of the **Agents on Azure** project, which demonstrates building reliable multi-agent AI systems using Azure messaging services.

## Core Concept

The project implements a **loosely coupled** multi-agent architecture where AI agents communicate through Azure messaging services rather than direct method calls. This design provides:

- **Resilience**: Messages are persisted in queues/topics, surviving agent failures
- **Scalability**: Agents can scale independently based on workload
- **Observability**: All inter-agent communication is traceable
- **Flexibility**: Agents can be implemented in different frameworks

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agents on Azure                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Analyzer   │    │  Summarizer  │    │   Reviewer   │                  │
│  │    Agent     │    │    Agent     │    │    Agent     │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         │            Azure Messaging Services   │                          │
│         │    ┌──────────────────────────────────┴──────┐                   │
│         │    │                                         │                   │
│  ┌──────▼────▼──────────────────────────────────────────▼──────┐           │
│  │                                                              │           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │           │
│  │  │ Service Bus │  │ Event Hubs  │  │    Event Grid       │  │           │
│  │  │   Queues    │  │   Streams   │  │ + Storage Queues    │  │           │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │           │
│  │                                                              │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Azure OpenAI (GPT-4o)                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Application Insights (Observability)                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Frameworks

The project provides implementations using four major AI agent frameworks:

| Framework | Description | Best For |
|-----------|-------------|----------|
| **Semantic Kernel** | Microsoft's SDK for AI orchestration | Enterprise integration, .NET/Python |
| **LangGraph** | State-based graph workflows | Complex control flows, checkpointing |
| **AutoGen** | Conversational multi-agent patterns | Agent collaboration, chat-based |
| **MS Agent Framework** | Azure AI Agent Service | Azure-native, managed agents |

## Pipeline Scenario

All samples implement the same **Document Analysis Pipeline**:

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  Input   │────────▶│ Analyzer │────────▶│Summarizer│────────▶│ Reviewer │
│ Document │         │  Agent   │         │  Agent   │         │  Agent   │
└──────────┘         └──────────┘         └──────────┘         └──────────┘
                          │                    │                    │
                          ▼                    ▼                    ▼
                     Analysis             Summary              Review +
                      Output              Output             Final Output
```

### Pipeline Stages

1. **Analyzer Agent**: Extracts key information from the input document
2. **Summarizer Agent**: Creates a concise summary from the analysis
3. **Reviewer Agent**: Reviews and validates the summary quality

## Security Architecture

The architecture follows Azure security best practices:

### Identity & Access

- **No API Keys**: All authentication uses Microsoft Entra ID (Azure AD)
- **Managed Identity**: Container Apps use system-assigned managed identity
- **Local Auth Disabled**: All Azure services have local authentication disabled
- **RBAC**: Minimum-privilege role assignments

### Required RBAC Roles

| Role | Resource | Purpose |
|------|----------|---------|
| Cognitive Services OpenAI User | Azure OpenAI | LLM API access |
| Azure Service Bus Data Owner | Service Bus | Send/receive messages |
| Azure Event Hubs Data Owner | Event Hubs | Produce/consume events |
| EventGrid Data Sender | Event Grid | Publish events |
| Storage Blob Data Contributor | Storage Account | Checkpoint storage |
| Storage Queue Data Contributor | Storage Account | Queue access |

## Messaging Patterns

Three messaging patterns are demonstrated:

1. **Service Bus (Point-to-Point)**: Reliable 1:1 messaging with DLQ support
2. **Event Hubs (Streaming)**: High-throughput real-time event streaming
3. **Event Grid (Pub/Sub)**: Event-driven reactive architecture

See [Messaging Patterns](messaging-patterns.md) for detailed pattern descriptions.

## Project Structure

```
agents-on-azure/
├── samples/                    # Framework implementations
│   ├── semantic-kernel/        # 4 samples (single + 3 messaging)
│   ├── langgraph/             # 4 samples
│   ├── autogen/               # 4 samples
│   └── microsoft-agent-framework/  # 4 samples
├── shared/                     # Shared code packages
│   ├── contracts/             # Message schemas
│   ├── azure_clients/         # Azure SDK wrappers
│   ├── utils/                 # Configuration, logging
│   └── benchmarks/            # Performance measurement
├── infra/                      # Infrastructure as Code
│   ├── bicep/                 # Bicep templates
│   └── scripts/               # Deployment scripts
├── tests/                      # Test suites
└── docs/                       # Documentation
```

## Resilience Demonstration

The architecture demonstrates resilience through:

### Message Persistence
- Messages survive agent crashes in Service Bus queues
- Event Hubs retain events for configurable periods
- Dead Letter Queues capture failed messages

### Recovery Scenarios
1. **Agent Crash**: Agent B crashes while Analyzer sends message
2. **Message Preserved**: Service Bus retains the message
3. **Agent Recovery**: Agent B restarts and receives pending message
4. **Pipeline Continues**: Processing completes without data loss

### Failure Handling
- Automatic retry with exponential backoff
- Dead Letter Queue for poison messages
- Circuit breaker patterns for external calls
- Graceful degradation on partial failures

## Performance Considerations

### Scalability
- Agents scale independently via Container Apps
- Event Hubs partitions enable parallel processing
- Service Bus sessions group related messages

### Latency
- Azure OpenAI adds ~1-5s per LLM call
- Messaging adds ~10-100ms per hop
- End-to-end pipeline: ~5-15s typical

### Throughput
- Service Bus: ~1000 msg/sec per queue
- Event Hubs: ~1M events/sec with partitions
- Bottleneck: LLM API rate limits

## Next Steps

- [Getting Started](../getting-started.md): Quick start guide
- [Azure Setup](../azure-setup.md): Resource provisioning
- [Messaging Patterns](messaging-patterns.md): Pattern deep-dive
