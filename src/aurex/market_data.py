from urllib.parse import urlencode

from aurex.candles import normalize_candles


async def get_candles(env, settings, fetch_json):
    params = urlencode(
        {
            "symbol": settings.symbol,
            "interval": settings.timeframe,
            "outputsize": str(settings.candle_limit),
            "apikey": getattr(env, "TWELVEDATA_API_KEY", None),
            "format": "JSON",
        }
    )
    payload = await fetch_json(f"https://api.twelvedata.com/time_series?{params}")

    if payload.get("status") == "error":
        raise RuntimeError(payload.get("message") or "Twelve Data returned an error")
    values = payload.get("values")
    if not isinstance(values, list) or len(values) == 0:
        raise RuntimeError("Twelve Data returned no candle values")

    return normalize_candles(values)

