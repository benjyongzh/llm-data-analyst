from __future__ import annotations

from workflows.base import WorkflowState, logger, track_step


@track_step("task_execution")
def task_execution(state: WorkflowState) -> WorkflowState:
    """Advance through the task list and accumulate token usage."""
    logger.info("Step 5: Task execution")
    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", -1)
    if idx == -1:
        state["tokens_in"] = 0
        state["tokens_out"] = 0
    elif 0 <= idx < len(tasks):
        task = tasks[idx]
        state["tokens_in"] = state.get("tokens_in", 0) + task.get("token_in", 0)
        state["tokens_out"] = state.get("tokens_out", 0) + task.get("token_out", 0)
    state["current_task_index"] = idx + 1
    state.setdefault("thought", []).append(
        {"step": "task_execution", "thought": "Advanced task pointer"}
    )
    return state
