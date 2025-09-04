from __future__ import annotations

import asyncio
import json
import os
from typing import Dict, Iterable

from db.database import get_pool
from redis import Redis


def _cache_key(db_connection_id: str, user_id: str) -> str:
    return f"semantic:{db_connection_id}:{user_id}"


_redis = Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
)


async def load_mapping_into_cache(db_connection_id: str, user_id: str) -> None:
    """Fetch mapping from the database and store it in the cache.

    The database table ``semantic_mapping`` stores mappings in a canonical ->
    [synonyms] format. This loader inverts the structure for fast
    synonym-to-canonical lookups.
    """
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
    data = row["mappings"] if row else {}
    inverted: Dict[str, str] = {}
    for canonical, synonyms in data.items():
        terms: Iterable[str]
        if isinstance(synonyms, list):
            terms = [canonical, *synonyms]
        elif synonyms:
            terms = [canonical, synonyms]
        else:
            terms = [canonical]
        for term in terms:
            inverted[term.lower()] = canonical
    _redis.set(_cache_key(db_connection_id, user_id), json.dumps(inverted))


def resolve_term(term: str, db_connection_id: str, user_id: str) -> str:
    """Resolve a natural-language term using cached mappings.

    If the mapping for ``(db_connection_id, user_id)`` or the term itself is
    missing, ``load_mapping_into_cache`` is triggered and the lookup retried.
    If the term is still absent after reloading, a ``KeyError`` is raised so
    callers know the cache is stale or incomplete.
    """
    key = _cache_key(db_connection_id, user_id)
    term_lc = term.lower()
    raw = _redis.get(key)
    mapping = json.loads(raw) if raw else {}
    if not mapping or term_lc not in mapping:
        # Attempt to refresh the cache and retry once
        try:
            asyncio.run(load_mapping_into_cache(db_connection_id, user_id))
        except RuntimeError:
            raise RuntimeError(
                "load_mapping_into_cache must be awaited before calling resolve_term"
            )
        raw = _redis.get(key)
        mapping = json.loads(raw) if raw else {}
    if not mapping or term_lc not in mapping:
        raise KeyError(
            f"Term '{term}' not found in semantic mapping for connection '{db_connection_id}'"
        )
    return mapping[term_lc]
