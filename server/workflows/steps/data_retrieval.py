from __future__ import annotations

from typing import Any, Dict, List

from schemas.conversation import ChartSpecification, DataContent
from workflows.base import WorkflowState, logger, track_step, append_error
from db.adapters import get_adapter


@track_step("data_retrieval")
def data_retrieval(state: WorkflowState) -> WorkflowState:
    """Retrieve and process data using the unified adapter interface."""
    logger.info("Step 5: Data retrieval & processing")
    db_url = state.get("db_url")
    entities = state.get("entities", {})
    idx = state.get("current_task_index")
    tasks = state.get("tasks", [])
    task = tasks[idx] if isinstance(idx, int) and idx < len(tasks) else None
    initial_errors = len(state.get("error", []))

    if not db_url:
        logger.warning("No database URL provided; skipping data retrieval")
        msg = "No database URL provided."
        append_error(state, "data_retrieval", msg)
        if task is not None:
            task["error"] = msg
        return state

    adapter = None
    sql = ""
    try:
        adapter = get_adapter(db_url)
    except Exception as exc:  # pragma: no cover - depends on adapter implementations
        logger.exception("Invalid database URL: %s", exc)
        msg = "Invalid database URL."
        append_error(state, "data_retrieval", msg)
        if task is not None:
            task["error"] = msg
        return state

    try:
        table_name = entities.get("table")
        if not table_name:
            logger.error("No table specified in entities")
            msg = "No table specified."
            append_error(state, "data_retrieval", msg)
            if task is not None:
                task["error"] = msg
            return state

        # Entities are expected to contain canonical names from the mapping layer
        dims: List[str] = entities.get("dimensions", []) or []
        metrics: List[str] = entities.get("metrics", []) or []
        filters: Dict[str, Any] = entities.get("filters", {}) or {}

        data, sql = adapter.fetch_data(table_name, dims, metrics, filters)
        state["_data"] = data

        from workflows.steps.visualization_spec import visualization_spec

        pre_viz_errors = len(state.get("error", []))
        state = visualization_spec(state)
        if task is not None and len(state.get("error", [])) > pre_viz_errors:
            task["error"] = state["error"][-1]["message"]
        chart_spec = state.get("_chart_spec", {})
        if task is not None:
            task["sql"] = sql
            task["result"] = DataContent(
                content=ChartSpecification(**chart_spec)
            ).model_dump()
    except Exception as exc:
        logger.exception("Data retrieval failed: %s", exc)
        msg = str(exc)
        append_error(state, "data_retrieval", msg)
        if task is not None:
            task["error"] = msg
    finally:
        if adapter:
            adapter.close()
    error_count = len(state.get("error", []))
    success = error_count == initial_errors
    thought = "Retrieved data successfully" if success else "Data retrieval failed"
    state.setdefault("thought", []).append(
        {"step": "data_retrieval", "thought": thought}
    )
    return state
