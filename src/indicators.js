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

export { atr, ema, rsi };
