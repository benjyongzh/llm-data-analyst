from typing import Any, Dict, List, Optional, Literal

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


class MessageContent(BaseModel):
    """Single message component."""

    type: Literal["text", "data"]
    content: Any


class QueryResponseData(BaseModel):
    message: List[MessageContent]


class QueryResponse(BaseModel):
    """Standardized API response."""

    status: str
    code: int
    data: QueryResponseData
    error: Optional[str] = None


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
    contents: List[MessageContent]


class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    messages: List[MessageItem]
