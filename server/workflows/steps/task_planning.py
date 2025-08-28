from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI

from ...config import settings
from ..base import WorkflowState, logger, track_step


@track_step("task_planning")
def task_planning(state: WorkflowState) -> WorkflowState:
    """Plan required actions and select tools for each step."""
    logger.info("Step 4: Task planning & tool selection")
    prompt = state.get("prompt", "")
    intent = state.get("intent", "analysis")
    client = OpenAI(api_key=settings.LLM_API_KEY)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "task_plan",
            "schema": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "requires_data": {"type": "boolean"},
                            },
                            "required": ["description", "requires_data"],
                        },
                    }
                },
                "required": ["tasks"],
            },
        },
    }
    inp = (
        "Break down the user's request into a linear sequence of tasks. "
        "For each task, state whether database data is required.\n"
        f"Intent: {intent}\nPrompt: {prompt}"
    )
    resp = client.responses.create(
        model=settings.LLM_RESPONSE_MODEL,
        input=inp,
        response_format=response_format,
    )
    if getattr(resp, "usage", None):
        state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
        state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
    try:
        data = json.loads(resp.output[0].content[0].text)
        planned = data.get("tasks", [])
    except Exception:
        planned = []
    tasks: List[Dict[str, Any]] = []
    for t in planned:
        tasks.append(
            {
                "description": t.get("description", ""),
                "requires_data": t.get("requires_data", False),
                "result": None,
                "token_in": 0,
                "token_out": 0,
                "sql": None,
                "error": "",
            }
        )
    state["tasks"] = tasks
    use_db = any(t.get("requires_data") for t in tasks)
    state["plan"] = {"use_db": use_db, "visualization": use_db}
    state.setdefault("thought", []).append(
        {"step": "task_planning", "thought": "Created task plan"}
    )
    return state
