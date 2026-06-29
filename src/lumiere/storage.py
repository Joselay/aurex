import sqlite3
from pathlib import Path

from lumiere.models import Signal


class SignalStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def has_signal(self, key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute("select 1 from signals where key = ?", (key,)).fetchone()
        return row is not None

    def save_signal(self, signal: Signal) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                insert or ignore into signals (
                    key, symbol, timeframe, direction, candle_time,
                    entry, stop_loss, take_profit_1, take_profit_2, reason
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.key,
                    signal.symbol,
                    signal.timeframe,
                    signal.direction,
                    signal.candle_time.isoformat(),
                    signal.entry,
                    signal.stop_loss,
                    signal.take_profit_1,
                    signal.take_profit_2,
                    signal.reason,
                ),
            )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                create table if not exists signals (
                    key text primary key,
                    symbol text not null,
                    timeframe text not null,
                    direction text not null,
                    candle_time text not null,
                    entry real not null,
                    stop_loss real not null,
                    take_profit_1 real not null,
                    take_profit_2 real not null,
                    reason text not null,
                    created_at text not null default current_timestamp
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)
