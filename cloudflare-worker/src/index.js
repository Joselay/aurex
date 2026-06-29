const XAUUSD_SYMBOL = "XAU/USD";
const XAUUSD_DISPLAY_SYMBOL = "XAUUSD";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return jsonResponse({ ok: true, service: "lumiere", runtime: "cloudflare-worker" });
    }

    if (url.pathname === "/signal") {
      const signal = await latestSignal(env);
      return jsonResponse({ signal });
    }

    return jsonResponse({
      service: "lumiere",
      symbol: XAUUSD_DISPLAY_SYMBOL,
      timeframe: getString(env, "TIMEFRAME", "15min"),
    });
  },

  async scheduled(_event, env, ctx) {
    ctx.waitUntil(publishNewSignal(env, ctx));
  },
};

async function publishNewSignal(env, ctx) {
  const signal = await latestSignal(env);
  if (signal === null) {
    console.log("No signal");
    return null;
  }

  const existing = await env.SIGNALS.get(signal.key);
  if (existing !== null) {
    console.log(`Signal already sent: ${signal.key}`);
    return signal;
  }

  await sendTelegramMessage(env, toTelegramMessage(signal));
  await env.SIGNALS.put(signal.key, JSON.stringify(signal));
  console.log(`Published signal: ${signal.key}`);
  return signal;
}

async function latestSignal(env) {
  const settings = getSettings(env);
  const candles = await getCandles(env, settings);
  return generateSignal(candles, settings);
}

async function getCandles(env, settings) {
  const url = new URL("https://api.twelvedata.com/time_series");
  url.searchParams.set("symbol", settings.symbol);
  url.searchParams.set("interval", settings.timeframe);
  url.searchParams.set("outputsize", String(settings.candleLimit));
  url.searchParams.set("apikey", env.TWELVEDATA_API_KEY);
  url.searchParams.set("format", "JSON");

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Twelve Data HTTP ${response.status}`);
  }

  const payload = await response.json();
  if (payload.status === "error") {
    throw new Error(payload.message || "Twelve Data returned an error");
  }
  if (!Array.isArray(payload.values) || payload.values.length === 0) {
    throw new Error("Twelve Data returned no candle values");
  }

  return normalizeCandles(payload.values);
}

function generateSignal(candles, settings) {
  const minimumCandles =
    Math.max(settings.emaTrend, settings.emaSlow, settings.rsiPeriod, settings.atrPeriod) + 2;
  if (candles.length < minimumCandles) {
    return null;
  }

  const closes = candles.map((candle) => candle.close);
  const highs = candles.map((candle) => candle.high);
  const lows = candles.map((candle) => candle.low);

  const emaFast = ema(closes, settings.emaFast);
  const emaSlow = ema(closes, settings.emaSlow);
  const emaTrend = ema(closes, settings.emaTrend);
  const rsiValues = rsi(closes, settings.rsiPeriod);
  const atrValues = atr(highs, lows, closes, settings.atrPeriod);

  const latestIndex = candles.length - 1;
  const previousIndex = candles.length - 2;
  const latest = candles[latestIndex];
  const riskDistance = atrValues[latestIndex] * settings.atrStopMultiple;

  if (
    !Number.isFinite(emaFast[latestIndex]) ||
    !Number.isFinite(emaSlow[latestIndex]) ||
    !Number.isFinite(emaTrend[latestIndex]) ||
    !Number.isFinite(rsiValues[latestIndex]) ||
    !Number.isFinite(atrValues[latestIndex]) ||
    !Number.isFinite(rsiValues[previousIndex]) ||
    !Number.isFinite(riskDistance) ||
    riskDistance <= 0
  ) {
    return null;
  }

  const buySetup =
    latest.close > emaTrend[latestIndex] &&
    emaFast[latestIndex] > emaSlow[latestIndex] &&
    latest.close > emaFast[latestIndex] &&
    rsiValues[previousIndex] <= 50 &&
    rsiValues[latestIndex] > 50;

  const sellSetup =
    latest.close < emaTrend[latestIndex] &&
    emaFast[latestIndex] < emaSlow[latestIndex] &&
    latest.close < emaFast[latestIndex] &&
    rsiValues[previousIndex] >= 50 &&
    rsiValues[latestIndex] < 50;

  if (buySetup) {
    return buildSignal(settings, latest, "BUY", riskDistance);
  }
  if (sellSetup) {
    return buildSignal(settings, latest, "SELL", riskDistance);
  }
  return null;
}

function buildSignal(settings, candle, direction, riskDistance) {
  const entry = candle.close;
  const isBuy = direction === "BUY";
  const stopLoss = isBuy ? entry - riskDistance : entry + riskDistance;
  const takeProfit1 = isBuy
    ? entry + riskDistance * settings.rewardMultiple1
    : entry - riskDistance * settings.rewardMultiple1;
  const takeProfit2 = isBuy
    ? entry + riskDistance * settings.rewardMultiple2
    : entry - riskDistance * settings.rewardMultiple2;
  const relation = isBuy ? ["above", "above", "reclaimed"] : ["below", "below", "lost"];
  const reason = `${settings.timeframe} trend ${relation[0]} EMA${settings.emaTrend}, EMA${settings.emaFast} ${relation[1]} EMA${settings.emaSlow}, RSI ${relation[2]} 50.`;

  const signal = {
    symbol: settings.symbol,
    timeframe: settings.timeframe,
    direction,
    candleTime: candle.datetime,
    entry,
    stopLoss,
    takeProfit1,
    takeProfit2,
    reason,
  };
  signal.key = `${signal.symbol}:${signal.timeframe}:${signal.candleTime}:${signal.direction}`;
  return signal;
}

function normalizeCandles(values) {
  const deduped = new Map();

  for (const value of values) {
    for (const column of ["datetime", "open", "high", "low", "close"]) {
      if (!(column in value)) {
        throw new Error(`Missing candle column: ${column}`);
      }
    }

    const datetime = parseUtcIso(value.datetime);
    deduped.set(datetime, {
      datetime,
      open: toNumber(value.open, "open"),
      high: toNumber(value.high, "high"),
      low: toNumber(value.low, "low"),
      close: toNumber(value.close, "close"),
    });
  }

  return [...deduped.values()].sort((left, right) => left.datetime.localeCompare(right.datetime));
}

function ema(values, window) {
  const output = Array(values.length).fill(Number.NaN);
  if (values.length < window) {
    return output;
  }

  const alpha = 2 / (window + 1);
  let current = values[0];
  for (let index = 1; index < values.length; index += 1) {
    current = values[index] * alpha + current * (1 - alpha);
    if (index >= window - 1) {
      output[index] = current;
    }
  }
  return output;
}

function rsi(values, window) {
  const output = Array(values.length).fill(Number.NaN);
  if (values.length <= window) {
    return output;
  }

  let averageGain = 0;
  let averageLoss = 0;
  for (let index = 1; index <= window; index += 1) {
    const change = values[index] - values[index - 1];
    averageGain += Math.max(change, 0);
    averageLoss += Math.max(-change, 0);
  }
  averageGain /= window;
  averageLoss /= window;
  output[window] = rsiFromAverages(averageGain, averageLoss);

  for (let index = window + 1; index < values.length; index += 1) {
    const change = values[index] - values[index - 1];
    averageGain = (averageGain * (window - 1) + Math.max(change, 0)) / window;
    averageLoss = (averageLoss * (window - 1) + Math.max(-change, 0)) / window;
    output[index] = rsiFromAverages(averageGain, averageLoss);
  }
  return output;
}

function rsiFromAverages(averageGain, averageLoss) {
  if (averageLoss === 0) {
    return 100;
  }
  const relativeStrength = averageGain / averageLoss;
  return 100 - 100 / (1 + relativeStrength);
}

function atr(highs, lows, closes, window) {
  const output = Array(closes.length).fill(Number.NaN);
  if (closes.length < window) {
    return output;
  }

  const trueRanges = closes.map((close, index) => {
    if (index === 0) {
      return highs[index] - lows[index];
    }
    return Math.max(
      highs[index] - lows[index],
      Math.abs(highs[index] - closes[index - 1]),
      Math.abs(lows[index] - closes[index - 1]),
    );
  });

  let current = trueRanges.slice(0, window).reduce((total, value) => total + value, 0) / window;
  output[window - 1] = current;
  for (let index = window; index < trueRanges.length; index += 1) {
    current = (current * (window - 1) + trueRanges[index]) / window;
    output[index] = current;
  }
  return output;
}

async function sendTelegramMessage(env, text) {
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: env.TELEGRAM_CHAT_ID,
      text,
    }),
  });
  if (!response.ok) {
    throw new Error(`Telegram HTTP ${response.status}: ${await response.text()}`);
  }
}

function toTelegramMessage(signal) {
  return [
    `${XAUUSD_DISPLAY_SYMBOL} ${signal.direction}`,
    "",
    `Timeframe: ${signal.timeframe}`,
    `Candle: ${signal.candleTime}`,
    "",
    `Entry: ${formatPrice(signal.entry)}`,
    `SL: ${formatPrice(signal.stopLoss)}`,
    `TP1: ${formatPrice(signal.takeProfit1)}`,
    `TP2: ${formatPrice(signal.takeProfit2)}`,
    "",
    `Reason: ${signal.reason}`,
    "Risk: signal only; demo test before live trading.",
  ].join("\n");
}

function getSettings(env) {
  const symbol = normalizeXauUsdSymbol(getString(env, "SYMBOL", XAUUSD_SYMBOL));
  return {
    symbol,
    timeframe: getString(env, "TIMEFRAME", "15min"),
    candleLimit: getInteger(env, "CANDLE_LIMIT", 260),
    emaFast: getInteger(env, "EMA_FAST", 20),
    emaSlow: getInteger(env, "EMA_SLOW", 50),
    emaTrend: getInteger(env, "EMA_TREND", 200),
    rsiPeriod: getInteger(env, "RSI_PERIOD", 14),
    atrPeriod: getInteger(env, "ATR_PERIOD", 14),
    atrStopMultiple: getNumber(env, "ATR_STOP_MULTIPLE", 1.5),
    rewardMultiple1: getNumber(env, "REWARD_MULTIPLE_1", 1.0),
    rewardMultiple2: getNumber(env, "REWARD_MULTIPLE_2", 2.0),
  };
}

function normalizeXauUsdSymbol(symbol) {
  const value = symbol.trim().toUpperCase();
  if (value === XAUUSD_SYMBOL || value === XAUUSD_DISPLAY_SYMBOL) {
    return XAUUSD_SYMBOL;
  }
  throw new Error(`Lumiere only supports gold ${XAUUSD_DISPLAY_SYMBOL}`);
}

function parseUtcIso(value) {
  const normalized = String(value).replace(" ", "T");
  const withTimezone = /(?:Z|[+-]\d\d:?\d\d)$/.test(normalized) ? normalized : `${normalized}Z`;
  const timestamp = new Date(withTimezone);
  if (Number.isNaN(timestamp.getTime())) {
    throw new Error(`Invalid candle datetime: ${value}`);
  }
  return timestamp.toISOString();
}

function toNumber(value, fieldName) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`Invalid numeric candle column ${fieldName}: ${value}`);
  }
  return number;
}

function getString(env, key, fallback) {
  const value = env[key];
  return value === undefined || value === null || value === "" ? fallback : String(value);
}

function getInteger(env, key, fallback) {
  const value = Number.parseInt(getString(env, key, String(fallback)), 10);
  if (!Number.isInteger(value)) {
    throw new Error(`Invalid integer setting: ${key}`);
  }
  return value;
}

function getNumber(env, key, fallback) {
  const value = Number(getString(env, key, String(fallback)));
  if (!Number.isFinite(value)) {
    throw new Error(`Invalid numeric setting: ${key}`);
  }
  return value;
}

function formatPrice(value) {
  return value.toFixed(2);
}

function jsonResponse(value, init = {}) {
  return new Response(JSON.stringify(value, null, 2), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...init.headers,
    },
  });
}
