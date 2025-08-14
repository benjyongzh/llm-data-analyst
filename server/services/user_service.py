from ..db.database import get_pool
from ..schemas.user import UserCreateRequest, UserUpdateRequest


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
            user.password,
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
        values.append(user.password)
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
