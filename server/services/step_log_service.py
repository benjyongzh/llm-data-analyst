"""Service helpers for workflow step logging."""

import logging
from typing import Optional, List

from db.database import get_pool
from schemas import WorkflowStepLog


logger = logging.getLogger(__name__)


async def log_step_start(message_id: str, step_name: str) -> str:
    """Insert a new step log row and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO workflow_step_log (message_id, step_name)
            VALUES ($1, $2)
            RETURNING id
            """,
            message_id,
            step_name,
        )
        return str(row["id"])


async def log_step_end(
    step_log_id: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    status: str = "completed",
    thought: Optional[str] = None,
    plan_sql: Optional[str] = None,
) -> None:
    """Finalize a step log row with token usage and status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflow_step_log
            SET tokens_in=$2, tokens_out=$3, ended_at=now(), status=$4,
                thought=COALESCE($5, thought),
                plan_sql=COALESCE($6, plan_sql)
            WHERE id=$1
            """,
            step_log_id,
            tokens_in,
            tokens_out,
            status,
            thought,
            plan_sql,
        )


async def get_step_logs(message_id: str) -> List[WorkflowStepLog]:
    """Return logs for a message ordered by start time."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, message_id, step_name, thought, plan_sql,
                   tokens_in, tokens_out, started_at, ended_at, status
            FROM workflow_step_log
            WHERE message_id=$1
            ORDER BY started_at
            """,
            message_id,
        )
    return [WorkflowStepLog(**dict(r)) for r in rows]


__all__ = ["log_step_start", "log_step_end", "get_step_logs"]

