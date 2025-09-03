from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlalchemy import MetaData, Table, create_engine, func, inspect, select

from .base import DataAdapter


class SQLAdapter(DataAdapter):
    """Adapter for SQL databases using SQLAlchemy reflection."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def fetch_data(
        self, table: str, dims: List[str], metrics: List[str], filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], str]:
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        if table not in tables:
            raise ValueError(f"Table '{table}' not found")

        metadata = MetaData()
        table_obj = Table(table, metadata, autoload_with=self.engine)

        if metrics:
            group_cols = [table_obj.c[d] for d in dims if d in table_obj.c]
            agg_cols = [
                func.sum(table_obj.c[m]).label(m) for m in metrics if m in table_obj.c
            ]
            stmt = select(*group_cols, *agg_cols)
            if group_cols:
                stmt = stmt.group_by(*group_cols)
        else:
            cols = [table_obj.c[c] for c in dims if c in table_obj.c]
            if not cols:
                cols = list(table_obj.c)
            stmt = select(*cols)

        for col, val in filters.items():
            if col in table_obj.c:
                stmt = stmt.where(table_obj.c[col] == val)

        stmt = stmt.limit(100)
        sql = str(stmt)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = [dict(row._mapping) for row in result]
        return rows, sql

    def close(self) -> None:
        self.engine.dispose()
