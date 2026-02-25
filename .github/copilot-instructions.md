# Agents on Azure - 프로젝트 지침서

## 1. 프로젝트 개요

이 프로젝트는 다양한 AI Agent 프레임워크를 Azure 클라우드 리소스와 결합하여, **느슨한 연결(Loose Coupling)** 기반의 **신뢰성 있는 멀티 에이전트 시스템** 예제를 구축하는 것을 목표로 한다.

### 핵심 목표
- 4가지 주요 에이전트 프레임워크(Microsoft Agent Framework, LangGraph, Semantic Kernel, AutoGen)에 대한 실용적 예제 제공
- Azure 메시징 서비스(Service Bus, Event Hubs, Event Grid)를 활용한 에이전트 간 비동기 통신 패턴 구현
- **느슨한 연결(Loose Coupling)** 을 통한 복원력(Resiliency) 시연: 에이전트 장애 시에도 메시지 유실 없이 복구 후 자동 처리
- 프로덕션 환경에서 활용 가능한 확장성, 내결함성, 관찰 가능성을 갖춘 아키텍처 제시

### 공통 시연 시나리오

모든 샘플은 동일한 비즈니스 시나리오를 구현하여 프레임워크 간 비교를 용이하게 한다:

**"문서 분석-요약-리뷰 파이프라인"**
1. **Analyzer Agent**: 입력 문서를 분석하여 핵심 정보를 추출
2. **Summarizer Agent**: 분석 결과를 기반으로 요약 생성
3. **Reviewer Agent**: 요약의 품질을 검토하고 최종 결과 확정

**복원력(Resiliency) 시연 포인트**:
- 에이전트 B(Summarizer)가 다운된 상태에서 에이전트 A(Analyzer)가 메시지 전송 → 메시지는 큐/토픽에 보존
- 에이전트 B 복구 후 보존된 메시지를 자동으로 처리하여 파이프라인 완료
- Dead Letter Queue를 통한 실패 메시지 격리 및 재처리
- 메시지 TTL 만료, 재시도 한도 초과 시의 graceful degradation

### 기술 스택
- **언어**: Python (전체 프로젝트 통일)
- **가상환경 관리**: `uv` (빠르고 신뢰성 있는 Python 패키지 관리자)
- **패키지 정의**: `pyproject.toml`

### 문서 작성 언어 규칙
- **지침서(copilot-instructions.md)**: 한국어로 작성
- **그 외 모든 파일**: 영어로 작성 (README.md, 코드 주석, 커밋 메시지, .env.example, 스크립트 등)

---

## 2. 프로젝트 디렉터리 구조

```
agents-on-azure/
├── .github/
│   ├── copilot-instructions.md          # 이 지침서
│   └── workflows/                       # CI/CD 파이프라인
├── docs/
│   ├── architecture/                    # 아키텍처 다이어그램 및 설계 문서
│   │   ├── overview.md
│   │   ├── messaging-patterns.md
│   │   └── diagrams/
│   ├── getting-started.md               # 빠른 시작 가이드
│   └── azure-setup.md                   # Azure 리소스 프로비저닝 가이드
├── infra/
│   ├── bicep/                           # Azure Bicep IaC 템플릿
│   │   ├── main.bicep
│   │   ├── modules/
│   │   │   ├── service-bus.bicep
│   │   │   ├── event-hubs.bicep
│   │   │   ├── event-grid.bicep
│   │   │   ├── openai.bicep
│   │   │   ├── app-insights.bicep
│   │   │   └── container-apps.bicep
│   │   └── parameters/
│   │       ├── dev.bicepparam
│   │       └── prod.bicepparam
│   └── scripts/                         # 배포 스크립트
│       ├── deploy.sh
│       └── teardown.sh
├── samples/
│   ├── microsoft-agent-framework/       # Microsoft Agent Framework 예제
│   │   ├── single-agent/
│   │   ├── multi-agent-servicebus/
│   │   ├── multi-agent-eventhub/
│   │   └── multi-agent-eventgrid/
│   ├── langgraph/                       # LangGraph 예제
│   │   ├── single-agent/
│   │   ├── multi-agent-servicebus/
│   │   ├── multi-agent-eventhub/
│   │   └── multi-agent-eventgrid/
│   ├── semantic-kernel/                 # Semantic Kernel 예제
│   │   ├── single-agent/
│   │   ├── multi-agent-servicebus/
│   │   ├── multi-agent-eventhub/
│   │   └── multi-agent-eventgrid/
│   └── autogen/                         # AutoGen 예제
│       ├── single-agent/
│       ├── multi-agent-servicebus/
│       ├── multi-agent-eventhub/
│       └── multi-agent-eventgrid/
├── shared/                              # 공유 패키지 (uv workspace 멤버)
│   ├── pyproject.toml                   # 공유 패키지 정의
│   ├── contracts/                       # 에이전트 간 공유 메시지 스키마
│   │   └── message_schemas.py
│   ├── azure_clients/                   # Azure 서비스 클라이언트 래퍼
│   │   ├── servicebus_client.py
│   │   ├── eventhub_client.py
│   │   └── eventgrid_client.py
│   └── utils/                           # 공통 유틸리티
├── tests/
│   ├── integration/
│   └── e2e/
├── .env.example                         # 환경 변수 템플릿
├── README.md
└── pyproject.toml
```

---

## 3. 에이전트 프레임워크별 가이드라인

### 3.1 Microsoft Agent Framework (Azure AI Agent Service)

- **언어**: Python
- **SDK**: `azure-ai-projects`, `azure-identity`
- **핵심 개념**: Azure AI Foundry 프로젝트 내에서 에이전트를 생성하고, 도구(Tools)와 연결하여 작업을 수행
- **멀티 에이전트 패턴**: 
  - 에이전트 간 작업 위임(delegation)을 Azure Service Bus 큐를 통해 구현
  - 각 에이전트는 독립적인 Service Bus 큐를 구독하며, 작업 완료 시 결과를 응답 큐로 전송
- **코드 작성 규칙**:
  - `AIProjectClient`를 사용하여 에이전트 생성 및 관리
  - `DefaultAzureCredential`을 통한 인증 필수 (연결 문자열 사용 금지)
  - 에이전트의 도구 정의는 별도 모듈로 분리

### 3.2 LangGraph

- **언어**: Python
- **패키지**: `langgraph`, `langchain-openai`, `langchain-community`
- **핵심 개념**: 상태 기반 그래프(StateGraph)로 에이전트 흐름을 정의하고, 노드 간 제어 흐름을 명시적으로 관리
- **멀티 에이전트 패턴**:
  - 각 에이전트를 LangGraph의 노드로 정의
  - 에이전트 간 통신은 Azure Event Grid 이벤트를 통해 트리거
  - 그래프 상태(State)는 Azure Cosmos DB 또는 Redis에 영속화
- **코드 작성 규칙**:
  - `StateGraph`를 사용하여 워크플로우 정의
  - 각 노드 함수는 순수 함수(pure function)로 작성하여 테스트 용이성 확보
  - 체크포인트(checkpointer)를 반드시 설정하여 상태 복원 가능하도록 구성
  - Azure OpenAI 엔드포인트 사용 (`AzureChatOpenAI`)

### 3.3 Semantic Kernel

- **언어**: Python
- **패키지**: `semantic-kernel`
- **핵심 개념**: 커널(Kernel)에 플러그인(Plugin)과 AI 서비스를 등록하고, 에이전트가 이를 활용하여 작업 수행
- **멀티 에이전트 패턴**:
  - `AgentGroupChat`을 사용한 에이전트 간 대화 오케스트레이션
  - Azure Service Bus Topic/Subscription을 사용하여 에이전트 간 pub/sub 통신 구현
  - `SelectionStrategy`와 `TerminationStrategy`를 커스터마이징하여 에이전트 선택 및 종료 로직 제어
- **코드 작성 규칙**:
  - `kernel_function` 데코레이터를 사용하여 플러그인 함수 정의
  - `AzureChatCompletion` 서비스를 통한 Azure OpenAI 연동
  - 프롬프트는 YAML 또는 별도 템플릿 파일로 관리

### 3.4 AutoGen

- **언어**: Python
- **패키지**: `autogen-agentchat`, `autogen-ext`
- **핵심 개념**: 대화형(Conversational) 에이전트를 정의하고, 그룹챗 매니저를 통해 멀티 에이전트 협업을 오케스트레이션
- **멀티 에이전트 패턴**:
  - `SelectorGroupChat` 또는 `RoundRobinGroupChat`을 사용한 에이전트 조율
  - Azure Event Hubs를 활용한 이벤트 스트리밍 기반 에이전트 간 통신
  - 대규모 이벤트 처리 시 Event Hubs 파티션을 활용한 병렬 처리
- **코드 작성 규칙**:
  - `AssistantAgent`에 `model_client`로 `AzureOpenAIChatCompletionClient` 사용
  - 도구(Tool)는 Python 함수로 정의하고 에이전트에 등록
  - `TextMentionTermination` 등 종료 조건을 명시적으로 설정
  - `Console` 스트리밍으로 실행 과정 시각화

---

## 4. Azure 메시징 서비스 활용 가이드

### 4.1 Azure Service Bus

**용도**: 신뢰성 있는 1:1 또는 1:N 에이전트 간 메시지 전달

```
┌──────────┐    Queue/Topic     ┌──────────┐
│ Agent A  │ ──────────────────→│ Agent B  │
│(Producer)│                    │(Consumer)│
└──────────┘                    └──────────┘
```

- **Queue**: 1:1 점대점(point-to-point) 통신. 작업 지시 및 결과 반환에 사용
- **Topic/Subscription**: 1:N pub/sub 통신. 여러 에이전트에게 브로드캐스트할 때 사용
- **활용 시나리오**:
  - 에이전트 A가 분석 작업을 요청하면 Service Bus Queue에 메시지 전송
  - Agent B가 큐에서 메시지를 수신하여 작업 수행 후 결과를 응답 큐로 전송
  - Dead Letter Queue(DLQ)를 활용한 실패 메시지 처리
- **구현 규칙**:
  - `azure-servicebus` SDK 사용
  - 세션(Session) 기능을 활용하여 관련 메시지를 그룹핑
  - 메시지 TTL 및 재시도 정책 반드시 설정
  - `DefaultAzureCredential` 인증 사용 (connection string 사용 금지)

### 4.2 Azure Event Hubs

**용도**: 대용량 이벤트 스트리밍 기반의 에이전트 간 실시간 데이터 파이프라인

```
┌──────────┐                              ┌──────────┐
│ Agent A  │ ──→ Event Hub ──→ Consumer ──→│ Agent B  │
│(Producer)│     (Partitioned)   Group     │(Consumer)│
└──────────┘                              └──────────┘
```

- **활용 시나리오**:
  - 여러 에이전트가 생성하는 이벤트를 중앙 집중식으로 수집
  - 이벤트 스트림을 기반으로 실시간 분석 에이전트 트리거
  - 파티션을 활용한 병렬 처리로 대규모 에이전트 팜 구성
- **구현 규칙**:
  - `azure-eventhub` SDK 사용
  - Consumer Group을 에이전트 유형별로 분리
  - 체크포인트를 Azure Blob Storage에 저장하여 이벤트 처리 위치 추적
  - 파티션 키를 에이전트 ID 또는 세션 ID로 설정하여 순서 보장

### 4.3 Azure Event Grid

**용도**: 이벤트 기반(Event-Driven) 에이전트 활성화 및 리액티브 패턴

```
┌──────────┐    Event Grid     ┌──────────────┐    Webhook/     ┌──────────┐
│  Source   │ ──────────────→  │  Topic +      │ ──────────────→│ Agent    │
│  Agent   │    (Publish)      │  Subscription │   (Push)       │(Handler) │
└──────────┘                   └──────────────┘                └──────────┘
```

- **활용 시나리오**:
  - Azure 리소스 변경 이벤트를 감지하여 에이전트 자동 실행
  - 에이전트 작업 완료 이벤트를 다른 에이전트에게 팬아웃(fan-out)
  - 커스텀 토픽을 사용한 도메인 이벤트 기반 에이전트 오케스트레이션
- **구현 규칙**:
  - `azure-eventgrid` SDK 사용
  - CloudEvents 스키마 표준 사용
  - 이벤트 필터링을 활용하여 에이전트별 관심 이벤트만 수신
  - 재시도 정책 및 Dead Letter 대상 설정
  - Webhook 엔드포인트는 Azure Functions 또는 Container Apps로 호스팅

---

## 5. 메시지 스키마(Contract) 표준

모든 에이전트 간 통신 메시지는 아래 표준 스키마를 따른다.

### 5.1 기본 메시지 구조

```json
{
  "messageId": "uuid-v4",
  "correlationId": "uuid-v4",
  "timestamp": "2026-02-24T12:00:00Z",
  "source": {
    "agentId": "agent-analyzer-01",
    "framework": "semantic-kernel",
    "instanceId": "instance-uuid"
  },
  "destination": {
    "agentId": "agent-summarizer-01",
    "queue": "summarizer-tasks"
  },
  "messageType": "TaskRequest | TaskResponse | Event | Heartbeat",
  "payload": {
    "taskType": "summarize | analyze | translate | review",
    "input": {},
    "context": {},
    "constraints": {
      "timeout_seconds": 300,
      "max_retries": 3,
      "priority": "high | medium | low"
    }
  },
  "metadata": {
    "traceId": "w3c-trace-id",
    "spanId": "span-id",
    "version": "1.0"
  }
}
```

### 5.2 메시지 타입별 규격

| 메시지 타입 | 용도 | 필수 필드 |
|---|---|---|
| `TaskRequest` | 에이전트에게 작업 요청 | `payload.taskType`, `payload.input` |
| `TaskResponse` | 작업 완료 결과 반환 | `payload.output`, `payload.status` |
| `Event` | 상태 변경 알림 | `payload.eventType`, `payload.data` |
| `Heartbeat` | 에이전트 상태 확인 | `source.agentId`, `payload.status` |

---

## 6. 아키텍처 패턴

### 6.1 Orchestrator 패턴 (중앙 집중식)

```
                    ┌──────────────┐
                    │ Orchestrator │
                    │    Agent     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │ Worker A │ │ Worker B │ │ Worker C │
        │ (Analyze)│ │(Summarize)│ │ (Review) │
        └──────────┘ └──────────┘ └──────────┘
```

- Orchestrator가 Service Bus를 통해 Worker에게 작업 분배
- 각 Worker는 독립적인 큐를 구독
- Orchestrator는 모든 Worker의 응답을 수집하여 최종 결과 생성

### 6.2 Choreography 패턴 (분산형)

```
┌──────────┐     Event Grid      ┌──────────┐
│ Agent A  │ ──────────────────→ │ Agent B  │
└──────────┘   (TaskCompleted)   └─────┬────┘
                                       │
                                  Event Grid
                                  (AnalysisDone)
                                       │
                                 ┌─────▼────┐
                                 │ Agent C  │
                                 └──────────┘
```

- 각 에이전트가 자신의 작업 완료 후 Event Grid로 이벤트 발행
- 관심 있는 에이전트가 이벤트를 구독하여 자율적으로 후속 작업 수행
- 중앙 조율자 없이 에이전트 간 협업 수행

### 6.3 Hybrid 패턴 (실시간 스트리밍 + 큐)

```
┌───────────┐   Event Hubs    ┌────────────┐   Service Bus   ┌──────────┐
│ Streaming │ ──────────────→ │ Processing │ ──────────────→ │  Action  │
│  Agents   │  (Real-time)    │   Agents   │   (Reliable)   │  Agents  │
└───────────┘                 └────────────┘                 └──────────┘
```

- Event Hubs로 실시간 데이터 수집, Service Bus로 신뢰성 있는 작업 전달
- 대용량 이벤트 스트림 처리와 정확한 작업 수행을 결합

---

## 7. 코딩 컨벤션 및 표준

### 7.1 공통 규칙

- **인증**: 모든 Azure 서비스 연결에 `DefaultAzureCredential` 사용. Connection String / Access Key 사용 **절대 금지**
- **Managed Identity 필수**: 모든 Azure 리소스는 키 기반 인증을 비활성화하고 Microsoft Entra ID(Managed Identity / RBAC) 기반 인증만 허용
  - Storage Account: `--allow-shared-key-access false`
  - Service Bus / Event Hubs: `--disable-local-auth true`
  - Cognitive Services: `--disable-local-auth true` (API Key 비활성화)
  - 로컬 개발 시 `az login` + `DefaultAzureCredential` 으로 인증하며, RBAC 역할을 사전 할당
  - 프로비저닝 스크립트에서 리소스 생성 시 키 접근을 명시적으로 차단
- **환경 변수**: `.env` 파일로 관리하며, `.env.example`에 필요한 변수를 문서화. **환경 변수에 키/연결 문자열을 저장하지 않는다** (엔드포인트/네임스페이스 FQDN만 저장)
- **필수 환경 변수**:
  ```bash
  # Azure OpenAI
  AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
  AZURE_OPENAI_MODEL=gpt-4o              # 배포된 모델(deployment) 이름

  # Azure Service Bus
  AZURE_SERVICEBUS_NAMESPACE=<your-namespace>.servicebus.windows.net

  # Azure Event Hubs
  AZURE_EVENTHUB_NAMESPACE=<your-namespace>.servicebus.windows.net
  AZURE_EVENTHUB_NAME=<hub-name>

  # Azure Event Grid
  AZURE_EVENTGRID_ENDPOINT=https://<your-topic>.eventgrid.azure.net/api/events

  # Observability
  APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
  ```
- **시크릿 관리**: Azure Key Vault를 통한 시크릿 관리 권장. 코드에 시크릿 직접 포함 금지. 단, Managed Identity 사용 시 대부분의 시크릿(키, 연결 문자열)이 불필요
- **로깅**: 구조화된 로깅(Structured Logging) 사용. `structlog` 패키지 활용
- **분산 추적**: OpenTelemetry를 사용하여 에이전트 간 호출 체인 추적
- **에러 처리**: 모든 Azure 서비스 호출에 재시도 로직 포함. Exponential Backoff 적용
- **타임아웃**: 모든 외부 호출에 타임아웃 설정 필수

### 7.2 Python 프로젝트 규칙

- **Python 버전**: 3.11 이상
- **가상환경 및 패키지 관리**: `uv` 사용 (필수)
- **패키지 정의**: `pyproject.toml`
- **코드 포맷**: `ruff` 사용 (line-length=120)
- **타입 힌트**: 모든 함수에 타입 힌트 필수
- **비동기**: `asyncio` 기반 비동기 프로그래밍 우선
- **테스트**: `pytest` + `pytest-asyncio`

#### `uv` 사용 규칙

```bash
# 프로젝트 초기화 (새 샘플 생성 시)
uv init sample-name
cd sample-name

# 가상환경 생성 (Python 3.11 이상)
uv venv --python 3.11

# 의존성 추가
uv add azure-servicebus azure-identity structlog
uv add --dev pytest pytest-asyncio ruff

# 의존성 설치 (lock 파일 기반)
uv sync

# 스크립트 실행
uv run python src/main.py

# 테스트 실행
uv run pytest
```

- 각 샘플 디렉터리마다 독립적인 `pyproject.toml`과 `uv.lock` 파일을 유지
- `uv.lock` 파일은 반드시 Git에 커밋하여 재현 가능한 빌드 보장
- `.python-version` 파일로 Python 버전을 명시 (예: `3.11`)
- 가상환경 디렉터리(`.venv/`)는 `.gitignore`에 추가

#### 디렉터리 구조 (각 샘플)

  ```
  sample-name/
  ├── src/
  │   ├── agents/          # 에이전트 정의
  │   ├── tools/           # 도구/플러그인
  │   ├── messaging/       # Azure 메시징 클라이언트
  │   └── main.py          # 진입점
  ├── tests/
  ├── pyproject.toml       # uv 프로젝트 정의
  ├── uv.lock              # 의존성 lock 파일 (커밋 필수)
  ├── .python-version      # Python 버전 명시
  ├── .env.example
  └── README.md
  ```

---

## 8. Azure 리소스 프로비저닝 규칙

### 8.1 IaC (Infrastructure as Code)

- **도구**: Azure Bicep을 사용한 인프라 정의 (ARM 템플릿 직접 작성 금지)
- **모듈화**: 각 Azure 리소스를 독립 Bicep 모듈로 분리
- **매개변수화**: 환경별(dev/staging/prod) 파라미터 파일 분리
- **네이밍 규칙**: `{리소스약어}-{프로젝트명}-{환경}-{리전약어}` (예: `sb-agents-dev-krc`)

### 8.2 필수 Azure 리소스

| 리소스 | 용도 | SKU 권장 |
|---|---|---|
| Azure OpenAI | LLM 모델 호스팅 | Standard S0 |
| Azure Service Bus | 신뢰성 메시징 | Standard 이상 |
| Azure Event Hubs | 이벤트 스트리밍 | Standard 이상 |
| Azure Event Grid | 이벤트 라우팅 | Basic |
| Azure Container Apps | 에이전트 호스팅 | Consumption |
| Azure Application Insights | 모니터링/추적 | - |
| Azure Key Vault | 시크릿 관리 | Standard |
| Azure Blob Storage | 체크포인트/상태 저장 | Standard LRS |

### 8.3 네트워크 및 보안

- RBAC(역할 기반 액세스 제어)를 사용하여 최소 권한 원칙 적용
- **Managed Identity 전용 인증**: 모든 Azure 리소스에서 로컬 인증(키/SAS) 비활성화
  - **프로비저닝 시 적용 항목**:
    - Storage Account: `--allow-shared-key-access false`
    - Service Bus: `--disable-local-auth true`
    - Event Hubs: `--disable-local-auth true`
    - Cognitive Services (OpenAI): `--disable-local-auth true`
  - **필수 RBAC 역할 할당**:
    - `Cognitive Services OpenAI User` — Azure OpenAI
    - `Azure Service Bus Data Owner` — Service Bus
    - `Azure Event Hubs Data Owner` — Event Hubs
    - `EventGrid Data Sender` — Event Grid
    - `Storage Blob Data Contributor` — Blob Storage
    - `Storage Queue Data Contributor` — Storage Queue
- Managed Identity를 사용하여 에이전트가 Azure 서비스에 접근
- 프로덕션 환경에서는 Private Endpoint 사용 권장
- 모든 데이터 전송은 TLS 1.2 이상 적용

---

## 9. 관찰 가능성(Observability)

### 9.1 로깅

- 모든 에이전트 요청/응답을 구조화된 로그로 기록
- `correlationId`를 사용하여 멀티 에이전트 흐름 전체를 추적
- 로그 레벨: `DEBUG` (개발), `INFO` (운영), `WARNING/ERROR` (알림)

### 9.2 메트릭

- 에이전트별 처리 시간, 성공/실패율, 큐 깊이 모니터링
- Application Insights 커스텀 메트릭으로 에이전트 성능 데이터 수집
- Azure Monitor 대시보드를 통한 실시간 모니터링

### 9.3 분산 추적

- OpenTelemetry SDK를 사용하여 에이전트 간 trace context 전파
- 메시지 헤더에 `traceparent`, `tracestate`를 포함하여 추적 연속성 유지
- Application Insights의 Transaction Search로 end-to-end 흐름 시각화

---

## 10. 각 샘플 README 작성 기준

각 예제 폴더의 README.md는 반드시 다음 섹션을 포함해야 한다:

1. **개요**: 예제가 시연하는 패턴과 시나리오 설명
2. **아키텍처 다이어그램**: Mermaid 또는 이미지로 시각화
3. **사전 요구사항**: 필요한 Azure 리소스, SDK 버전, 환경 변수 목록
4. **빠른 시작**: 3단계 이내로 실행 가능한 가이드 (`azd up` 또는 스크립트 기반)
5. **코드 설명**: 핵심 코드 블록에 대한 주석과 설명
6. **커스터마이징 가이드**: 사용자가 자신의 시나리오에 맞게 수정할 수 있는 포인트
7. **트러블슈팅**: 자주 발생하는 문제와 해결 방법

---

## 11. 메시징 서비스 선택 가이드

각 시나리오에 적합한 Azure 메시징 서비스를 선택하는 기준:

| 요구사항 | Service Bus | Event Hubs | Event Grid |
|---|---|---|---|
| 신뢰성 있는 1:1 통신 | ✅ 최적 | ❌ | ❌ |
| Pub/Sub 브로드캐스트 | ✅ Topic | ⚠️ | ✅ 최적 |
| 대용량 실시간 스트리밍 | ❌ | ✅ 최적 | ❌ |
| 이벤트 기반 트리거 | ⚠️ | ⚠️ | ✅ 최적 |
| 메시지 순서 보장 | ✅ Session | ✅ 파티션 내 | ❌ |
| 메시지 재처리 (Replay) | ❌ | ✅ 최적 | ❌ |
| Dead Letter 처리 | ✅ 최적 | ❌ | ✅ |
| 트랜잭션 지원 | ✅ | ❌ | ❌ |

---

## 12. 보안 및 인증 체크리스트

- [ ] 모든 Azure 서비스에 Managed Identity 연결 확인
- [ ] `DefaultAzureCredential` 사용 확인 (하드코딩된 키/연결 문자열 없음)
- [ ] **모든 리소스에서 로컬 인증(키/SAS) 비활성화 확인**
  - [ ] Storage Account: `allowSharedKeyAccess = false`
  - [ ] Service Bus: `disableLocalAuth = true`
  - [ ] Event Hubs: `disableLocalAuth = true`
  - [ ] Cognitive Services: `disableLocalAuth = true`
- [ ] RBAC 역할 할당 확인 (최소 권한 원칙)
- [ ] `.env` 파일에 키/연결 문자열이 아닌 **엔드포인트/FQDN만** 포함 확인
- [ ] Key Vault에 시크릿 저장 확인 (Managed Identity 외 시크릿이 있는 경우)
- [ ] 네트워크 보안 그룹(NSG) 규칙 검토
- [ ] TLS 1.2 이상 강제 확인
- [ ] 에이전트 간 메시지에 민감 정보 포함 여부 검토
- [ ] 입력 유효성 검사(Input Validation) 구현 확인

---

## 13. CI/CD 파이프라인

### GitHub Actions 워크플로우 구성

- **인프라 배포**: `infra/` 디렉터리 변경 시 Bicep 배포 자동 실행
- **코드 빌드/테스트**: 각 샘플의 코드 변경 시 빌드 및 테스트 실행
- **통합 테스트**: 스케줄 기반으로 Azure 리소스에 대한 통합 테스트 수행
- **환경**:
  - `dev`: PR 생성 시 자동 배포
  - `prod`: `main` 브랜치 머지 시 수동 승인 후 배포

---

## 14. 기여 가이드라인

### 새로운 예제 추가 시

1. 해당 프레임워크 폴더 아래에 새 디렉터리 생성
2. 표준 디렉터리 구조(섹션 7.2) 준수
3. 메시지 스키마(섹션 5) 표준 준수
4. README.md 작성 기준(섹션 10) 충족
5. 최소 1개의 통합 테스트 작성
6. `.env.example` 업데이트
7. 루트 README.md의 예제 목록 업데이트

### 코드 리뷰 체크리스트

- [ ] `DefaultAzureCredential` 사용 여부
- [ ] 에러 처리 및 재시도 로직 포함 여부
- [ ] 구조화된 로깅 적용 여부
- [ ] 타입 힌트 / 타입 안전성 확보 여부
- [ ] 메시지 스키마 표준 준수 여부
- [ ] 테스트 커버리지 확인
- [ ] README 및 코드 주석 충분성
