from typing import Any, List, Optional
from pydantic import BaseModel


class DBConnection(BaseModel):
    """Connection parameters for the target database."""

    db_name: str
    user: str
    password: str
    host: str = "localhost"
    port: int


class ChartData(BaseModel):
    """Data and metadata for a single chart."""

    chart_type: str
    data: Any
    reasoning: Optional[str] = None


class QueryRequest(BaseModel):
    """Request payload from the client."""

    prompt: str
    db_connection: DBConnection
    available_charts: List[str]
    model_name: str


class QueryResponse(BaseModel):
    """Response payload containing chart suggestions and data."""

    charts: List[ChartData]
