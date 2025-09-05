"""Service helpers for tracking workflow steps."""

import logging

from db.database import get_pool

logger = logging.getLogger(__name__)


async def start_workflow_step(workflow_run_id: str, step_name: str, state_in: dict) -> str:
    """Insert a new workflow_step row and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO workflow_step (workflow_run_id, step_name, status, state_in)
            VALUES ($1, $2, 'running', $3)
            RETURNING id
            """,
            workflow_run_id,
            step_name,
            state_in,
        )
        return str(row["id"])


async def finish_workflow_step(step_id: str, state_out: dict, status: str) -> None:
    """Finalize a workflow_step row with its output state and status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflow_step
            SET state_out=$2, completed_at=now(), status=$3
            WHERE id=$1
            """,
            step_id,
            state_out,
            status,
        )


__all__ = ["start_workflow_step", "finish_workflow_step"]

