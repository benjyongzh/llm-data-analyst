from pydantic import BaseModel
from typing import Optional


class UserCreateRequest(BaseModel):
    """Payload to register a new user."""

    name: str
    email: str
    password: str


class UserCreateResponse(BaseModel):
    """Response containing the created user's id."""

    user_id: str


class UserUpdateRequest(BaseModel):
    """Fields available for updating a user."""

    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
