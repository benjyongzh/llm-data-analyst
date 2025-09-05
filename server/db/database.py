from typing import Optional

import asyncpg
import logging

from config import get_settings


logger = logging.getLogger(__name__)

_POOL: Optional[asyncpg.Pool] = None

settings = get_settings()

CREATE_TABLES_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  CREATE TYPE run_status AS ENUM ('running','succeeded','failed','cancelled');
EXCEPTION WHEN duplicate_object THEN
  NULL;
END $$;

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

CREATE TABLE IF NOT EXISTS semantic_mapping (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  db_connection_id UUID NOT NULL REFERENCES db_connection(id),
  user_id UUID NOT NULL REFERENCES app_user(id),
  mappings JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
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

CREATE TABLE IF NOT EXISTS workflow_run (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status run_status NOT NULL,
  error VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS workflow_step (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_run_id UUID NOT NULL REFERENCES workflow_run(id) ON DELETE CASCADE,
  state_in JSONB,
  state_out JSONB,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_run (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_run_id UUID NOT NULL REFERENCES workflow_run(id) ON DELETE CASCADE,
  model_name VARCHAR(100),
  workflow_step_id UUID REFERENCES workflow_step(id) ON DELETE CASCADE,
  prompt TEXT,
  input JSONB,
  output JSONB,
  thought TEXT,
  log JSONB,
  status run_status NOT NULL,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  token_usage INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS conversation_checkpoint (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
  workflow_run_id UUID NOT NULL REFERENCES workflow_run(id) ON DELETE CASCADE,
  checkpoint JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_step_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES message(id) ON DELETE CASCADE,
  step_name VARCHAR(255) NOT NULL,
  thought TEXT,
  plan_sql TEXT,
  tokens_in INT DEFAULT 0,
  tokens_out INT DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  status VARCHAR(50) NOT NULL DEFAULT 'started'
);
"""


async def get_pool() -> asyncpg.Pool:
    """Create (or reuse) a connection pool and ensure tables exist."""
    global _POOL
    if _POOL is None:
        try:
            _POOL = await asyncpg.create_pool(settings.DATABASE_URL)
            async with _POOL.acquire() as conn:
                await conn.execute(CREATE_TABLES_SQL)
        except asyncpg.PostgresError:
            logger.exception("Failed to connect to database")
            raise SystemExit("Database connection failed")
    return _POOL
