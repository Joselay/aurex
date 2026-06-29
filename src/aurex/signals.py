import json
import re
from datetime import UTC, datetime

from aurex.market_data import get_candles
from aurex.settings import get_settings
from aurex.strategy import generate_signal
from aurex.telegram import to_telegram_message

LATEST_SIGNAL_PREFIX = "latest:"


async def publish_new_signals(env, fetch_json, send_telegram_message, scheduled_time=None):
    signals = await refresh_due_signals(env, fetch_json, scheduled_time)
    if len(signals) == 0:
        print("No signal")
        return []

    published = []
    for signal in signals:
        existing = await env.SIGNALS.get(signal["key"])
        if existing is not None:
            print(f"Signal already sent: {signal['key']}")
            continue

        await send_telegram_message(to_telegram_message(signal))
        await env.SIGNALS.put(signal["key"], json.dumps(signal))
        published.append(signal)
        print(f"Published signal: {signal['key']}")

    return published


async def latest_signals(env):
    settings = get_settings(env)
    return await read_cached_signals(env, settings.timeframes)


async def refresh_due_signals(env, fetch_json, scheduled_time=None):
    settings = get_settings(env)
    run_date = to_run_date(scheduled_time)
    signals = []
    due_timeframes = [
        timeframe
        for timeframe in settings.timeframes
        if should_poll_timeframe(timeframe, run_date)
    ]

    for timeframe in due_timeframes:
        timeframe_settings = settings.for_timeframe(timeframe)
        candles = await get_candles(env, timeframe_settings, fetch_json)
        signal = generate_signal(candles, timeframe_settings)
        await write_cached_signal(env, timeframe, signal, run_date)
        if signal is not None:
            signals.append(signal)

    return signals


async def read_cached_signals(env, timeframes):
    signals = []
    for timeframe in timeframes:
        value = await env.SIGNALS.get(latest_signal_key(timeframe))
        if value is None:
            continue

        cached = json.loads(value)
        if cached.get("signal") is not None:
            signals.append(cached["signal"])
    return signals


async def write_cached_signal(env, timeframe, signal, run_date):
    await env.SIGNALS.put(
        latest_signal_key(timeframe),
        json.dumps(
            {
                "timeframe": timeframe,
                "checkedAt": to_js_iso(run_date),
                "signal": signal,
            }
        ),
    )


def latest_signal_key(timeframe):
    return f"{LATEST_SIGNAL_PREFIX}{timeframe}"


def should_poll_timeframe(timeframe, run_date):
    interval_minutes = timeframe_interval_minutes(timeframe)
    if interval_minutes is None:
        return True
    return int(run_date.timestamp() // 60) % interval_minutes == 0


def timeframe_interval_minutes(timeframe):
    match = re.fullmatch(r"(\d+)(min|h|day|week)", str(timeframe).strip().lower())
    if match is None:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    unit_minutes = {
        "min": 1,
        "h": 60,
        "day": 1440,
        "week": 10080,
    }[unit]
    return amount * unit_minutes if amount > 0 else None


def to_run_date(scheduled_time=None):
    if scheduled_time is None:
        return datetime.now(UTC)
    if isinstance(scheduled_time, datetime):
        return scheduled_time.astimezone(UTC)
    if isinstance(scheduled_time, (int, float)):
        return datetime.fromtimestamp(scheduled_time / 1000, UTC)
    if isinstance(scheduled_time, str):
        try:
            return datetime.fromtimestamp(float(scheduled_time) / 1000, UTC)
        except ValueError:
            return datetime.fromisoformat(scheduled_time.replace("Z", "+00:00")).astimezone(UTC)
    raise ValueError(f"Invalid scheduled time: {scheduled_time}")


def to_js_iso(value):
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

