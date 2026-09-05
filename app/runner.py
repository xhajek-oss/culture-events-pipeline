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
    initialized = db.is_initialized()

    discovered = []
    all_sources_ok = True

    for venue in venues:
        for source_name, source_cfg in venue.sources.items():
            spec = SOURCES[source_name]
            result = await spec.factory().fetch(venue, source_cfg)
            db.record_source_run(result)

            if result.status != "ok":
                all_sources_ok = False
                print(f"source_error source={source_name} venue={venue.id} error={result.error}")
                continue

            if not result.events and not spec.allow_empty:
                all_sources_ok = False
                print(f"source_empty source={source_name} venue={venue.id} allow_empty=false")
                continue

            discovered.extend(result.events)

    new_count = 0
    for event in discovered:
        is_new = db.upsert_event(event)
        if initialized and is_new:
            db.enqueue_notification(event.id)
            new_count += 1

    if not initialized:
        if all_sources_ok:
            db.mark_initialized()
            print(f"baseline_initialized events={len(discovered)}")
        else:
            print("baseline_not_initialized reason=source_failure_or_unexpected_empty")

    if notifier.enabled:
        for event in db.pending_events():
            try:
                notifier.send_new_event(event)
                db.mark_notification_sent(event.id, datetime.now(timezone.utc))
            except Exception as exc:
                db.mark_notification_failed(event.id, str(exc))
                print(f"telegram_error event={event.id} error={exc}")

    print(f"discovered={len(discovered)} new_events={new_count} all_sources_ok={all_sources_ok}")
    return 0 if all_sources_ok else 1


def main() -> None:
    raise SystemExit(asyncio.run(run_production()))


if __name__ == "__main__":
    main()
