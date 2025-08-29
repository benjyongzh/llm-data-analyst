from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, TypedDict

from ..services import step_log_service

logger = logging.getLogger(__name__)


def track_step(step_name: str):
    """Decorator to log step execution start and end."""

    def decorator(func):
        def wrapper(state: WorkflowState, *args, **kwargs):
            msg_id = state.get("message_id")
            log_id = None
            # Clear token leftovers from previous steps
            for key in ("tokens_in", "tokens_out"):
                state.pop(key, None)
            thoughts = state.setdefault("thought", [])
            start_len = len(thoughts)

            if msg_id:
                try:
                    log_id = asyncio.run(
                        step_log_service.log_step_start(msg_id, step_name)
                    )
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                    log_id = loop.run_until_complete(
                        step_log_service.log_step_start(msg_id, step_name)
                    )

            exc: Exception | None = None
            try:
                result = func(state, *args, **kwargs)
            except Exception as e:  # pragma: no cover - defensive
                result = state
                state["error"] = str(e)
                exc = e
            finally:
                tokens_in = state.pop("tokens_in", 0)
                tokens_out = state.pop("tokens_out", 0)
                thoughts = state.get("thought", [])
                thought = None
                if len(thoughts) > start_len:
                    thought = thoughts[-1].get("thought")
                status = "error" if exc or state.get("error") else "success"
                if msg_id and log_id:
                    try:
                        asyncio.run(
                            step_log_service.log_step_end(
                                log_id,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                status=status,
                                thought=thought,
                                plan_sql=None,
                            )
                        )
                    except RuntimeError:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(
                            step_log_service.log_step_end(
                                log_id,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                status=status,
                                thought=thought,
                                plan_sql=None,
                            )
                        )
            if exc:
                raise exc
            return result

        return wrapper

    return decorator


class WorkflowState(TypedDict, total=False):
    """Shared state passed between workflow nodes."""

    conversation_id: str
    message_id: str
    user_id: str
    prompt: str
    history: str
    intent: str
    entities: Dict[str, Any]
    needs_clarification: bool
    clarification_questions: List[str]
    clarification_answers: Dict[str, Any]
    clarification_attempts: int
    clarification_limit: int
    clarification_escalated: bool
    db_url: str
    error: str
    response: str
    summary: str
    messages: List[Dict[str, Any]]
    timeframe: str
    timezone: str
    currency: str
    available_charts: List[str]
    model_name: str
    thought: List[Dict[str, str]]
    tokens_in: int
    tokens_out: int
    tasks: List[Dict[str, Any]]
    current_task_index: int
