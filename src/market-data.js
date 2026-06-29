import { normalizeCandles } from "./candles.js";

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

export { getCandles };
