from __future__ import annotations

from openai import OpenAI

from config import get_settings

settings = get_settings()
from schemas.conversation import TextContent
from workflows.base import WorkflowState, logger, track_step, append_error


@track_step("text_generation")
def text_generation(state: WorkflowState) -> WorkflowState:
    """Generate a text answer for a task that doesn't require data."""
    logger.info("Text generation sub-step")
    idx = state.get("current_task_index")
    tasks = state.get("tasks", [])
    task = tasks[idx] if isinstance(idx, int) and idx < len(tasks) else None
    if task is None:
        append_error(state, "text_generation", "Invalid task index")
        return state

    client = OpenAI(api_key=settings.LLM_API_KEY)
    prompt = (
        f"Task: {task.get('description', '')}\n" "Provide the best possible answer."
    )
    try:
        resp = client.responses.create(
            model=settings.LLM_RESPONSE_MODEL,
            input=prompt,
        )
        ti = getattr(resp.usage, "input_tokens", 0) if getattr(resp, "usage", None) else 0
        to = getattr(resp.usage, "output_tokens", 0) if getattr(resp, "usage", None) else 0
        state["tokens_in"] = ti
        state["tokens_out"] = to
        task["token_in"] = ti
        task["token_out"] = to
        task["result"] = TextContent(
            content=resp.output[0].content[0].text.strip()
        ).model_dump()
    except Exception as exc:  # pragma: no cover - LLM failure fallback
        logger.exception("Text generation failed: %s", exc)
        msg = str(exc)
        append_error(state, "text_generation", msg)
        task["error"] = msg
        return state
    state.setdefault("thought", []).append(
        {"step": "text_generation", "thought": "Generated text"}
    )
    return state
