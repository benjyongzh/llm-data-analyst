from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List

from ...config import settings
from ...services.llm_service import choose_charts
from ..base import WorkflowState, logger, track_step


@track_step("visualization_spec")
def visualization_spec(state: WorkflowState) -> WorkflowState:
    """Determine chart types and build a rich chart specification."""
    logger.info("Step 6: Visualization spec & data packaging")

    data: List[Dict[str, Any]] = state.pop("_data", [])
    entities = state.get("entities", {})

    # Infer dimensions and measures from entities or data sample
    dims: List[str] = entities.get("dimensions", []) or []
    measures: List[str] = entities.get("metrics", []) or entities.get("measures", []) or []

    if data:
        sample = data[0]
        if not dims:
            dims = [k for k, v in sample.items() if not isinstance(v, (int, float))]
        if not measures:
            measures = [k for k, v in sample.items() if isinstance(v, (int, float))]

    available = state.get("available_charts", [])
    chart_types: List[str] = [available[0]] if available else ["bar"]

    idx = state.get("current_task_index")
    tasks = state.get("tasks", [])
    task_desc = ""
    if isinstance(idx, int) and idx < len(tasks):
        task_desc = tasks[idx].get("description", "")
    prompt = task_desc or state.get("prompt", "")

    model_name = state.get("model_name", settings.LLM_RESPONSE_MODEL)
    if available:
        try:
            charts = asyncio.run(
                choose_charts(
                    prompt=prompt,
                    available_charts=available,
                    data=data,
                    model_name=model_name,
                )
            )
            if charts:
                chart_types = list(charts)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Chart selection via LLM failed: %s", exc)
            # Fallback heuristic if LLM call fails
            time_like = [
                d
                for d in dims
                if any(t in d.lower() for t in ["date", "time", "year", "month", "day"])
            ]
            preferred: List[str]
            if time_like:
                preferred = ["line", "bar"]
            elif len(measures) > 1:
                preferred = ["bar", "line"]
            else:
                preferred = ["bar", "line"]
            chart_types = [c for c in preferred if c in available] or [available[0]]

    # Build new chart specification schema
    x_label = dims[0] if dims else ""
    title_parts: List[str] = []
    if measures:
        title_parts.append(", ".join(measures))
    if dims:
        title_parts.append("by " + ", ".join(dims))
    title = " ".join(title_parts) if title_parts else "Chart"

    x_values = [row.get(x_label) for row in data] if x_label else []
    data_type = "category"
    if x_values:
        first = x_values[0]
        if isinstance(first, (int, float)):
            data_type = "numeric"
        elif isinstance(first, str) and re.match(r"\d{4}-\d{2}-\d{2}", first):
            data_type = "date"

    y_axes: List[Dict[str, Any]] = []
    for m in measures:
        values = [float(row.get(m, 0)) for row in data]
        y_axes.append({"label": m, "values": values})

    chart_spec = {
        "title": title,
        "xAxis": {
            "label": x_label,
            "dataType": data_type,
            "values": x_values,
        },
        "yAxis": y_axes,
        "chartTypes": chart_types,
    }

    state["_chart_spec"] = chart_spec
    state.setdefault("thought", []).append(
        {"step": "visualization_spec", "thought": "Created visualization spec"}
    )
    return state
