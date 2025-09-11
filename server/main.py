"""FastAPI application serving the data analyst chatbot."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import iterate_in_threadpool

from api.v1.routes import (
    users_router,
    db_connections_router,
    conversations_router,
    step_logs_router,
    mappings_router,
    debug_router,
    worker_router,
)
from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate configuration and set logging on startup
    s = get_settings()
    logging.basicConfig(
        level=getattr(logging, s.LOG_LEVEL.upper(), logging.DEBUG),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    yield


app = FastAPI(title="LLM Data Analyst", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("api")
    logger.info(
        "Endpoint hit %s %s params=%s",
        request.method,
        request.url.path,
        dict(request.query_params),
    )
    response = await call_next(request)
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    response.body_iterator = iterate_in_threadpool(iter([body]))
    logger.info(
        "Response %s %s status=%s body=%s",
        request.method,
        request.url.path,
        response.status_code,
        body.decode() if body else "",
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(db_connections_router)
app.include_router(conversations_router)
app.include_router(step_logs_router)
app.include_router(mappings_router)
app.include_router(debug_router)
app.include_router(worker_router)  # internal worker/Redis endpoints
