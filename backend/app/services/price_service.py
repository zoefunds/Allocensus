import httpx
import redis.asyncio as aioredis
import json
from app.config import settings
import structlog

log = structlog.get_logger()
CACHE_TTL = 60  # seconds


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_crypto_prices(coingecko_ids: list[str]) -> dict[str, float]:
    """Fetch USD prices from CoinGecko. Redis-cached for 60 seconds."""
    if not coingecko_ids:
        return {}
    cache_key = f"prices:cg:{','.join(sorted(coingecko_ids))}"
    try:
        r = await _get_redis()
        cached = await r.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    try:
        ids_param = ",".join(coingecko_ids)
        headers = {"x-cg-demo-api-key": settings.COINGECKO_API_KEY} if settings.COINGECKO_API_KEY else {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ids_param, "vs_currencies": "usd"},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            prices = {coin_id: info["usd"] for coin_id, info in data.items()}
            try:
                r = await _get_redis()
                await r.setex(cache_key, CACHE_TTL, json.dumps(prices))
            except Exception:
                pass
            return prices
    except Exception as e:
        log.error("price_fetch_failed", error=str(e))
        return {}


async def get_market_context() -> dict:
    """Fetch basic market context for the Genlayer contract call."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/global",
                headers={"x-cg-demo-api-key": settings.COINGECKO_API_KEY} if settings.COINGECKO_API_KEY else {},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "total_market_cap_usd": data.get("total_market_cap", {}).get("usd"),
                "market_cap_change_24h": data.get("market_cap_change_percentage_24h_usd"),
                "btc_dominance": data.get("market_cap_percentage", {}).get("btc"),
                "active_cryptocurrencies": data.get("active_cryptocurrencies"),
            }
    except Exception:
        return {}
