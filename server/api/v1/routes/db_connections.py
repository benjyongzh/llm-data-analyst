from fastapi import APIRouter, HTTPException, Depends

from schemas import (
    DBConnectionCreateRequest,
    DBConnectionCreateResponse,
    DBConnectionUpdateRequest,
    DBConnectionToggleRequest,
    StatusResponse,
    DBConnectionListItem,
)
from services import db_connection_service
from auth import verify_token

router = APIRouter(prefix="/db-connections")


@router.post("", response_model=DBConnectionCreateResponse)
async def create_db_connection(
    request: DBConnectionCreateRequest,
    token_data: dict = Depends(verify_token),
) -> DBConnectionCreateResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn_id = await db_connection_service.create_db_connection(
        request.user_id, request
    )
    return DBConnectionCreateResponse(db_connection_id=conn_id)


@router.put("/{db_connection_id}", response_model=StatusResponse)
async def update_db_connection(
    db_connection_id: str,
    request: DBConnectionUpdateRequest,
    token_data: dict = Depends(verify_token),
) -> StatusResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        await db_connection_service.update_db_connection(
            request.user_id, db_connection_id, request
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()


@router.post("/{db_connection_id}/disable", response_model=StatusResponse)
async def disable_db_connection(
    db_connection_id: str,
    request: DBConnectionToggleRequest,
    token_data: dict = Depends(verify_token),
) -> StatusResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        await db_connection_service.disable_db_connection(
            request.user_id, db_connection_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()


@router.post("/{db_connection_id}/enable", response_model=StatusResponse)
async def enable_db_connection(
    db_connection_id: str,
    request: DBConnectionToggleRequest,
    token_data: dict = Depends(verify_token),
) -> StatusResponse:
    if token_data["user_id"] != request.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        await db_connection_service.enable_db_connection(
            request.user_id, db_connection_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()


@router.get("", response_model=list[DBConnectionListItem])
async def list_db_connections(
    token_data: dict = Depends(verify_token),
):
    conns = await db_connection_service.list_db_connections(token_data["user_id"])
    return conns
