from fastapi import APIRouter, HTTPException

from ....schemas import (
    UserCreateRequest,
    UserCreateResponse,
    UserUpdateRequest,
    StatusResponse,
)
from ....services import user_service

router = APIRouter(prefix="/users")


@router.post("", response_model=UserCreateResponse)
async def create_user(request: UserCreateRequest) -> UserCreateResponse:
    user_id = await user_service.create_user(request)
    return UserCreateResponse(user_id=user_id)


@router.put("/{user_id}", response_model=StatusResponse)
async def update_user(user_id: str, request: UserUpdateRequest) -> StatusResponse:
    try:
        await user_service.update_user(user_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return StatusResponse()
