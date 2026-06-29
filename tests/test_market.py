import pytest
from pydantic import ValidationError

from lumiere.config import Settings
from lumiere.data_provider import TwelveDataProvider
from lumiere.market import XAUUSD_SYMBOL, normalize_xauusd_symbol
from lumiere.strategy import XauUsdTrendStrategy


def _settings(**overrides: str) -> Settings:
    values = {
        "TELEGRAM_BOT_TOKEN": "123456:replace_me",
        "TELEGRAM_CHAT_ID": "replace_me",
        "TWELVEDATA_API_KEY": "replace_me",
        **overrides,
    }
    return Settings(**values)


def test_normalizes_supported_xauusd_aliases() -> None:
    assert normalize_xauusd_symbol("XAU/USD") == XAUUSD_SYMBOL
    assert normalize_xauusd_symbol("xauusd") == XAUUSD_SYMBOL


def test_rejects_crypto_symbols() -> None:
    with pytest.raises(ValueError, match="only supports gold XAUUSD"):
        normalize_xauusd_symbol("BTC/USD")


def test_settings_reject_non_xauusd_symbol() -> None:
    with pytest.raises(ValidationError, match="only supports gold XAUUSD"):
        _settings(SYMBOL="ETH/USD")


def test_settings_accept_xauusd_alias() -> None:
    settings = _settings(SYMBOL="XAUUSD")

    assert settings.symbol == XAUUSD_SYMBOL


def test_strategy_rejects_non_xauusd_symbol() -> None:
    with pytest.raises(ValueError, match="only supports gold XAUUSD"):
        XauUsdTrendStrategy().generate_signal([], symbol="BTC/USD")


@pytest.mark.asyncio
async def test_twelvedata_provider_rejects_non_xauusd_symbol_before_fetch() -> None:
    with pytest.raises(ValueError, match="only supports gold XAUUSD"):
        await TwelveDataProvider("replace_me").get_candles("BTC/USD", "15min", 260)
