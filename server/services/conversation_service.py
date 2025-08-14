import json
from typing import Any, Dict, Optional

import json
from typing import Any, Dict, Optional

from ..db.database import get_pool
from ..schemas.db_connection import DBConnection


async def create_conversation(
    user_id: str, db_connection_id: str, title: Optional[str], model: Optional[str]
) -> str:
    """Create a new conversation and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO conversation (user_id, db_connection_id, title, model)
            VALUES ($1, $2, $3, $4) RETURNING id
            """,
            user_id,
            db_connection_id,
            title,
            model,
        )
        return str(row["id"])


async def get_conversation_db_connection(conversation_id: str) -> DBConnection:
    """Fetch the database connection associated with a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT dc.db_name, dc.db_user, dc.password, dc.host, dc.port,
                   dc.enabled_at, dc.disabled_at
            FROM conversation c
            JOIN db_connection dc ON c.db_connection_id = dc.id
            WHERE c.id = $1
            """,
            conversation_id,
        )
        if not row:
            raise ValueError("Conversation not found")
        disabled_at = row["disabled_at"]
        enabled_at = row["enabled_at"]
        if disabled_at and (enabled_at is None or disabled_at >= enabled_at):
            raise ValueError("DB connection disabled")
        return DBConnection(
            db_name=row["db_name"],
            user=row["db_user"],
            password=row["password"],
            host=row["host"],
            port=row["port"],
        )


async def add_message(
    conversation_id: str,
    role: str,
    content: Dict[str, Any],
    token_count: Optional[int] = None,
    parent_id: Optional[str] = None,
) -> str:
    """Persist a message and return its id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO message (conversation_id, role, content, token_count, parent_id)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
            """,
            conversation_id,
            role,
            json.dumps(content),
            token_count,
            parent_id,
        )
        return str(row["id"])


async def get_context(conversation_id: str, limit: int = 20) -> Dict[str, Any]:
    """Fetch summary and the latest messages for a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        summary_row = await conn.fetchrow(
            "SELECT summary FROM convo_summary WHERE conversation_id = $1",
            conversation_id,
        )
        summary = summary_row["summary"] if summary_row else None
        rows = await conn.fetch(
            """
            SELECT role, content FROM message
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            conversation_id,
            limit,
        )
        messages = [
            {"role": r["role"], "content": r["content"]} for r in reversed(rows)
        ]
    return {"summary": summary, "messages": messages}
