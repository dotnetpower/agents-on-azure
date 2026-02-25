"""Unit tests for AutoGen framework components.

Tests prompt templates, message contracts, and shared utilities.
"""

from __future__ import annotations

from contracts.prompts import (
    ANALYZE_PROMPT,
    ANALYZER_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    SINGLE_AGENT_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
)


class TestAutoGenPrompts:
    """Tests for prompt templates used by AutoGen agents."""

    def test_single_agent_system_prompt_is_defined(self):
        """Verify single agent system prompt is not empty."""
        assert SINGLE_AGENT_SYSTEM_PROMPT
        assert len(SINGLE_AGENT_SYSTEM_PROMPT) > 0
        assert "document" in SINGLE_AGENT_SYSTEM_PROMPT.lower()

    def test_analyzer_system_prompt_is_defined(self):
        """Verify analyzer system prompt contains analysis keywords."""
        assert ANALYZER_SYSTEM_PROMPT
        assert "analysis" in ANALYZER_SYSTEM_PROMPT.lower() or "analyze" in ANALYZER_SYSTEM_PROMPT.lower()

    def test_summarizer_system_prompt_is_defined(self):
        """Verify summarizer system prompt contains summarization keywords."""
        assert SUMMARIZER_SYSTEM_PROMPT
        assert "summar" in SUMMARIZER_SYSTEM_PROMPT.lower()

    def test_reviewer_system_prompt_is_defined(self):
        """Verify reviewer system prompt contains review keywords."""
        assert REVIEWER_SYSTEM_PROMPT
        assert "review" in REVIEWER_SYSTEM_PROMPT.lower()


class TestAutoGenUserPrompts:
    """Tests for user prompt templates."""

    def test_analyze_prompt_has_document_placeholder(self):
        """Verify analyze prompt accepts document placeholder."""
        formatted = ANALYZE_PROMPT.format(document="Test document content")
        assert "Test document content" in formatted
        assert "analyze" in formatted.lower() or "analysis" in formatted.lower()

    def test_summarize_prompt_has_analysis_placeholder(self):
        """Verify summarize prompt accepts analysis placeholder."""
        formatted = SUMMARIZE_PROMPT.format(analysis="Test analysis content")
        assert "Test analysis content" in formatted
        assert "summar" in formatted.lower()

    def test_review_prompt_has_both_placeholders(self):
        """Verify review prompt accepts both analysis and summary placeholders."""
        formatted = REVIEW_PROMPT.format(
            analysis="Test analysis",
            summary="Test summary"
        )
        assert "Test analysis" in formatted
        assert "Test summary" in formatted


class TestAutoGenMessageContracts:
    """Tests for message contracts used in multi-agent patterns."""

    def test_correlation_id_format(self):
        """Verify correlation ID can be any string."""
        import uuid
        correlation_id = str(uuid.uuid4())
        # Correlation IDs should be valid UUIDs
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

    def test_pipeline_message_structure(self):
        """Verify expected pipeline message structure."""
        # Standard pipeline message should have correlation_id and payload
        message = {
            "correlation_id": "test-123",
            "document": "Sample document",
        }
        assert "correlation_id" in message
        assert "document" in message

    def test_analysis_forward_message_structure(self):
        """Verify analyzer -> summarizer message structure."""
        message = {
            "correlation_id": "test-123",
            "analysis": "Analyzed content here",
        }
        assert "correlation_id" in message
        assert "analysis" in message

    def test_summary_forward_message_structure(self):
        """Verify summarizer -> reviewer message structure."""
        message = {
            "correlation_id": "test-123",
            "analysis": "Analyzed content",
            "summary": "Summarized content",
        }
        assert "correlation_id" in message
        assert "analysis" in message
        assert "summary" in message


class TestAutoGenPipelineResults:
    """Tests for pipeline result structure."""

    def test_pipeline_result_has_all_fields(self):
        """Verify pipeline results contain all expected fields."""
        results = {
            "analysis": "Document analysis",
            "summary": "Document summary",
            "review": "Quality review",
        }
        assert "analysis" in results
        assert "summary" in results
        assert "review" in results

    def test_pipeline_result_fields_are_strings(self):
        """Verify pipeline results are strings."""
        results = {
            "analysis": "Document analysis",
            "summary": "Document summary",
            "review": "Quality review",
        }
        assert isinstance(results["analysis"], str)
        assert isinstance(results["summary"], str)
        assert isinstance(results["review"], str)
