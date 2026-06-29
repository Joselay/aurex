# XAUUSD Telegram Signal Bot

Python bot that watches XAUUSD candles, generates rule-based signals, and sends them to Telegram.

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

To find your chat ID, message your bot once, then open:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

For a channel, add the bot as an admin and use the channel ID or username.

## Run

Check once and exit:

```bash
uv run xauusd-signal-bot --once
```

Run the Telegram command bot and scheduled signal checks:

```bash
uv run xauusd-signal-bot
```

Telegram commands:

- `/start`: confirm the bot is online.
- `/status`: show the watched symbol and timeframe.
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
