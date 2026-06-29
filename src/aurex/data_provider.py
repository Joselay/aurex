from abc import ABC, abstractmethod

import httpx
import pandas as pd

from aurex.market import normalize_xauusd_symbol
from aurex.models import normalize_candles


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Return normalized OHLC candles sorted oldest to newest."""


class TwelveDataProvider(MarketDataProvider):
    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._client = client

    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        symbol = normalize_xauusd_symbol(symbol)
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "outputsize": limit,
            "apikey": self._api_key,
            "format": "JSON",
        }

        if self._client is None:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(self.BASE_URL, params=params)
        else:
            response = await self._client.get(self.BASE_URL, params=params)

        response.raise_for_status()
        payload = response.json()

        if payload.get("status") == "error":
            message = payload.get("message", "Twelve Data returned an error")
            raise RuntimeError(message)

        values = payload.get("values")
        if not values:
            raise RuntimeError("Twelve Data returned no candle values")

        frame = pd.DataFrame(values)
        return normalize_candles(frame)
