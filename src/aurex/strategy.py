import math

from aurex.formatting import format_candle_time
from aurex.indicators import atr, ema, rsi
from aurex.market_structure import analyze_market_structure


def generate_signal(candles, settings):
    minimum_candles = max(
        settings.ema_trend,
        settings.ema_slow,
        settings.rsi_period,
        settings.atr_period,
    ) + 2
    if len(candles) < minimum_candles:
        return None

    closes = [candle["close"] for candle in candles]
    highs = [candle["high"] for candle in candles]
    lows = [candle["low"] for candle in candles]

    ema_fast = ema(closes, settings.ema_fast)
    ema_slow = ema(closes, settings.ema_slow)
    ema_trend = ema(closes, settings.ema_trend)
    rsi_values = rsi(closes, settings.rsi_period)
    atr_values = atr(highs, lows, closes, settings.atr_period)

    latest_index = len(candles) - 1
    previous_index = len(candles) - 2
    latest = candles[latest_index]
    risk_distance = atr_values[latest_index] * settings.atr_stop_multiple

    if (
        not math.isfinite(ema_fast[latest_index])
        or not math.isfinite(ema_slow[latest_index])
        or not math.isfinite(ema_trend[latest_index])
        or not math.isfinite(rsi_values[latest_index])
        or not math.isfinite(atr_values[latest_index])
        or not math.isfinite(rsi_values[previous_index])
        or not math.isfinite(risk_distance)
        or risk_distance <= 0
    ):
        return None

    buy_setup = (
        latest["close"] > ema_trend[latest_index]
        and ema_fast[latest_index] > ema_slow[latest_index]
        and latest["close"] > ema_fast[latest_index]
        and rsi_values[previous_index] <= 50
        and rsi_values[latest_index] > 50
    )

    sell_setup = (
        latest["close"] < ema_trend[latest_index]
        and ema_fast[latest_index] < ema_slow[latest_index]
        and latest["close"] < ema_fast[latest_index]
        and rsi_values[previous_index] >= 50
        and rsi_values[latest_index] < 50
    )

    market_structure = analyze_market_structure(candles, settings)
    if buy_setup:
        return build_signal(settings, latest, "BUY", risk_distance, market_structure)
    if sell_setup:
        return build_signal(settings, latest, "SELL", risk_distance, market_structure)
    return None


def build_signal(settings, candle, direction, risk_distance, market_structure):
    entry = candle["close"]
    is_buy = direction == "BUY"
    stop_loss = entry - risk_distance if is_buy else entry + risk_distance
    take_profit_1 = (
        entry + risk_distance * settings.reward_multiple_1
        if is_buy
        else entry - risk_distance * settings.reward_multiple_1
    )
    take_profit_2 = (
        entry + risk_distance * settings.reward_multiple_2
        if is_buy
        else entry - risk_distance * settings.reward_multiple_2
    )
    relation = ("above", "above", "reclaimed") if is_buy else ("below", "below", "lost")
    reason = (
        f"{settings.timeframe} trend {relation[0]} EMA{settings.ema_trend}, "
        f"EMA{settings.ema_fast} {relation[1]} EMA{settings.ema_slow}, "
        f"RSI {relation[2]} 50."
    )

    signal = {
        "symbol": settings.symbol,
        "timeframe": settings.timeframe,
        "direction": direction,
        "candleTime": candle["datetime"],
        "candleTimeDisplay": format_candle_time(candle["datetime"]),
        "entry": entry,
        "stopLoss": stop_loss,
        "takeProfit1": take_profit_1,
        "takeProfit2": take_profit_2,
        "marketStructure": market_structure,
        "reason": reason,
    }
    signal["key"] = (
        f"{signal['symbol']}:{signal['timeframe']}:{signal['candleTime']}:{signal['direction']}"
    )
    return signal

