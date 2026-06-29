import { XAUUSD_DISPLAY_SYMBOL } from "./constants.js";
import { formatCandleTime, formatOptionalPrice, formatPrice } from "./format.js";

async function sendTelegramMessage(env, text) {
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: env.TELEGRAM_CHAT_ID,
      text,
    }),
  });
  if (!response.ok) {
    throw new Error(`Telegram HTTP ${response.status}: ${await response.text()}`);
  }
}

function toTelegramMessage(signal) {
  return [
    `${XAUUSD_DISPLAY_SYMBOL} ${signal.direction}`,
    "",
    `Timeframe: ${signal.timeframe}`,
    `Candle: ${signal.candleTimeDisplay ?? formatCandleTime(signal.candleTime)}`,
    "",
    `Entry: ${formatPrice(signal.entry)}`,
    `SL: ${formatPrice(signal.stopLoss)}`,
    `TP1: ${formatPrice(signal.takeProfit1)}`,
    `TP2: ${formatPrice(signal.takeProfit2)}`,
    "",
    ...toMarketStructureMessageLines(signal.marketStructure),
    "",
    `Reason: ${signal.reason}`,
    "Risk: signal only; demo test before live trading.",
  ].join("\n");
}

function toMarketStructureMessageLines(marketStructure = {}) {
  return [
    `Support: ${formatOptionalPrice(marketStructure.support)}`,
    `Resistance: ${formatOptionalPrice(marketStructure.resistance)}`,
    `Support trendline: ${formatOptionalPrice(marketStructure.supportTrendline)}`,
    `Resistance trendline: ${formatOptionalPrice(marketStructure.resistanceTrendline)}`,
  ];
}

export { sendTelegramMessage, toTelegramMessage };
