from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple


class DataAdapter(Protocol):
    """Protocol for database adapters returning canonical query results."""

    def fetch_data(
        self, table: str, dims: List[str], metrics: List[str], filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Fetch data given canonical entities and return rows plus raw query."""
        ...

    def close(self) -> None:
        """Release any open resources held by the adapter."""
        ...
