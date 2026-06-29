# Aurex

Cloudflare Worker that watches XAUUSD candles, generates rule-based signals, and sends new signals
to Telegram.

Aurex is intentionally XAUUSD-only. It does not accept crypto, equities, or other forex pairs.

This is a signal bot, not an auto-trading bot. Demo test and backtest before risking live money.

## Setup

```bash
npm install
cp .dev.vars.example .dev.vars
```

Edit `.dev.vars` for local Wrangler development:

- `TELEGRAM_BOT_TOKEN`: token from BotFather.
- `TELEGRAM_CHAT_ID`: your group chat ID.
- `TWELVEDATA_API_KEY`: Twelve Data API key.

For a Telegram group, add the bot to the group, send any message in that group, then open:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

Use the `message.chat.id` value for `TELEGRAM_CHAT_ID`. Group chat IDs are usually negative, and
supergroup IDs usually start with `-100`.

## Configure Cloudflare

Set production secrets with Wrangler:

```bash
npx wrangler secret put TELEGRAM_BOT_TOKEN --config cloudflare-worker/wrangler.toml
npx wrangler secret put TELEGRAM_CHAT_ID --config cloudflare-worker/wrangler.toml
npx wrangler secret put TWELVEDATA_API_KEY --config cloudflare-worker/wrangler.toml
```

Runtime defaults live in `cloudflare-worker/wrangler.toml`.

Key defaults:

- `SYMBOL`: fixed to `XAU/USD`.
- `TIMEFRAMES`: `5min,15min,1h`.
- Cron trigger: every five minutes.
- Signal de-duplication: Workers KV namespace bound as `SIGNALS`.

## Deploy

```bash
npm run deploy:cloudflare
```

Tail logs:

```bash
npm run tail:cloudflare
```

Public endpoints:

- `/health`: deployment health check.
- `/signal`: read-only latest signal check for every configured timeframe; does not send Telegram
  messages.

## Strategy

Default rule set:

- Long bias when price is above EMA200.
- Short bias when price is below EMA200.
- Directional confirmation from EMA20 versus EMA50.
- Trigger when RSI crosses back through 50.
- Stop loss uses `1.5 * ATR`.
- TP1 and TP2 use 1R and 2R.

## Development

```bash
npm test
npm run check:cloudflare
```
