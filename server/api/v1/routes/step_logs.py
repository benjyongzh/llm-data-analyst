from fastapi import APIRouter, Depends

from auth import verify_token
from schemas import WorkflowStepLog
from services import step_log_service


router = APIRouter(prefix="/step-logs")


@router.get("/{message_id}", response_model=list[WorkflowStepLog])
async def list_step_logs(message_id: str, token_data: dict = Depends(verify_token)):
    return await step_log_service.get_step_logs(message_id)


__all__ = ["router"]

