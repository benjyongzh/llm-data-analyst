import json
from typing import Any, Dict, Optional

from ..db.database import get_pool


async def get_checkpoint(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch checkpoint data for a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT checkpoint FROM conversation_checkpoint WHERE conversation_id=$1",
            conversation_id,
        )
        if row:
            return row["checkpoint"]
        return None


async def upsert_checkpoint(conversation_id: str, checkpoint: Dict[str, Any]) -> None:
    """Insert or update checkpoint data for a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversation_checkpoint (conversation_id, checkpoint, updated_at)
            VALUES ($1, $2, now())
            ON CONFLICT (conversation_id)
            DO UPDATE SET checkpoint=$2, updated_at=now()
            """,
            conversation_id,
            json.dumps(checkpoint),
        )
