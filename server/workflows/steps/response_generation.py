from __future__ import annotations

import json

from openai import OpenAI

from ...config import settings
from ..base import WorkflowState, logger, track_step


@track_step("response_generation")
def response_generation(state: WorkflowState) -> WorkflowState:
    """Compose a narrative summary and attach chart spec for the frontend."""
    logger.info("Step 7: Response generation & delivery")
    if state.get("error"):
        state["response"] = state["error"]
        return state

    client = OpenAI(api_key=settings.LLM_API_KEY)
    tasks_json = json.dumps(state.get("tasks", []))
    prompt = (
        "Create a final user-facing answer based on the following ordered task results. "
        "If a task includes data and a chart specification, mention the chart in the response.\n"
        f"Tasks: {tasks_json}"
    )

    resp = client.responses.create(
        model=settings.LLM_RESPONSE_MODEL,
        input=prompt,
    )
    if getattr(resp, "usage", None):
        state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
        state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
    state["response"] = resp.output[0].content[0].text.strip()
    state.setdefault("thought", []).append(
        {"step": "response_generation", "thought": state["response"]}
    )
    return state
