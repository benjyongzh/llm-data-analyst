from ..db.database import get_pool
from ..schemas.db_connection import DBConnection


async def create_db_connection(user_id: str, conn_info: DBConnection) -> str:
    """Persist a database connection configuration and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO db_connection (user_id, db_name, db_user, password, host, port)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """,
            user_id,
            conn_info.db_name,
            conn_info.user,
            conn_info.password,
            conn_info.host,
            conn_info.port,
        )
        return str(row["id"])


async def update_db_connection(
    user_id: str, db_connection_id: str, conn_info: DBConnection
) -> None:
    """Update a database connection if owned by the user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute(
            """
            UPDATE db_connection
            SET db_name=$3, db_user=$4, password=$5, host=$6, port=$7,
                updated_at=now()
            WHERE id=$1 AND user_id=$2
            """,
            db_connection_id,
            user_id,
            conn_info.db_name,
            conn_info.user,
            conn_info.password,
            conn_info.host,
            conn_info.port,
        )
        if status.split()[-1] == "0":
            raise ValueError("DB connection not found or unauthorized")


async def disable_db_connection(user_id: str, db_connection_id: str) -> None:
    """Mark a database connection as disabled."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute(
            """
            UPDATE db_connection
            SET disabled_at=now(), updated_at=now()
            WHERE id=$1 AND user_id=$2
            """,
            db_connection_id,
            user_id,
        )
        if status.split()[-1] == "0":
            raise ValueError("DB connection not found or unauthorized")


async def enable_db_connection(user_id: str, db_connection_id: str) -> None:
    """Re-enable a previously disabled database connection."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute(
            """
            UPDATE db_connection
            SET enabled_at=now(), updated_at=now()
            WHERE id=$1 AND user_id=$2
            """,
            db_connection_id,
            user_id,
        )
        if status.split()[-1] == "0":
            raise ValueError("DB connection not found or unauthorized")


async def get_db_connection(db_connection_id: str) -> DBConnection:
    """Retrieve connection info by id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT db_name, db_user, password, host, port
            FROM db_connection WHERE id = $1
            """,
            db_connection_id,
        )
        if not row:
            raise ValueError("DB connection not found")
        return DBConnection(
            db_name=row["db_name"],
            user=row["db_user"],
            password=row["password"],
            host=row["host"],
            port=row["port"],
        )
