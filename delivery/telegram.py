import os

import httpx

from models.culture_event import CultureEvent


class TelegramNotifier:
    def __init__(self, token: str | None, chat_id: str | None) -> None:
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)

    @classmethod
    def from_env(cls) -> "TelegramNotifier":
        return cls(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))

    def send_new_event(self, event: CultureEvent) -> None:
        if not self.enabled:
            return
        start = event.start_at.isoformat() if event.start_at else "čas neuveden"
        text = f"🎭 Nová událost\n{event.title}\n{start}\n{event.url}"
        response = httpx.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json={"chat_id": self.chat_id, "text": text}, timeout=20)
        response.raise_for_status()
