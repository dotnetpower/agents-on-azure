"""Shared fixtures for benchmark and framework tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from benchmarks.enums import Framework, Messaging, Topology
from benchmarks.metrics import LLMMetrics, SubscriberMetrics
from benchmarks.run import BenchmarkRun
from benchmarks.segments import FanOutSegments

# ---------------------------------------------------------------------------
# Path Setup: Add sample directories to Python path for test imports
# ---------------------------------------------------------------------------

SAMPLES_DIR = Path(__file__).parent.parent / "samples"

SAMPLE_PATHS = [
    SAMPLES_DIR / "autogen" / "single-agent",
    SAMPLES_DIR / "autogen" / "multi-agent-servicebus",
    SAMPLES_DIR / "autogen" / "multi-agent-eventhub",
    SAMPLES_DIR / "autogen" / "multi-agent-eventgrid",
    SAMPLES_DIR / "langgraph" / "single-agent",
    SAMPLES_DIR / "langgraph" / "multi-agent-servicebus",
    SAMPLES_DIR / "langgraph" / "multi-agent-eventhub",
    SAMPLES_DIR / "langgraph" / "multi-agent-eventgrid",
    SAMPLES_DIR / "semantic-kernel" / "single-agent",
    SAMPLES_DIR / "semantic-kernel" / "multi-agent-servicebus",
    SAMPLES_DIR / "semantic-kernel" / "multi-agent-eventhub",
    SAMPLES_DIR / "semantic-kernel" / "multi-agent-eventgrid",
    SAMPLES_DIR / "microsoft-agent-framework" / "single-agent",
    SAMPLES_DIR / "microsoft-agent-framework" / "multi-agent-servicebus",
    SAMPLES_DIR / "microsoft-agent-framework" / "multi-agent-eventhub",
    SAMPLES_DIR / "microsoft-agent-framework" / "multi-agent-eventgrid",
]


def pytest_configure(config):
    """Add sample directories to sys.path for test imports."""
    for path in SAMPLE_PATHS:
        str_path = str(path)
        if str_path not in sys.path and path.exists():
            sys.path.insert(0, str_path)


# ---------------------------------------------------------------------------
# Framework Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_azure_openai_settings():
    """Mock settings for Azure OpenAI configuration."""
    settings = MagicMock()
    settings.azure_openai_endpoint = "https://test.openai.azure.com/"
    settings.azure_openai_model = "gpt-4o"
    return settings


@pytest.fixture
def mock_servicebus_settings(mock_azure_openai_settings):
    """Mock settings for Service Bus configuration."""
    mock_azure_openai_settings.servicebus_namespace = "test.servicebus.windows.net"
    mock_azure_openai_settings.servicebus_queue_analyzer = "analyzer-queue"
    mock_azure_openai_settings.servicebus_queue_summarizer = "summarizer-queue"
    mock_azure_openai_settings.servicebus_queue_reviewer = "reviewer-queue"
    mock_azure_openai_settings.servicebus_queue_results = "results-queue"
    return mock_azure_openai_settings


@pytest.fixture
def mock_eventhub_settings(mock_azure_openai_settings):
    """Mock settings for Event Hub configuration."""
    mock_azure_openai_settings.eventhub_namespace = "test.servicebus.windows.net"
    mock_azure_openai_settings.eventhub_name = "agent-events"
    mock_azure_openai_settings.eventhub_consumer_group = "$Default"
    return mock_azure_openai_settings


@pytest.fixture
def mock_eventgrid_settings(mock_azure_openai_settings):
    """Mock settings for Event Grid configuration."""
    mock_azure_openai_settings.eventgrid_endpoint = "https://test.eventgrid.azure.net/api/events"
    mock_azure_openai_settings.eventgrid_topic_name = "agent-topic"
    return mock_azure_openai_settings


@pytest.fixture
def mock_pipeline_messaging():
    """Mock PipelineMessaging for testing agent communication."""
    messaging = AsyncMock()
    messaging.send = AsyncMock()
    messaging.receive_one = AsyncMock(return_value=None)
    messaging.close = AsyncMock()
    return messaging


@pytest.fixture
def sample_document():
    """Sample document for pipeline testing."""
    return """
    Artificial Intelligence in Healthcare

    AI is transforming healthcare through improved diagnostics,
    personalized treatment plans, and drug discovery acceleration.
    Machine learning models can analyze medical images with high accuracy,
    while natural language processing helps extract insights from clinical notes.

    Key benefits include:
    - Earlier disease detection
    - Reduced diagnostic errors
    - More efficient resource allocation
    - Improved patient outcomes
    """


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for pipeline testing."""
    return {
        "topics": ["AI", "Healthcare", "Machine Learning", "Diagnostics"],
        "sentiment": "positive",
        "key_entities": ["artificial intelligence", "healthcare", "ML models"],
        "main_arguments": [
            "AI improves diagnostics",
            "ML enables personalized treatment",
            "NLP extracts clinical insights",
        ],
    }


@pytest.fixture
def sample_summary_result():
    """Sample summary result for pipeline testing."""
    return "AI is revolutionizing healthcare through improved diagnostics, personalized treatments, and accelerated drug discovery, leading to better patient outcomes."


@pytest.fixture
def sample_review_result():
    """Sample review result for pipeline testing."""
    return {
        "quality_score": 8.5,
        "completeness": "high",
        "accuracy": "verified",
        "suggestions": ["Consider adding specific statistics"],
    }


@pytest.fixture
def sample_pipeline_run() -> BenchmarkRun:
    """A fully populated linear pipeline BenchmarkRun."""
    run = BenchmarkRun()
    run.framework = Framework.LANGGRAPH
    run.messaging = Messaging.SERVICE_BUS
    run.topology = Topology.LINEAR

    s = run.segments
    s.s1_request_submit_ms = 5.0
    s.s2_analyzer_prompt_build_ms = 10.0
    s.s3_analyzer_ttft_ms = 150.0
    s.s4_analyzer_llm_total_ms = 800.0
    s.s4_analyzer_output_tokens = 200
    s.s4_analyzer_tokens_per_sec = 25.0
    s.s5_msg_send_ms = 12.0
    s.s6_msg_delivery_ms = 45.0
    s.s7_msg_receive_ms = 8.0
    s.s8_summarizer_ttft_ms = 120.0
    s.s8_summarizer_llm_total_ms = 600.0
    s.s8_summarizer_output_tokens = 150
    s.s8_summarizer_tokens_per_sec = 30.0
    s.s9_msg_send_ms = 10.0
    s.s10_msg_receive_ms = 7.0
    s.s11_reviewer_ttft_ms = 100.0
    s.s11_reviewer_llm_total_ms = 400.0
    s.s11_reviewer_output_tokens = 100
    s.s11_reviewer_tokens_per_sec = 20.0
    s.s12_result_delivery_ms = 3.0

    run.derived.e2e_pipeline_ms = 1900.0
    run.compute_derived()
    return run


@pytest.fixture
def sample_fanout_run() -> BenchmarkRun:
    """A BenchmarkRun with fan-out segments."""
    run = BenchmarkRun()
    run.framework = Framework.SEMANTIC_KERNEL
    run.messaging = Messaging.EVENT_HUBS
    run.topology = Topology.FAN_OUT

    run.fan_out = FanOutSegments(
        pf1_publisher_prepare_ms=5.0,
        pf2_publish_latency_ms=15.0,
        subscribers=[
            SubscriberMetrics(
                subscriber_id="summarizer",
                delivery_ms=20.0,
                receive_ms=5.0,
                agent_processing_ms=500.0,
                llm=LLMMetrics(ttft_ms=80.0, total_latency_ms=450.0, output_tokens=120),
                total_ms=525.0,
            ),
            SubscriberMetrics(
                subscriber_id="translator",
                delivery_ms=25.0,
                receive_ms=6.0,
                agent_processing_ms=600.0,
                llm=LLMMetrics(ttft_ms=90.0, total_latency_ms=550.0, output_tokens=140),
                total_ms=631.0,
            ),
            SubscriberMetrics(
                subscriber_id="sentiment",
                delivery_ms=22.0,
                receive_ms=4.0,
                agent_processing_ms=300.0,
                llm=LLMMetrics(ttft_ms=70.0, total_latency_ms=260.0, output_tokens=80),
                total_ms=326.0,
            ),
        ],
        wall_clock_ms=650.0,
    )
    return run


@pytest.fixture
def multiple_runs() -> list[BenchmarkRun]:
    """Multiple runs for aggregation testing (30 runs with varying values)."""
    import random

    random.seed(42)
    runs: list[BenchmarkRun] = []
    for i in range(30):
        run = BenchmarkRun()
        run.framework = Framework.LANGGRAPH
        run.messaging = Messaging.SERVICE_BUS
        run.topology = Topology.LINEAR

        base_ttft = 140 + random.gauss(0, 15)
        run.segments.s3_analyzer_ttft_ms = base_ttft
        run.segments.s4_analyzer_llm_total_ms = base_ttft + 600 + random.gauss(0, 50)
        run.segments.s5_msg_send_ms = 10 + random.gauss(0, 2)
        run.segments.s6_msg_delivery_ms = 40 + random.gauss(0, 8)
        run.segments.s7_msg_receive_ms = 7 + random.gauss(0, 1)
        run.segments.s8_summarizer_llm_total_ms = 550 + random.gauss(0, 40)
        run.segments.s9_msg_send_ms = 9 + random.gauss(0, 2)
        run.segments.s10_msg_receive_ms = 6 + random.gauss(0, 1)
        run.segments.s11_reviewer_llm_total_ms = 380 + random.gauss(0, 30)

        run.derived.e2e_pipeline_ms = 1800 + random.gauss(0, 100)
        run.compute_derived()
        runs.append(run)
    return runs
