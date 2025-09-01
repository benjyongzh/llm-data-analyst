from __future__ import annotations

from workflows.base import WorkflowState, logger, track_step


@track_step("clarification")
def clarification(state: WorkflowState) -> WorkflowState:
    """Ask clarifying questions and merge user responses."""
    logger.info("Step 3: Clarification loop")
    if state.get("needs_clarification"):
        state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
        questions = state.get("clarification_questions", [])
        answers = state.get("clarification_answers")
        if answers:
            logger.debug("Received clarification answers: %s", answers)
            entities = state.get("entities", {})
            entities.update(answers)
            state["entities"] = entities
            # Re-evaluate intent with the new information
            from workflows.steps.intent_understanding import intent_understanding

            state = intent_understanding(state)
        else:
            logger.debug("Clarification needed. Questions: %s", questions)
        limit = state.get("clarification_limit", 3)
        if state.get("needs_clarification") and state["clarification_attempts"] >= limit:
            logger.warning(
                "Maximum clarification attempts (%d) reached; escalating", limit
            )
            state["clarification_escalated"] = True
            state["needs_clarification"] = False
    state.setdefault("thought", []).append(
        {"step": "clarification", "thought": "Clarified user inputs"}
    )
    return state
