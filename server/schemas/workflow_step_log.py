from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkflowStepLog(BaseModel):
    id: str
    message_id: str
    step_name: str
    thought: Optional[str] = None
    plan_sql: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str


__all__ = ["WorkflowStepLog"]

