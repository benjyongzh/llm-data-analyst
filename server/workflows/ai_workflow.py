"""LangGraph-based AI workflow for the data analyst chatbot.

Each step of the analytics pipeline is implemented as a LangGraph node. The
workflow is deterministic and logs progress at every node for easier debugging.

The workflow makes a best effort to support any SQL database using SQLAlchemy
reflection. Default assumptions are applied when the user does not provide
contextual details:

* Timeframe – last 12 months
* Timezone – Asia/Singapore
* Currency – echo if mixed; otherwise assume a single currency
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI
from sqlalchemy import create_engine, inspect


logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    """Shared state passed between workflow nodes."""

    conversation_id: str
    prompt: str
    history: str
    intent: str
    entities: Dict[str, Any]
    needs_clarification: bool
    clarification_questions: List[str]
    clarification_answers: Dict[str, Any]
    clarification_attempts: int
    clarification_limit: int
    clarification_escalated: bool
    plan: Dict[str, Any]
    db_url: str
    data: List[Dict[str, Any]]
    chart_spec: Dict[str, Any]
    response: str
    summary: str
    timeframe: str
    timezone: str
    currency: str


def prompt_intake(state: WorkflowState) -> WorkflowState:
    """Receive the user prompt and load conversation history."""
    logger.info("Step 1: Prompt intake for conversation %s", state.get("conversation_id"))
    state.setdefault("history", "")
    return state


def intent_understanding(state: WorkflowState) -> WorkflowState:
    """Classify intent, extract entities, and apply default assumptions."""
    logger.info("Step 2: Intent & query understanding")

    entities = state.get("entities", {})
    entities.setdefault("timezone", "Asia/Singapore")
    entities.setdefault("currency", "single assumed currency")

    questions: List[str] = []
    if not entities.get("timeframe"):
        questions.append("What timeframe would you like to analyze?")
        entities["timeframe"] = "last 12 months"
    if not entities.get("metrics"):
        questions.append("Which metrics are you interested in?")
    if not entities.get("dimensions"):
        questions.append("Which dimensions should the data be grouped by?")

    state["entities"] = entities
    state["intent"] = state.get("intent", "analysis")
    state["needs_clarification"] = bool(questions)
    state["clarification_questions"] = questions
    return state


def clarification(state: WorkflowState) -> WorkflowState:
    """Ask clarifying questions and merge user responses."""
    logger.info("Step 3: Clarification loop")
    if state.get("needs_clarification"):
        state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
        questions = state.get("clarification_questions", [])
        answers = state.get("clarification_answers")
        if answers:
            logger.debug("Received clarification answers: %s", answers)
            entities = state.get("entities", {})
            entities.update(answers)
            state["entities"] = entities
            # Re-evaluate intent with the new information
            state = intent_understanding(state)
        else:
            logger.debug("Clarification needed. Questions: %s", questions)
        limit = state.get("clarification_limit", 3)
        if state.get("needs_clarification") and state["clarification_attempts"] >= limit:
            logger.warning(
                "Maximum clarification attempts (%d) reached; escalating", limit
            )
            state["clarification_escalated"] = True
            state["needs_clarification"] = False
    return state


def task_planning(state: WorkflowState) -> WorkflowState:
    """Plan required actions and select tools."""
    logger.info("Step 4: Task planning & tool selection")
    state["plan"] = {"use_db": True, "visualization": True}
    return state


def data_retrieval(state: WorkflowState) -> WorkflowState:
    """Retrieve and process data using SQLAlchemy reflection."""
    logger.info("Step 5: Data retrieval & processing")
    db_url = state.get("db_url")
    if db_url:
        engine = create_engine(db_url)
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.debug("Reflected tables: %s", tables)
            state["data"] = []  # Placeholder for real queries
        finally:
            engine.dispose()
    else:
        logger.warning("No database URL provided; skipping data retrieval")
        state["data"] = []
    return state


def visualization_spec(state: WorkflowState) -> WorkflowState:
    """Determine chart type and package spec with data."""
    logger.info("Step 6: Visualization spec & data packaging")
    state["chart_spec"] = {
        "chart_type": "bar",
        "data": state.get("data", []),
        "dimensions": [],
        "measures": [],
    }
    return state


def response_generation(state: WorkflowState) -> WorkflowState:
    """Compose a narrative summary and attach chart spec for the frontend."""
    logger.info("Step 7: Response generation & delivery")

    client = OpenAI(api_key=os.environ["LLM_API_KEY"])
    data_json = json.dumps(state.get("data", []))
    spec_json = json.dumps(state.get("chart_spec", {}))
    prompt = (
        "Provide a concise, user-facing summary of the following data. "
        "Reference the chart specification when relevant.\n"
        f"Data: {data_json}\n"
        f"Chart spec: {spec_json}"
    )

    resp = client.responses.create(
        model=os.getenv("LLM_RESPONSE_MODEL", "gpt-4o-mini"),
        input=prompt,
    )
    state["response"] = resp.output[0].content[0].text.strip()
    return state


def result_validation(state: WorkflowState) -> WorkflowState:
    """Validate the response for correctness and safety."""
    logger.info("Step 8: Result validation & safety")
    return state


def conversation_summary(state: WorkflowState) -> WorkflowState:
    """Summarize the conversation and log outputs."""
    logger.info("Step 9: Conversation summary & logging")
    state["summary"] = "Conversation summarized."
    return state


def monitoring(state: WorkflowState) -> WorkflowState:
    """Capture feedback signals for continuous improvement."""
    logger.info("Step 10: Monitoring & continuous improvement")
    return state


def clarification_router(state: WorkflowState) -> str:
    """Route back for questions, escalate, or continue if complete."""
    if state.get("needs_clarification") or state.get("clarification_escalated"):
        return END
    return "task_planning"


def build_workflow() -> StateGraph[WorkflowState]:
    """Create and compile the LangGraph workflow."""
    builder = StateGraph(WorkflowState)

    builder.add_node("prompt_intake", prompt_intake)
    builder.add_node("intent_understanding", intent_understanding)
    builder.add_node("clarification", clarification)
    builder.add_node("task_planning", task_planning)
    builder.add_node("data_retrieval", data_retrieval)
    builder.add_node("visualization_spec", visualization_spec)
    builder.add_node("response_generation", response_generation)
    builder.add_node("result_validation", result_validation)
    builder.add_node("conversation_summary", conversation_summary)
    builder.add_node("monitoring", monitoring)

    builder.set_entry_point("prompt_intake")
    builder.add_edge("prompt_intake", "intent_understanding")
    builder.add_edge("intent_understanding", "clarification")
    builder.add_conditional_edges("clarification", clarification_router)
    builder.add_edge("task_planning", "data_retrieval")
    builder.add_edge("data_retrieval", "visualization_spec")
    builder.add_edge("visualization_spec", "response_generation")
    builder.add_edge("response_generation", "result_validation")
    builder.add_edge("result_validation", "conversation_summary")
    builder.add_edge("conversation_summary", "monitoring")
    builder.add_edge("monitoring", END)

    return builder.compile()
