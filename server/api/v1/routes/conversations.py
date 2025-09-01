import asyncio

from fastapi import APIRouter, HTTPException, Depends
from schemas import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationQueryRequest,
    QueryResponse,
    QueryResponseData,
    ConversationDetail,
    ConversationListItem,
    TextContent,
)
from services import conversation_service
from workflows import build_workflow
from workflows.checkpointer import ConversationCheckpointer
from workflows.ai_workflow import WorkflowState
from auth import verify_token
from config import settings

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
    state: WorkflowState = {
        "conversation_id": conversation_id,
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
    state = await asyncio.to_thread(workflow.invoke, state, config=config)

    response = state.get("response", {"message": []})
    questions: list[str] = []
    if state.get("needs_clarification") or state.get("clarification_escalated"):
        questions = state.get("clarification_questions", [])

    if questions:
        assistant_contents = [TextContent(content=q).model_dump() for q in questions]
        response_texts = questions
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
        status="ok",
        code=200,
        data=QueryResponseData(message=assistant_contents),
    )

    # Update conversation memory
    new_messages = [
        {"role": "user", "content": {"text": request.prompt}},
        {"role": "assistant", "content": {"text": "\n".join(response_texts)}},
    ]
    summary = state.get("summary", "")
    messages = state.get("messages", [])
    history_update = {"summary": summary, "messages": messages + new_messages}
    checkpointer.save(conversation_id, history_update)

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
