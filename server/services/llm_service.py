"""LLM-powered data extraction and chart recommendation utilities."""
import json
import os
from typing import Any, Dict, List

from openai import OpenAI
from langchain.agents import AgentType
from langchain.agents.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

from ..schemas import DBConnection, ChartData


def _build_dsn(conn: DBConnection) -> str:
    """Create a PostgreSQL DSN string from connection details."""
    return (
        f"postgresql://{conn.user}:{conn.password}@{conn.host}:{conn.port}/{conn.db_name}"
    )


def extract_data(prompt: str, db_connection: DBConnection, model_name: str) -> List[Dict[str, Any]]:
    """Use LangChain's SQLAgent to fetch data from the database.

    The agent interprets ``prompt`` and runs whatever SQL queries are needed to
    satisfy the request. The final response is a JSON array where each item is
    an object mapping column names to values.
    """

    dsn = _build_dsn(db_connection)
    db = SQLDatabase.from_uri(dsn)
    llm = ChatOpenAI(model=model_name, api_key=os.environ["LLM_API_KEY"])
    agent = create_sql_agent(llm, db, agent_type=AgentType.OPENAI_FUNCTIONS, verbose=False)

    query = (
        f"{prompt}\n" "Return the results as a JSON array of objects."
    )
    result = agent.invoke({"input": query})
    data_text = result["output"] if isinstance(result, dict) else result
    payload = json.loads(data_text)
    if not isinstance(payload, list):
        raise ValueError("Expected JSON array from SQL agent")
    return payload


def choose_charts(
    prompt: str, available_charts: List[str], data: List[Dict[str, Any]], model_name: str
) -> List[ChartData]:
    """Ask the LLM to pick chart types and shape data for each chart."""

    client = OpenAI(api_key=os.environ["LLM_API_KEY"])

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "chart_recommendations",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "chart_type": {
                            "type": "string",
                            "enum": available_charts,
                        },
                        "data": {"type": "object"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["chart_type", "data"],
                },
            },
        },
    }

    message = (
        "Choose suitable charts for the user's request and shape the data for each selection.\n"\
        + f"User request: {prompt}\n"\
        + f"Available chart types: {available_charts}\n"\
        + f"Data: {json.dumps(data)}"
    )

    resp = client.responses.create(
        model=model_name,
        input=message,
        response_format=response_format,
    )

    selections = json.loads(resp.output[0].content[0].text)
    charts: List[ChartData] = []
    for item in selections:
        charts.append(
            ChartData(
                chart_type=item["chart_type"],
                data=item["data"],
                reasoning=item.get("reasoning"),
            )
        )
    return charts
