"""LLM-powered data extraction and chart recommendation utilities."""
import asyncio
import json
from typing import Any, Dict, List

from openai import OpenAI
from langchain.agents import AgentType
from langchain.agents.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

from schemas import DBConnection, LLMResponse
from services.prompt_wrapper import wrap_prompt
from config import get_settings
from services.logging_service import log_llm_output, create_logged_response

settings = get_settings()


def _build_dsn(conn: DBConnection) -> str:
    """Create a PostgreSQL DSN string from connection details."""
    return (
        f"postgresql://{conn.user}:{conn.password}@{conn.host}:{conn.port}/{conn.db_name}"
    )


async def extract_data(
    prompt: str, db_connection: DBConnection, model_name: str
) -> List[Dict[str, Any]]:
    """Use LangChain's SQLAgent to fetch data from the database.

    The agent interprets ``prompt`` and runs whatever SQL queries are needed to
    satisfy the request. The final response is a JSON array where each item is
    an object mapping column names to values.
    """

    def _run() -> List[Dict[str, Any]]:
        dsn = _build_dsn(db_connection)
        db = SQLDatabase.from_uri(dsn)
        llm = ChatOpenAI(model=model_name, api_key=settings.LLM_API_KEY)
        agent = create_sql_agent(
            llm, db, agent_type=AgentType.OPENAI_FUNCTIONS, verbose=False
        )

        base_query = f"{prompt}\nReturn the results as a JSON array of objects."
        # Ensure prompt is wrapped so the agent returns a JSON object
        # matching schemas.LLMResponse, with the array inside `response`.
        query = wrap_prompt(base_query)
        result = agent.invoke({"input": query})
        log_llm_output("extract_data", result)
        data_text = result["output"] if isinstance(result, dict) else result

        # Try to parse wrapped response first, then fall back to legacy parsing.
        payload = None
        try:
            wrapped = LLMResponse.model_validate_json(data_text).response
            # If the `response` itself is a JSON string, decode it.
            if isinstance(wrapped, str):
                payload = json.loads(wrapped)
            else:
                payload = wrapped
        except Exception:
            # Fallback for unwrapped outputs (older agents) that directly
            # returned a JSON array as text.
            payload = json.loads(data_text)

        if not isinstance(payload, list):
            raise ValueError("Expected JSON array from SQL agent")
        return payload

    return await asyncio.to_thread(_run)


async def choose_charts(
    prompt: str,
    available_charts: List[str],
    data: List[Dict[str, Any]],
    model_name: str,

) -> List[str]:
    """Ask the LLM for relevant chart types from ``available_charts``."""

    def _run() -> List[str]:
        client = OpenAI(api_key=settings.LLM_API_KEY)

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "chart_recommendations",
                "schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": available_charts,
                            },
                        }
                    },
                    "required": ["response"],
                },
            },
        }

        message = (
            "Select the most appropriate chart types for the user's request.\n"
            + f"User request: {prompt}\n"
            + f"Available chart types: {available_charts}\n"
            + f"Data: {json.dumps(data)}"
        )

        resp, raw = create_logged_response(
            client,
            step="choose_charts",
            model=model_name,
            input=message,
            response_format=response_format,
        )
        selections = LLMResponse.model_validate_json(raw).response
        return list(selections)

    return await asyncio.to_thread(_run)


async def generate_title(prompt: str, model_name: str | None = None) -> str:
    """Generate a short conversation title from the user's prompt."""

    def _run() -> str:
        client = OpenAI(api_key=settings.LLM_API_KEY)
        model = model_name or settings.LLM_RESPONSE_MODEL
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "conversation_title",
                "schema": {
                    "type": "object",
                    "properties": {"response": {"type": "string"}},
                    "required": ["response"],
                },
            },
        }
        message = (
            "Generate a concise title using between 2 and 7 words for the "
            f"following user message.\nUser message: {prompt}"
        )
        resp, raw = create_logged_response(
            client,
            step="title_generator",
            model=model,
            input=message,
            response_format=response_format,
        )
        title = LLMResponse.model_validate_json(raw).response
        return str(title).strip()

    return await asyncio.to_thread(_run)
