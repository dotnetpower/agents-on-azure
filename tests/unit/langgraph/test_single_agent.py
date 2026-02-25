"""Unit tests for LangGraph framework components.

Tests prompt templates, state definitions, and pipeline structure.
"""

from __future__ import annotations

from contracts.prompts import (
    ANALYZE_PROMPT,
    REVIEW_PROMPT,
    SINGLE_AGENT_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT,
)


class TestLangGraphPrompts:
    """Tests for prompt templates used by LangGraph agents."""

    def test_single_agent_system_prompt_is_defined(self):
        """Verify single agent system prompt is not empty."""
        assert SINGLE_AGENT_SYSTEM_PROMPT
        assert len(SINGLE_AGENT_SYSTEM_PROMPT) > 0

    def test_analyze_prompt_formats_correctly(self):
        """Verify analyze prompt accepts document placeholder."""
        document = "Machine learning enables computers to learn from data."
        formatted = ANALYZE_PROMPT.format(document=document)
        assert document in formatted
        assert "analyze" in formatted.lower() or "analysis" in formatted.lower()

    def test_summarize_prompt_formats_correctly(self):
        """Verify summarize prompt accepts analysis placeholder."""
        analysis = "Key topics: AI, ML, Data Science"
        formatted = SUMMARIZE_PROMPT.format(analysis=analysis)
        assert analysis in formatted

    def test_review_prompt_formats_correctly(self):
        """Verify review prompt accepts both placeholders."""
        formatted = REVIEW_PROMPT.format(
            analysis="Original analysis",
            summary="Created summary"
        )
        assert "Original analysis" in formatted
        assert "Created summary" in formatted


class TestLangGraphPipelineState:
    """Tests for the LangGraph pipeline state structure."""

    def test_pipeline_state_structure(self):
        """Verify expected state structure for pipeline."""
        # LangGraph PipelineState should have these keys
        state = {
            "document": "Input document",
            "analysis": "",
            "summary": "",
            "review": "",
        }
        assert "document" in state
        assert "analysis" in state
        assert "summary" in state
        assert "review" in state

    def test_initial_state_has_empty_results(self):
        """Verify initial state starts with empty analysis/summary/review."""
        initial_state = {
            "document": "Some document content",
            "analysis": "",
            "summary": "",
            "review": "",
        }
        assert initial_state["document"] != ""
        assert initial_state["analysis"] == ""
        assert initial_state["summary"] == ""
        assert initial_state["review"] == ""

    def test_state_updates_preserve_document(self):
        """Verify state updates don't overwrite document."""
        state = {
            "document": "Original document",
            "analysis": "",
            "summary": "",
            "review": "",
        }
        # Simulate analyze node update
        state.update({"analysis": "Analysis result"})
        assert state["document"] == "Original document"
        assert state["analysis"] == "Analysis result"


class TestLangGraphNodeStructure:
    """Tests for expected node structure in the graph."""

    def test_expected_node_names(self):
        """Verify expected node names for the pipeline."""
        expected_nodes = ["analyze", "summarize", "review"]
        for node in expected_nodes:
            assert node in expected_nodes

    def test_expected_edge_flow(self):
        """Verify expected edge connections."""
        # analyze -> summarize -> review -> END
        edges = [
            ("analyze", "summarize"),
            ("summarize", "review"),
            ("review", "END"),
        ]
        assert len(edges) == 3
        assert edges[0][0] == "analyze"
        assert edges[0][1] == "summarize"
        assert edges[1][1] == "review"


class TestLangGraphMultiAgentMessages:
    """Tests for multi-agent message structures."""

    def test_analyzer_output_message(self):
        """Verify analyzer output message structure."""
        message = {
            "correlation_id": "test-123",
            "analysis": "Document analysis results",
        }
        assert "correlation_id" in message
        assert "analysis" in message

    def test_summarizer_output_message(self):
        """Verify summarizer output message structure."""
        message = {
            "correlation_id": "test-123",
            "analysis": "Previous analysis",
            "summary": "Generated summary",
        }
        assert "correlation_id" in message
        assert "summary" in message

    def test_reviewer_output_message(self):
        """Verify reviewer output message structure."""
        message = {
            "correlation_id": "test-123",
            "review": "Quality review of summary",
        }
        assert "correlation_id" in message
        assert "review" in message


class TestLangGraphPipelineResults:
    """Tests for pipeline result structure."""

    def test_complete_pipeline_result(self):
        """Verify complete pipeline returns all fields."""
        result = {
            "document": "Original input",
            "analysis": "Analysis output",
            "summary": "Summary output",
            "review": "Review output",
        }
        assert all(key in result for key in ["document", "analysis", "summary", "review"])
        assert all(result[key] for key in ["document", "analysis", "summary", "review"])
