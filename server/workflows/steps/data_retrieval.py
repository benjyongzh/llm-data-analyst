from __future__ import annotations

from typing import Any, Dict, List

from schemas.conversation import ChartSpecification, DataContent
from workflows.base import WorkflowState, logger, track_step
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

    if not db_url:
        logger.warning("No database URL provided; skipping data retrieval")
        state["error"] = "No database URL provided."
        if task is not None:
            task["error"] = state["error"]
        return state

    adapter = None
    sql = ""
    try:
        adapter = get_adapter(db_url)
    except Exception as exc:  # pragma: no cover - depends on adapter implementations
        logger.exception("Invalid database URL: %s", exc)
        state["error"] = "Invalid database URL."
        if task is not None:
            task["error"] = state["error"]
        return state

    try:
        table_name = entities.get("table")
        if not table_name:
            logger.error("No table specified in entities")
            state["error"] = "No table specified."
            if task is not None:
                task["error"] = state["error"]
            return state

        # Entities are expected to contain canonical names from the mapping layer
        dims: List[str] = entities.get("dimensions", []) or []
        metrics: List[str] = entities.get("metrics", []) or []
        filters: Dict[str, Any] = entities.get("filters", {}) or {}

        data, sql = adapter.fetch_data(table_name, dims, metrics, filters)
        state["_data"] = data

        from workflows.steps.visualization_spec import visualization_spec

        state = visualization_spec(state)
        chart_spec = state.get("_chart_spec", {})
        if task is not None:
            task["sql"] = sql
            task["result"] = DataContent(
                content=ChartSpecification(**chart_spec)
            ).model_dump()
    except Exception as exc:
        logger.exception("Data retrieval failed: %s", exc)
        state["error"] = str(exc)
        if task is not None:
            task["error"] = state["error"]
    finally:
        if adapter:
            adapter.close()
    success = not state.get("error")
    thought = "Retrieved data successfully" if success else "Data retrieval failed"
    state.setdefault("thought", []).append(
        {"step": "data_retrieval", "thought": thought}
    )
    return state
