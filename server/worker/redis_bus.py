import json
from redis.asyncio import Redis


class RedisStreamsBus:
    """Publish workflow events to a Redis Stream."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def publish(self, run_id: str, payload: dict):
        key = f"run:{run_id}:events"
        data = json.dumps(payload)
        await self.redis.xadd(key, {"data": data}, maxlen=10000, approximate=True)
