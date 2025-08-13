"""FastAPI application serving the data analyst chatbot."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from .schemas import QueryRequest, QueryResponse
from . import llm_service

app = FastAPI(title="LLM Data Analyst")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Handle a natural language data query from the client.

    The endpoint delegates to the LLM to both extract data from the target
    database and decide which charts to render. The LLM API key is expected in
    the ``LLM_API_KEY`` environment variable.
    """

    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    data = llm_service.extract_data(
        request.prompt, request.db_connection, request.model_name
    )
    charts = llm_service.choose_charts(
        request.prompt, request.available_charts, data, request.model_name
    )

    return QueryResponse(charts=charts)
