import os

import httpx

from models.culture_event import CultureEvent


class TelegramNotifier:
    def __init__(self, token: str | None, chat_id: str | None) -> None:
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)

    @classmethod
    def events_from_env(cls) -> "TelegramNotifier":
        return cls(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_EVENTS_CHAT_ID"))

    @classmethod
    def alerts_from_env(cls) -> "TelegramNotifier":
        return cls(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_ALERT_CHAT_ID"))

    def send_text(self, text: str) -> None:
        if not self.enabled:
            return
        response = httpx.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": self.chat_id, "text": text},
            timeout=20,
        )
        response.raise_for_status()

    def send_new_event(self, event: CultureEvent) -> None:
        start = event.start_at.strftime("%d.%m.%Y %H:%M") if event.start_at else "čas neuveden"
        text = (
            "🎭 Nová kulturní akce\n"
            f"{event.title}\n"
            f"📅 {start}\n"
            f"🌐 {event.source}\n"
            f"{event.url}"
        )
        self.send_text(text)

    def send_source_alert(self, source: str, venue_id: str, reason: str) -> None:
        self.send_text(
            "🚨 Culture monitor\n"
            f"{source}: DOWN\n"
            f"Venue: {venue_id}\n"
            f"{reason}"
        )

    def send_source_recovery(self, source: str, venue_id: str) -> None:
        self.send_text(
            "✅ Culture monitor\n"
            f"{source}: OK again\n"
            f"Venue: {venue_id}"
        )
