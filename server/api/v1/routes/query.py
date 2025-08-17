import os
from fastapi import APIRouter, HTTPException, Depends

from ....schemas import QueryRequest, QueryResponse
from ....auth import verify_token
from ....workflows import build_workflow

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest, token_data: dict = Depends(verify_token)
) -> QueryResponse:
    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    workflow = build_workflow()
    state_input = {
        "prompt": request.prompt,
        "db_url": (
            f"postgresql://{request.db_connection.user}:"
            f"{request.db_connection.password}@"
            f"{request.db_connection.host}:{request.db_connection.port}/"
            f"{request.db_connection.db_name}"
        ),
    }
    try:
        result = workflow.invoke(state_input)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return QueryResponse(chart_spec=result.get("chart_spec"), response=result.get("response"))
