XAUUSD_SYMBOL = "XAU/USD"
XAUUSD_DISPLAY_SYMBOL = "XAUUSD"

_XAUUSD_ALIASES = {XAUUSD_SYMBOL, XAUUSD_DISPLAY_SYMBOL}


def normalize_xauusd_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if value in _XAUUSD_ALIASES:
        return XAUUSD_SYMBOL

    raise ValueError(
        f"Aurex only supports gold {XAUUSD_DISPLAY_SYMBOL}; "
        f"use {XAUUSD_SYMBOL} for Twelve Data."
    )


def format_symbol_for_display(symbol: str) -> str:
    normalize_xauusd_symbol(symbol)
    return XAUUSD_DISPLAY_SYMBOL
