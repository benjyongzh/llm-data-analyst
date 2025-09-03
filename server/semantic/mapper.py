from __future__ import annotations

from typing import Dict, Iterable, Tuple

from db.database import get_pool

# In-memory cache keyed by (db_connection_id, user_id)
_MAPPING_CACHE: Dict[Tuple[str, str], Dict[str, str]] = {}


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
    _MAPPING_CACHE[(db_connection_id, user_id)] = inverted


def resolve_term(term: str, db_connection_id: str, user_id: str) -> str:
    """Resolve a natural-language term using the cached mappings.

    This stub intentionally avoids querying the database on cache miss. The
    caller should invoke ``load_mapping_into_cache`` ahead of time to populate
    the cache.
    """
    mapping = _MAPPING_CACHE.get((db_connection_id, user_id), {})
    return mapping.get(term.lower(), term)
