import hashlib
import json
import time
from datetime import datetime, timezone

from models.culture_event import CultureEvent
from models.source_result import SourceResult
from models.venue import Venue
from sources.base import CultureSource
from sources.goout.client import GoOutClient


class GoOutSource(CultureSource):
    name = "goout"

    async def fetch(self, venue: Venue, config: dict) -> SourceResult:
        started = time.perf_counter()
        fetched_at = datetime.now(timezone.utc)
        try:
            venue_id = int(config["venue_id"])
            if venue_id <= 0:
                raise ValueError("GoOut venue_id is not configured")
            payload = await GoOutClient().get_venue_schedules(venue_id)
            events = self._parse(payload, venue, fetched_at)
            return SourceResult(source=self.name, venue_id=venue.id, status="ok", transport="api", fetched_at=fetched_at, duration_ms=int((time.perf_counter() - started) * 1000), events=events)
        except Exception as exc:
            return SourceResult(source=self.name, venue_id=venue.id, status="error", transport="api", fetched_at=fetched_at, duration_ms=int((time.perf_counter() - started) * 1000), error=str(exc))

    def _parse(self, payload: dict, venue: Venue, fetched_at: datetime) -> list[CultureEvent]:
        result: list[CultureEvent] = []
        schedules = payload.get("schedules") or payload.get("schedule") or []
        if isinstance(schedules, dict):
            schedules = list(schedules.values())
        if not isinstance(schedules, list):
            return result

        for item in schedules:
            if not isinstance(item, dict):
                continue
            event = item.get("event")
            if not isinstance(event, dict):
                continue
            source_id = str(event.get("id") or item.get("id") or "")
            title = str(event.get("name") or event.get("title") or "").strip()
            url = str(event.get("url") or item.get("url") or "")
            if url.startswith("/"):
                url = "https://goout.net" + url
            if not (source_id and title and url):
                continue

            raw_start = item.get("start") or item.get("startAt") or event.get("start")
            start_at = None
            if isinstance(raw_start, str):
                try:
                    start_at = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
                except ValueError:
                    pass

            content = {"title": title, "start_at": raw_start, "url": url}
            content_hash = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            result.append(CultureEvent(id=f"goout:{source_id}", source="goout", source_event_id=source_id, venue_id=venue.id, title=title, start_at=start_at, url=url, fetched_at=fetched_at, content_hash=content_hash))
        return result
