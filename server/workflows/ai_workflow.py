"""LangGraph-based AI workflow for the data analyst chatbot.

Each step of the analytics pipeline is implemented as a LangGraph node. For
readability, individual step implementations live in ``server/workflows/steps``.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from workflows.base import WorkflowState
from workflows.steps.prompt_intake import prompt_intake
from workflows.steps.intent_understanding import intent_understanding
from workflows.steps.clarification import clarification
from workflows.steps.task_planning import task_planning
from workflows.steps.task_execution import task_execution
from workflows.steps.text_generation import text_generation
from workflows.steps.data_retrieval import data_retrieval
from workflows.steps.response_generation import response_generation
from workflows.steps.result_validation import result_validation
from workflows.steps.monitoring import monitoring


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


def execution_router(state: WorkflowState) -> str:
    """Select text or data tasks and stop when finished or on error."""
    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", 0)
    prev = idx - 1
    if state.get("error"):
        return "response_generation"
    if 0 <= prev < len(tasks) and tasks[prev].get("error"):
        return "response_generation"
    if idx >= len(tasks):
        return "response_generation"
    task = tasks[idx]
    if task.get("requires_data"):
        return "data_retrieval"
    return "text_generation"


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
    builder.add_node("text_generation", text_generation)
    builder.add_node("data_retrieval", data_retrieval)
    builder.add_node("response_generation", response_generation)
    builder.add_node("result_validation", result_validation)
    # builder.add_node("conversation_summary", conversation_summary)
    builder.add_node("monitoring", monitoring)

    builder.set_entry_point("prompt_intake")
    builder.add_edge("prompt_intake", "intent_understanding")
    builder.add_edge("intent_understanding", "clarification")
    builder.add_conditional_edges("clarification", clarification_router)
    builder.add_edge("task_planning", "task_execution")
    builder.add_conditional_edges("task_execution", execution_router)
    builder.add_edge("text_generation", "task_execution")
    builder.add_edge("data_retrieval", "task_execution")
    builder.add_edge("response_generation", "result_validation")
    builder.add_conditional_edges("result_validation", validation_router)
    # builder.add_edge("conversation_summary", "monitoring")
    builder.add_edge("monitoring", END)

    return builder.compile(checkpointer=checkpointer)
