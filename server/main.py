"""FastAPI application serving the data analyst chatbot."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.routes import (
    users_router,
    db_connections_router,
    conversations_router,
    step_logs_router,
)
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
)

app = FastAPI(title="LLM Data Analyst")

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
