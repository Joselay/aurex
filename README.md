# Lumiere

Python bot that watches XAUUSD candles, generates rule-based signals, and sends them to Telegram.

Lumiere is intentionally XAUUSD-only. It does not accept crypto, equities, or other forex pairs.

This is a signal bot, not an auto-trading bot. Demo test and backtest before risking live money.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env`:

- `TELEGRAM_BOT_TOKEN`: token from BotFather.
- `TELEGRAM_CHAT_ID`: your user, group, or channel chat ID.
- `TWELVEDATA_API_KEY`: Twelve Data API key.

The market is fixed to gold XAUUSD. Existing `.env` files may keep `SYMBOL=XAU/USD`, but any other
symbol is rejected at startup.

To find your chat ID, message your bot once, then open:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

For a channel, add the bot as an admin and use the channel ID or username.

## Run

Check once and exit:

```bash
uv run lumiere --once
```

Run the Telegram command bot and scheduled signal checks:

```bash
uv run lumiere
```

Telegram commands:

- `/start`: confirm the bot is online.
- `/status`: show the watched XAUUSD timeframe.
- `/signal`: force a fresh signal check.

## Strategy

Default rule set:

- Long bias when price is above EMA200.
- Short bias when price is below EMA200.
- Directional confirmation from EMA20 versus EMA50.
- Trigger when RSI crosses back through 50.
- Stop loss uses `1.5 * ATR`.
- TP1 and TP2 use 1R and 2R.

Signals are de-duplicated in SQLite at `data/signals.sqlite3`.

## Development

```bash
uv run pytest
uv run ruff check .
```

## Cloudflare Worker

The `cloudflare-worker/` deployment runs the same XAUUSD signal rules on a Cloudflare Worker Cron
Trigger every five minutes. It uses Workers KV to de-duplicate sent signals.

Deploy with:

```bash
npx wrangler deploy --config cloudflare-worker/wrangler.toml
```

Required Cloudflare secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TWELVEDATA_API_KEY`

Public endpoints:

- `/health`: deployment health check.
- `/signal`: read-only latest signal check; does not send Telegram messages.
