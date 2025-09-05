"""Logging helpers for workflow and LLM interactions."""
import asyncio
import json
import logging
from contextvars import ContextVar, Token
from typing import Any, Tuple

from openai import OpenAI

from services import agent_run_service

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
    client: OpenAI,
    *,
    step: str | None = None,
    workflow_run_id: str | None = None,
    workflow_step_id: str | None = None,
    **kwargs: Any,
) -> Tuple[Any, str]:
    """Call ``client.responses.create`` and log the raw text output.

    If ``step`` is omitted, the current step name from ``@track_step`` is used
    when available. Returns the full response object along with the extracted
    text so callers can handle token accounting or parse the text as needed.
    When ``workflow_run_id`` is provided, the call is recorded in ``agent_run``
    for auditing.
    """

    step_name = step or get_current_step() or "unknown"
    prompt = kwargs.get("input")
    model_name = kwargs.get("model")

    agent_run_id: str | None = None
    if workflow_run_id and prompt and model_name:
        try:
            agent_run_id = asyncio.run(
                agent_run_service.log_agent_run_start(
                    workflow_run_id,
                    prompt,
                    model_name,
                    workflow_step_id,
                )
            )
        except RuntimeError:
            loop = asyncio.get_event_loop()
            agent_run_id = loop.run_until_complete(
                agent_run_service.log_agent_run_start(
                    workflow_run_id,
                    prompt,
                    model_name,
                    workflow_step_id,
                )
            )

    try:
        resp = client.responses.create(**kwargs)
    except Exception as exc:
        if agent_run_id:
            try:
                asyncio.run(
                    agent_run_service.log_agent_run_end(
                        agent_run_id,
                        input_json=kwargs,
                        output_json={"error": str(exc)},
                        status="failed",
                    )
                )
            except RuntimeError:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    agent_run_service.log_agent_run_end(
                        agent_run_id,
                        input_json=kwargs,
                        output_json={"error": str(exc)},
                        status="failed",
                    )
                )
        raise

    try:
        raw = resp.output[0].content[0].text
    except Exception:  # pragma: no cover - unexpected response shape
        raw = resp

    log_llm_output(step_name, raw)

    if agent_run_id:
        usage = getattr(resp, "usage", None)
        token_usage = 0
        if usage:
            token_usage = (
                getattr(usage, "total_tokens", 0)
                or getattr(usage, "input_tokens", 0)
                + getattr(usage, "output_tokens", 0)
            )
        output_json = resp.model_dump() if hasattr(resp, "model_dump") else raw
        try:
            asyncio.run(
                agent_run_service.log_agent_run_end(
                    agent_run_id,
                    input_json=kwargs,
                    output_json=output_json,
                    log=raw,
                    token_usage=token_usage,
                )
            )
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                agent_run_service.log_agent_run_end(
                    agent_run_id,
                    input_json=kwargs,
                    output_json=output_json,
                    log=raw,
                    token_usage=token_usage,
                )
            )

    return resp, raw
