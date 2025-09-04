import asyncio
import json
import pathlib
import sys
import types

import pytest

# Stub modules so importing ``mapper`` doesn't pull heavy dependencies
asyncpg_stub = types.SimpleNamespace(PostgresError=Exception)
sys.modules.setdefault("asyncpg", asyncpg_stub)
db_pkg = types.ModuleType("db")
database_mod = types.ModuleType("database")


async def _noop_get_pool():
    raise RuntimeError("DB access not expected in tests")


database_mod.get_pool = _noop_get_pool
db_pkg.database = database_mod
sys.modules.setdefault("db", db_pkg)
sys.modules.setdefault("db.database", database_mod)


class _RedisStub:
    @classmethod
    def from_url(cls, *args, **kwargs):
        return None


sys.modules.setdefault("redis", types.SimpleNamespace(Redis=_RedisStub))

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from semantic import mapper


class _DummyRedis:
    def __init__(self):
        self.store: dict = {}

    def set(self, key: str, value: str) -> None:
        self.store[key] = value

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def clear(self) -> None:
        self.store.clear()


@pytest.fixture(autouse=True)
def stub_redis(monkeypatch):
    client = _DummyRedis()
    monkeypatch.setattr(mapper, "_redis", client)
    yield
    client.clear()


async def _fake_loader(db_connection_id: str, user_id: str, mapping: dict):
    key = f"semantic:{db_connection_id}:{user_id}"
    mapper._redis.set(key, json.dumps(mapping))


def test_resolve_term_reload(monkeypatch):
    async def loader(conn_id, user_id):
        await _fake_loader(conn_id, user_id, {"column": "column"})

    monkeypatch.setattr(mapper, "load_mapping_into_cache", loader)
    assert mapper.resolve_term("column", "db1", "u1") == "column"


def test_resolve_term_missing(monkeypatch):
    async def loader(conn_id, user_id):
        await _fake_loader(conn_id, user_id, {})

    monkeypatch.setattr(mapper, "load_mapping_into_cache", loader)
    with pytest.raises(KeyError):
        mapper.resolve_term("unknown", "db1", "u1")
