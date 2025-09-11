import asyncio
from typing import AsyncGenerator
from fastapi import Request
from redis.asyncio import Redis


async def event_stream(
    request: Request, redis: Redis, run_id: str, start_id: str = "0-0"
) -> AsyncGenerator[str, None]:
    key = f"run:{run_id}:events"
    last_id = start_id
    while True:
        if await request.is_disconnected():
            break
        results = await redis.xread({key: last_id}, block=500, count=10)
        if results:
            for _stream, messages in results:
                for msg_id, fields in messages:
                    last_id = msg_id
                    data = fields.get("data", "")
                    yield f"id: {msg_id}\n" f"event: message\n" f"data: {data}\n\n"
        else:
            yield "event: ping\n\n"
        await asyncio.sleep(0.1)
