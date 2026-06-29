import json
from urllib.parse import urlparse

from js import Object, fetch
from pyodide.ffi import to_js as _to_js
from workers import Response, WorkerEntrypoint

from aurex.constants import XAUUSD_DISPLAY_SYMBOL
from aurex.settings import get_settings
from aurex.signals import latest_signals, publish_new_signals


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlparse(request.url).path

        if path == "/health":
            return Response.json(
                {"ok": True, "service": "aurex", "runtime": "cloudflare-python-worker"}
            )

        if path == "/signal":
            signals = await latest_signals(self.env)
            return Response.json({"signals": signals, "signal": signals[0] if signals else None})

        settings = get_settings(self.env)
        return Response.json(
            {
                "service": "aurex",
                "symbol": XAUUSD_DISPLAY_SYMBOL,
                "timeframes": settings.timeframes,
            }
        )

    async def scheduled(self, controller, env, ctx):
        await publish_new_signals(
            env,
            fetch_json=fetch_json,
            send_telegram_message=lambda text: send_telegram_message(env, text),
            scheduled_time=controller.scheduledTime,
        )


async def fetch_json(url):
    response = await fetch(url)
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status}")
    return await response.json()


async def send_telegram_message(env, text):
    url = f"https://api.telegram.org/bot{env.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = await fetch(
        url,
        to_js(
            {
                "method": "POST",
                "headers": {"content-type": "application/json"},
                "body": json.dumps(
                    {
                        "chat_id": env.TELEGRAM_CHAT_ID,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    }
                ),
            }
        ),
    )
    if not response.ok:
        raise RuntimeError(f"Telegram HTTP {response.status}: {await response.text()}")


def to_js(value):
    return _to_js(value, dict_converter=Object.fromEntries)

