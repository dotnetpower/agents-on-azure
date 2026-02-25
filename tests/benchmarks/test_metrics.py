"""Tests for benchmarks.metrics module."""

from dataclasses import asdict

import pytest
from benchmarks.metrics import (
    AgentStageMetrics,
    DerivedMetrics,
    LLMMetrics,
    MessagingMetrics,
    SubscriberMetrics,
)


class TestLLMMetrics:
    """Tests for the LLMMetrics dataclass."""

    def test_defaults(self) -> None:
        m = LLMMetrics()
        assert m.ttft_ms == 0.0
        assert m.total_latency_ms == 0.0
        assert m.output_tokens == 0
        assert m.input_tokens == 0
        assert m.tokens_per_second == 0.0
        assert m.prompt_build_ms == 0.0

    def test_custom_values(self) -> None:
        m = LLMMetrics(
            ttft_ms=120.5,
            total_latency_ms=800.0,
            output_tokens=200,
            input_tokens=500,
            tokens_per_second=25.0,
            prompt_build_ms=10.0,
        )
        assert m.ttft_ms == 120.5
        assert m.output_tokens == 200
        assert m.tokens_per_second == 25.0

    def test_serializable(self) -> None:
        m = LLMMetrics(ttft_ms=100.0, output_tokens=50)
        d = asdict(m)
        assert isinstance(d, dict)
        assert d["ttft_ms"] == 100.0
        assert d["output_tokens"] == 50


class TestMessagingMetrics:
    """Tests for the MessagingMetrics dataclass."""

    def test_defaults(self) -> None:
        m = MessagingMetrics()
        assert m.send_ms == 0.0
        assert m.delivery_ms == 0.0
        assert m.receive_ms == 0.0
        assert m.total_ms == 0.0
        assert m.retry_count == 0
        assert m.subscriber_id == ""

    def test_with_subscriber(self) -> None:
        m = MessagingMetrics(
            send_ms=5.0,
            delivery_ms=30.0,
            receive_ms=3.0,
            total_ms=38.0,
            retry_count=1,
            subscriber_id="summarizer",
        )
        assert m.subscriber_id == "summarizer"
        assert m.retry_count == 1


class TestSubscriberMetrics:
    """Tests for the SubscriberMetrics dataclass."""

    def test_defaults_with_nested_llm(self) -> None:
        m = SubscriberMetrics()
        assert isinstance(m.llm, LLMMetrics)
        assert m.llm.ttft_ms == 0.0

    def test_nested_llm_is_independent(self) -> None:
        """Each instance should have its own LLMMetrics."""
        a = SubscriberMetrics(subscriber_id="a")
        b = SubscriberMetrics(subscriber_id="b")
        a.llm.ttft_ms = 100.0
        assert b.llm.ttft_ms == 0.0

    def test_full_construction(self) -> None:
        m = SubscriberMetrics(
            subscriber_id="translator",
            delivery_ms=20.0,
            receive_ms=5.0,
            agent_processing_ms=500.0,
            llm=LLMMetrics(ttft_ms=80.0, total_latency_ms=450.0),
            total_ms=525.0,
        )
        assert m.subscriber_id == "translator"
        assert m.llm.ttft_ms == 80.0


class TestAgentStageMetrics:
    """Tests for the AgentStageMetrics dataclass."""

    def test_defaults(self) -> None:
        m = AgentStageMetrics()
        assert m.stage_name == ""
        assert m.agent_total_ms == 0.0
        assert isinstance(m.llm, LLMMetrics)
        assert m.framework_overhead_ms == 0.0

    def test_overhead_calculation(self) -> None:
        m = AgentStageMetrics(
            stage_name="analyzer",
            agent_total_ms=900.0,
            llm=LLMMetrics(total_latency_ms=800.0),
            framework_overhead_ms=100.0,
        )
        assert m.agent_total_ms - m.llm.total_latency_ms == m.framework_overhead_ms


class TestDerivedMetrics:
    """Tests for the DerivedMetrics dataclass."""

    def test_defaults(self) -> None:
        m = DerivedMetrics()
        assert m.e2e_pipeline_ms == 0.0
        assert m.messaging_overhead_pct == 0.0
        assert m.llm_time_pct == 0.0

    def test_all_fields(self) -> None:
        m = DerivedMetrics(
            e2e_pipeline_ms=2000.0,
            total_messaging_overhead_ms=100.0,
            total_llm_time_ms=1800.0,
            total_framework_overhead_ms=100.0,
            messaging_overhead_pct=5.0,
            llm_time_pct=90.0,
        )
        assert m.messaging_overhead_pct == pytest.approx(5.0)
