from fastapi import APIRouter, HTTPException, Depends
from ....schemas import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationQueryRequest,
    QueryResponse,
    ConversationDetail,
    ConversationListItem,
)
import asyncio

from ....services import conversation_service
from ....workflows.ai_workflow import build_workflow, WorkflowState
from ....auth import verify_token
from ....config import settings

router = APIRouter(prefix="/conversations")


@router.post("", response_model=ConversationCreateResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    token_data: dict = Depends(verify_token),
) -> ConversationCreateResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    conv_id = await conversation_service.create_conversation(
        request.user_id, request.db_connection_id, request.title, request.model
    )
    return ConversationCreateResponse(conversation_id=conv_id)


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
    context = await conversation_service.get_context(
        conversation_id, token_data["user_id"]
    )
    history_parts = []
    if context.get("summary"):
        history_parts.append(context["summary"])
    for msg in context["messages"]:
        text = msg["content"].get("text", "")
        history_parts.append(f"{msg['role']}: {text}")
    history = "\n".join(history_parts)

    await conversation_service.add_message(
        conversation_id, "user", {"text": request.prompt}
    )

    db_url = (
        f"postgresql://{db_conn.user}:{db_conn.password}@"
        f"{db_conn.host}:{db_conn.port}/{db_conn.db_name}"
    )

    workflow = build_workflow()
    state: WorkflowState = {
        "conversation_id": conversation_id,
        "prompt": request.prompt,
        "history": history,
        "db_url": db_url,
    }
    result = await asyncio.to_thread(workflow.invoke, state)

    await conversation_service.add_message(
        conversation_id,
        "assistant",
        {
            "text": result.get("response"),
            "chart_spec": result.get("chart_spec"),
        },
    )

    return QueryResponse(
        response=result.get("response", ""),
        chart_spec=result.get("chart_spec"),
    )


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(token_data: dict = Depends(verify_token)):
    conns = await conversation_service.list_conversations(token_data["user_id"])
    return conns


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
