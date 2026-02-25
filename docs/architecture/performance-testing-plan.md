# Performance Testing Plan

## 1. Objectives

Compare **latency, throughput, and reliability** across:

- **4 Agent Frameworks**: Microsoft Agent Framework, LangGraph, Semantic Kernel, AutoGen
- **3 Messaging Services**: Azure Service Bus, Azure Event Hubs, Azure Event Grid
- **4 Topologies**:
  - Single-agent (baseline)
  - Multi-agent linear pipeline (point-to-point)
  - Multi-agent pub/sub (fan-out / fan-in)
  - Multi-agent choreography (event-driven chain)

The same business scenario ("Document Analyze → Summarize → Review") is used in every combination to enable apples-to-apples comparison.

---

## 2. Test Matrix

### 2.1 Topology × Messaging (per framework)

| Topology | No Messaging | Service Bus | Event Hubs | Event Grid |
|---|:---:|:---:|:---:|:---:|
| Single Agent (baseline) | ✅ | — | — | — |
| Linear Pipeline (P2P) | — | ✅ Queue | ✅ Hub→CG | ✅ Topic→Queue |
| Pub/Sub Fan-out | — | ✅ Topic/Sub | ✅ Hub→Multi-CG | ✅ Topic→Multi-Sub |
| Pub/Sub Fan-in | — | ✅ Multi-Queue→1 | ✅ Multi-Hub→1 | ✅ Multi-Event→1 |
| Choreography (chain) | — | — | — | ✅ Event chain |

### 2.2 Full Matrix (4 frameworks × above)

| Framework | Single | SB Linear | SB Pub/Sub | EH Linear | EH Pub/Sub | EG Linear | EG Pub/Sub | EG Choreo |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Microsoft Agent Framework | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LangGraph | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Semantic Kernel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AutoGen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Total: 4 frameworks × 8 topologies = 32 combinations**

---

## 3. Metrics Definition

### 3.1 Primary Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        End-to-End Pipeline Timeline                        │
│                                                                             │
│  [Request]──┬──[Analyzer Agent]──┬──[Msg Tx]──┬──[Summarizer]──┬──[Msg Tx]─┤
│             │                    │            │                │           │
│             ├─ TTFT_analyzer     │            ├─ TTFT_summ     │           │
│             ├─ LLM_latency       │            ├─ LLM_latency   │           │
│             ├─ agent_total       │            ├─ agent_total   │           │
│             │                    │            │                │           │
│             │              msg_send_latency   │          msg_send_latency  │
│             │              msg_delivery_lat   │          msg_delivery_lat  │
│             │              msg_receive_lat    │          msg_receive_lat   │
│                                                                             │
│  ──┬──[Msg Tx]──┬──[Reviewer Agent]──┬──[Response]                         │
│    │            │                    │                                      │
│    │            ├─ TTFT_reviewer     │                                      │
│    │            ├─ LLM_latency       │                                      │
│    │            ├─ agent_total       │                                      │
│    │            │                    │                                      │
│    │      msg_send_latency           │                                      │
│    │      msg_delivery_latency       │                                      │
│    │      msg_receive_latency        │                                      │
│                                                                             │
│  ◄──────────────── e2e_pipeline_latency ──────────────────────────────────► │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Metric | Description | Unit |
|---|---|---|
| **TTFT** (Time To First Token) | Time from LLM API call to first streamed token | ms |
| **LLM Latency** | Time from LLM API call to full response completion | ms |
| **Token Generation Rate** | Output tokens per second (after first token) | tokens/s |
| **Agent Processing Time** | Total time an agent takes (prompt build + LLM + tool calls + post-processing) | ms |
| **Message Send Latency** | Time to publish a message to the messaging service | ms |
| **Message Delivery Latency** | Time from publish to message becoming available to consumer | ms |
| **Message Receive Latency** | Time to receive/dequeue a message from the messaging service | ms |
| **Messaging Round-Trip** | Send + Delivery + Receive (full messaging overhead) | ms |
| **E2E Pipeline Latency** | Total time from initial request to final review result | ms |
| **Input/Output Token Count** | Number of tokens consumed per agent per stage | count |

### 3.2 Secondary Metrics

| Metric | Description | Unit |
|---|---|---|
| **Cold Start Latency** | First invocation after deployment (agent + connection init) | ms |
| **Warm Start Latency** | Subsequent invocation (reused connections) | ms |
| **P50 / P95 / P99 Latency** | Percentile distribution per metric | ms |
| **Throughput** | Concurrent pipeline executions per minute | pipelines/min |
| **Error Rate** | Percentage of failed pipeline runs | % |
| **Message Retry Count** | Number of retries before successful delivery | count |
| **DLQ Message Count** | Messages landing in Dead Letter Queue | count |
| **Memory Usage** | Peak RSS per agent process | MB |

### 3.3 Resiliency Metrics

| Metric | Description | Unit |
|---|---|---|
| **Recovery Time** | Time from agent restart to processing resumed | ms |
| **Message Preservation Rate** | % of messages retained during agent downtime | % |
| **Replay Completeness** | % of checkpointed events successfully replayed (Event Hubs) | % |

---

## 4. Measurement Segments (구간 정의)

### 4.1 Linear Pipeline Segments (Point-to-Point)

Each pipeline run is broken into **12 measurable segments**:

```
Segment ID   Description                          Where Measured
─────────────────────────────────────────────────────────────────
S1           Client → Request Submission          Client-side
S2           Analyzer: Prompt Construction        Agent process
S3           Analyzer: TTFT                       LLM streaming callback
S4           Analyzer: Full LLM Response          LLM streaming callback
S5           Analyzer → Messaging: Send           Messaging client
S6           Messaging: Delivery (in-transit)     Timestamp diff (send vs receive)
S7           Messaging → Summarizer: Receive      Messaging client
S8           Summarizer: TTFT + Full Response     LLM streaming callback
S9           Summarizer → Messaging: Send         Messaging client
S10          Messaging → Reviewer: Receive        Messaging client (includes delivery)
S11          Reviewer: TTFT + Full Response       LLM streaming callback
S12          Reviewer → Final Result Delivery     Messaging client / Client-side
```

### 4.2 Pub/Sub Fan-out Segments

Analyzer publishes once → multiple subscribers receive and process in parallel.

```
                              ┌──[Sub A: Summarizer-Style]──┐
[Analyzer]──publish──→ Topic ─┼──[Sub B: Translator]────────┼──→ collect
                              └──[Sub C: Sentiment]─────────┘
```

```
Segment ID   Description                              Where Measured
─────────────────────────────────────────────────────────────────────────
PF1          Publisher: Prepare + Send                  Agent process
PF2          Publish Latency (client → broker accept)   Messaging client
PF3          Topic/Hub Routing Overhead                 Broker-side (est.)
PF4-A        Subscriber A: Delivery Latency             Timestamp diff
PF4-B        Subscriber B: Delivery Latency             Timestamp diff
PF4-C        Subscriber C: Delivery Latency             Timestamp diff
PF5-A        Subscriber A: Receive + Dequeue            Messaging client
PF5-B        Subscriber B: Receive + Dequeue            Messaging client
PF5-C        Subscriber C: Receive + Dequeue            Messaging client
PF6-A        Subscriber A: Agent Processing (TTFT+LLM)  LLM callback
PF6-B        Subscriber B: Agent Processing (TTFT+LLM)  LLM callback
PF6-C        Subscriber C: Agent Processing (TTFT+LLM)  LLM callback
PF7          Fan-out Spread (max - min delivery time)   Derived
PF8          All Subscribers Complete (wall clock)       Client-side
```

**Key Pub/Sub Fan-out Metrics:**

| Metric | Description | Unit |
|---|---|---|
| **Fan-out Spread** | Difference between first and last subscriber delivery | ms |
| **Subscription Filtering Overhead** | Added latency from event type / subject filters | ms |
| **Parallel Processing Efficiency** | Wall-clock time vs. sum of individual agent times | ratio |
| **Subscriber Skew** | Std deviation of delivery times across subscribers | ms |
| **Per-Subscriber TTFT** | TTFT measured independently per subscriber agent | ms |

### 4.3 Pub/Sub Fan-in Segments

Multiple agents publish results → single collector aggregates.

```
[Agent A: Analyzer] ──publish──→
[Agent B: Summarizer]──publish──→  Collector Queue/Hub  ──→ [Orchestrator]
[Agent C: Reviewer] ──publish──→
```

```
Segment ID   Description                              Where Measured
─────────────────────────────────────────────────────────────────────────
FI1-A        Agent A: Processing + Publish              Agent process
FI1-B        Agent B: Processing + Publish              Agent process
FI1-C        Agent C: Processing + Publish              Agent process
FI2-A        Agent A → Collector: Delivery Latency      Timestamp diff
FI2-B        Agent B → Collector: Delivery Latency      Timestamp diff
FI2-C        Agent C → Collector: Delivery Latency      Timestamp diff
FI3          Collector: First Message Received           Messaging client
FI4          Collector: Last Message Received            Messaging client
FI5          Collector: Aggregation Processing           Agent process
FI6          Fan-in Completion (all results gathered)    Client-side
```

**Key Pub/Sub Fan-in Metrics:**

| Metric | Description | Unit |
|---|---|---|
| **Fan-in Wait Time** | Time from first to last result arrival at collector | ms |
| **Aggregation Latency** | Collector processing time after all results received | ms |
| **Straggler Penalty** | Extra wait caused by slowest agent vs. average | ms |
| **Message Ordering** | Were results received in send order? (Event Hubs partition) | bool |

### 4.4 Choreography Segments (Event-Driven Chain)

No central orchestrator — each agent reacts to events and publishes next event.

```
[Analyzer]──AnalysisCompleted──→ Event Grid ──→ [Summarizer]
                                                    │
                              SummaryCompleted ◄─────┘
                                    │
                              Event Grid ──→ [Reviewer]
                                                 │
                            ReviewCompleted ◄─────┘
```

```
Segment ID   Description                              Where Measured
─────────────────────────────────────────────────────────────────────────
CH1          Trigger Event Published                    Client-side
CH2          Event Grid → Analyzer: Delivery + Trigger  Storage Queue poll
CH3          Analyzer: Agent Processing (TTFT+LLM)      LLM callback
CH4          Analyzer: Publish AnalysisCompleted         Event Grid SDK
CH5          Event Grid Routing (internal)               Timestamp diff
CH6          Event Grid → Summarizer: Delivery           Storage Queue poll
CH7          Summarizer: Agent Processing (TTFT+LLM)     LLM callback
CH8          Summarizer: Publish SummaryCompleted         Event Grid SDK
CH9          Event Grid → Reviewer: Delivery              Storage Queue poll
CH10         Reviewer: Agent Processing (TTFT+LLM)        LLM callback
CH11         Reviewer: Publish ReviewCompleted             Event Grid SDK
CH12         Final Event → Result Collector                Storage Queue poll
```

**Key Choreography Metrics:**

| Metric | Description | Unit |
|---|---|---|
| **Event Routing Latency** | Event Grid internal routing per hop | ms |
| **Hop Count** | Number of event hops in the chain | count |
| **Cumulative Routing Overhead** | Sum of all Event Grid routing latencies | ms |
| **Choreography vs Orchestrator** | E2E comparison with linear pipeline | ms delta |

---

## 5. Instrumentation Architecture

### 5.1 Approach: OpenTelemetry + Custom Spans

```python
# Layered tracing strategy
#
# Layer 1: OpenTelemetry auto-instrumentation (HTTP, Azure SDK)
# Layer 2: Custom spans for agent-level segments
# Layer 3: Custom metrics for TTFT, token rates, messaging latency
# Layer 4: Structured logs with correlationId for cross-agent tracing
```

### 5.2 Core Instrumentation Module

```
shared/
├── benchmarks/
│   ├── __init__.py
│   ├── tracer.py            # OpenTelemetry tracer setup
│   ├── metrics.py           # Custom metrics (TTFT, token rate, etc.)
│   ├── timer.py             # High-resolution timer context manager
│   ├── llm_callback.py      # Streaming callback to capture TTFT
│   ├── msg_instrumentor.py  # Messaging send/receive latency wrapper
│   ├── collector.py         # Results aggregation & export
│   └── report.py            # Comparison report generator
```

### 5.3 TTFT Measurement (Key Implementation)

```python
import time
from dataclasses import dataclass, field

@dataclass
class TTFTResult:
    ttft_ms: float = 0.0            # Time to first token
    total_latency_ms: float = 0.0   # Time to full response
    output_tokens: int = 0
    tokens_per_second: float = 0.0  # After first token

class TTFTCallback:
    """Streaming callback that captures TTFT and token generation rate."""

    def __init__(self):
        self._start_time: float = 0.0
        self._first_token_time: float | None = None
        self._token_count: int = 0

    def start(self):
        self._start_time = time.perf_counter()
        self._first_token_time = None
        self._token_count = 0

    def on_token(self, token: str):
        if self._first_token_time is None:
            self._first_token_time = time.perf_counter()
        self._token_count += 1

    def result(self) -> TTFTResult:
        end = time.perf_counter()
        ttft = ((self._first_token_time - self._start_time) * 1000
                if self._first_token_time else 0)
        total = (end - self._start_time) * 1000
        gen_time = (end - self._first_token_time) if self._first_token_time else 0
        tps = self._token_count / gen_time if gen_time > 0 else 0
        return TTFTResult(
            ttft_ms=ttft,
            total_latency_ms=total,
            output_tokens=self._token_count,
            tokens_per_second=tps,
        )
```

### 5.4 Messaging Latency Measurement

```python
# Key: Embed timestamps in message properties/headers for cross-process measurement

message_properties = {
    "bench_send_ts": str(time.time_ns()),  # nanosecond-precision
    "correlation_id": correlation_id,
    "trace_id": trace_id,
}

# On receive side:
send_ts = int(msg.properties["bench_send_ts"])
receive_ts = time.time_ns()
delivery_latency_ms = (receive_ts - send_ts) / 1_000_000
```

> **Clock Sync Note**: For cross-process latency, NTP-synced clocks introduce ~1-5ms jitter.
> For high-accuracy: run sender and receiver on the same VM, or use relative measurements.

---

## 6. Test Scenarios

### 6.1 Scenario A — Single Agent Baseline (No Messaging)

**Purpose**: Isolate pure LLM + framework overhead without messaging.

```
[Input Document] → [Single Agent: Analyze+Summarize+Review] → [Result]
```

| Measured | Details |
|---|---|
| TTFT | Per-stage prompt within the single agent |
| LLM Latency | Full response time for each internal step |
| Framework Overhead | Agent initialization, tool dispatch, state management |

### 6.2 Scenario B — Multi-Agent Pipeline (with Messaging)

**Purpose**: Measure full pipeline with messaging overhead.

```
[Analyzer] ──messaging──→ [Summarizer] ──messaging──→ [Reviewer]
```

| Measured | Details |
|---|---|
| All Segment S1-S12 | Full pipeline timing |
| Messaging Overhead | Comparison vs. single-agent to isolate messaging cost |

### 6.3 Scenario C — Pub/Sub Fan-out

**Purpose**: Measure fan-out delivery spread and parallel subscriber performance.

```
                                ┌──[Summarizer Agent]──┐
[Analyzer Agent]──publish──→ ───┼──[Translator Agent]──┼──→ (independent results)
                                └──[Sentiment Agent]───┘
```

| Measured | Details |
|---|---|
| Fan-out Spread | Delivery time difference: first vs last subscriber |
| Per-Subscriber TTFT | Each subscriber's independent TTFT + LLM latency |
| Parallel Efficiency | Max(subscriber latency) vs sum(all) |
| Subscription Filter Cost | With vs without event type filtering |

**Messaging-specific considerations:**

| Service | Pub/Sub Mechanism | Notes |
|---|---|---|
| Service Bus | Topic + 3 Subscriptions | SQL filter rules per subscription |
| Event Hubs | Single Hub + 3 Consumer Groups | Same partition, different CGs |
| Event Grid | Topic + 3 Subscriptions (type filter) | Push to separate Storage Queues |

### 6.4 Scenario D — Pub/Sub Fan-in

**Purpose**: Measure aggregation latency when multiple agents publish to a single collector.

```
[Analyzer] ──────→
[Summarizer]─────→  Collector Queue  ──→ [Orchestrator Agent]
[Reviewer] ──────→
```

| Measured | Details |
|---|---|
| Fan-in Wait Time | First result arrival → last result arrival |
| Straggler Penalty | Slowest agent delta vs average |
| Aggregation Latency | Orchestrator processing after all results collected |
| Ordering Guarantee | Were messages received in expected order? |

### 6.5 Scenario E — Choreography (Event-Driven Chain)

**Purpose**: Measure cascading event-driven agent activation without central orchestration.

```
TaskSubmitted → [Analyzer] → AnalysisCompleted → [Summarizer] → SummaryCompleted → [Reviewer]
```

| Measured | Details |
|---|---|
| Per-Hop Routing Latency | Event Grid internal routing time per event |
| Cumulative Overhead | Total Event Grid overhead across all hops |
| vs. Linear Pipeline | Compare with direct queue-based pipeline |
| Cold Trigger Latency | Time from event publish to agent activation (polling interval) |

### 6.6 Scenario F — Concurrent Load

**Purpose**: Measure throughput and latency under concurrent load.

| Load Level | Concurrent Pipelines |
|---|---|
| Light | 1 (sequential baseline) |
| Medium | 5 concurrent |
| Heavy | 10 concurrent |
| Stress | 20 concurrent |

Apply to **all topologies** (linear, fan-out, fan-in, choreography).

### 6.7 Scenario G — Resiliency (Agent Failure & Recovery)

**Purpose**: Measure message preservation and recovery behavior.

```
1. Start pipeline, let Analyzer complete and send message
2. Kill Summarizer process
3. Wait 30s
4. Restart Summarizer
5. Measure: time to resume, message loss, final completion
```

---

## 7. Test Execution Plan

### 7.1 Environment

| Component | Specification |
|---|---|
| Region | Korea Central (same as Azure resources) |
| Client Machine | Azure VM Standard_D4s_v5 (same region, minimize network variance) |
| Python | 3.11+ |
| Clock Sync | chrony NTP service (< 1ms drift) |
| Warm-up Runs | 3 (discarded) |
| Measured Runs | 30 per combination |
| Cool-down | 5s between runs |

### 7.2 Test Input (Fixed Document)

Use a standardized input document across all tests:

| Property | Value |
|---|---|
| Document Type | Technical report (English) |
| Word Count | ~500 words |
| Complexity | Medium (mixed entities, numbers, dates) |

### 7.3 Execution Order

```
Phase 1: Single-Agent Baseline (4 frameworks × 30 runs = 120 runs)
   ├── Microsoft Agent Framework
   ├── LangGraph
   ├── Semantic Kernel
   └── AutoGen

Phase 2: Linear Pipeline (4 frameworks × 3 messaging × 30 runs = 360 runs)
   ├── Service Bus Queue (point-to-point)
   ├── Event Hubs (hub → consumer group)
   └── Event Grid (topic → storage queue)

Phase 3: Pub/Sub Fan-out (4 frameworks × 3 messaging × 30 runs = 360 runs)
   ├── Service Bus Topic + 3 Subscriptions
   ├── Event Hubs + 3 Consumer Groups
   └── Event Grid + 3 Filtered Subscriptions

Phase 4: Pub/Sub Fan-in (4 frameworks × 3 messaging × 30 runs = 360 runs)
   ├── 3 agents → Service Bus Queue → Orchestrator
   ├── 3 agents → Event Hub → Orchestrator
   └── 3 agents → Event Grid → Orchestrator

Phase 5: Choreography (4 frameworks × Event Grid × 30 runs = 120 runs)
   └── Event-driven chain (TaskSubmitted → Analysis → Summary → Review)

Phase 6: Concurrent Load (selected combos × 4 load levels × 10 runs)

Phase 7: Resiliency Tests (4 frameworks × 3 messaging)

Total estimated runs: ~1,400+ pipeline executions
```

---

## 8. Results Collection & Storage

### 8.1 Output Schema

Each run produces a JSON record:

```json
{
  "run_id": "uuid",
  "timestamp": "2026-02-24T12:00:00Z",
  "framework": "semantic-kernel",
  "messaging": "servicebus",
  "scenario": "multi-agent-pipeline",
  "concurrency": 1,
  "input_doc_hash": "sha256:...",
  "segments": {
    "s1_request_submit_ms": 2.1,
    "s2_analyzer_prompt_build_ms": 5.3,
    "s3_analyzer_ttft_ms": 245.0,
    "s4_analyzer_llm_total_ms": 1820.0,
    "s4_analyzer_output_tokens": 312,
    "s4_analyzer_tokens_per_sec": 198.1,
    "s5_msg_send_ms": 12.4,
    "s6_msg_delivery_ms": 8.7,
    "s7_msg_receive_ms": 3.2,
    "s8_summarizer_ttft_ms": 230.0,
    "s8_summarizer_llm_total_ms": 1450.0,
    "s8_summarizer_output_tokens": 185,
    "s8_summarizer_tokens_per_sec": 151.6,
    "s9_msg_send_ms": 11.8,
    "s10_msg_receive_ms": 9.1,
    "s11_reviewer_ttft_ms": 210.0,
    "s11_reviewer_llm_total_ms": 980.0,
    "s11_reviewer_output_tokens": 120,
    "s11_reviewer_tokens_per_sec": 156.1,
    "s12_result_delivery_ms": 4.5
  },
  "derived": {
    "e2e_pipeline_ms": 4560.0,
    "total_messaging_overhead_ms": 45.2,
    "total_llm_time_ms": 4250.0,
    "messaging_overhead_pct": 1.0,
    "framework_overhead_ms": 264.8
  },
  "metadata": {
    "trace_id": "w3c-trace-id",
    "correlation_id": "uuid",
    "error": null
  }
}
```

### 8.2 Storage

```
benchmarks/
├── results/
│   ├── raw/                    # Individual JSON records per run
│   │   └── {framework}-{messaging}-{timestamp}.jsonl
│   ├── aggregated/             # Aggregated stats (P50/P95/P99/mean/std)
│   │   └── summary.json
│   └── reports/                # Generated comparison reports
│       ├── framework-comparison.md
│       ├── messaging-comparison.md
│       └── charts/             # PNG/SVG charts
```

---

## 9. Analysis & Reporting

### 9.1 Comparison Dimensions

| Report | X-Axis | Y-Axis | Group By |
|---|---|---|---|
| **Framework TTFT** | Framework | TTFT (P50/P95) | Messaging |
| **Messaging Overhead** | Messaging Service | Overhead ms | Framework |
| **E2E Pipeline** | Framework × Messaging | Total Latency | — |
| **Throughput** | Concurrency Level | Pipelines/min | Framework × Messaging |
| **Token Rate** | Framework | tokens/s | — |
| **Breakdown Waterfall** | Segment | Cumulative ms | Per combination |
| **Fan-out Spread** | Messaging Service | Spread ms (P50/P95) | Subscriber count |
| **Fan-in Wait** | Messaging Service | Wait ms | Framework |
| **Choreography Overhead** | Hop Count | Cumulative routing ms | vs. Linear |
| **Topology Comparison** | Topology | E2E Latency | Framework × Messaging |

### 9.2 Key Questions to Answer

1. **Which framework has the lowest TTFT?**
   - Is it consistent across messaging services?

2. **What is the real messaging overhead per service?**
   - Service Bus vs Event Hubs vs Event Grid add how many ms?
   - Is overhead constant or does it grow under load?

3. **Which combination has the best E2E latency?**
   - Framework × Messaging leaderboard

4. **Where does time go?**
   - Waterfall breakdown: LLM (dominant) vs Messaging vs Framework overhead
   - Identify optimization targets

5. **How does concurrency affect performance?**
   - Linear scaling? Degradation point?

6. **Resiliency cost**: Does reliable messaging add meaningful latency vs. direct calls?

7. **Pub/Sub fan-out: How evenly do subscribers receive?**
   - Service Bus Topic vs Event Hubs CG vs Event Grid — which has the lowest spread?
   - Does subscription filtering add measurable overhead?

8. **Pub/Sub fan-in: What is the straggler penalty?**
   - How long does the collector wait for the slowest agent?
   - Does messaging service affect ordering/arrival patterns?

9. **Choreography vs Orchestrator: What is the overhead of event-driven chaining?**
   - Cumulative Event Grid routing overhead across 3 hops
   - Storage Queue polling interval impact on perceived latency
   - Is choreography viable for latency-sensitive workloads?

### 9.3 Visualization

```python
# Tool: matplotlib + seaborn for charts, rich for terminal tables

# Chart 1: Grouped bar chart — TTFT by framework, grouped by messaging
# Chart 2: Box plot — E2E latency distribution per combination
# Chart 3: Stacked bar — Segment breakdown (waterfall) per combination
# Chart 4: Line chart — Latency vs concurrency
# Chart 5: Heatmap — Framework × Messaging latency matrix
```

---

## 10. Implementation Phases

### Phase 1: Instrumentation Framework (Week 1)
- [ ] `shared/benchmarks/timer.py` — High-res timer context manager
- [ ] `shared/benchmarks/llm_callback.py` — TTFT streaming callback (per framework)
- [ ] `shared/benchmarks/msg_instrumentor.py` — Messaging latency wrappers
- [ ] `shared/benchmarks/collector.py` — JSON result collector
- [ ] `shared/benchmarks/tracer.py` — OpenTelemetry setup + Application Insights export

### Phase 2: Single-Agent Samples (Week 2)
- [ ] Build 4 single-agent samples (one per framework)
- [ ] Embed instrumentation in each
- [ ] Run baseline benchmarks

### Phase 3: Multi-Agent Linear Pipeline (Week 3)
- [ ] Build 12 linear pipeline samples (4 frameworks × 3 messaging)
- [ ] Embed full S1-S12 segment instrumentation
- [ ] Run pipeline benchmarks

### Phase 4: Pub/Sub + Choreography Samples (Week 4-5)
- [ ] Build fan-out samples (4 frameworks × 3 messaging = 12)
- [ ] Build fan-in samples (4 frameworks × 3 messaging = 12)
- [ ] Build choreography samples (4 frameworks × Event Grid = 4)
- [ ] Embed PF/FI/CH segment instrumentation
- [ ] Run pub/sub benchmarks

### Phase 5: Load & Resiliency Tests (Week 6)
- [ ] Concurrent load test harness
- [ ] Resiliency test automation (agent kill/restart scripts)
- [ ] Run all scenarios

### Phase 6: Analysis & Reporting (Week 7)
- [ ] Aggregation scripts
- [ ] Chart generation (including pub/sub-specific charts)
- [ ] Topology comparison report (linear vs fan-out vs fan-in vs choreography)
- [ ] Findings documentation

---

## 11. Key Design Decisions

### Same LLM Config
All frameworks use the same Azure OpenAI deployment (`gpt-4o`) with identical parameters:
- `temperature=0.7`
- `max_tokens=1024`
- Streaming enabled (for TTFT measurement)

### Same Prompts
System and user prompts are shared across frameworks (stored in `shared/prompts/`).

### Idempotent Runs
Each run uses the same input document. Output may vary due to LLM non-determinism, but timing is the focus.

### Statistical Rigor
- 30 runs per combination (sufficient for P95/P99 estimates)
- 3 warm-up runs discarded
- Report mean, median, P50, P95, P99, std dev
- Flag outliers (> 3σ from mean)
