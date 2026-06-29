from aurex.constants import (
    DEFAULT_PIVOT_STRENGTH,
    DEFAULT_STRUCTURE_LOOKBACK,
    DEFAULT_TRENDLINE_PIVOTS,
)


def analyze_market_structure(candles, settings=None):
    if len(candles) == 0:
        return empty_market_structure()

    settings = settings or {}
    latest_index = len(candles) - 1
    latest_close = candles[latest_index]["close"]
    lookback = max(5, _setting(settings, "structure_lookback", DEFAULT_STRUCTURE_LOOKBACK))
    pivot_strength = max(1, _setting(settings, "pivot_strength", DEFAULT_PIVOT_STRENGTH))
    trendline_pivot_count = max(
        2,
        _setting(settings, "trendline_pivot_count", DEFAULT_TRENDLINE_PIVOTS),
    )
    start_index = max(0, len(candles) - lookback)
    recent_candles = candles[start_index:]
    pivots = [
        pivot
        for pivot in find_swing_pivots(candles, pivot_strength)
        if pivot["index"] >= start_index
    ]

    swing_highs = [pivot for pivot in pivots if pivot["type"] == "high"]
    swing_lows = [pivot for pivot in pivots if pivot["type"] == "low"]

    return {
        "support": nearest_level_below(
            latest_close,
            [pivot["price"] for pivot in swing_lows],
            [candle["low"] for candle in recent_candles],
        ),
        "resistance": nearest_level_above(
            latest_close,
            [pivot["price"] for pivot in swing_highs],
            [candle["high"] for candle in recent_candles],
        ),
        "supportTrendline": projected_trendline_value(
            swing_lows,
            latest_index,
            trendline_pivot_count,
        ),
        "resistanceTrendline": projected_trendline_value(
            swing_highs,
            latest_index,
            trendline_pivot_count,
        ),
    }


def empty_market_structure():
    return {
        "support": None,
        "resistance": None,
        "supportTrendline": None,
        "resistanceTrendline": None,
    }


def find_swing_pivots(candles, strength):
    pivots = []

    for index in range(strength, len(candles) - strength):
        candle = candles[index]
        is_swing_high = True
        is_swing_low = True

        for offset in range(1, strength + 1):
            previous_high = candles[index - offset]["high"]
            next_high = candles[index + offset]["high"]
            previous_low = candles[index - offset]["low"]
            next_low = candles[index + offset]["low"]

            if candle["high"] <= previous_high or candle["high"] <= next_high:
                is_swing_high = False
            if candle["low"] >= previous_low or candle["low"] >= next_low:
                is_swing_low = False

        if is_swing_high:
            pivots.append({"type": "high", "index": index, "price": candle["high"]})
        if is_swing_low:
            pivots.append({"type": "low", "index": index, "price": candle["low"]})

    return pivots


def nearest_level_below(price, preferred_levels, fallback_levels):
    below = [level for level in preferred_levels if level <= price]
    if len(below) > 0:
        return max(below)
    if len(fallback_levels) == 0:
        return None
    return min(fallback_levels)


def nearest_level_above(price, preferred_levels, fallback_levels):
    above = [level for level in preferred_levels if level >= price]
    if len(above) > 0:
        return min(above)
    if len(fallback_levels) == 0:
        return None
    return max(fallback_levels)


def projected_trendline_value(pivots, target_index, pivot_count):
    selected = pivots[-pivot_count:]
    if len(selected) < 2:
        return None

    average_index = sum(pivot["index"] for pivot in selected) / len(selected)
    average_price = sum(pivot["price"] for pivot in selected) / len(selected)
    variance = sum((pivot["index"] - average_index) ** 2 for pivot in selected)
    if variance == 0:
        return None

    covariance = sum(
        (pivot["index"] - average_index) * (pivot["price"] - average_price)
        for pivot in selected
    )
    slope = covariance / variance
    intercept = average_price - slope * average_index
    return slope * target_index + intercept


def _setting(settings, field_name, fallback):
    if isinstance(settings, dict):
        return settings.get(field_name, fallback)
    return getattr(settings, field_name, fallback)
