import redis.asyncio as redis
from app.config import settings

redis_client: redis.Redis | None = None

def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return redis_client
