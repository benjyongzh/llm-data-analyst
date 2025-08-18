from typing import Any, Dict, List, Optional

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


class QueryResponse(BaseModel):
    """Response payload containing chart suggestions and data."""

    charts: List[ChartData]


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
    role: str
    content: Dict[str, Any]


class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    messages: List[MessageItem]
