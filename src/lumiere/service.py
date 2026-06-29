import logging

from lumiere.data_provider import MarketDataProvider
from lumiere.market import normalize_xauusd_symbol
from lumiere.models import Signal
from lumiere.storage import SignalStore
from lumiere.strategy import XauUsdTrendStrategy
from lumiere.telegram_bot import TelegramNotifier

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(
        self,
        *,
        provider: MarketDataProvider,
        strategy: XauUsdTrendStrategy,
        notifier: TelegramNotifier,
        store: SignalStore,
        symbol: str,
        timeframe: str,
        candle_limit: int,
    ) -> None:
        self.provider = provider
        self.strategy = strategy
        self.notifier = notifier
        self.store = store
        self.symbol = normalize_xauusd_symbol(symbol)
        self.timeframe = timeframe
        self.candle_limit = candle_limit

    async def latest_signal(self) -> Signal | None:
        candles = await self.provider.get_candles(self.symbol, self.timeframe, self.candle_limit)
        return self.strategy.generate_signal(candles, symbol=self.symbol, timeframe=self.timeframe)

    async def publish_new_signal(self) -> Signal | None:
        signal = await self.latest_signal()
        if signal is None:
            logger.info("No signal for %s %s", self.symbol, self.timeframe)
            return None

        if self.store.has_signal(signal.key):
            logger.info("Signal already sent: %s", signal.key)
            return signal

        await self.notifier.send(signal.to_telegram_message())
        self.store.save_signal(signal)
        logger.info("Published signal: %s", signal.key)
        return signal
