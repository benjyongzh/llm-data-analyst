from typing import Optional

import os
import asyncpg

_POOL: Optional[asyncpg.Pool] = None

CREATE_TABLES_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_user (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS db_connection (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES app_user(id),
  db_name VARCHAR(255) NOT NULL,
  db_user VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  host VARCHAR(255) NOT NULL,
  port INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  enabled_at TIMESTAMPTZ DEFAULT now(),
  disabled_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS conversation (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES app_user(id),
  db_connection_id UUID NOT NULL REFERENCES db_connection(id),
  title VARCHAR(255),
  model VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS message (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
  author VARCHAR(255) NOT NULL,
  user_id UUID REFERENCES app_user(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_message_convo_created ON message (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS message_content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES message(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL CHECK (type IN ('text','data')),
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_message_content_msg ON message_content (message_id, id);

-- CREATE TABLE IF NOT EXISTS convo_summary (
--   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   conversation_id UUID NOT NULL UNIQUE REFERENCES conversation(id) ON DELETE CASCADE,
--   summary VARCHAR(1000) NOT NULL,
--   last_message_id UUID NOT NULL REFERENCES message(id),
--   token_count INT,
--   created_at TIMESTAMPTZ DEFAULT now(),
--   updated_at TIMESTAMPTZ DEFAULT now()
-- );

CREATE TABLE IF NOT EXISTS conversation_checkpoint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL UNIQUE REFERENCES conversation(id) ON DELETE CASCADE,
  checkpoint JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
"""


async def get_pool() -> asyncpg.Pool:
    """Create (or reuse) a connection pool and ensure tables exist."""
    global _POOL
    if _POOL is None:
        dsn = os.environ["DATABASE_URL"]
        _POOL = await asyncpg.create_pool(dsn)
        async with _POOL.acquire() as conn:
            await conn.execute(CREATE_TABLES_SQL)
    return _POOL
