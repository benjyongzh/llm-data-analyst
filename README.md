# llm-data-analyst

Full‑stack demo of an LLM‑powered data analysis assistant. The repository contains a
React + Vite front end and a FastAPI backend.

## Features

- User registration and login with JWT stored in HTTP‑only cookies
- Manage and enable/disable database connections
- Create conversations and retrieve full message history
- Toggleable sidebar for switching conversations and configuring connections
- Conversations are summarized after each assistant reply to keep context
  within token limits, and each summary records its last refresh time
- Inline error messages with cleared loading indicators for failed API calls
- Summarization failures are logged and warnings emitted after repeated errors
- Guardrail checks validate generated SQL and responses, detecting PII or
  profanity and halting the workflow on violations
- Intent classification and entity extraction are handled by an LLM instead of keyword heuristics

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

Configuration values are loaded with `pydantic-settings` so you can define them in a `.env` file.

Environment variables:

- `LLM_API_KEY` – API key for the LLM provider
- `JWT_SECRET` – secret used to sign JWTs (`change-me` default)
- `JWT_EXP_SECONDS` – token lifetime in seconds (defaults to one day)
- `ENVIRONMENT` – set to `production` to enable secure cookie settings
- `LLM_RESPONSE_MODEL` – LLM model used for final summaries
- `DATABASE_URL` – connection string for the application's metadata DB
- `LOG_LEVEL` – logging level for the backend (default `INFO`)

## API overview

All routes are served under the `/api/v1` prefix and require a valid
JWT cookie unless noted.

### Users
- `POST /users` – register a new user
- `PUT /users/{id}` – update profile or password
- `POST /users/login` – authenticate and receive the JWT cookie
- `POST /users/logout` – clear authentication cookies

### Database connections
- `GET /db-connections` – list connections for the current user
- `POST /db-connections` – create a new connection
- `PUT /db-connections/{id}` – update a connection
- `POST /db-connections/{id}/enable` – enable a connection
- `POST /db-connections/{id}/disable` – disable a connection

### Conversations
- `GET /conversations` – list conversations for the current user
- `GET /conversations/{id}` – fetch a conversation with its messages
- `POST /conversations` – create a conversation bound to a DB connection
- `POST /conversations/{id}/query` – send a prompt and run the AI workflow. If
  clarification is needed, the response includes `needs_clarification` and a
  list of `clarification_questions`. Otherwise the payload contains the
  workflow's `response` text and a `chart_spec` object for rendering. Simply
  reply with another prompt to answer any clarification questions.

## Backend workflow

Each conversation stores the database connection it should use. When a user
sends a query, the API fetches the associated connection, gathers recent
messages for context, and checks whether more details are needed. If so, it
returns clarification questions before running any SQL. Otherwise it executes
the LangGraph workflow to produce an assistant `response` and `chart_spec`.
The resulting specification is saved as an assistant message. After each
assistant response, the conversation is
summarized and stored so later requests only need the summary plus the most
recent messages.

```mermaid
flowchart LR
    U[User] -->|query| API
    API -->|lookup| DB[(PostgreSQL)]
    API -->|prompt + data| LLM
    LLM -->|analysis| API
    API -->|assistant message| DB
    API -->|response + chart spec| U
```

### Detailed request flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI backend
    participant DB as Conversation DB
    participant LLM as LLM provider

    U->>API: POST /conversations/{id}/query
    API->>DB: Fetch conversation & selected connection
    API->>DB: Load recent messages for context
    API->>LLM: Prompt with messages and schema
    LLM-->>API: SQL + chart plan
    API->>DB: Execute SQL on bound connection
    DB-->>API: Result rows
    API->>LLM: Summarize rows into chart data
    LLM-->>API: Chart spec + summary
    API->>DB: Persist assistant response
    API-->>U: Return response + chart spec
```

1. **Resolve connection** – the API looks up the conversation to find the
   bound database connection and recent messages.
2. **Generate query** – context and schema are sent to the LLM to obtain an
   SQL statement and chart plan.
3. **Execute SQL** – the generated query runs against the conversation’s
   database and returns rows.
4. **Summarize results** – rows are fed back to the LLM to craft a chart
   specification and natural‑language summary, which are saved as an assistant
   message.
5. **Validate outputs** – generated SQL and summaries are checked against
   allowlists and guardrails for PII or profanity.
6. **Respond to user** – the API returns the generated response and chart
   specification to the client.

### AI workflow steps

The assistant adapts its path based on the user's intent. After any
clarification, requests branch into advice or data-driven flows. Intent and
entity recognition are powered by an LLM that extracts metrics, dimensions, and
timeframes from the user's prompt.

```mermaid
flowchart TD
    A[Prompt intake] --> B[Intent understanding]
    B --> C{Needs clarification?}
    C -->|Yes| D[Clarification loop]
    D --> B
    C -->|No| E{Intent type?}
    E -->|Advice| F[Task planning]
    E -->|Data or Combo| G[Task planning + data plan]
    F --> H[Response generation]
    G --> I[Data retrieval]
    I --> J[Visualization spec]
    J --> H
    H --> K[Result validation]
    K --> L[Conversation summary]
    L --> M[Monitoring]
```

Advice-only paths bypass data retrieval and visualization, generating a
direct narrative response from the user's prompt.

During the **Conversation summary** step, the workflow calls the conversation
service to generate and persist a running summary of the dialogue. The returned
text and the id of the last processed message are stored in the database and
made available to downstream nodes via the workflow state.

### Data model

```mermaid
erDiagram
    USER ||--o{ DB_CONNECTION : owns
    USER ||--o{ CONVERSATION : starts
    DB_CONNECTION ||--o{ CONVERSATION : "selected for"
    CONVERSATION ||--o{ MESSAGE : has
    CONVERSATION ||--o{ CONVO_SUMMARY : summarizes

    USER {
        uuid id PK
        string name
        string email
        string password_hash
        timestamp created_at
        timestamp updated_at
    }
    DB_CONNECTION {
        uuid id PK
        uuid user_id FK
        string db_name
        string db_user
        string password
        string host
        int port
        timestamp created_at
        timestamp updated_at
        timestamp enabled_at
        timestamp disabled_at
    }
    CONVERSATION {
        uuid id PK
        uuid user_id FK
        uuid db_connection_id FK
        string title
        string model
        timestamp created_at
        timestamp updated_at
    }
    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        string role
        json content
        int token_count
        timestamp created_at
    }
    CONVO_SUMMARY {
        uuid id PK
        uuid conversation_id FK
        text summary
        uuid last_message_id FK
        int token_count
        timestamp created_at
        timestamp updated_at
    }
```

## Running the frontend

```bash
cd client
npm install
npm run dev
```

The client expects the API at `http://localhost:8000`; override with
`VITE_API_BASE_URL` in a `.env` file if needed.

On first launch, register an account on the login page. After logging in, create a
database connection from the dropdown to start a conversation and run queries.
