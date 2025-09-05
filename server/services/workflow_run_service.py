"""Service helpers for workflow run tracking."""

from typing import Optional

from db.database import get_pool


async def create_run(conversation_id: str, status: str = "running") -> str:
    """Insert a new workflow_run row and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO workflow_run (conversation_id, status)
            VALUES ($1, $2)
            RETURNING id
            """,
            conversation_id,
            status,
        )
        return str(row["id"])


async def complete_run(run_id: str, status: str = "completed", error: Optional[str] = None) -> None:
    """Mark a workflow_run as completed with optional error info."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflow_run
            SET status=$2, completed_at=now(), error=COALESCE($3, error)
            WHERE id=$1
            """,
            run_id,
            status,
            error,
        )


__all__ = ["create_run", "complete_run"]
