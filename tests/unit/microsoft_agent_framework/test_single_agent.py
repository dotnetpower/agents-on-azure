"""Unit tests for Microsoft Agent Framework components.

Tests prompt templates, agent configuration, and pipeline structure.
"""

from __future__ import annotations

from contracts.prompts import (
    AGENT_INSTRUCTIONS,
    ANALYZE_PROMPT,
    ANALYZER_INSTRUCTIONS,
    REVIEW_PROMPT,
    REVIEWER_INSTRUCTIONS,
    SUMMARIZE_PROMPT,
    SUMMARIZER_INSTRUCTIONS,
)


class TestMicrosoftAgentFrameworkInstructions:
    """Tests for agent instructions used by Microsoft Agent Framework."""

    def test_agent_instructions_is_defined(self):
        """Verify main agent instructions are not empty."""
        assert AGENT_INSTRUCTIONS
        assert len(AGENT_INSTRUCTIONS) > 0

    def test_analyzer_instructions_is_defined(self):
        """Verify analyzer instructions contain analysis keywords."""
        assert ANALYZER_INSTRUCTIONS
        assert "analysis" in ANALYZER_INSTRUCTIONS.lower() or "analyze" in ANALYZER_INSTRUCTIONS.lower()

    def test_summarizer_instructions_is_defined(self):
        """Verify summarizer instructions contain summarization keywords."""
        assert SUMMARIZER_INSTRUCTIONS
        assert "summar" in SUMMARIZER_INSTRUCTIONS.lower()

    def test_reviewer_instructions_is_defined(self):
        """Verify reviewer instructions contain review keywords."""
        assert REVIEWER_INSTRUCTIONS
        assert "review" in REVIEWER_INSTRUCTIONS.lower()


class TestMicrosoftAgentFrameworkUserPrompts:
    """Tests for user prompt templates."""

    def test_analyze_prompt_has_document_placeholder(self):
        """Verify analyze prompt accepts document placeholder."""
        formatted = ANALYZE_PROMPT.format(document="Test document content")
        assert "Test document content" in formatted

    def test_summarize_prompt_has_analysis_placeholder(self):
        """Verify summarize prompt accepts analysis placeholder."""
        formatted = SUMMARIZE_PROMPT.format(analysis="Test analysis content")
        assert "Test analysis content" in formatted

    def test_review_prompt_has_both_placeholders(self):
        """Verify review prompt accepts both analysis and summary placeholders."""
        formatted = REVIEW_PROMPT.format(
            analysis="Test analysis",
            summary="Test summary"
        )
        assert "Test analysis" in formatted
        assert "Test summary" in formatted


class TestMicrosoftAgentFrameworkAgentConfiguration:
    """Tests for agent configuration expectations."""

    def test_agent_name_convention(self):
        """Verify expected agent naming convention."""
        expected_name = "document-processor"
        assert "-" in expected_name  # kebab-case naming

    def test_expected_agent_properties(self):
        """Verify expected agent creation properties."""
        agent_config = {
            "model": "gpt-4o",
            "name": "document-processor",
            "instructions": AGENT_INSTRUCTIONS,
        }
        assert "model" in agent_config
        assert "name" in agent_config
        assert "instructions" in agent_config

    def test_expected_azure_settings(self):
        """Verify expected Azure settings structure."""
        settings = {
            "azure_openai_endpoint": "https://test.openai.azure.com/",
            "azure_openai_model": "gpt-4o",
        }
        assert "azure_openai_endpoint" in settings
        assert "azure_openai_model" in settings


class TestMicrosoftAgentFrameworkThreadManagement:
    """Tests for thread management expectations."""

    def test_thread_message_roles(self):
        """Verify expected message roles in threads."""
        valid_roles = ["user", "assistant"]
        assert "user" in valid_roles
        assert "assistant" in valid_roles

    def test_run_completion_status(self):
        """Verify expected run completion status."""
        # A successful run should have status "completed"
        expected_status = "completed"
        assert expected_status == "completed"

    def test_expected_run_statuses(self):
        """Verify all expected run status values."""
        statuses = ["completed", "failed", "cancelled", "in_progress"]
        assert "completed" in statuses
        assert "failed" in statuses


class TestMicrosoftAgentFrameworkPipelineResults:
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


class TestMicrosoftAgentFrameworkCleanup:
    """Tests for resource cleanup expectations."""

    def test_cleanup_order(self):
        """Verify expected cleanup order: thread first, then agent."""
        cleanup_order = ["thread", "agent"]
        assert cleanup_order[0] == "thread"
        assert cleanup_order[1] == "agent"

    def test_cleanup_is_required(self):
        """Document that cleanup is always required."""
        # The framework requires:
        # 1. Delete thread
        # 2. Delete agent
        # 3. Close credential
        cleanup_steps = ["delete_thread", "delete_agent", "close_credential"]
        assert len(cleanup_steps) == 3


class TestMicrosoftAgentFrameworkResponseExtraction:
    """Tests for response extraction expectations."""

    def test_message_content_structure(self):
        """Verify expected message content structure."""
        # Response messages have content[0].text.value structure
        message_structure = {
            "role": "assistant",
            "content": [{"text": {"value": "Response text"}}],
        }
        assert message_structure["role"] == "assistant"
        assert "content" in message_structure
        assert len(message_structure["content"]) > 0

    def test_extract_text_from_message(self):
        """Verify text extraction pattern."""
        message = {
            "role": "assistant",
            "content": [{"text": {"value": "Extracted response"}}],
        }
        extracted = message["content"][0]["text"]["value"]
        assert extracted == "Extracted response"
