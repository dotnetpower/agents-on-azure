# Messaging Patterns

This document explains the three Azure messaging patterns used in the Agents on Azure project, with guidance on when to use each.

## Pattern Comparison

| Aspect | Service Bus | Event Hubs | Event Grid |
|--------|-------------|------------|------------|
| **Model** | Message Queue | Event Stream | Pub/Sub |
| **Delivery** | At-least-once | At-least-once | At-least-once |
| **Ordering** | Per session | Per partition | Not guaranteed |
| **Retention** | Until consumed | Time-based | Until delivered |
| **Best For** | Task queues | Streaming | Reactive systems |

---

## 1. Azure Service Bus (Point-to-Point)

### Overview

Service Bus provides enterprise-grade messaging with reliable delivery, FIFO ordering, and dead letter handling.

```
┌──────────┐                                        ┌──────────┐
│ Analyzer │──▶ [analyzer-tasks] ──▶ [summarizer-tasks] ──▶│Summarizer│
│  Agent   │                                        │  Agent   │
└──────────┘                                        └──────────┘
     │                                                   │
     │        ┌─────────────────┐                       │
     │        │ pipeline-results│◀──────────────────────│
     │        └─────────────────┘                       │
     │              │                                   │
     ▼              ▼                                   ▼
┌──────────────────────────────────────────────────────────────┐
│                Dead Letter Queue (DLQ) for failures          │
└──────────────────────────────────────────────────────────────┘
```

### Queue Configuration

```
analyzer-tasks     → Analyzer Agent reads, processes, sends to summarizer-tasks
summarizer-tasks   → Summarizer Agent reads, processes, sends to reviewer-tasks
reviewer-tasks     → Reviewer Agent reads, processes, sends to pipeline-results
pipeline-results   → Final results collected here
```

### When to Use

✅ **Use Service Bus when:**
- You need guaranteed, exactly-once processing semantics
- Message ordering is important (use sessions)
- You want automatic dead letter handling
- Task-based workloads with clear request/response patterns
- Integration with enterprise systems

❌ **Avoid when:**
- High-throughput streaming (millions of events/sec)
- You need to replay historical messages
- Fire-and-forget event notifications

### Code Pattern

```python
from azure_clients import PipelineMessaging

messaging = PipelineMessaging(namespace="sb-agents.servicebus.windows.net")

# Send task to next agent
await messaging.send("summarizer-tasks", {
    "correlation_id": cid,
    "analysis": analysis_result,
})

# Receive and process
msg = await messaging.receive_one("analyzer-tasks", max_wait_time=30)
if msg:
    # Process message
    await process(msg)
    # Message auto-completed on successful receive
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Sessions** | Group related messages for ordered processing |
| **DLQ** | Failed messages moved to dead letter queue |
| **Peek-Lock** | Message locked during processing |
| **TTL** | Messages expire after time-to-live |
| **Deferred** | Messages can be deferred for later processing |

---

## 2. Azure Event Hubs (Streaming)

### Overview

Event Hubs is a high-throughput event streaming platform for real-time analytics and data pipelines.

```
                          ┌─────────────┐
                          │  Partition 0 │
                          ├─────────────┤
┌──────────┐              │  Partition 1 │              ┌──────────┐
│ Producer │──────────────┼─────────────┼──────────────▶│ Consumer │
│  Agents  │              │  Partition 2 │              │  Agents  │
└──────────┘              ├─────────────┤              └──────────┘
                          │  Partition N │
                          └─────────────┘
                               ▲
                               │
                    Events retained for replay
```

### Hub Configuration

```
analysis-results  → Analyzer publishes analysis events
summary-results   → Summarizer publishes summary events
review-results    → Reviewer publishes review events
```

### When to Use

✅ **Use Event Hubs when:**
- Processing millions of events per second
- Building real-time analytics pipelines
- You need event replay capability
- Multiple consumers need the same events
- Temporal decoupling between producers and consumers

❌ **Avoid when:**
- You need message acknowledgment per item
- Strict FIFO ordering across all messages
- Simple task queue semantics

### Code Pattern

```python
from azure_clients import EventHubPipelineMessaging

messaging = EventHubPipelineMessaging(namespace="eh-agents.servicebus.windows.net")

# Publish event to hub
await messaging.send("analysis-results", {
    "correlation_id": cid,
    "analysis": analysis_result,
    "timestamp": datetime.utcnow().isoformat(),
})

# Consume events
event = await messaging.receive_one("analysis-results")
if event:
    # Process event
    await process(event)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Partitions** | Parallel processing lanes |
| **Consumer Groups** | Independent read positions |
| **Retention** | Events kept for 1-7 days (90 days premium) |
| **Checkpointing** | Track processing position per partition |
| **Capture** | Auto-archive to Azure Storage/ADLS |

### Partition Strategy

```
Partition Key Strategy:
- By correlation_id → All pipeline messages together
- By agent_type → All analyzer events in same partition
- Round-robin → Even distribution for throughput
```

---

## 3. Azure Event Grid (Pub/Sub)

### Overview

Event Grid is a fully managed event routing service for reactive, event-driven architectures.

```
                    ┌─────────────────────────────────────────┐
                    │            Event Grid Topic             │
                    │                                         │
                    │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
┌──────────┐        │  │Analyzer │  │Summarize│  │ Review  │ │
│ Publisher│───────▶│  │   Sub   │  │   Sub   │  │   Sub   │ │
│  Agent   │        │  └────┬────┘  └────┬────┘  └────┬────┘ │
└──────────┘        └───────│────────────│────────────│──────┘
                            │            │            │
                            ▼            ▼            ▼
                    ┌───────────┐ ┌───────────┐ ┌───────────┐
                    │  Storage  │ │  Storage  │ │  Storage  │
                    │   Queue   │ │   Queue   │ │   Queue   │
                    │ (analyzer)│ │(summarizer)│ │(reviewer) │
                    └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                          │             │             │
                          ▼             ▼             ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Analyzer │ │Summarizer│ │ Reviewer │
                    │  Agent   │ │  Agent   │ │  Agent   │
                    └──────────┘ └──────────┘ └──────────┘
```

### Event Types

```
Pipeline.AnalyzeRequest   → Triggers Analyzer via analyzer-events queue
Pipeline.SummarizeRequest → Triggers Summarizer via summarizer-events queue
Pipeline.ReviewRequest    → Triggers Reviewer via reviewer-events queue
Pipeline.Complete         → Final result to results-events queue
```

### When to Use

✅ **Use Event Grid when:**
- Building reactive, event-driven systems
- Need fan-out to multiple subscribers
- Integrating Azure services (Blob triggers, etc.)
- Loose coupling between services
- Push-based event delivery

❌ **Avoid when:**
- Need to query or replay events
- High-throughput streaming (use Event Hubs)
- Complex message transformations

### Code Pattern

```python
from azure_clients import EventGridPipelineMessaging

messaging = EventGridPipelineMessaging(
    eventgrid_endpoint="https://egt-agents.eventgrid.azure.net/api/events",
    storage_account_name="stagents",
)

# Publish event
await messaging.publish(
    event_type="Pipeline.AnalyzeRequest",
    subject=f"/pipeline/{cid}/analyze",
    data={"document": document, "correlation_id": cid},
)

# Receive from Storage Queue (subscription endpoint)
msg = await messaging.receive_one("analyzer-events")
if msg:
    # Event Grid unwraps the data payload
    await process(msg)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Event Filtering** | Route by event type, subject, data fields |
| **Push Delivery** | Events pushed to subscribers |
| **Retry Policy** | Configurable exponential backoff |
| **Dead Letter** | Failed events to dead letter destination |
| **Webhooks** | Deliver to HTTP endpoints |

### Subscription Routing

```yaml
# Event Grid Subscription Configuration
analyzer-sub:
  event_types: [Pipeline.AnalyzeRequest]
  endpoint: Storage Queue (analyzer-events)
  
summarizer-sub:
  event_types: [Pipeline.SummarizeRequest]
  endpoint: Storage Queue (summarizer-events)
  
reviewer-sub:
  event_types: [Pipeline.ReviewRequest]
  endpoint: Storage Queue (reviewer-events)
```

---

## Pattern Selection Guide

### Decision Tree

```
Is ordering critical?
├── YES → Service Bus (with sessions)
└── NO
    ├── Need event replay?
    │   ├── YES → Event Hubs
    │   └── NO
    │       ├── Fan-out to multiple consumers?
    │       │   ├── YES → Event Grid
    │       │   └── NO → Service Bus
    │       └── High throughput (>10K/sec)?
    │           ├── YES → Event Hubs
    │           └── NO → Service Bus or Event Grid
```

### Scenario Recommendations

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Task queue with retry | Service Bus | DLQ, message lock, retry |
| Real-time analytics | Event Hubs | High throughput, replay |
| Azure Blob trigger | Event Grid | Native integration |
| Fan-out notifications | Event Grid | Multiple subscribers |
| Ordered processing | Service Bus | Session support |
| Event sourcing | Event Hubs | Retention, replay |

---

## Hybrid Patterns

### Stream + Queue Hybrid

Combine Event Hubs for ingestion with Service Bus for reliable processing:

```
┌──────────┐    Event Hubs     ┌──────────┐    Service Bus    ┌──────────┐
│ Ingestion│ ────────────────▶ │ Processor│ ────────────────▶ │  Worker  │
│ (many)   │   (high volume)   │ (filter) │   (reliable)      │ (slow)   │
└──────────┘                   └──────────┘                   └──────────┘
```

### Event-Driven Saga

Use Event Grid for choreography with Service Bus for commands:

```
Event Grid: "OrderPlaced" ──▶ Payment Service ──▶ "PaymentProcessed"
                                     │
                              Service Bus "ship-order"
                                     │
                                     ▼
Event Grid: "PaymentProcessed" ──▶ Shipping Service ──▶ "OrderShipped"
```

---

## Next Steps

- [Architecture Overview](overview.md): System architecture
- [Getting Started](../getting-started.md): Run the samples
- [Azure Setup](../azure-setup.md): Provision resources
