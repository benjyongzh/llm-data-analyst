from typing import Any, Dict, List, Optional, Literal, Union

from pydantic import BaseModel



class ChartData(BaseModel):
    """Data and metadata for a single chart."""

    chart_type: str
    data: Any
    reasoning: Optional[str] = None


class ConversationQueryRequest(BaseModel):
    """Request body for a query tied to an existing conversation."""

    prompt: str
    available_charts: List[str]
    model_name: str


class XAxisSpec(BaseModel):
    """Metadata for the X axis of a chart."""

    label: str
    dataType: Literal["category", "date", "numeric"]
    values: List[Union[str, int, float]]
    unit: Optional[str] = None


class YAxisSpec(BaseModel):
    """Metadata for a Y axis series."""

    label: str
    values: List[float]
    unit: Optional[str] = None


class ChartSpecification(BaseModel):
    """Schema describing chartable data."""

    title: str
    xAxis: XAxisSpec
    yAxis: List[YAxisSpec]
    chartTypes: List[str]


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    content: str


class DataContent(BaseModel):
    type: Literal["data"] = "data"
    content: ChartSpecification


MessageContent = Union[TextContent, DataContent]


class QueryResponseData(BaseModel):
    message: List[MessageContent]


class QueryResponse(BaseModel):
    """Standardized API response."""

    status: str
    code: int
    data: QueryResponseData
    error: Optional[List[Dict[str, str]]] = None


class ConversationCreateRequest(BaseModel):
    """Request body to start a new conversation."""

    user_id: str
    db_connection_id: str
    title: Optional[str] = None
    model: Optional[str] = None


class ConversationCreateResponse(BaseModel):
    """Response containing the new conversation id."""

    conversation_id: str


class ConversationListItem(BaseModel):
    id: str
    title: Optional[str] = None


class MessageItem(BaseModel):
    id: str
    author: str
    user_id: Optional[str] = None
    contents: List[MessageContent]


class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    messages: List[MessageItem]
