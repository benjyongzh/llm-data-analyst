from fastapi import APIRouter, HTTPException

from ....schemas import (
    DBConnectionCreateRequest,
    DBConnectionCreateResponse,
    DBConnectionUpdateRequest,
    DBConnectionToggleRequest,
    StatusResponse,
)
from ....services import db_connection_service

router = APIRouter(prefix="/db-connections")


@router.post("", response_model=DBConnectionCreateResponse)
async def create_db_connection(
    request: DBConnectionCreateRequest,
) -> DBConnectionCreateResponse:
    conn_id = await db_connection_service.create_db_connection(
        request.user_id, request
    )
    return DBConnectionCreateResponse(db_connection_id=conn_id)


@router.put("/{db_connection_id}", response_model=StatusResponse)
async def update_db_connection(
    db_connection_id: str, request: DBConnectionUpdateRequest
) -> StatusResponse:
    try:
        await db_connection_service.update_db_connection(
            request.user_id, db_connection_id, request
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()


@router.post("/{db_connection_id}/disable", response_model=StatusResponse)
async def disable_db_connection(
    db_connection_id: str, request: DBConnectionToggleRequest
) -> StatusResponse:
    try:
        await db_connection_service.disable_db_connection(
            request.user_id, db_connection_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()


@router.post("/{db_connection_id}/enable", response_model=StatusResponse)
async def enable_db_connection(
    db_connection_id: str, request: DBConnectionToggleRequest
) -> StatusResponse:
    try:
        await db_connection_service.enable_db_connection(
            request.user_id, db_connection_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return StatusResponse()
