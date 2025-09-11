"""Worker and Redis-only endpoints shared with the main API server."""

import asyncio
import os
from fastapi import APIRouter, BackgroundTasks, Header, Request, status
from fastapi.responses import StreamingResponse
from redis.asyncio import from_url

from event_schema import WorkflowEvent
from worker.redis_bus import RedisStreamsBus
from worker.stream import event_stream

router = APIRouter()
redis = from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))


class RunStart(WorkflowEvent):
    prompt: str
    user_id: str


async def run_workflow(conversation_id: str, workflow_run_id: str, prompt: str):
    bus = RedisStreamsBus(redis)
    text = "placeholder response from worker"
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
async def runs_start(body: RunStart, background_tasks: BackgroundTasks):
    """Worker endpoint to kick off a workflow run."""
    background_tasks.add_task(
        run_workflow, body.conversation_id, body.workflow_run_id, body.prompt
    )
    return {"status": "started"}


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
