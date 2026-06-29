import math
import re
from dataclasses import dataclass

from aurex.constants import (
    DEFAULT_PIVOT_STRENGTH,
    DEFAULT_STRUCTURE_LOOKBACK,
    DEFAULT_TRENDLINE_PIVOTS,
    XAUUSD_DISPLAY_SYMBOL,
    XAUUSD_SYMBOL,
)


@dataclass(frozen=True)
class Settings:
    symbol: str
    timeframes: list[str]
    candle_limit: int
    ema_fast: int
    ema_slow: int
    ema_trend: int
    rsi_period: int
    atr_period: int
    atr_stop_multiple: float
    reward_multiple_1: float
    reward_multiple_2: float
    structure_lookback: int
    pivot_strength: int
    trendline_pivot_count: int
    timeframe: str | None = None

    def for_timeframe(self, timeframe):
        return Settings(
            symbol=self.symbol,
            timeframes=self.timeframes,
            candle_limit=self.candle_limit,
            ema_fast=self.ema_fast,
            ema_slow=self.ema_slow,
            ema_trend=self.ema_trend,
            rsi_period=self.rsi_period,
            atr_period=self.atr_period,
            atr_stop_multiple=self.atr_stop_multiple,
            reward_multiple_1=self.reward_multiple_1,
            reward_multiple_2=self.reward_multiple_2,
            structure_lookback=self.structure_lookback,
            pivot_strength=self.pivot_strength,
            trendline_pivot_count=self.trendline_pivot_count,
            timeframe=timeframe,
        )


def get_settings(env):
    symbol = normalize_xauusd_symbol(get_string(env, "SYMBOL", XAUUSD_SYMBOL))
    return Settings(
        symbol=symbol,
        timeframes=get_timeframes(env),
        candle_limit=get_positive_integer(env, "CANDLE_LIMIT", 260),
        ema_fast=get_positive_integer(env, "EMA_FAST", 20),
        ema_slow=get_positive_integer(env, "EMA_SLOW", 50),
        ema_trend=get_positive_integer(env, "EMA_TREND", 200),
        rsi_period=get_positive_integer(env, "RSI_PERIOD", 14),
        atr_period=get_positive_integer(env, "ATR_PERIOD", 14),
        atr_stop_multiple=get_positive_number(env, "ATR_STOP_MULTIPLE", 1.5),
        reward_multiple_1=get_positive_number(env, "REWARD_MULTIPLE_1", 1.0),
        reward_multiple_2=get_positive_number(env, "REWARD_MULTIPLE_2", 2.0),
        structure_lookback=get_positive_integer(
            env,
            "STRUCTURE_LOOKBACK",
            DEFAULT_STRUCTURE_LOOKBACK,
        ),
        pivot_strength=get_positive_integer(env, "PIVOT_STRENGTH", DEFAULT_PIVOT_STRENGTH),
        trendline_pivot_count=get_positive_integer(
            env,
            "TRENDLINE_PIVOTS",
            DEFAULT_TRENDLINE_PIVOTS,
        ),
    )


def get_timeframes(env):
    configured = get_string(env, "TIMEFRAMES", get_string(env, "TIMEFRAME", "15min"))
    timeframes = []
    for value in configured.split(","):
        timeframe = normalize_timeframe(value)
        if timeframe not in timeframes:
            timeframes.append(timeframe)

    if len(timeframes) == 0:
        raise ValueError("At least one timeframe is required")
    return timeframes


def normalize_timeframe(timeframe):
    value = str(timeframe).strip().lower()
    alias_match = re.fullmatch(r"(\d+)mn", value)
    if alias_match is not None:
        return f"{alias_match.group(1)}min"
    if value == "":
        raise ValueError("Blank timeframe is not supported")
    return value


def normalize_xauusd_symbol(symbol):
    value = str(symbol).strip().upper()
    if value in (XAUUSD_SYMBOL, XAUUSD_DISPLAY_SYMBOL):
        return XAUUSD_SYMBOL
    raise ValueError(f"Aurex only supports gold {XAUUSD_DISPLAY_SYMBOL}")


def get_string(env, key, fallback):
    value = getattr(env, key, None)
    return fallback if value is None or value == "" else str(value)


def get_integer(env, key, fallback):
    try:
        return int(get_string(env, key, str(fallback)))
    except ValueError as exc:
        raise ValueError(f"Invalid integer setting: {key}") from exc


def get_number(env, key, fallback):
    try:
        value = float(get_string(env, key, str(fallback)))
    except ValueError as exc:
        raise ValueError(f"Invalid numeric setting: {key}") from exc
    if not math.isfinite(value):
        raise ValueError(f"Invalid numeric setting: {key}")
    return value


def get_positive_integer(env, key, fallback):
    value = get_integer(env, key, fallback)
    if value <= 0:
        raise ValueError(f"Invalid positive integer setting: {key}")
    return value


def get_positive_number(env, key, fallback):
    value = get_number(env, key, fallback)
    if value <= 0:
        raise ValueError(f"Invalid positive numeric setting: {key}")
    return value
