from passlib.context import CryptContext

from ..db.database import get_pool
from ..schemas.user import UserCreateRequest, UserUpdateRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str):
    """Verify a user's credentials."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, password FROM app_user
            WHERE name=$1 AND deleted_at IS NULL
            """,
            username,
        )
        if row and _verify_password(password, row["password"]):
            return {"user_id": str(row["id"]), "username": row["name"]}
        return None


async def create_user(user: UserCreateRequest) -> str:
    """Insert a new application user and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO app_user (name, email, password)
            VALUES ($1, $2, $3) RETURNING id
            """,
            user.name,
            user.email,
            _hash_password(user.password),
        )
        return str(row["id"])


async def update_user(user_id: str, user: UserUpdateRequest) -> None:
    """Update fields for an existing user if not soft deleted."""
    fields = []
    values = []
    if user.name is not None:
        values.append(user.name)
        fields.append(f"name=${len(values)}")
    if user.email is not None:
        values.append(user.email)
        fields.append(f"email=${len(values)}")
    if user.password is not None:
        values.append(_hash_password(user.password))
        fields.append(f"password=${len(values)}")
    if not fields:
        return
    values.append(user_id)
    set_clause = ", ".join(fields) + ", updated_at=now()"
    query = f"UPDATE app_user SET {set_clause} WHERE id=${len(values)} AND deleted_at IS NULL"
    pool = await get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute(query, *values)
        if status.split()[-1] == "0":
            raise ValueError("User not found")
