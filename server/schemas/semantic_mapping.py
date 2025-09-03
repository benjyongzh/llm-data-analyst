from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class SemanticMappingResponse(BaseModel):
    mappings: Dict[str, List[str]]
