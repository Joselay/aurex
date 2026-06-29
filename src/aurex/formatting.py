from datetime import datetime


def format_price(value):
    return f"{value:.2f}"


def format_optional_price(value):
    return format_price(value) if isinstance(value, (int, float)) else "-"


def format_candle_time(value):
    timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return timestamp.strftime("%Y-%m-%d %H:%M UTC")

