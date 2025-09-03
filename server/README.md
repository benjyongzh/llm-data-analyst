LLM Data Analyst — Server

Overview
- FastAPI backend for the LLM Data Analyst app.
- Serves REST endpoints for users, DB connections, conversations, step logs, and semantic mappings under `/users`, `/db-connections`, `/conversations`, `/step-logs`, and `/mappings`.

Prerequisites
- Python 3.11+
- uv (https://docs.astral.sh/uv/)

Environment Variables
- Location: place a `.env` file in `server/` (same folder as `main.py`). It is automatically loaded by `pydantic-settings`.
- The server validates these settings at startup and exits with a clear message if any are invalid.
- Required variables and where they are used:
  - `DATABASE_URL`: Postgres connection string used by `db/database.py` (app runtime, migrations, and scripts). The server logs an error and exits if the pool cannot be created.
  - `LLM_API_KEY`: API key used by OpenAI clients in `workflows/steps/*` and `services/llm_service.py`.
  - `JWT_SECRET`: Cookie-signing secret used in `auth.py` for JWT creation/verification.
- Optional variables:
  - `JWT_EXP_SECONDS` (default `86400`): Token lifetime in seconds (`auth.py`).
  - `ENVIRONMENT` (default `development`): Controls cookie flags (`auth.py`).
  - `LLM_RESPONSE_MODEL` (default `gpt-4o-mini`): Model for summaries and some steps.
  - `LOG_LEVEL` (default `INFO`): Logging level configured in `main.py`.
  - `CONVERSATION_MEMORY_K` (default `5`): Rolling memory window in `workflows/checkpointer.py`.

Example `.env`
See `server/.env-example` for a complete, working template. Copy it to `.env` and adjust values:

```
LLM_API_KEY=your-openai-key
JWT_SECRET=change-me
JWT_EXP_SECONDS=86400
ENVIRONMENT=development
LLM_RESPONSE_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
CONVERSATION_MEMORY_K=5
DATABASE_URL=postgresql://localhost/metadata
```

Setup
- From `server/`, create a `.env` file (see `.env-example`) and set at least:
  - `LLM_API_KEY`: your model provider key
  - `JWT_SECRET`: secret for signing JWT cookies
  - `DATABASE_URL`: Postgres DSN for app data store
  - Optional: `LOG_LEVEL` (default `INFO`), `ENVIRONMENT`, `CONVERSATION_MEMORY_K`, `LLM_RESPONSE_MODEL`

Install and Run (recommended)
- In `server/`:
  - `uv run uvicorn main:app --reload --port 8000`

Notes on Imports
- All imports are absolute from the `server/` root (e.g., `from schemas import ...`, `from services import ...`, `from workflows.steps import ...`).
- The app entrypoint is `main:app`, so running from `server/` works with `uvicorn main:app`.
- This avoids errors like “Attempted relative import with no known parent package”.

Config Usage
- Access settings via `from config import get_settings` then `settings = get_settings()`.
- Do not import a `settings` object directly; the factory handles validation and caching.

Startup Validation
- On application startup, the server calls `get_settings()` via FastAPI's lifespan to validate configuration and set logging level.

Development Tips
- CORS is configured to allow `http://localhost:5173` by default. Adjust in `main.py` if your client runs elsewhere.
- Project dependencies are declared in `pyproject.toml`; `uv` will resolve and run without a manual install step.
