from __future__ import annotations

import re
from typing import Any, Dict, List

from ..base import WorkflowState, logger, track_step


@track_step("visualization_spec")
def visualization_spec(state: WorkflowState) -> WorkflowState:
    """Determine chart type and build a rich chart specification."""
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

    # Determine chart type based on dimensions, measures, and intent
    time_like = [d for d in dims if any(t in d.lower() for t in ["date", "time", "year", "month", "day"])]
    if time_like:
        chart_type = "line"
    elif len(measures) > 1:
        chart_type = "bar"
    else:
        chart_type = "bar"

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
        "chartTypes": [chart_type],
    }

    state["_chart_spec"] = chart_spec
    state.setdefault("thought", []).append(
        {"step": "visualization_spec", "thought": "Created visualization spec"}
    )
    return state
