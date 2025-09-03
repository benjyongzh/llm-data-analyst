from __future__ import annotations

from typing import Dict, List

from db.database import get_pool


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
