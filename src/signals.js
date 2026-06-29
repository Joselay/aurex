import { getSettings } from "./settings.js";
import { getCandles } from "./market-data.js";
import { generateSignal } from "./strategy.js";
import { sendTelegramMessage, toTelegramMessage } from "./telegram.js";

const LATEST_SIGNAL_PREFIX = "latest:";

async function publishNewSignals(env, options = {}) {
  const signals = await refreshDueSignals(env, options);
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
  return readCachedSignals(env, settings.timeframes);
}

async function refreshDueSignals(env, options = {}) {
  const settings = getSettings(env);
  const runDate = toRunDate(options.scheduledTime);
  const signals = [];
  const dueTimeframes = settings.timeframes.filter((timeframe) =>
    shouldPollTimeframe(timeframe, runDate),
  );

  for (const timeframe of dueTimeframes) {
    const timeframeSettings = { ...settings, timeframe };
    const candles = await getCandles(env, timeframeSettings);
    const signal = generateSignal(candles, timeframeSettings);
    await writeCachedSignal(env, timeframe, signal, runDate);
    if (signal !== null) {
      signals.push(signal);
    }
  }

  return signals;
}

async function readCachedSignals(env, timeframes) {
  const signals = [];
  for (const timeframe of timeframes) {
    const value = await env.SIGNALS.get(latestSignalKey(timeframe));
    if (value === null) {
      continue;
    }

    const cached = JSON.parse(value);
    if (cached.signal !== null) {
      signals.push(cached.signal);
    }
  }
  return signals;
}

async function writeCachedSignal(env, timeframe, signal, runDate) {
  await env.SIGNALS.put(
    latestSignalKey(timeframe),
    JSON.stringify({
      timeframe,
      checkedAt: runDate.toISOString(),
      signal,
    }),
  );
}

function latestSignalKey(timeframe) {
  return `${LATEST_SIGNAL_PREFIX}${timeframe}`;
}

function shouldPollTimeframe(timeframe, runDate) {
  const intervalMinutes = timeframeIntervalMinutes(timeframe);
  if (intervalMinutes === null) {
    return true;
  }
  return Math.floor(runDate.getTime() / 60000) % intervalMinutes === 0;
}

function timeframeIntervalMinutes(timeframe) {
  const value = String(timeframe).trim().toLowerCase();
  const match = value.match(/^(\d+)(min|h|day|week)$/);
  if (match === null) {
    return null;
  }

  const amount = Number.parseInt(match[1], 10);
  const unit = match[2];
  const unitMinutes = {
    min: 1,
    h: 60,
    day: 1440,
    week: 10080,
  }[unit];

  return amount > 0 ? amount * unitMinutes : null;
}

function toRunDate(scheduledTime) {
  if (scheduledTime === undefined || scheduledTime === null) {
    return new Date();
  }

  const numericTime = Number(scheduledTime);
  const date =
    scheduledTime instanceof Date
      ? scheduledTime
      : new Date(Number.isFinite(numericTime) ? numericTime : scheduledTime);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid scheduled time: ${scheduledTime}`);
  }
  return date;
}

export {
  latestSignalKey,
  latestSignals,
  publishNewSignals,
  refreshDueSignals,
  shouldPollTimeframe,
  timeframeIntervalMinutes,
};
