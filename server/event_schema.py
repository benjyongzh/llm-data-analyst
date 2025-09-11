from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal


class WorkflowEvent(BaseModel):
    type: Literal['agent_token', 'agent_message', 'step_update', 'error', 'done']
    conversation_id: str
    workflow_run_id: str
    step_id: str
    agent_id: str
    delta: Optional[str] = None
    content: Optional[str] = None
    state_patch: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


__all__ = ['WorkflowEvent']
