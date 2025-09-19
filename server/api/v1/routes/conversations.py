import asyncio
import logging
import os
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Depends, status
from schemas import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationQueryRequest,
    ConversationStopRequest,
    QueryResponse,
    QueryResponseData,
    ConversationDetail,
    ConversationListItem,
    TextContent,
)
from services import conversation_service, workflow_run_service
from workflows import build_workflow
from workflows.checkpointer import ConversationCheckpointer
from workflows.ai_workflow import WorkflowState
from workflows.base import append_error
from auth import verify_token
from config import get_settings

settings = get_settings()

router = APIRouter(prefix="/conversations")
logger = logging.getLogger(__name__)


@router.post("", response_model=ConversationCreateResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    token_data: dict = Depends(verify_token),
) -> ConversationCreateResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    conv_id, title = await conversation_service.create_conversation(
        request.conversation_id,
        request.user_id,
        request.db_connection_id,
        request.prompt,
        request.model,
    )
    if title is None:
        return ConversationCreateResponse(conversation_id=conv_id)
    return ConversationCreateResponse(conversation_id=conv_id, title=title)


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_chat(
    conversation_id: str,
    request: ConversationQueryRequest,
    token_data: dict = Depends(verify_token),
):
    try:
        await conversation_service.get_conversation_db_connection(
            conversation_id, token_data["user_id"]
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400 if detail == "DB connection disabled" else 404
        raise HTTPException(status_code=status_code, detail=detail)

    workflow_run_id = str(uuid.uuid4())
    worker_base = os.environ.get("FLY_WORKER_BASE_URL", "")
    stream_base = os.environ.get("FLY_STREAM_BASE_URL", "")

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{worker_base}/runs/start",
            json={
                "conversation_id": conversation_id,
                "workflow_run_id": workflow_run_id,
                "prompt": request.prompt,
                "user_id": token_data["user_id"],
                "available_charts": request.available_charts,
                "model_name": request.model_name,
            },
        )

    return {
        "workflow_run_id": workflow_run_id,
        "sse_url": f"{stream_base}/stream/{workflow_run_id}",
    }


@router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_chat(
    request: ConversationStopRequest,
    token_data: dict = Depends(verify_token),
):
    try:
        await conversation_service.verify_conversation_owner(
            request.conversation_id, token_data["user_id"]
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    worker_base = os.environ.get("FLY_WORKER_BASE_URL", "")
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{worker_base}/runs/{request.workflow_run_id}/stop",
            json={"conversation_id": request.conversation_id},
        )
    return {"status": "stopping"}


@router.post("/{conversation_id}/query", response_model=QueryResponse)
async def conversation_query(
    conversation_id: str,
    request: ConversationQueryRequest,
    token_data: dict = Depends(verify_token),
) -> QueryResponse:
    if not settings.LLM_API_KEY:
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")
    try:
        db_conn = await conversation_service.get_conversation_db_connection(
            conversation_id, token_data["user_id"]
        )
    except ValueError as exc:
        detail = str(exc)
        status = 400 if detail == "DB connection disabled" else 404
        raise HTTPException(status_code=status, detail=detail)
    user_message_id = await conversation_service.add_message(
        conversation_id,
        "user",
        [TextContent(content=request.prompt).model_dump()],
        token_data["user_id"],
    )

    dsn = (
        f"postgresql://{db_conn.user}:{db_conn.password}"
        f"@{db_conn.host}:{db_conn.port}/{db_conn.db_name}"
    )

    workflow_run_id = await workflow_run_service.create_run(conversation_id)

    state: WorkflowState = {
        "conversation_id": conversation_id,
        "workflow_run_id": workflow_run_id,
        "message_id": user_message_id,
        "user_id": token_data["user_id"],
        "prompt": request.prompt,
        "db_url": dsn,
        "available_charts": request.available_charts,
        "model_name": request.model_name,
    }

    checkpointer = ConversationCheckpointer(k=settings.CONVERSATION_MEMORY_K)
    workflow = build_workflow(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": conversation_id}}
    workflow_error = False
    try:
        state = await asyncio.to_thread(workflow.invoke, state, config=config)
    except Exception as exc:
        logger.exception("Workflow invocation failed: %s", exc)
        append_error(state, "workflow", str(exc))
        workflow_error = True
    finally:
        run_status = "failed" if workflow_error else "completed"
        run_error = None
        if workflow_error and state.get("error"):
            run_error = "; ".join(err["message"] for err in state["error"])
        await workflow_run_service.complete_run(
            workflow_run_id, status=run_status, error=run_error
        )

    response = state.get("response", {"message": []})
    questions: list[str] = []
    if state.get("needs_clarification") or state.get("clarification_escalated"):
        questions = state.get("clarification_questions", [])

    if questions:
        assistant_contents = [TextContent(content=q).model_dump() for q in questions]
        response_texts = questions
    else:
        if state.get("error") and not response.get("message"):
            messages = [err["message"] for err in state.get("error", [])]
            joined = "; ".join(messages)
            assistant_contents = [
                TextContent(content=joined).model_dump()
            ]
            response_texts = messages
        else:
            assistant_contents = response.get("message", [])
            response_texts = [
                c.get("content") for c in assistant_contents if c.get("type") == "text"
            ]

    await conversation_service.add_message(
        conversation_id,
        "assistant",
        assistant_contents,
    )

    result = QueryResponse(
        status="error" if workflow_error else "ok",
        code=500 if workflow_error else 200,
        data=QueryResponseData(message=assistant_contents),
        error=state.get("error"),
    )

    # Update conversation memory
    new_messages = [
        {"role": "user", "content": {"text": request.prompt}},
        {"role": "assistant", "content": {"text": "\n".join(response_texts)}},
    ]
    summary = state.get("summary", "")
    messages = state.get("messages", [])
    history_update = {"summary": summary, "messages": messages + new_messages}
    checkpointer.save(conversation_id, workflow_run_id, history_update)

    return result


@router.get("/", response_model=list[ConversationListItem])
async def list_conversations(token_data: dict = Depends(verify_token)):
    """Return the conversations belonging to the authenticated user."""
    return await conversation_service.list_conversations(token_data["user_id"])


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str, token_data: dict = Depends(verify_token)
):
    try:
        convo = await conversation_service.get_conversation(
            conversation_id, token_data["user_id"]
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return convo
