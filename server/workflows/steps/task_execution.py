from __future__ import annotations

from ..base import WorkflowState, logger, track_step


@track_step("task_execution")
def task_execution(state: WorkflowState) -> WorkflowState:
    """Execute planned tasks sequentially, using data or text tools."""
    logger.info("Step 5: Task execution")
    tasks = state.get("tasks", [])
    tokens_in = tokens_out = 0
    for idx, task in enumerate(tasks):
        state["current_task_index"] = idx
        state.pop("error", None)
        if task.get("requires_data"):
            from .data_retrieval import data_retrieval

            state = data_retrieval(state)
        else:
            from .text_generation import text_generation

            state = text_generation(state)
        tokens_in += task.get("token_in", 0)
        tokens_out += task.get("token_out", 0)
        if state.get("error") or task.get("error"):
            break
    state["tokens_in"] = tokens_in
    state["tokens_out"] = tokens_out
    state.setdefault("thought", []).append(
        {"step": "task_execution", "thought": "Executed task plan"}
    )
    return state
