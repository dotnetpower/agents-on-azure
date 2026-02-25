"""LangGraph state graph for the document analysis pipeline."""

from __future__ import annotations

from typing import TypedDict

from contracts.prompts import ANALYZE_PROMPT, REVIEW_PROMPT, SINGLE_AGENT_SYSTEM_PROMPT, SUMMARIZE_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, StateGraph


class PipelineState(TypedDict):
    """State that flows through the document pipeline graph."""

    document: str
    analysis: str
    summary: str
    review: str


def create_pipeline_graph(llm: AzureChatOpenAI) -> StateGraph:
    """Build a LangGraph StateGraph for the 3-step pipeline.

    Nodes: analyze -> summarize -> review -> END
    """

    async def analyze_node(state: PipelineState) -> dict[str, str]:
        prompt = ANALYZE_PROMPT.format(document=state["document"])
        response = await llm.ainvoke([
            SystemMessage(content=SINGLE_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"analysis": response.content}

    async def summarize_node(state: PipelineState) -> dict[str, str]:
        prompt = SUMMARIZE_PROMPT.format(analysis=state["analysis"])
        response = await llm.ainvoke([
            SystemMessage(content=SINGLE_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"summary": response.content}

    async def review_node(state: PipelineState) -> dict[str, str]:
        prompt = REVIEW_PROMPT.format(analysis=state["analysis"], summary=state["summary"])
        response = await llm.ainvoke([
            SystemMessage(content=SINGLE_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"review": response.content}

    graph = StateGraph(PipelineState)
    graph.add_node("analyze", analyze_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("review", review_node)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "summarize")
    graph.add_edge("summarize", "review")
    graph.add_edge("review", END)

    return graph
