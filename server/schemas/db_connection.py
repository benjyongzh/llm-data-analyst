from pydantic import BaseModel


class DBConnection(BaseModel):
    """Connection parameters for the target database."""

    db_name: str
    user: str
    password: str
    host: str = "localhost"
    port: int


class DBConnectionCreateRequest(DBConnection):
    """Payload to register a new database connection."""

    user_id: str


class DBConnectionCreateResponse(BaseModel):
    """Response containing the new connection id."""

    db_connection_id: str


class DBConnectionUpdateRequest(DBConnection):
    """Payload to update an existing database connection."""

    user_id: str


class DBConnectionToggleRequest(BaseModel):
    """Request body for enable/disable operations."""

    user_id: str


class DBConnectionListItem(BaseModel):
    id: str
    db_name: str
    host: str
    port: int
    user: str
    enabled: bool
