# llm-data-analyst

Monorepo containing a React client and a FastAPI backend for an LLM-powered data analysis chatbot.

## Structure

- `client/` – React front-end (empty placeholder).
- `server/` – FastAPI application exposing the chatbot API.

## Running the backend

```bash
uvicorn server.main:app --reload
```

Set the `LLM_API_KEY` environment variable before starting the server. The backend uses
LangChain's SQLAgent to translate natural language prompts into SQL queries and select
appropriate charts via the OpenAI API.

### API

The `/query` endpoint expects a JSON payload:

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
