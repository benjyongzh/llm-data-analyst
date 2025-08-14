# llm-data-analyst

Monorepo containing a React client and a FastAPI backend for an LLM-powered data analysis chatbot.

## Structure

- `client/` – React front-end (empty placeholder).
- `server/` – FastAPI application exposing the chatbot API.
  - `api/` – route declarations grouped by resource.
  - `schemas/` – Pydantic models for requests and responses.
  - `services/` – business logic and database access helpers.
  - `main.py` – creates the FastAPI app and wires the routes.

## Running the backend

The backend uses [uv](https://docs.astral.sh/uv/) for dependency management. Install
dependencies and start the server with:

```bash
cd server
uv sync
uv run uvicorn server.main:app --reload
```

Set the `LLM_API_KEY` environment variable before starting the server. The backend uses
LangChain's SQLAgent to translate natural language prompts into SQL queries and select
appropriate charts via the OpenAI API.

### API

The backend exposes the following REST endpoints:

#### Users
- `POST /users` – create a new user.
- `PUT /users/{user_id}` – update an existing user.

#### Database connections
- `POST /db-connections` – register a database connection for a user.
- `PUT /db-connections/{db_connection_id}` – update connection settings.
- `POST /db-connections/{db_connection_id}/disable` – disable a connection.
- `POST /db-connections/{db_connection_id}/enable` – re-enable a connection.

#### Conversations
- `POST /conversations` – start a new conversation tied to a database connection.
- `POST /conversations/{conversation_id}/query` – send a prompt in the context of a conversation.

#### Ad-hoc query
The `POST /query` endpoint processes a one-off prompt without conversation state and expects a JSON payload:

```json
{
  "prompt": "total sales by month",
  "model_name": "gpt-4.1-mini",
  "db_connection": {
    "db_name": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
  },
  "available_charts": ["bar", "line", "pie"]
}
```

`extract_data` returns a raw JSON array of objects from the database. `choose_charts` uses
the natural-language request, the available chart types and that JSON data to select chart
types and shape the data for each chart in the response.
