import { XAUUSD_DISPLAY_SYMBOL } from "./constants.js";
import { jsonResponse } from "./http.js";
import { getSettings } from "./settings.js";
import { latestSignals, publishNewSignals } from "./signals.js";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return jsonResponse({ ok: true, service: "aurex", runtime: "cloudflare-worker" });
    }

    if (url.pathname === "/signal") {
      const signals = await latestSignals(env);
      return jsonResponse({ signals, signal: signals[0] ?? null });
    }

    const settings = getSettings(env);
    return jsonResponse({
      service: "aurex",
      symbol: XAUUSD_DISPLAY_SYMBOL,
      timeframes: settings.timeframes,
    });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(publishNewSignals(env, { scheduledTime: event.scheduledTime }));
  },
};

export { normalizeCandles } from "./candles.js";
export { formatCandleTime } from "./format.js";
export { atr, ema, rsi } from "./indicators.js";
export { analyzeMarketStructure } from "./market-structure.js";
export { generateSignal } from "./strategy.js";
export { getSettings, normalizeTimeframe, normalizeXauUsdSymbol } from "./settings.js";
export { toTelegramMessage } from "./telegram.js";
