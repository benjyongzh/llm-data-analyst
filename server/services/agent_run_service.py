"""Service helpers for logging LLM agent executions."""
import json
import logging
from typing import Any, Optional

from db.database import get_pool

logger = logging.getLogger(__name__)


async def log_agent_run_start(
    workflow_run_id: str,
    prompt: str,
    model_name: str,
    workflow_step_id: Optional[str] = None,
) -> str:
    """Insert a new agent_run row and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO agent_run (workflow_run_id, workflow_step_id, model_name, prompt, status)
            VALUES ($1, $2, $3, $4, 'running')
            RETURNING id
            """,
            workflow_run_id,
            workflow_step_id,
            model_name,
            prompt,
        )
        return str(row["id"])


async def log_agent_run_end(
    agent_run_id: str,
    *,
    input_json: Optional[Any] = None,
    output_json: Optional[Any] = None,
    thought: Optional[str] = None,
    log: Optional[Any] = None,
    token_usage: int = 0,
    status: str = "succeeded",
) -> None:
    """Update an agent_run row with completion details."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE agent_run
            SET input=$2,
                output=$3,
                thought=COALESCE($4, thought),
                log=COALESCE($5, log),
                token_usage=$6,
                status=$7,
                completed_at=now()
            WHERE id=$1
            """,
            agent_run_id,
            json.dumps(input_json) if input_json is not None else None,
            json.dumps(output_json) if output_json is not None else None,
            thought,
            json.dumps(log) if log is not None else None,
            token_usage,
            status,
        )


__all__ = ["log_agent_run_start", "log_agent_run_end"]
