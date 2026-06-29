import {
  DEFAULT_PIVOT_STRENGTH,
  DEFAULT_STRUCTURE_LOOKBACK,
  DEFAULT_TRENDLINE_PIVOTS,
  XAUUSD_DISPLAY_SYMBOL,
  XAUUSD_SYMBOL,
} from "./constants.js";

function getSettings(env) {
  const symbol = normalizeXauUsdSymbol(getString(env, "SYMBOL", XAUUSD_SYMBOL));
  return {
    symbol,
    timeframes: getTimeframes(env),
    candleLimit: getInteger(env, "CANDLE_LIMIT", 260),
    emaFast: getInteger(env, "EMA_FAST", 20),
    emaSlow: getInteger(env, "EMA_SLOW", 50),
    emaTrend: getInteger(env, "EMA_TREND", 200),
    rsiPeriod: getInteger(env, "RSI_PERIOD", 14),
    atrPeriod: getInteger(env, "ATR_PERIOD", 14),
    atrStopMultiple: getNumber(env, "ATR_STOP_MULTIPLE", 1.5),
    rewardMultiple1: getNumber(env, "REWARD_MULTIPLE_1", 1.0),
    rewardMultiple2: getNumber(env, "REWARD_MULTIPLE_2", 2.0),
    structureLookback: getInteger(env, "STRUCTURE_LOOKBACK", DEFAULT_STRUCTURE_LOOKBACK),
    pivotStrength: getInteger(env, "PIVOT_STRENGTH", DEFAULT_PIVOT_STRENGTH),
    trendlinePivotCount: getInteger(env, "TRENDLINE_PIVOTS", DEFAULT_TRENDLINE_PIVOTS),
  };
}

function getTimeframes(env) {
  const configured = getString(env, "TIMEFRAMES", getString(env, "TIMEFRAME", "15min"));
  const timeframes = configured
    .split(",")
    .map((value) => normalizeTimeframe(value))
    .filter((value, index, values) => values.indexOf(value) === index);

  if (timeframes.length === 0) {
    throw new Error("At least one timeframe is required");
  }
  return timeframes;
}

function normalizeTimeframe(timeframe) {
  const value = timeframe.trim();
  if (/^\d+mn$/i.test(value)) {
    return `${value.slice(0, -2)}min`;
  }
  if (value === "") {
    throw new Error("Blank timeframe is not supported");
  }
  return value;
}

function normalizeXauUsdSymbol(symbol) {
  const value = symbol.trim().toUpperCase();
  if (value === XAUUSD_SYMBOL || value === XAUUSD_DISPLAY_SYMBOL) {
    return XAUUSD_SYMBOL;
  }
  throw new Error(`Aurex only supports gold ${XAUUSD_DISPLAY_SYMBOL}`);
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

export { getSettings, normalizeTimeframe, normalizeXauUsdSymbol };
