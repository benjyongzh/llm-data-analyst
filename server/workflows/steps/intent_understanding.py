from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI

from config import get_settings
from semantic.mapper import resolve_term

settings = get_settings()
from workflows.base import WorkflowState, logger, track_step, append_error
from services.logging_service import create_logged_response


@track_step("intent_understanding")
def intent_understanding(state: WorkflowState) -> WorkflowState:
    """Classify intent, extract entities, and apply default assumptions."""
    logger.info("Step 2: Intent & query understanding")

    prompt = state.get("prompt", "")
    history = state.get("history", "")
    client = OpenAI(api_key=settings.LLM_API_KEY)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "intent_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "entities": {
                        "type": "object",
                        "properties": {
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "dimensions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "timeframe": {"type": "string"},
                        },
                    },
                    "clarification_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["intent", "entities", "clarification_questions"],
            },
        },
    }
    message = (
        "Summarize the user's intent in a single sentence capturing all requested actions or questions. "
        "Extract any metrics, dimensions, and timeframe mentioned. If the request is ambiguous or "
        "missing details you need to fulfill it, ask clarifying questions. "
        "Otherwise return an empty list of questions.\n"
        f"Conversation so far:\n{history}\nUser request: {prompt}"
    )
    raw_text = ""
    try:
        resp, raw_text = create_logged_response(
            client,
            model=settings.LLM_RESPONSE_MODEL,
            input=message,
            response_format=response_format,
        )
        if getattr(resp, "usage", None):
            state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
            state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
        parsed = json.loads(raw_text)
    except Exception as exc:  # pragma: no cover - LLM failure fallback
        logger.exception("Failed to parse intent response: %s", exc)
        append_error(state, "intent_understanding", str(exc))
        return state

    # Resolve natural-language terms to canonical schema names
    parsed_entities = parsed.get("entities", {})
    db_key = state.get("db_connection_id", "default")
    user_id = state.get("user_id", "")
    def _resolve(t: str) -> str:
        try:
            return resolve_term(t, db_key, user_id)
        except KeyError:
            logger.warning("Missing semantic mapping for term '%s'", t)
            return t

    metrics = [_resolve(m) for m in parsed_entities.get("metrics", [])]
    if metrics:
        parsed_entities["metrics"] = metrics
    dimensions = [_resolve(d) for d in parsed_entities.get("dimensions", [])]
    if dimensions:
        parsed_entities["dimensions"] = dimensions
    if "table" in parsed_entities:
        parsed_entities["table"] = _resolve(parsed_entities["table"])
    if "table_name" in parsed_entities:
        parsed_entities["table"] = _resolve(parsed_entities.pop("table_name"))

    entities = state.get("entities", {})
    entities.setdefault("timezone", "Asia/Singapore")
    entities.setdefault("currency", "single assumed currency")
    entities.update(parsed_entities)
    if "timeframe" not in entities:
        entities["timeframe"] = "last 12 months"

    intent = parsed.get("intent", "")
    questions: List[str] = parsed.get("clarification_questions", [])

    state["entities"] = entities
    state["intent"] = intent
    state["needs_clarification"] = bool(questions)
    state["clarification_questions"] = questions
    state.setdefault("thought", []).append(
        {"step": "intent_understanding", "thought": raw_text}
    )
    return state
