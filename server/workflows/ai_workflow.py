"""LangGraph-based AI workflow for the data analyst chatbot.

Each step of the analytics pipeline is implemented as a LangGraph node. The
workflow is deterministic and logs progress at every node for easier debugging.

The workflow makes a best effort to support any SQL database using SQLAlchemy
reflection. Default assumptions are applied when the user does not provide
contextual details:

* Timeframe – last 12 months
* Timezone – Asia/Singapore
* Currency – echo if mixed; otherwise assume a single currency
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI

from ..config import settings
# from ..services import conversation_service
from ..services import step_log_service
from ..schemas.conversation import DataContent, TextContent, ChartSpecification
from sqlalchemy import MetaData, Table, create_engine, func, inspect, select


logger = logging.getLogger(__name__)


def track_step(step_name: str):
    """Decorator to log step execution start and end."""

    def decorator(func):
        def wrapper(state: WorkflowState, *args, **kwargs):
            msg_id = state.get("message_id")
            log_id = None
            # Clear token leftovers from previous steps
            for key in ("tokens_in", "tokens_out"):
                state.pop(key, None)
            thoughts = state.setdefault("thought", [])
            start_len = len(thoughts)

            if msg_id:
                try:
                    log_id = asyncio.run(
                        step_log_service.log_step_start(msg_id, step_name)
                    )
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                    log_id = loop.run_until_complete(
                        step_log_service.log_step_start(msg_id, step_name)
                    )

            exc: Exception | None = None
            try:
                result = func(state, *args, **kwargs)
            except Exception as e:  # pragma: no cover - defensive
                result = state
                state["error"] = str(e)
                exc = e
            finally:
                tokens_in = state.pop("tokens_in", 0)
                tokens_out = state.pop("tokens_out", 0)
                thoughts = state.get("thought", [])
                thought = None
                if len(thoughts) > start_len:
                    thought = thoughts[-1].get("thought")
                status = "error" if exc or state.get("error") else "success"
                if msg_id and log_id:
                    try:
                        asyncio.run(
                            step_log_service.log_step_end(
                                log_id,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                status=status,
                                thought=thought,
                                plan_sql=None,
                            )
                        )
                    except RuntimeError:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(
                            step_log_service.log_step_end(
                                log_id,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                status=status,
                                thought=thought,
                                plan_sql=None,
                            )
                        )
            if exc:
                raise exc
            return result

        return wrapper

    return decorator


class WorkflowState(TypedDict, total=False):
    """Shared state passed between workflow nodes."""

    conversation_id: str
    message_id: str
    user_id: str
    prompt: str
    history: str
    intent: str
    entities: Dict[str, Any]
    needs_clarification: bool
    clarification_questions: List[str]
    clarification_answers: Dict[str, Any]
    clarification_attempts: int
    clarification_limit: int
    clarification_escalated: bool
    plan: Dict[str, Any]
    db_url: str
    error: str
    response: str
    summary: str
    messages: List[Dict[str, Any]]
    timeframe: str
    timezone: str
    currency: str
    available_charts: List[str]
    model_name: str
    thought: List[Dict[str, str]]
    tokens_in: int
    tokens_out: int
    tasks: List[Dict[str, Any]]
    current_task_index: int


@track_step("prompt_intake")
def prompt_intake(state: WorkflowState, checkpointer=None) -> WorkflowState:
    """Receive the user prompt and load conversation history."""
    logger.info("Step 1: Prompt intake for conversation %s", state.get("conversation_id"))
    conv_id = state.get("conversation_id")
    if conv_id and checkpointer:
        history = checkpointer.load(conv_id)
        summary = history.get("summary", "")
        messages = history.get("messages", [])
        history_parts: List[str] = []
        if summary:
            history_parts.append(summary)
        for msg in messages:
            text = msg.get("content", {}).get("text")
            if text:
                history_parts.append(f"{msg['role']}: {text}")
        if history_parts:
            state["history"] = "\n".join(history_parts)
        state["summary"] = summary
        state["messages"] = messages
    state.setdefault("history", "")
    state.setdefault("thought", []).append(
        {"step": "prompt_intake", "thought": "Loaded conversation context"}
    )
    return state


@track_step("intent_understanding")
def intent_understanding(state: WorkflowState) -> WorkflowState:
    """Classify intent, extract entities, and apply default assumptions."""
    logger.info("Step 2: Intent & query understanding")

    prompt = state.get("prompt", "")
    history = state.get("history", "")
    client = OpenAI(api_key=settings.LLM_API_KEY)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "intent_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "entities": {
                        "type": "object",
                        "properties": {
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "dimensions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "timeframe": {"type": "string"},
                        },
                    },
                    "clarification_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["intent", "entities", "clarification_questions"],
            },
        },
    }
    message = (
        "Summarize the user's intent in a single sentence capturing all requested actions or questions. "
        "Extract any metrics, dimensions, and timeframe mentioned. If the request is ambiguous or "
        "missing details you need to fulfill it, ask clarifying questions. "
        "Otherwise return an empty list of questions.\n"
        f"Conversation so far:\n{history}\nUser request: {prompt}"
    )
    raw_text = ""
    try:
        resp = client.responses.create(
            model=settings.LLM_RESPONSE_MODEL,
            input=message,
            response_format=response_format,
        )
        if getattr(resp, "usage", None):
            state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
            state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
        raw_text = resp.output[0].content[0].text
        parsed = json.loads(raw_text)
    except Exception as exc:  # pragma: no cover - LLM failure fallback
        logger.exception("Failed to parse intent response: %s", exc)
        parsed = {"intent": "analysis", "entities": {}}

    entities = state.get("entities", {})
    entities.setdefault("timezone", "Asia/Singapore")
    entities.setdefault("currency", "single assumed currency")
    entities.update(parsed.get("entities", {}))
    if "timeframe" not in entities:
        entities["timeframe"] = "last 12 months"

    intent = parsed.get("intent", "")
    questions: List[str] = parsed.get("clarification_questions", [])

    state["entities"] = entities
    state["intent"] = intent
    state["needs_clarification"] = bool(questions)
    state["clarification_questions"] = questions
    state.setdefault("thought", []).append(
        {"step": "intent_understanding", "thought": raw_text}
    )
    return state


@track_step("clarification")
def clarification(state: WorkflowState) -> WorkflowState:
    """Ask clarifying questions and merge user responses."""
    logger.info("Step 3: Clarification loop")
    if state.get("needs_clarification"):
        state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
        questions = state.get("clarification_questions", [])
        answers = state.get("clarification_answers")
        if answers:
            logger.debug("Received clarification answers: %s", answers)
            entities = state.get("entities", {})
            entities.update(answers)
            state["entities"] = entities
            # Re-evaluate intent with the new information
            state = intent_understanding(state)
        else:
            logger.debug("Clarification needed. Questions: %s", questions)
        limit = state.get("clarification_limit", 3)
        if state.get("needs_clarification") and state["clarification_attempts"] >= limit:
            logger.warning(
                "Maximum clarification attempts (%d) reached; escalating", limit
            )
            state["clarification_escalated"] = True
            state["needs_clarification"] = False
    state.setdefault("thought", []).append(
        {"step": "clarification", "thought": "Clarified user inputs"}
    )
    return state


@track_step("task_planning")
def task_planning(state: WorkflowState) -> WorkflowState:
    """Plan required actions and select tools for each step."""
    logger.info("Step 4: Task planning & tool selection")
    prompt = state.get("prompt", "")
    intent = state.get("intent", "analysis")
    client = OpenAI(api_key=settings.LLM_API_KEY)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "task_plan",
            "schema": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "requires_data": {"type": "boolean"},
                            },
                            "required": ["description", "requires_data"],
                        },
                    }
                },
                "required": ["tasks"],
            },
        },
    }
    inp = (
        "Break down the user's request into a linear sequence of tasks. "
        "For each task, state whether database data is required.\n"
        f"Intent: {intent}\nPrompt: {prompt}"
    )
    resp = client.responses.create(
        model=settings.LLM_RESPONSE_MODEL,
        input=inp,
        response_format=response_format,
    )
    if getattr(resp, "usage", None):
        state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
        state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
    try:
        data = json.loads(resp.output[0].content[0].text)
        planned = data.get("tasks", [])
    except Exception:
        planned = []
    tasks: List[Dict[str, Any]] = []
    for t in planned:
        tasks.append(
            {
                "description": t.get("description", ""),
                "requires_data": t.get("requires_data", False),
                "result": None,
                "token_in": 0,
                "token_out": 0,
                "sql": None,
                "error": "",
            }
        )
    state["tasks"] = tasks
    use_db = any(t.get("requires_data") for t in tasks)
    state["plan"] = {"use_db": use_db, "visualization": use_db}
    state.setdefault("thought", []).append(
        {"step": "task_planning", "thought": "Created task plan"}
    )
    return state


@track_step("task_execution")
def task_execution(state: WorkflowState) -> WorkflowState:
    """Execute planned tasks sequentially, using data or text tools."""
    logger.info("Step 5: Task execution")
    tasks = state.get("tasks", [])
    tokens_in = tokens_out = 0
    for idx, task in enumerate(tasks):
        state["current_task_index"] = idx
        state.pop("error", None)
        if task.get("requires_data"):
            state = data_retrieval(state)
        else:
            state = text_generation(state)
        tokens_in += task.get("token_in", 0)
        tokens_out += task.get("token_out", 0)
        if state.get("error") or task.get("error"):
            break
    state["tokens_in"] = tokens_in
    state["tokens_out"] = tokens_out
    state.setdefault("thought", []).append(
        {"step": "task_execution", "thought": "Executed task plan"}
    )
    return state


@track_step("data_retrieval")
def data_retrieval(state: WorkflowState) -> WorkflowState:
    """Retrieve and process data using SQLAlchemy reflection."""
    logger.info("Step 5: Data retrieval & processing")
    db_url = state.get("db_url")
    entities = state.get("entities", {})
    idx = state.get("current_task_index")
    tasks = state.get("tasks", [])
    task = tasks[idx] if isinstance(idx, int) and idx < len(tasks) else None

    if not db_url:
        logger.warning("No database URL provided; skipping data retrieval")
        state["error"] = "No database URL provided."
        if task is not None:
            task["error"] = state["error"]
        return state

    engine = None
    sql = ""
    try:
        engine = create_engine(db_url)
    except Exception as exc:  # pragma: no cover - depends on SQLAlchemy internals
        logger.exception("Invalid database URL: %s", exc)
        state["error"] = "Invalid database URL."
        if task is not None:
            task["error"] = state["error"]
        return state

    try:
        inspector = inspect(engine)
        table_name = entities.get("table") or entities.get("table_name")
        if not table_name:
            logger.error("No table specified in entities")
            state["error"] = "No table specified."
            if task is not None:
                task["error"] = state["error"]
            return state

        tables = inspector.get_table_names()
        logger.debug("Reflected tables: %s", tables)
        if table_name not in tables:
            logger.error("Table %s not found", table_name)
            state["error"] = f"Table '{table_name}' not found."
            if task is not None:
                task["error"] = state["error"]
            return state

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        dims: List[str] = entities.get("dimensions", []) or []
        metrics: List[str] = (
            entities.get("metrics", []) or entities.get("measures", []) or []
        )
        filters: Dict[str, Any] = entities.get("filters", {}) or {}

        if metrics:
            group_cols = [table.c[d] for d in dims if d in table.c]
            agg_cols = [
                func.sum(table.c[m]).label(m)
                for m in metrics
                if m in table.c
            ]
            stmt = select(*group_cols, *agg_cols)
            if group_cols:
                stmt = stmt.group_by(*group_cols)
        else:
            cols = [table.c[c] for c in dims if c in table.c]
            if not cols:
                cols = list(table.c)
            stmt = select(*cols)

        for col, val in filters.items():
            if col in table.c:
                stmt = stmt.where(table.c[col] == val)

        stmt = stmt.limit(100)
        try:
            sql = str(stmt)
        except Exception:  # pragma: no cover - defensive
            sql = ""

        with engine.connect() as conn:
            result = conn.execute(stmt)
            state["_data"] = [dict(row._mapping) for row in result]

        state = visualization_spec(state)
        chart_spec = state.get("_chart_spec", {})
        if task is not None:
            task["sql"] = sql
            task["result"] = DataContent(
                content=ChartSpecification(**chart_spec)
            ).model_dump()
    except Exception as exc:
        logger.exception("Data retrieval failed: %s", exc)
        state["error"] = str(exc)
        if task is not None:
            task["error"] = state["error"]
    finally:
        if engine:
            engine.dispose()
    success = not state.get("error")
    thought = "Retrieved data successfully" if success else "Data retrieval failed"
    state.setdefault("thought", []).append(
        {"step": "data_retrieval", "thought": thought}
    )
    return state


@track_step("text_generation")
def text_generation(state: WorkflowState) -> WorkflowState:
    """Generate a text answer for a task that doesn't require data."""
    logger.info("Text generation sub-step")
    idx = state.get("current_task_index")
    tasks = state.get("tasks", [])
    task = tasks[idx] if isinstance(idx, int) and idx < len(tasks) else None
    if task is None:
        state["error"] = "Invalid task index"
        return state

    client = OpenAI(api_key=settings.LLM_API_KEY)
    prompt = (
        f"Task: {task.get('description', '')}\n" "Provide the best possible answer."
    )
    resp = client.responses.create(
        model=settings.LLM_RESPONSE_MODEL,
        input=prompt,
    )
    ti = getattr(resp.usage, "input_tokens", 0) if getattr(resp, "usage", None) else 0
    to = getattr(resp.usage, "output_tokens", 0) if getattr(resp, "usage", None) else 0
    state["tokens_in"] = ti
    state["tokens_out"] = to
    task["token_in"] = ti
    task["token_out"] = to
    task["result"] = TextContent(
        content=resp.output[0].content[0].text.strip()
    ).model_dump()
    state.setdefault("thought", []).append(
        {"step": "text_generation", "thought": "Generated text"}
    )
    return state


@track_step("visualization_spec")
def visualization_spec(state: WorkflowState) -> WorkflowState:
    """Determine chart type and build a rich chart specification."""
    logger.info("Step 6: Visualization spec & data packaging")

    data: List[Dict[str, Any]] = state.pop("_data", [])
    entities = state.get("entities", {})

    # Infer dimensions and measures from entities or data sample
    dims: List[str] = entities.get("dimensions", []) or []
    measures: List[str] = entities.get("metrics", []) or entities.get("measures", []) or []

    if data:
        sample = data[0]
        if not dims:
            dims = [k for k, v in sample.items() if not isinstance(v, (int, float))]
        if not measures:
            measures = [k for k, v in sample.items() if isinstance(v, (int, float))]

    # Determine chart type based on dimensions, measures, and intent
    time_like = [d for d in dims if any(t in d.lower() for t in ["date", "time", "year", "month", "day"])]
    if time_like:
        chart_type = "line"
    elif len(measures) > 1:
        chart_type = "bar"
    else:
        chart_type = "bar"

    # Build new chart specification schema
    x_label = dims[0] if dims else ""
    title_parts: List[str] = []
    if measures:
        title_parts.append(", ".join(measures))
    if dims:
        title_parts.append("by " + ", ".join(dims))
    title = " ".join(title_parts) if title_parts else "Chart"

    x_values = [row.get(x_label) for row in data] if x_label else []
    data_type = "category"
    if x_values:
        first = x_values[0]
        if isinstance(first, (int, float)):
            data_type = "numeric"
        elif isinstance(first, str) and re.match(r"\d{4}-\d{2}-\d{2}", first):
            data_type = "date"

    y_axes: List[Dict[str, Any]] = []
    for m in measures:
        values = [float(row.get(m, 0)) for row in data]
        y_axes.append({"label": m, "values": values})

    chart_spec = {
        "title": title,
        "xAxis": {
            "label": x_label,
            "dataType": data_type,
            "values": x_values,
        },
        "yAxis": y_axes,
        "chartTypes": [chart_type],
    }

    state["_chart_spec"] = chart_spec
    state.setdefault("thought", []).append(
        {"step": "visualization_spec", "thought": "Created visualization spec"}
    )
    return state


@track_step("response_generation")
def response_generation(state: WorkflowState) -> WorkflowState:
    """Compose a narrative summary and attach chart spec for the frontend."""
    logger.info("Step 7: Response generation & delivery")
    if state.get("error"):
        state["response"] = state["error"]
        return state

    client = OpenAI(api_key=settings.LLM_API_KEY)
    tasks_json = json.dumps(state.get("tasks", []))
    prompt = (
        "Create a final user-facing answer based on the following ordered task results. "
        "If a task includes data and a chart specification, mention the chart in the response.\n"
        f"Tasks: {tasks_json}"
    )

    resp = client.responses.create(
        model=settings.LLM_RESPONSE_MODEL,
        input=prompt,
    )
    if getattr(resp, "usage", None):
        state["tokens_in"] = getattr(resp.usage, "input_tokens", 0)
        state["tokens_out"] = getattr(resp.usage, "output_tokens", 0)
    state["response"] = resp.output[0].content[0].text.strip()
    state.setdefault("thought", []).append(
        {"step": "response_generation", "thought": state["response"]}
    )
    return state


@track_step("result_validation")
def result_validation(state: WorkflowState) -> WorkflowState:
    """Validate the response for correctness and safety."""
    logger.info("Step 8: Result validation & safety")
    tasks = state.get("tasks", [])
    sql_statements = [t.get("sql", "") for t in tasks if t.get("sql")]
    summary = state.get("response", "")

    # SQL allowlist: only simple SELECT statements without dangerous keywords
    allowed = re.compile(r"^\s*select\b", re.IGNORECASE)
    forbidden = re.compile(
        r";|\b(drop|delete|insert|update|alter|grant|revoke)\b",
        re.IGNORECASE,
    )
    for sql in sql_statements:
        if not allowed.match(sql) or forbidden.search(sql):
            state["error"] = "SQL validation failed."
            return state

    if summary:
        # Basic character allowlist
        summary_ok = re.compile(r"^[\w\s.,!?:;'\-]*$", re.UNICODE)
        if not summary_ok.match(summary):
            state["error"] = "Summary validation failed."
            return state

        # Guardrail checks for PII
        pii_patterns = [
            re.compile(r"[\w.-]+@[\w.-]+", re.IGNORECASE),
            re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        ]
        if any(p.search(summary) for p in pii_patterns):
            state["error"] = "PII detected in summary."
            return state

        # Simple profanity filter
        profanity = {"damn", "shit"}
        if any(word in summary.lower() for word in profanity):
            state["error"] = "Profanity detected in summary."
            return state

    state.setdefault("thought", []).append(
        {"step": "result_validation", "thought": "Validated result"}
    )
    return state


# def conversation_summary(state: WorkflowState) -> WorkflowState:
#     """Summarize the conversation and log outputs."""
#     logger.info("Step 9: Conversation summary & logging")
#     conv_id = state.get("conversation_id")
#     if conv_id:
#         try:
#             try:
#                 result = asyncio.run(
#                     conversation_service.summarize_conversation(conv_id)
#                 )
#             except RuntimeError:
#                 loop = asyncio.get_event_loop()
#                 result = loop.run_until_complete(
#                     conversation_service.summarize_conversation(conv_id)
#                 )
#             if result:
#                 summary_text, _last_id = result
#                 state["summary"] = summary_text
#         except Exception:
#             logger.exception("Conversation summarization failed for %s", conv_id)
#     return state


@track_step("monitoring")
def monitoring(state: WorkflowState) -> WorkflowState:
    """Capture feedback signals for continuous improvement."""
    logger.info("Step 9: Monitoring & continuous improvement")
    state.setdefault("thought", []).append(
        {"step": "monitoring", "thought": "Monitoring step completed"}
    )
    return state


def validation_router(state: WorkflowState) -> str:
    """Route to monitoring or halt on validation errors."""
    if state.get("error"):
        return END
    return "monitoring"


def clarification_router(state: WorkflowState) -> str:
    """Route clarifying questions to response generation or proceed."""
    if state.get("needs_clarification"):
        attempts = state.get("clarification_attempts", 0)
        limit = state.get("clarification_limit", 3)
        if not state.get("clarification_escalated") and attempts < limit:
            return "response_generation"
        return END
    if state.get("clarification_escalated"):
        return END
    return "task_planning"


def build_workflow(checkpointer=None) -> StateGraph[WorkflowState]:
    """Create and compile the LangGraph workflow."""
    builder = StateGraph(WorkflowState)

    def _prompt_intake(state: WorkflowState) -> WorkflowState:
        return prompt_intake(state, checkpointer)

    builder.add_node("prompt_intake", _prompt_intake)
    builder.add_node("intent_understanding", intent_understanding)
    builder.add_node("clarification", clarification)
    builder.add_node("task_planning", task_planning)
    builder.add_node("task_execution", task_execution)
    builder.add_node("response_generation", response_generation)
    builder.add_node("result_validation", result_validation)
    # builder.add_node("conversation_summary", conversation_summary)
    builder.add_node("monitoring", monitoring)

    builder.set_entry_point("prompt_intake")
    builder.add_edge("prompt_intake", "intent_understanding")
    builder.add_edge("intent_understanding", "clarification")
    builder.add_conditional_edges("clarification", clarification_router)
    builder.add_edge("task_planning", "task_execution")
    builder.add_edge("task_execution", "response_generation")
    builder.add_edge("response_generation", "result_validation")
    builder.add_conditional_edges("result_validation", validation_router)
    # builder.add_edge("conversation_summary", "monitoring")
    builder.add_edge("monitoring", END)

    return builder.compile(checkpointer=checkpointer)
