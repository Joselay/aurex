from datetime import UTC, datetime, timedelta

import pandas as pd

from xauusd_signal_bot.models import Direction
from xauusd_signal_bot.strategy import XauUsdTrendStrategy


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


def test_generates_buy_signal_when_trend_and_rsi_reclaim_align() -> None:
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

    signal = XauUsdTrendStrategy().generate_signal(
        _candles(closes), symbol="XAU/USD", timeframe="15min"
    )

    assert signal is not None
    assert signal.direction == Direction.BUY
    assert signal.stop_loss < signal.entry < signal.take_profit_1 < signal.take_profit_2


def test_returns_none_without_trigger() -> None:
    closes = [2000 + index * 0.2 for index in range(220)]

    signal = XauUsdTrendStrategy().generate_signal(
        _candles(closes), symbol="XAU/USD", timeframe="15min"
    )

    assert signal is None
