from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: SecretStr = Field(..., alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(..., alias="TELEGRAM_CHAT_ID")

    market_data_provider: Literal["twelvedata"] = Field("twelvedata", alias="MARKET_DATA_PROVIDER")
    twelvedata_api_key: SecretStr = Field(..., alias="TWELVEDATA_API_KEY")

    symbol: str = Field("XAU/USD", alias="SYMBOL")
    timeframe: str = Field("15min", alias="TIMEFRAME")
    candle_limit: int = Field(260, alias="CANDLE_LIMIT", ge=220)
    poll_seconds: int = Field(300, alias="POLL_SECONDS", ge=30)

    storage_path: Path = Field(Path("data/signals.sqlite3"), alias="STORAGE_PATH")

    ema_fast: int = Field(20, alias="EMA_FAST")
    ema_slow: int = Field(50, alias="EMA_SLOW")
    ema_trend: int = Field(200, alias="EMA_TREND")
    rsi_period: int = Field(14, alias="RSI_PERIOD")
    atr_period: int = Field(14, alias="ATR_PERIOD")
    atr_stop_multiple: float = Field(1.5, alias="ATR_STOP_MULTIPLE", gt=0)
    reward_multiple_1: float = Field(1.0, alias="REWARD_MULTIPLE_1", gt=0)
    reward_multiple_2: float = Field(2.0, alias="REWARD_MULTIPLE_2", gt=0)
