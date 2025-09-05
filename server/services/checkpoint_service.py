import json
from typing import Any, Dict, Optional

from db.database import get_pool


async def get_latest_checkpoint(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the most recent checkpoint for a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT checkpoint
            FROM conversation_checkpoint
            WHERE conversation_id=$1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            conversation_id,
        )
        if row:
            return row["checkpoint"]
        return None


async def create_checkpoint(
    conversation_id: str, workflow_run_id: str, checkpoint: Dict[str, Any]
) -> None:
    """Insert checkpoint data for a conversation and workflow run."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversation_checkpoint (
                conversation_id, workflow_run_id, checkpoint
            )
            VALUES ($1, $2, $3)
            """,
            conversation_id,
            workflow_run_id,
            json.dumps(checkpoint),
        )
