from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as aioredis
import time
from app.config import settings

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/auth"):
            limit = 10
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE

        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{client_ip}:{int(time.time() // 60)}"

        try:
            r = await get_redis()
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again in a minute."},
                    headers={"Retry-After": "60"},
                )
        except Exception:
            pass  # degrade gracefully if Redis is unavailable

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response
