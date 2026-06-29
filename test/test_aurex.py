import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aurex.candles import normalize_candles
from aurex.formatting import format_candle_time
from aurex.market_data import get_candles
from aurex.market_structure import analyze_market_structure
from aurex.settings import get_settings, normalize_timeframe, normalize_xauusd_symbol
from aurex.signals import (
    latest_signal_key,
    latest_signals,
    refresh_due_signals,
    should_poll_timeframe,
    timeframe_interval_minutes,
)
from aurex.strategy import generate_signal
from aurex.telegram import to_telegram_message


def candles_from_closes(closes):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candles = []
    for index, close in enumerate(closes):
        candle_time = start.timestamp() + index * 15 * 60
        candles.append(
            {
                "datetime": datetime.fromtimestamp(candle_time, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
            }
        )
    return candles


def buy_signal_closes():
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


def candles_from_high_low(highs, lows, closes=None):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    closes = closes or []
    candles = []
    for index, high in enumerate(highs):
        candle_time = start.timestamp() + index * 15 * 60
        close = closes[index] if index < len(closes) else (high + lows[index]) / 2
        candles.append(
            {
                "datetime": datetime.fromtimestamp(candle_time, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "open": close,
                "high": high,
                "low": lows[index],
                "close": close,
            }
        )
    return candles


def test_normalizes_supported_xauusd_aliases():
    assert normalize_xauusd_symbol("XAU/USD") == "XAU/USD"
    assert normalize_xauusd_symbol("xauusd") == "XAU/USD"


def test_rejects_non_gold_symbols():
    with pytest.raises(ValueError, match="only supports gold XAUUSD"):
        normalize_xauusd_symbol("BTC/USD")
    with pytest.raises(ValueError, match="only supports gold XAUUSD"):
        get_settings(SimpleNamespace(SYMBOL="ETH/USD"))


def test_normalizes_and_deduplicates_configured_timeframes():
    settings = get_settings(SimpleNamespace(TIMEFRAMES="5mn,15MIN,5min,1H"))
    assert settings.timeframes == ["5min", "15min", "1h"]


def test_rejects_blank_timeframes():
    with pytest.raises(ValueError, match="Blank timeframe"):
        normalize_timeframe(" ")


def test_rejects_non_positive_strategy_settings():
    with pytest.raises(ValueError, match="Invalid positive integer setting: RSI_PERIOD"):
        get_settings(SimpleNamespace(RSI_PERIOD="0"))
    with pytest.raises(ValueError, match="Invalid positive numeric setting: ATR_STOP_MULTIPLE"):
        get_settings(SimpleNamespace(ATR_STOP_MULTIPLE="-1"))


def test_normalizes_sorts_and_deduplicates_candle_rows():
    candles = normalize_candles(
        [
            {"datetime": "2026-01-01 00:15:00", "open": "2", "high": "3", "low": "1", "close": "2"},
            {"datetime": "2026-01-01 00:00:00", "open": "1", "high": "2", "low": "0", "close": "1"},
            {"datetime": "2026-01-01 00:15:00", "open": "4", "high": "5", "low": "3", "close": "4"},
        ]
    )

    assert len(candles) == 2
    assert candles[0]["datetime"] == "2026-01-01T00:00:00.000Z"
    assert candles[1]["close"] == 4


def test_formats_candle_time_for_human_facing_messages():
    assert format_candle_time("2026-01-01T00:15:00.000Z") == "2026-01-01 00:15 UTC"
    assert format_candle_time("2026-01-01T07:15:00+07:00") == "2026-01-01 00:15 UTC"


def test_converts_supported_timeframes_to_minutes():
    assert timeframe_interval_minutes("5min") == 5
    assert timeframe_interval_minutes("1h") == 60
    assert timeframe_interval_minutes("1day") == 1440
    assert timeframe_interval_minutes("custom") is None


def test_polls_slower_timeframes_only_when_their_candle_should_close():
    quarter_hour = datetime(2026, 1, 1, 1, 15, tzinfo=UTC)

    assert should_poll_timeframe("5min", quarter_hour) is True
    assert should_poll_timeframe("15min", quarter_hour) is True
    assert should_poll_timeframe("1h", quarter_hour) is False
    assert should_poll_timeframe("custom", quarter_hour) is True


@pytest.mark.asyncio
async def test_refreshes_and_caches_only_due_timeframes():
    requested_intervals = []
    kv = MapKv()

    async def fetch_json(url):
        requested_intervals.append(url.split("interval=", 1)[1].split("&", 1)[0])
        return {
            "values": [
                {
                    "datetime": "2026-01-01 00:00:00",
                    "open": "1",
                    "high": "2",
                    "low": "0",
                    "close": "1",
                },
                {
                    "datetime": "2026-01-01 00:05:00",
                    "open": "2",
                    "high": "3",
                    "low": "1",
                    "close": "2",
                },
            ]
        }

    env = SimpleNamespace(
        SYMBOL="XAU/USD",
        TIMEFRAMES="5min,15min,1h",
        TWELVEDATA_API_KEY="key",
        SIGNALS=kv,
    )

    signals = await refresh_due_signals(
        env,
        fetch_json,
        scheduled_time=datetime(2026, 1, 1, 1, 15, tzinfo=UTC),
    )

    assert signals == []
    assert requested_intervals == ["5min", "15min"]
    assert latest_signal_key("5min") in kv.values
    assert latest_signal_key("15min") in kv.values
    assert latest_signal_key("1h") not in kv.values


@pytest.mark.asyncio
async def test_requires_twelve_data_api_key_before_fetching_candles():
    async def fetch_json(_url):
        raise AssertionError("fetch_json should not be called without an API key")

    settings = get_settings(SimpleNamespace(TIMEFRAMES="5min")).for_timeframe("5min")

    with pytest.raises(RuntimeError, match="TWELVEDATA_API_KEY is required"):
        await get_candles(SimpleNamespace(TWELVEDATA_API_KEY=" "), settings, fetch_json)


@pytest.mark.asyncio
async def test_rejects_invalid_twelve_data_response_shape():
    async def fetch_json(_url):
        return ["not", "a", "payload"]

    settings = get_settings(SimpleNamespace(TIMEFRAMES="5min")).for_timeframe("5min")

    with pytest.raises(RuntimeError, match="Twelve Data returned an invalid response"):
        await get_candles(SimpleNamespace(TWELVEDATA_API_KEY="key"), settings, fetch_json)


@pytest.mark.asyncio
async def test_reads_latest_signals_from_kv_without_fetching_candles():
    signal = {
        "key": "XAU/USD:5min:2026-01-01T00:05:00.000Z:BUY",
        "symbol": "XAU/USD",
        "timeframe": "5min",
        "direction": "BUY",
        "candleTime": "2026-01-01T00:05:00.000Z",
    }
    kv = MapKv(
        {
            latest_signal_key("5min"): json.dumps(
                {
                    "timeframe": "5min",
                    "checkedAt": "2026-01-01T00:05:00.000Z",
                    "signal": signal,
                }
            )
        }
    )

    assert await latest_signals(SimpleNamespace(TIMEFRAMES="5min", SIGNALS=kv)) == [signal]


@pytest.mark.asyncio
async def test_ignores_malformed_latest_signal_cache_entries():
    signal = {
        "key": "XAU/USD:15min:2026-01-01T00:15:00.000Z:BUY",
        "symbol": "XAU/USD",
        "timeframe": "15min",
        "direction": "BUY",
        "candleTime": "2026-01-01T00:15:00.000Z",
    }
    kv = MapKv(
        {
            latest_signal_key("5min"): "not-json",
            latest_signal_key("15min"): json.dumps({"signal": signal}),
            latest_signal_key("1h"): json.dumps(["bad-shape"]),
            latest_signal_key("1day"): ["bad-json-type"],
        }
    )

    env = SimpleNamespace(TIMEFRAMES="5min,15min,1h,1day", SIGNALS=kv)

    assert await latest_signals(env) == [signal]


def test_calculates_support_resistance_and_trendline_levels_from_recent_swings():
    market_structure = analyze_market_structure(
        candles_from_high_low(
            [10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17],
            [5, 7, 6, 8, 7, 9, 8, 10, 9, 11, 10, 12],
            [7, 10, 8, 11, 9, 12, 10, 13, 11, 14, 12, 12.5],
        ),
        {"structure_lookback": 12, "pivot_strength": 1, "trendline_pivot_count": 6},
    )

    assert market_structure["support"] == 10
    assert market_structure["resistance"] == 13
    assert market_structure["supportTrendline"] == 10.5
    assert market_structure["resistanceTrendline"] == 17


def test_generates_buy_signal_when_trend_and_rsi_reclaim_align():
    settings = get_settings(SimpleNamespace()).for_timeframe("15min")
    signal = generate_signal(candles_from_closes(buy_signal_closes()), settings)

    assert signal is not None
    assert signal["direction"] == "BUY"
    assert signal["candleTimeDisplay"] == "2026-01-03 06:45 UTC"
    assert isinstance(signal["marketStructure"]["support"], (int, float))
    assert isinstance(signal["marketStructure"]["resistance"], (int, float))
    assert signal["reason"].startswith("15min trend above EMA200")
    assert signal["stopLoss"] < signal["entry"]
    assert signal["entry"] < signal["takeProfit1"]
    assert signal["takeProfit1"] < signal["takeProfit2"]


def test_returns_null_without_a_trigger():
    settings = get_settings(SimpleNamespace()).for_timeframe("15min")
    closes = [2000 + index * 0.2 for index in range(220)]
    assert generate_signal(candles_from_closes(closes), settings) is None


def test_formats_telegram_messages_from_generated_signals():
    settings = get_settings(SimpleNamespace()).for_timeframe("1h")
    signal = generate_signal(candles_from_closes(buy_signal_closes()), settings)

    message = to_telegram_message(signal)

    assert message.startswith("🟢 <b>XAUUSD BUY SIGNAL</b>\n⏱ <b>Timeframe:</b> 1h")
    assert "\n🕯 <b>Candle:</b> 2026-01-03 06:45 UTC\n" in message
    assert "\n📍 <b>Trade Plan</b>\n" in message
    assert "\n🎯 Entry: <code>" in message
    assert "\n🟢 Support: <code>" in message
    assert "\n📉 Resistance trendline: <code>" in message
    assert message.endswith("⚠️ <b>Risk:</b> Signal only. Demo test before live trading.")


def test_escapes_dynamic_telegram_message_content_for_html_parse_mode():
    message = to_telegram_message(
        {
            "symbol": "XAU/USD",
            "timeframe": "bad <frame>",
            "direction": "BUY",
            "candleTime": "2026-01-01T00:15:00.000Z",
            "entry": 2000,
            "stopLoss": 1990,
            "takeProfit1": 2010,
            "takeProfit2": 2020,
            "marketStructure": {},
            "reason": "EMA20 > EMA50 & RSI < 70",
        }
    )

    assert "bad &lt;frame&gt;" in message
    assert "EMA20 &gt; EMA50 &amp; RSI &lt; 70" in message


class MapKv:
    def __init__(self, values=None):
        self.values = values or {}

    async def get(self, key):
        return self.values.get(key)

    async def put(self, key, value):
        self.values[key] = value
