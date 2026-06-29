function normalizeCandles(values) {
  const deduped = new Map();

  for (const value of values) {
    for (const column of ["datetime", "open", "high", "low", "close"]) {
      if (!(column in value)) {
        throw new Error(`Missing candle column: ${column}`);
      }
    }

    const datetime = parseUtcIso(value.datetime);
    deduped.set(datetime, {
      datetime,
      open: toNumber(value.open, "open"),
      high: toNumber(value.high, "high"),
      low: toNumber(value.low, "low"),
      close: toNumber(value.close, "close"),
    });
  }

  return [...deduped.values()].sort((left, right) => left.datetime.localeCompare(right.datetime));
}

function parseUtcIso(value) {
  const normalized = String(value).replace(" ", "T");
  const withTimezone = /(?:Z|[+-]\d\d:?\d\d)$/.test(normalized) ? normalized : `${normalized}Z`;
  const timestamp = new Date(withTimezone);
  if (Number.isNaN(timestamp.getTime())) {
    throw new Error(`Invalid candle datetime: ${value}`);
  }
  return timestamp.toISOString();
}

function toNumber(value, fieldName) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`Invalid numeric candle column ${fieldName}: ${value}`);
  }
  return number;
}

export { normalizeCandles };
