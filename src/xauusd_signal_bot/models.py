from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import pandas as pd


class Direction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Signal:
    symbol: str
    timeframe: str
    direction: Direction
    candle_time: datetime
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    reason: str

    @property
    def key(self) -> str:
        return f"{self.symbol}:{self.timeframe}:{self.candle_time.isoformat()}:{self.direction}"

    def to_telegram_message(self) -> str:
        return (
            f"{self.symbol} {self.direction}\n\n"
            f"Timeframe: {self.timeframe}\n"
            f"Candle: {self.candle_time.isoformat()}\n\n"
            f"Entry: {self.entry:.2f}\n"
            f"SL: {self.stop_loss:.2f}\n"
            f"TP1: {self.take_profit_1:.2f}\n"
            f"TP2: {self.take_profit_2:.2f}\n\n"
            f"Reason: {self.reason}\n"
            "Risk: signal only; demo test before live trading."
        )


REQUIRED_CANDLE_COLUMNS = {"datetime", "open", "high", "low", "close"}


def normalize_candles(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_CANDLE_COLUMNS - set(frame.columns)
    if missing:
        joined = ", ".join(sorted(missing))
        raise ValueError(f"Missing candle columns: {joined}")

    candles = frame.copy()
    candles["datetime"] = pd.to_datetime(candles["datetime"], utc=True)
    for column in ["open", "high", "low", "close"]:
        candles[column] = pd.to_numeric(candles[column], errors="raise")

    candles = candles.sort_values("datetime").drop_duplicates("datetime", keep="last")
    return candles.reset_index(drop=True)
