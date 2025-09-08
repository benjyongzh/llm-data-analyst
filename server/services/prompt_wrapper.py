"""Utilities for wrapping LLM prompts with standard instructions."""
from __future__ import annotations

import json

from schemas import LLMResponse


def _build_prefix() -> str:
    schema = json.dumps(LLMResponse.model_json_schema(), separators=(",", ":"))
    example = (
        "\nExample of a valid response (values are illustrative only):\n"
        "{\n"
        # '  "thoughts": ["step 1 reasoning", "step 2 reasoning"],\n'
        '  "response": "This is the final user-facing answer."\n'
        "}\n\n"
    )
    return (
        "You must respond with a JSON object that strictly matches this schema:\n"
        f"{schema}\n\n"
        "Requirements:\n"
        "- Output ONLY a single JSON object (no extra text before or after).\n"
        "- If the instructional prompt itself asks for JSON, put that JSON inside the `response` field.\n"
        "- The `response` field must always contain the final user-facing answer.\n"
        f"{example}"
        "Here is the instructional prompt:\n"
    )


PROMPT_PREFIX = _build_prefix()


def _build_suffix() -> str:
    return (
        "End of instructional prompt.\n"
        "Reminder: Return only the JSON object that matches the schema mentioned at the start of this entire prompt.\n"
        "Do not include explanations, commentary, or any text outside the JSON."
    )


PROMPT_SUFFIX = _build_suffix()


def wrap_prompt(prompt: str) -> str:
    """Wrap ``prompt`` with :data:`PROMPT_PREFIX` and :data:`PROMPT_SUFFIX`."""

    return f"{PROMPT_PREFIX.strip()}\n{prompt}\n{PROMPT_SUFFIX.strip()}"
