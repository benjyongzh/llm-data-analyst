import asyncio
import json
import logging
from collections import Counter
from typing import Any, Dict, Optional, Tuple

from ..db.database import get_pool
from ..schemas.db_connection import DBConnection


logger = logging.getLogger(__name__)
_summary_failures: Counter[str] = Counter()


def _estimate_tokens_from_text(text: str) -> int:
    """Rough token estimator based on whitespace splitting."""
    return max(1, len(text.split()))


def _estimate_tokens_from_content(content: Dict[str, Any]) -> int:
    text = content.get("text") if isinstance(content, dict) else None
    if not text:
        text = json.dumps(content)
    return _estimate_tokens_from_text(text)


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


async def get_conversation_db_connection(
    conversation_id: str, user_id: str
) -> DBConnection:
    """Fetch the database connection associated with a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT dc.db_name, dc.db_user, dc.password, dc.host, dc.port,
                   dc.enabled_at, dc.disabled_at
            FROM conversation c
            JOIN db_connection dc ON c.db_connection_id = dc.id
            WHERE c.id = $1 AND c.user_id = $2
            """,
            conversation_id,
            user_id,
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
    if token_count is None:
        token_count = _estimate_tokens_from_content(content)
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
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
            await conn.execute(
                "UPDATE conversation SET updated_at=now() WHERE id=$1",
                conversation_id,
            )
    message_id = str(row["id"])
    if role == "assistant":
        asyncio.create_task(summarize_conversation(conversation_id))
    return message_id


async def summarize_conversation(
    conversation_id: str, token_limit: int = 1000
) -> Optional[Tuple[str, str]]:
    """Summarize conversation messages and upsert into convo_summary.

    The summary concatenates the existing summary (if any) with new messages
    since the last summarized message. The resulting text is truncated to
    ``token_limit`` tokens (approximate) and stored along with the id of the
    latest message it covers.

    Returns:
        Tuple of ``(summary_text, last_message_id)`` if successful, otherwise ``None``.
    """
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            summary_row = await conn.fetchrow(
                """
                SELECT summary, last_message_id
                FROM convo_summary
                WHERE conversation_id = $1
                """,
                conversation_id,
            )
            summary_text = summary_row["summary"] if summary_row else ""
            last_message_id = summary_row["last_message_id"] if summary_row else None
            last_created_at = None
            if last_message_id:
                ts_row = await conn.fetchrow(
                    "SELECT created_at FROM message WHERE id=$1", last_message_id
                )
                last_created_at = ts_row["created_at"] if ts_row else None
            rows = await conn.fetch(
                """
                SELECT id, role, content
                FROM message
                WHERE conversation_id=$1
                  AND ($2::timestamptz IS NULL OR created_at > $2)
                ORDER BY created_at
                """,
                conversation_id,
                last_created_at,
            )
            if not rows:
                return summary_text, last_message_id
            parts = []
            if summary_text:
                parts.append(summary_text)
            for r in rows:
                text = r["content"].get("text") if isinstance(r["content"], dict) else None
                if text:
                    parts.append(f"{r['role']}: {text}")
            combined = "\n".join(parts)
            tokens = _estimate_tokens_from_text(combined)
            while tokens > token_limit and parts:
                parts.pop(0)
                combined = "\n".join(parts)
                tokens = _estimate_tokens_from_text(combined)
            summary_text = combined[-1000:]
            token_count = _estimate_tokens_from_text(summary_text)
            last_message_id = rows[-1]["id"]
            if summary_row:
                await conn.execute(
                    """
                    UPDATE convo_summary
                    SET summary=$1, last_message_id=$2, token_count=$3, updated_at=now()
                    WHERE conversation_id=$4
                    """,
                    summary_text,
                    last_message_id,
                    token_count,
                    conversation_id,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO convo_summary (
                        conversation_id, summary, last_message_id, token_count, updated_at
                    )
                    VALUES ($1, $2, $3, $4, now())
                    """,
                    conversation_id,
                    summary_text,
                    last_message_id,
                    token_count,
                )
            return summary_text, last_message_id
    except Exception as e:
        _summary_failures[conversation_id] += 1
        logger.exception("Failed to summarize conversation %s: %s", conversation_id, e)
        if _summary_failures[conversation_id] >= 3:
            logger.warning(
                "Conversation %s has %d summarization failures",
                conversation_id,
                _summary_failures[conversation_id],
            )
    return None


async def get_context(
    conversation_id: str, user_id: str, token_limit: int = 2000
) -> Dict[str, Any]:
    """Fetch summary and latest messages within a token budget."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        convo = await conn.fetchrow(
            "SELECT 1 FROM conversation WHERE id=$1 AND user_id=$2",
            conversation_id,
            user_id,
        )
        if not convo:
            raise ValueError("Conversation not found")
        summary_row = await conn.fetchrow(
            "SELECT summary, last_message_id, token_count FROM convo_summary WHERE conversation_id = $1",
            conversation_id,
        )
        summary = summary_row["summary"] if summary_row else None
        total_tokens = summary_row["token_count"] if summary_row else 0
        last_message_id = summary_row["last_message_id"] if summary_row else None
        last_created_at = None
        if last_message_id:
            ts_row = await conn.fetchrow(
                "SELECT created_at FROM message WHERE id=$1", last_message_id
            )
            last_created_at = ts_row["created_at"] if ts_row else None
        rows = await conn.fetch(
            """
            SELECT role, content, token_count
            FROM message
            WHERE conversation_id = $1
              AND ($2::timestamptz IS NULL OR created_at > $2)
            ORDER BY created_at DESC
            """,
            conversation_id,
            last_created_at,
        )
        messages = []
        for r in rows:
            tcount = r["token_count"] or _estimate_tokens_from_content(r["content"])
            if total_tokens + tcount > token_limit:
                break
            messages.append({"role": r["role"], "content": r["content"]})
            total_tokens += tcount
        messages.reverse()
    return {"summary": summary, "messages": messages}


async def list_conversations(user_id: str):
    """Return ids and titles for a user's conversations."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title FROM conversation WHERE user_id=$1 ORDER BY created_at DESC",
            user_id,
        )
    return [{"id": str(r["id"]), "title": r["title"]} for r in rows]


async def get_conversation(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """Fetch a conversation with all its messages if owned by the user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        convo = await conn.fetchrow(
            "SELECT id, title FROM conversation WHERE id=$1 AND user_id=$2",
            conversation_id,
            user_id,
        )
        if not convo:
            raise ValueError("Conversation not found")
        rows = await conn.fetch(
            """SELECT id, role, content FROM message
            WHERE conversation_id=$1 ORDER BY created_at""",
            conversation_id,
        )
    return {
        "id": str(convo["id"]),
        "title": convo["title"],
        "messages": [
            {
                "id": str(r["id"]),
                "role": r["role"],
                "content": r["content"],
            }
            for r in rows
        ],
    }
