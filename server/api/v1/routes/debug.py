from fastapi import APIRouter, Depends

from auth import verify_token
from workflows.base import WorkflowState
from workflows.steps.prompt_intake import prompt_intake
from workflows.steps.intent_understanding import intent_understanding
from workflows.steps.clarification import clarification
from workflows.steps.task_planning import task_planning
from workflows.steps.task_execution import task_execution
from workflows.steps.text_generation import text_generation
from workflows.steps.data_retrieval import data_retrieval
from workflows.steps.visualization_spec import visualization_spec
from workflows.steps.response_generation import response_generation
from workflows.steps.result_validation import result_validation
from workflows.steps.monitoring import monitoring

router = APIRouter(prefix="/api/v1/debug")


@router.post("/prompt_intake")
async def debug_prompt_intake(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return prompt_intake(state)


@router.post("/intent_understanding")
async def debug_intent_understanding(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return intent_understanding(state)


@router.post("/clarification")
async def debug_clarification(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return clarification(state)


@router.post("/task_planning")
async def debug_task_planning(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return task_planning(state)


@router.post("/task_execution")
async def debug_task_execution(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return task_execution(state)


@router.post("/text_generation")
async def debug_text_generation(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return text_generation(state)


@router.post("/data_retrieval")
async def debug_data_retrieval(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return data_retrieval(state)


@router.post("/visualization_spec")
async def debug_visualization_spec(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return visualization_spec(state)


@router.post("/response_generation")
async def debug_response_generation(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return response_generation(state)


@router.post("/result_validation")
async def debug_result_validation(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return result_validation(state)


@router.post("/monitoring")
async def debug_monitoring(
    state: WorkflowState, token_data: dict = Depends(verify_token)
) -> WorkflowState:
    return monitoring(state)


__all__ = ["router"]
