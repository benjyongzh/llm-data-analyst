import os
from fastapi import APIRouter, HTTPException

from ....schemas import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationQueryRequest,
    QueryResponse,
)
from ....services import conversation_service, llm_service

router = APIRouter(prefix="/conversations")


@router.post("", response_model=ConversationCreateResponse)
async def create_conversation(
    request: ConversationCreateRequest,
) -> ConversationCreateResponse:
    conv_id = await conversation_service.create_conversation(
        request.user_id, request.db_connection_id, request.title, request.model
    )
    return ConversationCreateResponse(conversation_id=conv_id)


@router.post("/{conversation_id}/query", response_model=QueryResponse)
async def conversation_query(
    conversation_id: str, request: ConversationQueryRequest
) -> QueryResponse:
    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")
    try:
        db_conn = await conversation_service.get_conversation_db_connection(
            conversation_id
        )
    except ValueError as exc:
        detail = str(exc)
        status = 400 if detail == "DB connection disabled" else 404
        raise HTTPException(status_code=status, detail=detail)
    context = await conversation_service.get_context(conversation_id)
    history_parts = []
    if context.get("summary"):
        history_parts.append(context["summary"])
    for msg in context["messages"]:
        text = msg["content"].get("text", "")
        history_parts.append(f"{msg['role']}: {text}")
    history_parts.append(f"user: {request.prompt}")
    full_prompt = "\n".join(history_parts)

    await conversation_service.add_message(
        conversation_id, "user", {"text": request.prompt}
    )

    data = llm_service.extract_data(
        full_prompt, db_conn, request.model_name
    )
    charts = llm_service.choose_charts(
        full_prompt, request.available_charts, data, request.model_name
    )

    await conversation_service.add_message(
        conversation_id,
        "assistant",
        {"charts": [chart.model_dump() for chart in charts]},
    )

    return QueryResponse(charts=charts)
