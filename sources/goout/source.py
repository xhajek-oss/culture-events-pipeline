import time
from datetime import datetime, timezone

from models.culture_event import CultureEvent
from models.source_result import SourceResult
from models.venue import Venue
from sources.base import CultureSource
from sources.goout.client import GoOutClient
from sources.parsing import make_content_hash


class GoOutSource(CultureSource):
    name = "goout"

    async def fetch(self, venue: Venue, config: dict) -> SourceResult:
        started = time.perf_counter()
        fetched_at = datetime.now(timezone.utc)
        try:
            venue_id = int(config["venue_id"])
            payload = await GoOutClient().get_venue_schedules(venue_id)
            events = self._parse(payload, venue, fetched_at)
            return SourceResult(
                source=self.name,
                venue_id=venue.id,
                status="ok",
                transport="api",
                fetched_at=fetched_at,
                duration_ms=int((time.perf_counter() - started) * 1000),
                events=events,
            )
        except Exception as exc:
            return SourceResult(
                source=self.name,
                venue_id=venue.id,
                status="error",
                transport="api",
                fetched_at=fetched_at,
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )

    def _parse(self, payload: dict, venue: Venue, fetched_at: datetime) -> list[CultureEvent]:
        included: dict[str, dict[object, dict]] = {}
        for entity_type, entities in (payload.get("included") or {}).items():
            included[entity_type] = {entity.get("id"): entity for entity in entities}

        result: list[CultureEvent] = []
        for schedule in payload.get("schedules", []):
            if not isinstance(schedule, dict):
                continue

            schedule_id = schedule.get("id")
            attrs = schedule.get("attributes") or {}
            relationships = schedule.get("relationships") or {}
            event_ref = relationships.get("event") or {}
            event = included.get("events", {}).get(event_ref.get("id"), {})
            event_cs = (event.get("locales") or {}).get("cs") or {}

            title = str(event_cs.get("name") or "").strip()
            raw_start = attrs.get("startAt")
            url = ((schedule.get("locales") or {}).get("cs") or {}).get("siteUrl")
            if not url:
                url = event_cs.get("siteUrl") or event.get("url")

            if not (schedule_id and title and raw_start and url):
                continue

            start_at = datetime.fromisoformat(str(raw_start).replace("Z", "+00:00"))
            price = attrs.get("pricing")
            if isinstance(price, str) and price.startswith(("http://", "https://")):
                price = None

            source_id = str(schedule_id)
            result.append(
                CultureEvent(
                    id=f"goout:{source_id}",
                    source="goout",
                    source_event_id=source_id,
                    venue_id=venue.id,
                    title=title,
                    start_at=start_at,
                    price=str(price) if price else None,
                    availability=attrs.get("ticketingState"),
                    url=str(url),
                    fetched_at=fetched_at,
                    content_hash=make_content_hash(
                        title=title,
                        start_at=raw_start,
                        price=price,
                        availability=attrs.get("ticketingState"),
                        url=url,
                    ),
                )
            )
        return result
