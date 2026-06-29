import {
  DEFAULT_PIVOT_STRENGTH,
  DEFAULT_STRUCTURE_LOOKBACK,
  DEFAULT_TRENDLINE_PIVOTS,
} from "./constants.js";

function analyzeMarketStructure(candles, settings = {}) {
  if (candles.length === 0) {
    return emptyMarketStructure();
  }

  const latestIndex = candles.length - 1;
  const latestClose = candles[latestIndex].close;
  const lookback = Math.max(5, settings.structureLookback ?? DEFAULT_STRUCTURE_LOOKBACK);
  const pivotStrength = Math.max(1, settings.pivotStrength ?? DEFAULT_PIVOT_STRENGTH);
  const trendlinePivotCount = Math.max(
    2,
    settings.trendlinePivotCount ?? DEFAULT_TRENDLINE_PIVOTS,
  );
  const startIndex = Math.max(0, candles.length - lookback);
  const recentCandles = candles.slice(startIndex);
  const pivots = findSwingPivots(candles, pivotStrength).filter(
    (pivot) => pivot.index >= startIndex,
  );

  const swingHighs = pivots.filter((pivot) => pivot.type === "high");
  const swingLows = pivots.filter((pivot) => pivot.type === "low");

  return {
    support: nearestLevelBelow(
      latestClose,
      swingLows.map((pivot) => pivot.price),
      recentCandles.map((candle) => candle.low),
    ),
    resistance: nearestLevelAbove(
      latestClose,
      swingHighs.map((pivot) => pivot.price),
      recentCandles.map((candle) => candle.high),
    ),
    supportTrendline: projectedTrendlineValue(swingLows, latestIndex, trendlinePivotCount),
    resistanceTrendline: projectedTrendlineValue(swingHighs, latestIndex, trendlinePivotCount),
  };
}

function emptyMarketStructure() {
  return {
    support: null,
    resistance: null,
    supportTrendline: null,
    resistanceTrendline: null,
  };
}

function findSwingPivots(candles, strength) {
  const pivots = [];

  for (let index = strength; index < candles.length - strength; index += 1) {
    const candle = candles[index];
    let isSwingHigh = true;
    let isSwingLow = true;

    for (let offset = 1; offset <= strength; offset += 1) {
      if (
        candle.high <= candles[index - offset].high ||
        candle.high <= candles[index + offset].high
      ) {
        isSwingHigh = false;
      }
      if (
        candle.low >= candles[index - offset].low ||
        candle.low >= candles[index + offset].low
      ) {
        isSwingLow = false;
      }
    }

    if (isSwingHigh) {
      pivots.push({ type: "high", index, price: candle.high });
    }
    if (isSwingLow) {
      pivots.push({ type: "low", index, price: candle.low });
    }
  }

  return pivots;
}

function nearestLevelBelow(price, preferredLevels, fallbackLevels) {
  const below = preferredLevels.filter((level) => level <= price);
  if (below.length > 0) {
    return Math.max(...below);
  }
  if (fallbackLevels.length === 0) {
    return null;
  }
  return Math.min(...fallbackLevels);
}

function nearestLevelAbove(price, preferredLevels, fallbackLevels) {
  const above = preferredLevels.filter((level) => level >= price);
  if (above.length > 0) {
    return Math.min(...above);
  }
  if (fallbackLevels.length === 0) {
    return null;
  }
  return Math.max(...fallbackLevels);
}

function projectedTrendlineValue(pivots, targetIndex, pivotCount) {
  const selected = pivots.slice(-pivotCount);
  if (selected.length < 2) {
    return null;
  }

  const averageIndex = selected.reduce((total, pivot) => total + pivot.index, 0) / selected.length;
  const averagePrice = selected.reduce((total, pivot) => total + pivot.price, 0) / selected.length;
  const variance = selected.reduce(
    (total, pivot) => total + (pivot.index - averageIndex) ** 2,
    0,
  );
  if (variance === 0) {
    return null;
  }

  const covariance = selected.reduce(
    (total, pivot) => total + (pivot.index - averageIndex) * (pivot.price - averagePrice),
    0,
  );
  const slope = covariance / variance;
  const intercept = averagePrice - slope * averageIndex;
  return slope * targetIndex + intercept;
}

export { analyzeMarketStructure };
