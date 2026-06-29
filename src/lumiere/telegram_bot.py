from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


class TelegramNotifier:
    def __init__(self, application: Application, chat_id: str) -> None:
        self.application = application
        self.chat_id = chat_id

    async def send(self, text: str) -> None:
        await self.application.bot.send_message(chat_id=self.chat_id, text=text)


def register_handlers(application: Application, service_getter) -> None:
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.effective_message:
            await update.effective_message.reply_text(
                "XAUUSD signal bot is online. Use /signal for a fresh check or /status."
            )

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        service = service_getter()
        if update.effective_message:
            await update.effective_message.reply_text(
                f"Watching {service.symbol} on {service.timeframe}."
            )

    async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        service = service_getter()
        if update.effective_message:
            await update.effective_message.reply_text("Checking latest candles...")
            generated = await service.latest_signal()
            if generated is None:
                await update.effective_message.reply_text("No valid XAUUSD signal right now.")
            else:
                await update.effective_message.reply_text(generated.to_telegram_message())

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("signal", signal))
