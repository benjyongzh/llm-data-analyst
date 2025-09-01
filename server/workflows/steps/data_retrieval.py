from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import MetaData, Table, create_engine, func, inspect, select

from schemas.conversation import ChartSpecification, DataContent
from workflows.base import WorkflowState, logger, track_step


@track_step("data_retrieval")
def data_retrieval(state: WorkflowState) -> WorkflowState:
    """Retrieve and process data using SQLAlchemy reflection."""
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

    engine = None
    sql = ""
    try:
        engine = create_engine(db_url)
    except Exception as exc:  # pragma: no cover - depends on SQLAlchemy internals
        logger.exception("Invalid database URL: %s", exc)
        state["error"] = "Invalid database URL."
        if task is not None:
            task["error"] = state["error"]
        return state

    try:
        inspector = inspect(engine)
        table_name = entities.get("table") or entities.get("table_name")
        if not table_name:
            logger.error("No table specified in entities")
            state["error"] = "No table specified."
            if task is not None:
                task["error"] = state["error"]
            return state

        tables = inspector.get_table_names()
        logger.debug("Reflected tables: %s", tables)
        if table_name not in tables:
            logger.error("Table %s not found", table_name)
            state["error"] = f"Table '{table_name}' not found."
            if task is not None:
                task["error"] = state["error"]
            return state

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        dims: List[str] = entities.get("dimensions", []) or []
        metrics: List[str] = (
            entities.get("metrics", []) or entities.get("measures", []) or []
        )
        filters: Dict[str, Any] = entities.get("filters", {}) or {}

        if metrics:
            group_cols = [table.c[d] for d in dims if d in table.c]
            agg_cols = [
                func.sum(table.c[m]).label(m)
                for m in metrics
                if m in table.c
            ]
            stmt = select(*group_cols, *agg_cols)
            if group_cols:
                stmt = stmt.group_by(*group_cols)
        else:
            cols = [table.c[c] for c in dims if c in table.c]
            if not cols:
                cols = list(table.c)
            stmt = select(*cols)

        for col, val in filters.items():
            if col in table.c:
                stmt = stmt.where(table.c[col] == val)

        stmt = stmt.limit(100)
        try:
            sql = str(stmt)
        except Exception:  # pragma: no cover - defensive
            sql = ""

        with engine.connect() as conn:
            result = conn.execute(stmt)
            state["_data"] = [dict(row._mapping) for row in result]

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
        if engine:
            engine.dispose()
    success = not state.get("error")
    thought = "Retrieved data successfully" if success else "Data retrieval failed"
    state.setdefault("thought", []).append(
        {"step": "data_retrieval", "thought": thought}
    )
    return state
