"""Worker and Redis-only endpoints shared with the main API server."""

import asyncio
import os
from typing import Dict

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis.asyncio import from_url

from event_schema import WorkflowEvent
from worker.redis_bus import RedisStreamsBus
from worker.stream import event_stream

router = APIRouter()
redis = from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
RUN_TASKS: Dict[str, asyncio.Task] = {}


class RunStart(WorkflowEvent):
    prompt: str
    user_id: str


class RunStop(BaseModel):
    conversation_id: str


async def run_workflow(conversation_id: str, workflow_run_id: str, prompt: str):
    bus = RedisStreamsBus(redis)
    text = "placeholder response from worker"
    try:
        for token in text.split():
            await bus.publish(
                workflow_run_id,
                {
                    "type": "agent_token",
                    "conversation_id": conversation_id,
                    "workflow_run_id": workflow_run_id,
                    "step_id": "write",
                    "agent_id": "writer",
                    "delta": token + " ",
                },
            )
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        await bus.publish(
            workflow_run_id,
            {
                "type": "done",
                "conversation_id": conversation_id,
                "workflow_run_id": workflow_run_id,
                "step_id": "write",
                "agent_id": "writer",
                "metadata": {"stopped": True},
            },
        )
        raise
    else:
        await bus.publish(
            workflow_run_id,
            {
                "type": "agent_message",
                "conversation_id": conversation_id,
                "workflow_run_id": workflow_run_id,
                "step_id": "write",
                "agent_id": "writer",
                "content": text,
            },
        )
        await bus.publish(
            workflow_run_id,
            {
                "type": "done",
                "conversation_id": conversation_id,
                "workflow_run_id": workflow_run_id,
                "step_id": "write",
                "agent_id": "writer",
            },
        )


@router.post("/runs/start", status_code=status.HTTP_202_ACCEPTED)
async def runs_start(body: RunStart):
    """Worker endpoint to kick off a workflow run."""

    task = asyncio.create_task(
        run_workflow, body.conversation_id, body.workflow_run_id, body.prompt
    )
    RUN_TASKS[body.workflow_run_id] = task
    task.add_done_callback(lambda _: RUN_TASKS.pop(body.workflow_run_id, None))
    return {"status": "started"}


@router.post("/runs/{workflow_run_id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def runs_stop(workflow_run_id: str, body: RunStop):
    """Cancel a running workflow and notify listeners."""

    task = RUN_TASKS.pop(workflow_run_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    elif task is None:
        bus = RedisStreamsBus(redis)
        await bus.publish(
            workflow_run_id,
            {
                "type": "done",
                "conversation_id": body.conversation_id,
                "workflow_run_id": workflow_run_id,
                "step_id": "write",
                "agent_id": "writer",
                "metadata": {"stopped": True},
            },
        )
    return {"status": "stopping"}


@router.get("/stream/{workflow_run_id}")
async def stream_events(
    workflow_run_id: str,
    request: Request,
    last_event_id: str | None = Header(None, convert_underscores=False),
):
    """SSE endpoint forwarding Redis events to the client."""
    start_id = last_event_id or "0-0"
    generator = event_stream(request, redis, workflow_run_id, start_id)
    return StreamingResponse(generator, media_type="text/event-stream")
