from html import escape

from aurex.constants import XAUUSD_DISPLAY_SYMBOL
from aurex.formatting import format_candle_time, format_optional_price, format_price


def to_telegram_message(signal):
    direction_label = "🟢" if signal["direction"] == "BUY" else "🔴"
    candle_time = signal.get("candleTimeDisplay") or format_candle_time(signal["candleTime"])
    title = f"{XAUUSD_DISPLAY_SYMBOL} {escape(str(signal['direction']))} SIGNAL"

    lines = [
        f"{direction_label} <b>{title}</b>",
        f"⏱ <b>Timeframe:</b> {escape(str(signal['timeframe']))}",
        f"🕯 <b>Candle:</b> {escape(candle_time)}",
        "",
        "📍 <b>Trade Plan</b>",
        f"🎯 Entry: <code>{format_price(signal['entry'])}</code>",
        f"🛑 Stop Loss: <code>{format_price(signal['stopLoss'])}</code>",
        f"✅ TP1: <code>{format_price(signal['takeProfit1'])}</code>",
        f"🏁 TP2: <code>{format_price(signal['takeProfit2'])}</code>",
        "",
        "🧱 <b>Market Structure</b>",
        *to_market_structure_message_lines(signal.get("marketStructure") or {}),
        "",
        f"🧠 <b>Reason:</b> {escape(str(signal['reason']))}",
        "⚠️ <b>Risk:</b> Signal only. Demo test before live trading.",
    ]
    return "\n".join(lines)


def to_market_structure_message_lines(market_structure):
    support_trendline = format_optional_price(market_structure.get("supportTrendline"))
    resistance_trendline = format_optional_price(market_structure.get("resistanceTrendline"))

    return [
        f"🟢 Support: <code>{format_optional_price(market_structure.get('support'))}</code>",
        f"🔴 Resistance: <code>{format_optional_price(market_structure.get('resistance'))}</code>",
        f"📈 Support trendline: <code>{support_trendline}</code>",
        f"📉 Resistance trendline: <code>{resistance_trendline}</code>",
    ]
