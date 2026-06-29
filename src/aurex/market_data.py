from urllib.parse import urlencode

from aurex.candles import normalize_candles


async def get_candles(env, settings, fetch_json):
    api_key = str(getattr(env, "TWELVEDATA_API_KEY", "")).strip()
    if api_key == "":
        raise RuntimeError("TWELVEDATA_API_KEY is required")

    params = urlencode(
        {
            "symbol": settings.symbol,
            "interval": settings.timeframe,
            "outputsize": str(settings.candle_limit),
            "apikey": api_key,
            "format": "JSON",
        }
    )
    payload = await fetch_json(f"https://api.twelvedata.com/time_series?{params}")

    if not isinstance(payload, dict):
        raise RuntimeError("Twelve Data returned an invalid response")
    if payload.get("status") == "error":
        raise RuntimeError(payload.get("message") or "Twelve Data returned an error")
    values = payload.get("values")
    if not isinstance(values, list) or len(values) == 0:
        raise RuntimeError("Twelve Data returned no candle values")

    return normalize_candles(values)
