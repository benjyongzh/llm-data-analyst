import os
from fastapi import APIRouter, HTTPException, Depends

from ....schemas import QueryRequest, QueryResponse
from ....services import llm_service
from ....auth import verify_token

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest, token_data: dict = Depends(verify_token)
) -> QueryResponse:
    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    data = llm_service.extract_data(
        request.prompt, request.db_connection, request.model_name
    )
    charts = llm_service.choose_charts(
        request.prompt, request.available_charts, data, request.model_name
    )

    return QueryResponse(charts=charts)
