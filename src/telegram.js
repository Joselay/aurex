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
      parse_mode: "HTML",
      disable_web_page_preview: true,
    }),
  });
  if (!response.ok) {
    throw new Error(`Telegram HTTP ${response.status}: ${await response.text()}`);
  }
}

function toTelegramMessage(signal) {
  const directionLabel = toDirectionLabel(signal.direction);
  const candleTime = signal.candleTimeDisplay ?? formatCandleTime(signal.candleTime);

  return [
    `${directionLabel} <b>${XAUUSD_DISPLAY_SYMBOL} ${escapeHtml(signal.direction)} SIGNAL</b>`,
    `⏱ <b>Timeframe:</b> ${escapeHtml(signal.timeframe)}`,
    `🕯 <b>Candle:</b> ${escapeHtml(candleTime)}`,
    "",
    "📍 <b>Trade Plan</b>",
    `🎯 Entry: <code>${formatPrice(signal.entry)}</code>`,
    `🛑 Stop Loss: <code>${formatPrice(signal.stopLoss)}</code>`,
    `✅ TP1: <code>${formatPrice(signal.takeProfit1)}</code>`,
    `🏁 TP2: <code>${formatPrice(signal.takeProfit2)}</code>`,
    "",
    "🧱 <b>Market Structure</b>",
    ...toMarketStructureMessageLines(signal.marketStructure),
    "",
    `🧠 <b>Reason:</b> ${escapeHtml(signal.reason)}`,
    "⚠️ <b>Risk:</b> Signal only. Demo test before live trading.",
  ].join("\n");
}

function toMarketStructureMessageLines(marketStructure = {}) {
  return [
    `🟢 Support: <code>${formatOptionalPrice(marketStructure.support)}</code>`,
    `🔴 Resistance: <code>${formatOptionalPrice(marketStructure.resistance)}</code>`,
    `📈 Support trendline: <code>${formatOptionalPrice(marketStructure.supportTrendline)}</code>`,
    `📉 Resistance trendline: <code>${formatOptionalPrice(
      marketStructure.resistanceTrendline,
    )}</code>`,
  ];
}

function toDirectionLabel(direction) {
  return direction === "BUY" ? "🟢" : "🔴";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export { sendTelegramMessage, toTelegramMessage };
