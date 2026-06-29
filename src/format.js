function formatPrice(value) {
  return value.toFixed(2);
}

function formatOptionalPrice(value) {
  return Number.isFinite(value) ? formatPrice(value) : "-";
}

function formatCandleTime(value) {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    throw new Error(`Invalid candle datetime: ${value}`);
  }

  const year = timestamp.getUTCFullYear();
  const month = pad2(timestamp.getUTCMonth() + 1);
  const day = pad2(timestamp.getUTCDate());
  const hour = pad2(timestamp.getUTCHours());
  const minute = pad2(timestamp.getUTCMinutes());
  return `${year}-${month}-${day} ${hour}:${minute} UTC`;
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

export { formatCandleTime, formatOptionalPrice, formatPrice };
