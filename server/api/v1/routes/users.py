import secrets

from fastapi import APIRouter, HTTPException, Depends, Response

from schemas import (
    UserCreateRequest,
    UserCreateResponse,
    UserUpdateRequest,
    StatusResponse,
    LoginRequest,
    LoginResponse,
)
from services import user_service
from auth import (
    create_access_token,
    verify_token,
    verify_csrf,
    JWT_EXP_SECONDS,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
)

router = APIRouter(prefix="/users")


@router.post("", response_model=UserCreateResponse)
async def create_user(request: UserCreateRequest) -> UserCreateResponse:
    user_id = await user_service.create_user(request)
    return UserCreateResponse(user_id=user_id)


@router.put("/{user_id}", response_model=StatusResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    token_data: dict = Depends(verify_token),
    _: None = Depends(verify_csrf),
) -> StatusResponse:
    if token_data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        await user_service.update_user(user_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return StatusResponse()


@router.post("/login", response_model=LoginResponse)
async def login(response: Response, request: LoginRequest) -> LoginResponse:
    user = await user_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["user_id"], user["username"])
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_EXP_SECONDS,
    )
    # Issue a CSRF token for double-submit protection. Routes that mutate state
    # should depend on `verify_csrf` to validate it.
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_EXP_SECONDS,
    )
    return LoginResponse(user_id=user["user_id"], username=user["username"])


@router.post("/logout", response_model=StatusResponse)
async def logout(response: Response) -> StatusResponse:
    """Clear authentication and CSRF cookies."""
    response.set_cookie(
        "access_token",
        "",
        max_age=0,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    response.set_cookie(
        "csrf_token",
        "",
        max_age=0,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    return StatusResponse()
