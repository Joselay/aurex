import argparse
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import ValidationError
from telegram.ext import Application

from lumiere.config import Settings
from lumiere.data_provider import TwelveDataProvider
from lumiere.service import SignalService
from lumiere.storage import SignalStore
from lumiere.strategy import XauUsdTrendStrategy
from lumiere.telegram_bot import TelegramNotifier, register_handlers


def build_service(settings: Settings, application: Application) -> SignalService:
    provider = TwelveDataProvider(settings.twelvedata_api_key.get_secret_value())
    strategy = XauUsdTrendStrategy(
        ema_fast=settings.ema_fast,
        ema_slow=settings.ema_slow,
        ema_trend=settings.ema_trend,
        rsi_period=settings.rsi_period,
        atr_period=settings.atr_period,
        atr_stop_multiple=settings.atr_stop_multiple,
        reward_multiple_1=settings.reward_multiple_1,
        reward_multiple_2=settings.reward_multiple_2,
    )
    notifier = TelegramNotifier(application, settings.telegram_chat_id)
    store = SignalStore(settings.storage_path)
    return SignalService(
        provider=provider,
        strategy=strategy,
        notifier=notifier,
        store=store,
        symbol=settings.symbol,
        timeframe=settings.timeframe,
        candle_limit=settings.candle_limit,
    )


async def run_once() -> None:
    settings = Settings()
    application = (
        Application.builder().token(settings.telegram_bot_token.get_secret_value()).build()
    )
    service = build_service(settings, application)

    async with application:
        await service.publish_new_signal()


def run_polling() -> None:
    settings = Settings()
    application = (
        Application.builder().token(settings.telegram_bot_token.get_secret_value()).build()
    )
    service = build_service(settings, application)

    register_handlers(application, lambda: service)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        service.publish_new_signal,
        "interval",
        seconds=settings.poll_seconds,
        id="xauusd-signal-check",
        max_instances=1,
        coalesce=True,
        next_run_time=None,
    )

    async def post_init(_: Application) -> None:
        scheduler.start()
        await service.publish_new_signal()

    async def post_shutdown(_: Application) -> None:
        scheduler.shutdown(wait=False)

    application.post_init = post_init
    application.post_shutdown = post_shutdown
    application.run_polling(allowed_updates=UpdateTypes.COMMANDS)


class UpdateTypes:
    COMMANDS = ["message"]


def cli() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Telegram signal bot for XAUUSD.")
    parser.add_argument(
        "--once", action="store_true", help="Check once, send a new signal if present, exit."
    )
    args = parser.parse_args()

    try:
        if args.once:
            asyncio.run(run_once())
        else:
            run_polling()
    except ValidationError as exc:
        raise SystemExit(f"Configuration error:\n{exc}") from exc


if __name__ == "__main__":
    cli()
