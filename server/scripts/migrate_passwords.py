"""Utility to hash existing plain-text passwords in the database.

Usage:
    export DATABASE_URL=postgresql://user:password@host/dbname
    python server/scripts/migrate_passwords.py
"""

import asyncio
import os
import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def migrate() -> None:
    """Hash any plain-text passwords in the app_user table."""
    dsn = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, password FROM app_user WHERE password NOT LIKE '$2b$%'"
        )
        for row in rows:
            hashed = pwd_context.hash(row["password"])
            await conn.execute(
                "UPDATE app_user SET password=$1 WHERE id=$2", hashed, row["id"]
            )
    await pool.close()


if __name__ == "__main__":
    asyncio.run(migrate())
