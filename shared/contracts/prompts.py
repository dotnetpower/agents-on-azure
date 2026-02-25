"""Shared prompt templates for the document analysis pipeline.

Provides a single source of truth for all agent system prompts and
user-facing prompt templates across all framework samples.

Responsibility: Define prompt text only. No I/O, no agent logic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompts — used for single-agent samples (one agent doing all 3 tasks)
# ---------------------------------------------------------------------------

SINGLE_AGENT_SYSTEM_PROMPT = (
    "You are a document processing assistant. "
    "You can analyze documents, create summaries, and review content quality. "
    "Follow the user's instructions precisely for each step."
)

# ---------------------------------------------------------------------------
# Per-role system prompts — used for multi-agent samples
# ---------------------------------------------------------------------------

ANALYZER_SYSTEM_PROMPT = (
    "You are a document analysis specialist. Your job is to analyze documents "
    "and extract key topics, arguments, entities, and sentiment."
)

SUMMARIZER_SYSTEM_PROMPT = (
    "You are a document summarization specialist. Your job is to create concise, "
    "accurate summaries from analysis results."
)

REVIEWER_SYSTEM_PROMPT = (
    "You are a quality review specialist. Your job is to evaluate summaries "
    "for quality, accuracy, and completeness."
)

# ---------------------------------------------------------------------------
# User prompt templates — shared by all frameworks and patterns
# Each has {document}, {analysis}, or {analysis}+{summary} placeholders.
# ---------------------------------------------------------------------------

ANALYZE_PROMPT = (
    "Analyze the following document. Extract the key topics, main arguments, "
    "important entities, and overall sentiment.\n\n"
    "Document:\n{document}\n\n"
    "Provide a structured analysis with sections: Topics, Arguments, Entities, Sentiment."
)

SUMMARIZE_PROMPT = (
    "Based on the following analysis, create a concise summary of the document.\n\n"
    "Analysis:\n{analysis}\n\n"
    "Provide a summary in 3-5 paragraphs that captures the essential information."
)

REVIEW_PROMPT = (
    "Review the following summary for quality, accuracy, and completeness.\n\n"
    "Original Analysis:\n{analysis}\n\n"
    "Summary:\n{summary}\n\n"
    "Provide a review with: Quality Score (1-10), Strengths, Weaknesses, and Final Verdict."
)

# ---------------------------------------------------------------------------
# Aliases for Microsoft Agent Framework (uses "instructions" instead of
# "system prompt" because the AgentsClient API takes an `instructions` field).
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS = SINGLE_AGENT_SYSTEM_PROMPT
ANALYZER_INSTRUCTIONS = ANALYZER_SYSTEM_PROMPT
SUMMARIZER_INSTRUCTIONS = SUMMARIZER_SYSTEM_PROMPT
REVIEWER_INSTRUCTIONS = REVIEWER_SYSTEM_PROMPT

# Framework-agnostic alias used by single-agent samples (SK, LG, AG).
SYSTEM_PROMPT = SINGLE_AGENT_SYSTEM_PROMPT
