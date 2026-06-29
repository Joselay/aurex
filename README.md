# Aurex

Python Cloudflare Worker that watches XAUUSD candles, generates rule-based signals, and sends new
signals to Telegram.

Aurex is intentionally XAUUSD-only. It does not accept crypto, equities, or other forex pairs.

This is a signal bot, not an auto-trading bot. Demo test and backtest before risking live money.

## Setup

```bash
uv sync
```

Production configuration is stored in Cloudflare, not in `.env` files.

Set production secrets with pywrangler:

```bash
uv run pywrangler secret put TELEGRAM_BOT_TOKEN
uv run pywrangler secret put TELEGRAM_CHAT_ID
uv run pywrangler secret put TWELVEDATA_API_KEY
```

For a Telegram group, add the bot to the group, send any message in that group, then open:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

Use the `message.chat.id` value for `TELEGRAM_CHAT_ID`. Group chat IDs are usually negative, and
supergroup IDs usually start with `-100`.

For local Cloudflare development only, create `.dev.vars`:

```bash
cp .dev.vars.example .dev.vars
```

Edit `.dev.vars` with the same secret names used in Cloudflare:

- `TELEGRAM_BOT_TOKEN`: token from BotFather.
- `TELEGRAM_CHAT_ID`: your group chat ID.
- `TWELVEDATA_API_KEY`: Twelve Data API key.

Do not use `.env`; this project is a Cloudflare Worker and Wrangler uses `.dev.vars` locally.

## Configure Cloudflare

Cloudflare production secrets are managed with `uv run pywrangler secret put`.

Runtime defaults live in `wrangler.toml`.

Key defaults:

- `SYMBOL`: fixed to `XAU/USD`.
- `TIMEFRAMES`: `5min,15min,1h`.
- Cron trigger: every five minutes.
- Market data source: Twelve Data `time_series`.
- Market data cadence: each timeframe is fetched only when that candle should close. With the
  default timeframes this is about 408 Twelve Data calls per day: 288 for `5min`, 96 for `15min`,
  and 24 for `1h`.
- Signal de-duplication: Workers KV namespace bound as `SIGNALS`.
- Latest signal cache: Workers KV stores the latest checked result for each timeframe, so `/signal`
  does not call Twelve Data.
- Structure levels: support/resistance from recent swing pivots, plus projected support/resistance
  trendlines.

## Deploy

```bash
uv run pywrangler deploy
```

Tail logs:

```bash
uv run pywrangler tail aurex
```

Public endpoints:

- `/health`: deployment health check.
- `/signal`: read-only cached latest signal check for every configured timeframe; does not send
  Telegram messages or call Twelve Data.

## Project Layout

- `src/entry.py`: Python Worker entrypoint and Cloudflare runtime adapters.
- `src/aurex/signals.py`: signal lookup and publish orchestration.
- `src/aurex/strategy.py`: XAUUSD signal rules.
- `src/aurex/market_structure.py`: support, resistance, and trendline analysis.
- `src/aurex/market_data.py`: Twelve Data candle fetching.
- `src/aurex/settings.py`: environment and Wrangler variable normalization.
- `src/aurex/telegram.py`: Telegram delivery and message formatting.
- `test/`: pytest coverage for settings, candles, cadence, strategy, and messages.

## Strategy

Default rule set:

- Long bias when price is above EMA200.
- Short bias when price is below EMA200.
- Directional confirmation from EMA20 versus EMA50.
- Trigger when RSI crosses back through 50.
- Stop loss uses `1.5 * ATR`.
- TP1 and TP2 use 1R and 2R.
- Support and resistance use recent swing lows/highs.
- Support and resistance trendlines project recent swing-low/swing-high regression lines to the
  latest candle.

## Development

```bash
uv run pywrangler dev
uv run pytest
uv run ruff check .
```
