import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  generateSignal,
  getSettings,
  normalizeCandles,
  normalizeXauUsdSymbol,
  toTelegramMessage,
} from "../src/index.js";

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
});

describe("strategy", () => {
  it("generates a buy signal when trend and RSI reclaim align", () => {
    const settings = { ...getSettings({}), timeframe: "15min" };
    const signal = generateSignal(candlesFromCloses(buySignalCloses()), settings);

    assert.ok(signal);
    assert.equal(signal.direction, "BUY");
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
    assert.match(toTelegramMessage(signal), /^XAUUSD BUY\n\nTimeframe: 1h/m);
  });
});
