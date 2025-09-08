from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standard response wrapper for LLM outputs."""

    response: Any
