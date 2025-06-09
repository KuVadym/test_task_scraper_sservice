from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.settings import settings
from redis.asyncio import ConnectionPool, Redis

redis_pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True, max_connections=10)


@asynccontextmanager
async def get_redis() -> AsyncIterator[Redis]:
    """Асинхронний контекстний менеджер для Redis з пулом з'єднань"""
    redis = Redis(connection_pool=redis_pool)
    try:
        yield redis
    finally:
        await redis.close()
