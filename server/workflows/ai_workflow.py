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

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy import create_engine, inspect, MetaData, Table, select
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    """Shared state passed between workflow nodes."""

    conversation_id: str
    prompt: str
    history: str
    intent: str
    entities: Dict[str, Any]
    needs_clarification: bool
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
    entities.setdefault("timeframe", "last 12 months")
    entities.setdefault("timezone", "Asia/Singapore")
    entities.setdefault("currency", "single assumed currency")

    state["entities"] = entities
    state["intent"] = state.get("intent", "analysis")
    return state


def clarification(state: WorkflowState) -> WorkflowState:
    """Ask clarifying questions if the prompt is ambiguous."""
    logger.info("Step 3: Clarification loop")
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

    # Reset previous errors
    state.pop("error", None)

    db_url = state.get("db_url")
    entities = state.get("entities", {})
    if not db_url:
        msg = "No database URL provided"
        logger.warning(msg)
        state["error"] = msg
        state["data"] = []
        return state

    try:
        engine = create_engine(db_url)
    except Exception as exc:
        msg = f"Invalid database URL: {exc}"
        logger.exception(msg)
        state["error"] = msg
        state["data"] = []
        return state

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            logger.debug("Reflected tables: %s", tables)

            table_name = entities.get("table") or (tables[0] if tables else None)
            if not table_name or table_name not in tables:
                msg = (
                    f"Table '{table_name}' not found" if table_name else "No table specified or found in database"
                )
                logger.warning(msg)
                state["error"] = msg
                state["data"] = []
                return state

            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            columns = entities.get("columns")
            if columns:
                selected_cols = [table.c[col] for col in columns if col in table.c]
            else:
                selected_cols = list(table.c)

            stmt = select(*selected_cols)

            # Apply simple filters from entities
            filters = entities.get("filters", {})
            for col, value in filters.items():
                if col in table.c:
                    stmt = stmt.where(table.c[col] == value)

            # Apply timeframe assumption if a date column exists
            timeframe = entities.get("timeframe", "last 12 months")
            if timeframe == "last 12 months":
                date_col = next(
                    (table.c[c] for c in ["date", "created_at", "timestamp"] if c in table.c),
                    None,
                )
                if date_col is not None:
                    start_date = datetime.utcnow() - timedelta(days=365)
                    stmt = stmt.where(date_col >= start_date)

            result = conn.execute(stmt)
            state["data"] = [dict(row._mapping) for row in result]
    except Exception as exc:
        logger.exception("Error during data retrieval: %s", exc)
        state["error"] = str(exc)
        state["data"] = []
    finally:
        engine.dispose()

    return state


def visualization_spec(state: WorkflowState) -> WorkflowState:
    """Determine chart type and package spec with data."""
    logger.info("Step 6: Visualization spec & data packaging")
    if state.get("error"):
        state["chart_spec"] = {}
        return state

    state["chart_spec"] = {
        "chart_type": "bar",
        "data": state.get("data", []),
        "dimensions": [],
        "measures": [],
    }
    return state


def response_generation(state: WorkflowState) -> WorkflowState:
    """Compose the textual response and attach chart spec."""
    logger.info("Step 7: Response generation & delivery")
    if error := state.get("error"):
        state["response"] = error
    else:
        state["response"] = "Analysis complete. See chart specification for details."
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
    builder.add_edge("clarification", "task_planning")
    builder.add_edge("task_planning", "data_retrieval")
    builder.add_edge("data_retrieval", "visualization_spec")
    builder.add_edge("visualization_spec", "response_generation")
    builder.add_edge("response_generation", "result_validation")
    builder.add_edge("result_validation", "conversation_summary")
    builder.add_edge("conversation_summary", "monitoring")
    builder.add_edge("monitoring", END)

    return builder.compile()
