from __future__ import annotations

from typing import Dict, List

from sqlalchemy import inspect

from db.adapters import get_adapter
from db.database import get_pool
from semantic.mapper import load_mapping_into_cache


async def get_mapping(user_id: str, db_connection_id: str) -> Dict[str, List[str]]:
    """Retrieve the raw canonical -> [synonyms] mapping for a connection."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT mappings FROM semantic_mapping
            WHERE db_connection_id=$1 AND user_id=$2
            """,
            db_connection_id,
            user_id,
        )
    return row["mappings"] if row else {}


async def ensure_mapping(
    user_id: str, db_connection_id: str, db_url: str
) -> None:
    """Ensure a semantic mapping exists and is cached for a connection."""

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1 FROM semantic_mapping
            WHERE db_connection_id=$1 AND user_id=$2
            """,
            db_connection_id,
            user_id,
        )

    if not row:
        adapter = get_adapter(db_url)
        inspector = inspect(adapter.engine)
        mapping: Dict[str, List[str]] = {}
        for table in inspector.get_table_names():
            for col in inspector.get_columns(table):
                name = col["name"]
                humanized = name.replace("_", " ")
                mapping[name] = [name, humanized]
        adapter.close()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO semantic_mapping (db_connection_id, user_id, mappings)
                VALUES ($1, $2, $3)
                """,
                db_connection_id,
                user_id,
                mapping,
            )

    await load_mapping_into_cache(db_connection_id, user_id)
