from __future__ import annotations

from workflows.base import WorkflowState, logger, track_step


@track_step("monitoring")
def monitoring(state: WorkflowState) -> WorkflowState:
    """Capture feedback signals for continuous improvement."""
    logger.info("Step 9: Monitoring & continuous improvement")
    state.setdefault("thought", []).append(
        {"step": "monitoring", "thought": "Monitoring step completed"}
    )
    return state
