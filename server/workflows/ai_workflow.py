"""LangGraph-based AI workflow for the data analyst chatbot.

Each step of the analytics pipeline is implemented as a LangGraph node. For
readability, individual step implementations live in ``server/workflows/steps``.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from .base import WorkflowState
from .steps.prompt_intake import prompt_intake
from .steps.intent_understanding import intent_understanding
from .steps.clarification import clarification
from .steps.task_planning import task_planning
from .steps.task_execution import task_execution
from .steps.response_generation import response_generation
from .steps.result_validation import result_validation
from .steps.monitoring import monitoring


def validation_router(state: WorkflowState) -> str:
    """Route to monitoring or halt on validation errors."""
    if state.get("error"):
        return END
    return "monitoring"


def clarification_router(state: WorkflowState) -> str:
    """Route clarifying questions directly to END or proceed."""
    if state.get("needs_clarification") and not state.get("clarification_escalated"):
        return END
    if state.get("clarification_escalated"):
        return END
    return "task_planning"


def build_workflow(checkpointer=None) -> StateGraph[WorkflowState]:
    """Create and compile the LangGraph workflow."""
    builder = StateGraph(WorkflowState)

    def _prompt_intake(state: WorkflowState) -> WorkflowState:
        return prompt_intake(state, checkpointer)

    builder.add_node("prompt_intake", _prompt_intake)
    builder.add_node("intent_understanding", intent_understanding)
    builder.add_node("clarification", clarification)
    builder.add_node("task_planning", task_planning)
    builder.add_node("task_execution", task_execution)
    builder.add_node("response_generation", response_generation)
    builder.add_node("result_validation", result_validation)
    # builder.add_node("conversation_summary", conversation_summary)
    builder.add_node("monitoring", monitoring)

    builder.set_entry_point("prompt_intake")
    builder.add_edge("prompt_intake", "intent_understanding")
    builder.add_edge("intent_understanding", "clarification")
    builder.add_conditional_edges("clarification", clarification_router)
    builder.add_edge("task_planning", "task_execution")
    builder.add_edge("task_execution", "response_generation")
    builder.add_edge("response_generation", "result_validation")
    builder.add_conditional_edges("result_validation", validation_router)
    # builder.add_edge("conversation_summary", "monitoring")
    builder.add_edge("monitoring", END)

    return builder.compile(checkpointer=checkpointer)
