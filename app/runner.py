import asyncio
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.registry import SOURCES
from delivery.telegram import TelegramNotifier
from models.venue import Venue
from storage.sqlite import Database


async def run_production(config_path: str = "config/venues.yaml") -> int:
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    venues = [Venue.model_validate(v) for v in raw.get("venues", [])]
    Path("data").mkdir(parents=True, exist_ok=True)
    db = Database("data/culture_events.db")
    db.init()
    notifier = TelegramNotifier.from_env()

    discovered = []
    for venue in venues:
        for source_name, source_cfg in venue.sources.items():
            spec = SOURCES[source_name]
            result = await spec.factory().fetch(venue, source_cfg)
            db.record_source_run(result)
            if result.status == "ok":
                discovered.extend(result.events)

    new_events = []
    for event in discovered:
        if db.upsert_event(event):
            db.enqueue_notification(event.id)
            new_events.append(event)

    for event in new_events:
        if notifier.enabled:
            notifier.send_new_event(event)
            db.mark_notification_sent(event.id, datetime.now(timezone.utc))

    return len(new_events)


def main() -> None:
    count = asyncio.run(run_production())
    print(f"new_events={count}")


if __name__ == "__main__":
    main()
