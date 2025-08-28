from __future__ import annotations

import re

from ..base import WorkflowState, logger, track_step


@track_step("result_validation")
def result_validation(state: WorkflowState) -> WorkflowState:
    """Validate the response for correctness and safety."""
    logger.info("Step 8: Result validation & safety")
    tasks = state.get("tasks", [])
    sql_statements = [t.get("sql", "") for t in tasks if t.get("sql")]
    summary = state.get("response", "")

    # SQL allowlist: only simple SELECT statements without dangerous keywords
    allowed = re.compile(r"^\s*select\b", re.IGNORECASE)
    forbidden = re.compile(
        r";|\b(drop|delete|insert|update|alter|grant|revoke)\b",
        re.IGNORECASE,
    )
    for sql in sql_statements:
        if not allowed.match(sql) or forbidden.search(sql):
            state["error"] = "SQL validation failed."
            return state

    if summary:
        # Basic character allowlist
        summary_ok = re.compile(r"^[\w\s.,!?:;'\-]*$", re.UNICODE)
        if not summary_ok.match(summary):
            state["error"] = "Summary validation failed."
            return state

        # Guardrail checks for PII
        pii_patterns = [
            re.compile(r"[\w.-]+@[\w.-]+", re.IGNORECASE),
            re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        ]
        if any(p.search(summary) for p in pii_patterns):
            state["error"] = "PII detected in summary."
            return state

        # Simple profanity filter
        profanity = {"damn", "shit"}
        if any(word in summary.lower() for word in profanity):
            state["error"] = "Profanity detected in summary."
            return state

    state.setdefault("thought", []).append(
        {"step": "result_validation", "thought": "Validated result"}
    )
    return state
