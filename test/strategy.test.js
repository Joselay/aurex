import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  analyzeMarketStructure,
  formatCandleTime,
  generateSignal,
  getSettings,
  normalizeCandles,
  normalizeXauUsdSymbol,
  toTelegramMessage,
} from "../src/index.js";
import { sendTelegramMessage } from "../src/telegram.js";

function candlesFromCloses(closes) {
  const start = Date.UTC(2026, 0, 1, 0, 0, 0);
  return closes.map((close, index) => ({
    datetime: new Date(start + index * 15 * 60 * 1000).toISOString(),
    open: close,
    high: close + 1,
    low: close - 1,
    close,
  }));
}

function buySignalCloses() {
  const closes = Array.from({ length: 220 }, (_, index) => 2000 + index * 0.1);
  closes.splice(
    -15,
    15,
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
  );
  return closes;
}

function candlesFromHighLow(highs, lows, closes = []) {
  const start = Date.UTC(2026, 0, 1, 0, 0, 0);
  return highs.map((high, index) => ({
    datetime: new Date(start + index * 15 * 60 * 1000).toISOString(),
    open: closes[index] ?? (high + lows[index]) / 2,
    high,
    low: lows[index],
    close: closes[index] ?? (high + lows[index]) / 2,
  }));
}

describe("market settings", () => {
  it("normalizes supported XAUUSD aliases", () => {
    assert.equal(normalizeXauUsdSymbol("XAU/USD"), "XAU/USD");
    assert.equal(normalizeXauUsdSymbol("xauusd"), "XAU/USD");
  });

  it("rejects non-gold symbols", () => {
    assert.throws(() => normalizeXauUsdSymbol("BTC/USD"), /only supports gold XAUUSD/);
    assert.throws(() => getSettings({ SYMBOL: "ETH/USD" }), /only supports gold XAUUSD/);
  });

  it("normalizes and deduplicates configured timeframes", () => {
    const settings = getSettings({ TIMEFRAMES: "5mn,15min,5min,1h" });

    assert.deepEqual(settings.timeframes, ["5min", "15min", "1h"]);
  });
});

describe("candles", () => {
  it("normalizes, sorts, and deduplicates candle rows", () => {
    const candles = normalizeCandles([
      { datetime: "2026-01-01 00:15:00", open: "2", high: "3", low: "1", close: "2" },
      { datetime: "2026-01-01 00:00:00", open: "1", high: "2", low: "0", close: "1" },
      { datetime: "2026-01-01 00:15:00", open: "4", high: "5", low: "3", close: "4" },
    ]);

    assert.equal(candles.length, 2);
    assert.equal(candles[0].datetime, "2026-01-01T00:00:00.000Z");
    assert.equal(candles[1].close, 4);
  });

  it("formats candle time for human-facing messages", () => {
    assert.equal(formatCandleTime("2026-01-01T00:15:00.000Z"), "2026-01-01 00:15 UTC");
  });
});

describe("strategy", () => {
  it("calculates support, resistance, and trendline levels from recent swings", () => {
    const marketStructure = analyzeMarketStructure(
      candlesFromHighLow(
        [10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17],
        [5, 7, 6, 8, 7, 9, 8, 10, 9, 11, 10, 12],
        [7, 10, 8, 11, 9, 12, 10, 13, 11, 14, 12, 12.5],
      ),
      { structureLookback: 12, pivotStrength: 1, trendlinePivotCount: 6 },
    );

    assert.equal(marketStructure.support, 10);
    assert.equal(marketStructure.resistance, 13);
    assert.equal(marketStructure.supportTrendline, 10.5);
    assert.equal(marketStructure.resistanceTrendline, 17);
  });

  it("generates a buy signal when trend and RSI reclaim align", () => {
    const settings = { ...getSettings({}), timeframe: "15min" };
    const signal = generateSignal(candlesFromCloses(buySignalCloses()), settings);

    assert.ok(signal);
    assert.equal(signal.direction, "BUY");
    assert.equal(signal.candleTimeDisplay, "2026-01-03 06:45 UTC");
    assert.ok(signal.marketStructure);
    assert.equal(typeof signal.marketStructure.support, "number");
    assert.equal(typeof signal.marketStructure.resistance, "number");
    assert.match(signal.reason, /^15min trend above EMA200/);
    assert.ok(signal.stopLoss < signal.entry);
    assert.ok(signal.entry < signal.takeProfit1);
    assert.ok(signal.takeProfit1 < signal.takeProfit2);
  });

  it("returns null without a trigger", () => {
    const settings = { ...getSettings({}), timeframe: "15min" };
    const closes = Array.from({ length: 220 }, (_, index) => 2000 + index * 0.2);

    assert.equal(generateSignal(candlesFromCloses(closes), settings), null);
  });

  it("formats Telegram messages from generated signals", () => {
    const settings = { ...getSettings({}), timeframe: "1h" };
    const signal = generateSignal(candlesFromCloses(buySignalCloses()), settings);

    assert.ok(signal);
    const message = toTelegramMessage(signal);

    assert.match(message, /^🟢 <b>XAUUSD BUY SIGNAL<\/b>\n⏱ <b>Timeframe:<\/b> 1h/m);
    assert.match(message, /\n🕯 <b>Candle:<\/b> 2026-01-03 06:45 UTC\n/);
    assert.match(message, /\n📍 <b>Trade Plan<\/b>\n/);
    assert.match(message, /\n🎯 Entry: <code>\d+\.\d{2}<\/code>\n/);
    assert.match(message, /\n🟢 Support: <code>\d+\.\d{2}<\/code>\n/);
    assert.match(message, /\n📉 Resistance trendline: <code>(?:-|\d+\.\d{2})<\/code>\n/);
    assert.match(message, /\n⚠️ <b>Risk:<\/b> Signal only\. Demo test before live trading\.$/);
  });

  it("escapes dynamic Telegram message content for HTML parse mode", () => {
    const message = toTelegramMessage({
      symbol: "XAU/USD",
      timeframe: "bad <frame>",
      direction: "BUY",
      candleTime: "2026-01-01T00:15:00.000Z",
      entry: 2000,
      stopLoss: 1990,
      takeProfit1: 2010,
      takeProfit2: 2020,
      marketStructure: {},
      reason: "EMA20 > EMA50 & RSI < 70",
    });

    assert.match(message, /bad &lt;frame&gt;/);
    assert.match(message, /EMA20 &gt; EMA50 &amp; RSI &lt; 70/);
  });
});

describe("telegram delivery", () => {
  it("sends messages with Telegram HTML parse mode", async () => {
    const originalFetch = globalThis.fetch;
    let requestBody;

    globalThis.fetch = async (_url, init) => {
      requestBody = JSON.parse(init.body);
      return new Response("{}", { status: 200 });
    };

    try {
      await sendTelegramMessage(
        { TELEGRAM_BOT_TOKEN: "token", TELEGRAM_CHAT_ID: "chat" },
        "<b>XAUUSD BUY SIGNAL</b>",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }

    assert.equal(requestBody.chat_id, "chat");
    assert.equal(requestBody.text, "<b>XAUUSD BUY SIGNAL</b>");
    assert.equal(requestBody.parse_mode, "HTML");
    assert.equal(requestBody.disable_web_page_preview, true);
  });
});
