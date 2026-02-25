"""Document processing plugins for Semantic Kernel."""

from __future__ import annotations

from semantic_kernel.functions import kernel_function


class DocumentPlugin:
    """Plugin with functions for document analysis, summarization, and review."""

    @kernel_function(
        name="analyze_document",
        description="Analyze a document and extract key information",
    )
    def analyze_document(self, document: str) -> str:
        """Return the analyze prompt filled with the document content."""
        from agents.prompts import ANALYZE_PROMPT
        return ANALYZE_PROMPT.format(document=document)

    @kernel_function(
        name="summarize_analysis",
        description="Create a summary from a document analysis",
    )
    def summarize_analysis(self, analysis: str) -> str:
        """Return the summarize prompt filled with analysis."""
        from agents.prompts import SUMMARIZE_PROMPT
        return SUMMARIZE_PROMPT.format(analysis=analysis)

    @kernel_function(
        name="review_summary",
        description="Review a summary for quality and completeness",
    )
    def review_summary(self, analysis: str, summary: str) -> str:
        """Return the review prompt filled with analysis and summary."""
        from agents.prompts import REVIEW_PROMPT
        return REVIEW_PROMPT.format(analysis=analysis, summary=summary)
