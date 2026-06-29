import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

from lumiere.models import Direction, Signal, normalize_candles


class XauUsdTrendStrategy:
    def __init__(
        self,
        *,
        ema_fast: int = 20,
        ema_slow: int = 50,
        ema_trend: int = 200,
        rsi_period: int = 14,
        atr_period: int = 14,
        atr_stop_multiple: float = 1.5,
        reward_multiple_1: float = 1.0,
        reward_multiple_2: float = 2.0,
    ) -> None:
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.ema_trend = ema_trend
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.atr_stop_multiple = atr_stop_multiple
        self.reward_multiple_1 = reward_multiple_1
        self.reward_multiple_2 = reward_multiple_2

    @property
    def minimum_candles(self) -> int:
        return max(self.ema_trend, self.ema_slow, self.rsi_period, self.atr_period) + 2

    def generate_signal(
        self, candles: pd.DataFrame, *, symbol: str = "XAU/USD", timeframe: str = "15min"
    ) -> Signal | None:
        frame = self._with_indicators(normalize_candles(candles))
        if len(frame) < self.minimum_candles:
            return None

        previous = frame.iloc[-2]
        latest = frame.iloc[-1]
        if latest[["ema_fast", "ema_slow", "ema_trend", "rsi", "atr"]].isna().any():
            return None

        buy_setup = (
            latest.close > latest.ema_trend
            and latest.ema_fast > latest.ema_slow
            and latest.close > latest.ema_fast
            and previous.rsi <= 50
            and latest.rsi > 50
        )
        sell_setup = (
            latest.close < latest.ema_trend
            and latest.ema_fast < latest.ema_slow
            and latest.close < latest.ema_fast
            and previous.rsi >= 50
            and latest.rsi < 50
        )

        if buy_setup:
            return self._build_signal(
                symbol=symbol,
                timeframe=timeframe,
                direction=Direction.BUY,
                row=latest,
                reason="M15 trend above EMA200, EMA20 above EMA50, RSI reclaimed 50.",
            )
        if sell_setup:
            return self._build_signal(
                symbol=symbol,
                timeframe=timeframe,
                direction=Direction.SELL,
                row=latest,
                reason="M15 trend below EMA200, EMA20 below EMA50, RSI lost 50.",
            )
        return None

    def _with_indicators(self, candles: pd.DataFrame) -> pd.DataFrame:
        frame = candles.copy()
        close = frame["close"]
        high = frame["high"]
        low = frame["low"]

        frame["ema_fast"] = EMAIndicator(close=close, window=self.ema_fast).ema_indicator()
        frame["ema_slow"] = EMAIndicator(close=close, window=self.ema_slow).ema_indicator()
        frame["ema_trend"] = EMAIndicator(close=close, window=self.ema_trend).ema_indicator()
        frame["rsi"] = RSIIndicator(close=close, window=self.rsi_period).rsi()
        frame["atr"] = AverageTrueRange(
            high=high, low=low, close=close, window=self.atr_period
        ).average_true_range()
        return frame

    def _build_signal(
        self, *, symbol: str, timeframe: str, direction: Direction, row: pd.Series, reason: str
    ) -> Signal:
        entry = float(row.close)
        risk_distance = float(row.atr) * self.atr_stop_multiple

        if direction == Direction.BUY:
            stop_loss = entry - risk_distance
            take_profit_1 = entry + risk_distance * self.reward_multiple_1
            take_profit_2 = entry + risk_distance * self.reward_multiple_2
        else:
            stop_loss = entry + risk_distance
            take_profit_1 = entry - risk_distance * self.reward_multiple_1
            take_profit_2 = entry - risk_distance * self.reward_multiple_2

        return Signal(
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            candle_time=row.datetime.to_pydatetime(),
            entry=entry,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            reason=reason,
        )
