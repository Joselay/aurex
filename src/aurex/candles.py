from datetime import UTC, datetime


def normalize_candles(values):
    deduped = {}

    for value in values:
        for column in ("datetime", "open", "high", "low", "close"):
            if column not in value:
                raise ValueError(f"Missing candle column: {column}")

        candle_time = parse_utc_iso(value["datetime"])
        deduped[candle_time] = {
            "datetime": candle_time,
            "open": to_number(value["open"], "open"),
            "high": to_number(value["high"], "high"),
            "low": to_number(value["low"], "low"),
            "close": to_number(value["close"], "close"),
        }

    return [deduped[key] for key in sorted(deduped)]


def parse_utc_iso(value):
    normalized = str(value).replace(" ", "T")
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    elif not _has_timezone(normalized):
        normalized = f"{normalized}+00:00"

    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid candle datetime: {value}") from exc

    return to_utc_iso(timestamp)


def to_utc_iso(timestamp):
    utc_timestamp = timestamp.astimezone(UTC)
    return utc_timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def to_number(value, field_name):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric candle column {field_name}: {value}") from exc
    if not _is_finite(number):
        raise ValueError(f"Invalid numeric candle column {field_name}: {value}")
    return number


def _has_timezone(value):
    if len(value) < 6:
        return False
    suffix = value[-6:]
    return suffix[0] in ("+", "-") and suffix[3] == ":"


def _is_finite(value):
    return value not in (float("inf"), float("-inf")) and value == value

