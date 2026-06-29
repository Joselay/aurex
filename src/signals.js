import { getSettings } from "./settings.js";
import { getCandles } from "./market-data.js";
import { generateSignal } from "./strategy.js";
import { sendTelegramMessage, toTelegramMessage } from "./telegram.js";

async function publishNewSignals(env) {
  const signals = await latestSignals(env);
  if (signals.length === 0) {
    console.log("No signal");
    return [];
  }

  const published = [];
  for (const signal of signals) {
    const existing = await env.SIGNALS.get(signal.key);
    if (existing !== null) {
      console.log(`Signal already sent: ${signal.key}`);
      continue;
    }

    await sendTelegramMessage(env, toTelegramMessage(signal));
    await env.SIGNALS.put(signal.key, JSON.stringify(signal));
    published.push(signal);
    console.log(`Published signal: ${signal.key}`);
  }

  return published;
}

async function latestSignals(env) {
  const settings = getSettings(env);
  const signals = [];

  for (const timeframe of settings.timeframes) {
    const timeframeSettings = { ...settings, timeframe };
    const candles = await getCandles(env, timeframeSettings);
    const signal = generateSignal(candles, timeframeSettings);
    if (signal !== null) {
      signals.push(signal);
    }
  }

  return signals;
}

export { latestSignals, publishNewSignals };
