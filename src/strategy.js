import { formatCandleTime } from "./format.js";
import { atr, ema, rsi } from "./indicators.js";
import { analyzeMarketStructure } from "./market-structure.js";

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

  const marketStructure = analyzeMarketStructure(candles, settings);

  if (buySetup) {
    return buildSignal(settings, latest, "BUY", riskDistance, marketStructure);
  }
  if (sellSetup) {
    return buildSignal(settings, latest, "SELL", riskDistance, marketStructure);
  }
  return null;
}

function buildSignal(settings, candle, direction, riskDistance, marketStructure) {
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
    candleTimeDisplay: formatCandleTime(candle.datetime),
    entry,
    stopLoss,
    takeProfit1,
    takeProfit2,
    marketStructure,
    reason,
  };
  signal.key = `${signal.symbol}:${signal.timeframe}:${signal.candleTime}:${signal.direction}`;
  return signal;
}

export { generateSignal };
