"""Utilities for wrapping LLM prompts with standard instructions."""
from __future__ import annotations

import json

from schemas import LLMResponse


def _build_prefix() -> str:
    schema = json.dumps(LLMResponse.model_json_schema(), separators=(",", ":"))
    return (
        "You must respond with a JSON object that matches this schema:\n"
        f"{schema}\n"
        "This is a 100% requirement. Do not include any text outside the JSON object. "
        "If the user's prompt requests its own JSON structure, place that JSON inside the `response` field. "
        "The `response` field must contain the final user-facing answer."
    )


PROMPT_PREFIX = _build_prefix()


def _build_suffix() -> str:
    return "Return only the JSON object described above and nothing else."


PROMPT_SUFFIX = _build_suffix()


def wrap_prompt(prompt: str) -> str:
    """Wrap ``prompt`` with :data:`PROMPT_PREFIX` and :data:`PROMPT_SUFFIX`."""

    return f"{PROMPT_PREFIX.strip()}\n{prompt}\n{PROMPT_SUFFIX.strip()}"
