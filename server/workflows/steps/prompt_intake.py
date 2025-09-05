from __future__ import annotations

from typing import List

from workflows.base import WorkflowState, logger, track_step, append_error


@track_step("prompt_intake")
def prompt_intake(state: WorkflowState, checkpointer=None) -> WorkflowState:
    """Receive the user prompt and load conversation history."""
    logger.info("Step 1: Prompt intake for conversation %s", state.get("conversation_id"))
    conv_id = state.get("conversation_id")
    if conv_id and checkpointer:
        try:
            history = checkpointer.load(conv_id, state.get("workflow_run_id"))
        except Exception as exc:
            logger.exception(
                "Failed to load conversation %s: %s", conv_id, exc
            )
            append_error(state, "prompt_intake", "Failed to load conversation history")
            return state
        summary = history.get("summary", "")
        messages = history.get("messages", [])
        history_parts: List[str] = []
        if summary:
            history_parts.append(summary)
        for msg in messages:
            text = msg.get("content", {}).get("text")
            if text:
                history_parts.append(f"{msg['role']}: {text}")
        if history_parts:
            state["history"] = "\n".join(history_parts)
        state["summary"] = summary
        state["messages"] = messages
    state.setdefault("history", "")
    state.setdefault("thought", []).append(
        {"step": "prompt_intake", "thought": "Loaded conversation context"}
    )
    return state
