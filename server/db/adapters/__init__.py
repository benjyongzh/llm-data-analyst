from __future__ import annotations

from typing import Any

from .base import DataAdapter
from .sql import SQLAdapter


def get_adapter(db_url: str) -> DataAdapter:
    """Return a data adapter appropriate for the given URL.

    Currently only SQL databases are supported. Other database types can be
    integrated by implementing ``DataAdapter`` and extending this factory.
    """
    # In a full implementation we would inspect the URL scheme to choose the
    # correct adapter. For now, always return the SQL adapter.
    return SQLAdapter(db_url)
