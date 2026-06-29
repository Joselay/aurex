from datetime import UTC, datetime, timedelta

import pandas as pd

from lumiere.models import Direction
from lumiere.strategy import XauUsdTrendStrategy


def _candles(closes: list[float]) -> pd.DataFrame:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return pd.DataFrame(
        {
            "datetime": [start + timedelta(minutes=15 * index) for index in range(len(closes))],
            "open": closes,
            "high": [close + 1 for close in closes],
            "low": [close - 1 for close in closes],
            "close": closes,
        }
    )


def _buy_signal_closes() -> list[float]:
    closes = [2000 + index * 0.1 for index in range(220)]
    closes[-15:] = [
        2024.0,
        2023.0,
        2022.0,
        2021.0,
        2020.0,
        2019.0,
        2018.0,
        2017.0,
        2016.0,
        2015.0,
        2014.0,
        2013.0,
        2012.0,
        2013.0,
        2028.0,
    ]
    return closes


def test_generates_buy_signal_when_trend_and_rsi_reclaim_align() -> None:
    signal = XauUsdTrendStrategy().generate_signal(
        _candles(_buy_signal_closes()), symbol="XAU/USD", timeframe="15min"
    )

    assert signal is not None
    assert signal.direction == Direction.BUY
    assert signal.reason.startswith("15min trend above EMA200")
    assert signal.stop_loss < signal.entry < signal.take_profit_1 < signal.take_profit_2


def test_signal_reason_uses_configured_timeframe() -> None:
    signal = XauUsdTrendStrategy().generate_signal(
        _candles(_buy_signal_closes()), symbol="XAU/USD", timeframe="1h"
    )

    assert signal is not None
    assert signal.reason.startswith("1h trend above EMA200")


def test_returns_none_when_risk_distance_is_not_positive() -> None:
    signal = XauUsdTrendStrategy(atr_stop_multiple=0).generate_signal(
        _candles(_buy_signal_closes()), symbol="XAU/USD", timeframe="15min"
    )

    assert signal is None


def test_returns_none_without_trigger() -> None:
    closes = [2000 + index * 0.2 for index in range(220)]

    signal = XauUsdTrendStrategy().generate_signal(
        _candles(closes), symbol="XAU/USD", timeframe="15min"
    )

    assert signal is None
