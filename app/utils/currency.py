from httpx import AsyncClient, Headers

from app.database.redis import get_redis
from app.schemas.currency import ExchangeRates
from app.settings import settings


async def get_currency_coefficient() -> float:
    cache_key = "currency_coefficient"
    async with get_redis() as redis:
        if cached_data := await redis.get(cache_key):
            return cached_data

    headers = Headers()
    headers.update(
        {
            "User-Agent": "Everapi_Python",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "apikey": settings.CURRENCY_API_KEY,
        }
    )
    async with AsyncClient(headers=headers) as client:
        response = await client.get(
            "https://api.currencyapi.com/v3/latest",
            params={
                "base_currency": "GBP",
                "currencies": "USD",
            },
        )

        json_result = response.json()
        exchange_rates = ExchangeRates.model_validate(json_result)
        currency_coefficient = exchange_rates.data["USD"].value

        await redis.setex(cache_key, 86400, currency_coefficient)

        return currency_coefficient
