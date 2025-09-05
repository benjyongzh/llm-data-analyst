"""Logging helpers for workflow and LLM interactions."""
import json
import logging
from contextvars import ContextVar, Token
from typing import Any, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)

# Context variable to track the current workflow step name
_current_step: ContextVar[str | None] = ContextVar("current_workflow_step", default=None)


def set_current_step(step: str) -> Token:
    """Store the current workflow step name in a context variable."""
    return _current_step.set(step)


def reset_current_step(token: Token) -> None:
    """Reset the current workflow step name."""
    _current_step.reset(token)


def get_current_step() -> str | None:
    """Retrieve the current workflow step name."""
    return _current_step.get()


def log_llm_output(step: str, output: Any) -> None:
    """Log raw LLM output for debugging."""
    try:
        formatted = json.dumps(output)
    except (TypeError, ValueError):
        formatted = str(output)
    logger.debug("[LLM OUTPUT %s] %s", step, formatted)


def create_logged_response(
    client: OpenAI, *, step: str | None = None, **kwargs: Any
) -> Tuple[Any, str]:
    """Call ``client.responses.create`` and log the raw text output.

    If ``step`` is omitted, the current step name from ``@track_step`` is used
    when available. Returns the full response object along with the extracted
    text so callers can handle token accounting or parse the text as needed.
    """

    step_name = step or get_current_step() or "unknown"

    resp = client.responses.create(**kwargs)
    try:
        raw = resp.output[0].content[0].text
    except Exception:  # pragma: no cover - unexpected response shape
        raw = resp
    log_llm_output(step_name, raw)
    return resp, raw
