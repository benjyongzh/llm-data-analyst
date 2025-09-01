from __future__ import annotations

from schemas.conversation import QueryResponseData, TextContent
from workflows.base import WorkflowState, logger, track_step


@track_step("response_generation")
def response_generation(state: WorkflowState) -> WorkflowState:
    """Package task results into a QueryResponseData JSON structure."""
    logger.info("Step 7: Response generation & delivery")
    tasks = state.get("tasks", [])
    messages = []

    if state.get("error"):
        messages.append(TextContent(content=state["error"]).model_dump())
    else:
        for task in tasks:
            result = task.get("result")
            if result:
                messages.append(result)

    state["response"] = QueryResponseData(message=messages).model_dump()
    state.setdefault("thought", []).append(
        {"step": "response_generation", "thought": "Compiled task results"}
    )
    return state
