from datetime import datetime, timedelta
from typing import Optional, Dict

import jwt
from fastapi import HTTPException, Request

from config import get_settings

settings = get_settings()

JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = settings.JWT_EXP_SECONDS  # 1 day default

# Cookie settings
IS_PRODUCTION = settings.ENVIRONMENT == "production"
COOKIE_SECURE = IS_PRODUCTION
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


def create_access_token(user_id: str, username: str, expires_delta: Optional[int] = None) -> str:
    exp = datetime.utcnow() + timedelta(seconds=expires_delta or JWT_EXP_SECONDS)
    payload = {"user_id": user_id, "username": username, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(request: Request) -> Dict[str, str]:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_csrf(request: Request) -> None:
    """Simple double-submit CSRF protection.

    Expects a matching token in the `csrf_token` cookie and `X-CSRF-Token` header.
    """
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
