import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from models.culture_event import CultureEvent
from models.source_result import SourceResult
from models.venue import Venue
from sources.base import CultureSource
from sources.parsing import PRAGUE, local_datetime, make_content_hash, normalize_text, parse_ticketportal_date, parse_time


class TicketportalSource(CultureSource):
    name = "ticketportal"
    base_url = "https://www.ticketportal.cz"

    async def fetch(self, venue: Venue, config: dict) -> SourceResult:
        started = time.perf_counter()
        fetched_at = datetime.now(timezone.utc)
        url = config["url"]
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 culture-events-pipeline/1.0",
                        "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.5",
                    },
                )
                response.raise_for_status()
            events = self._parse(response.text, venue, fetched_at)
            return SourceResult(
                source=self.name,
                venue_id=venue.id,
                status="ok",
                transport="html",
                fetched_at=fetched_at,
                duration_ms=int((time.perf_counter() - started) * 1000),
                events=events,
            )
        except Exception as exc:
            return SourceResult(
                source=self.name,
                venue_id=venue.id,
                status="error",
                transport="html",
                fetched_at=fetched_at,
                duration_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )

    def _parse(self, html: str, venue: Venue, fetched_at: datetime) -> list[CultureEvent]:
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, CultureEvent] = {}
        today = fetched_at.astimezone(PRAGUE).date()

        for link in soup.find_all("a", href=True):
            href = str(link.get("href") or "")
            match = re.search(r"/event/(\d+)(?:[/?#]|$)", href, flags=re.IGNORECASE)
            if not match:
                continue

            source_id = match.group(1)
            block = self._find_local_event_context(link)
            event_date = parse_ticketportal_date(block)
            event_time = parse_time(block)
            if not event_date or not event_time or event_date < today:
                continue

            title = normalize_text(link.get_text(" ", strip=True))
            if not title or title.lower() in {"koupit", "více informací", "detail", "kd hronovická", "pardubice"}:
                container = self._find_event_container(link)
                title = self._find_title(container, link) if container is not None else ""
            if not title:
                continue

            full_url = urljoin(self.base_url, href)
            lower = block.lower()
            if "vyprodáno" in lower:
                availability = "Vyprodáno"
            elif "nově v prodeji" in lower or "v prodeji" in lower:
                availability = "V prodeji"
            else:
                availability = None

            start_at = local_datetime(event_date, event_time)
            event = CultureEvent(
                id=f"ticketportal:{source_id}",
                source="ticketportal",
                source_event_id=source_id,
                venue_id=venue.id,
                title=title,
                start_at=start_at,
                availability=availability,
                url=full_url,
                fetched_at=fetched_at,
                content_hash=make_content_hash(
                    title=title,
                    start_at=start_at,
                    availability=availability,
                    url=full_url,
                ),
            )
            result[event.id] = event

        return sorted(result.values(), key=lambda e: (e.start_at or datetime.max.replace(tzinfo=timezone.utc), e.title.lower()))

    @staticmethod
    def _find_local_event_context(link, max_text_nodes: int = 24) -> str:
        """Return the nearest preceding text that contains this ticket slot's date/time.

        Ticketportal includes hidden/template content elsewhere in the page (including an
        old 2017 demo event). Walking far up the ancestor tree can therefore attach that
        unrelated date to a real event. The visible ticket layout places date/time just
        before the event link, so prefer the closest preceding text nodes.
        """
        preceding: list[str] = []
        for node in link.find_all_previous(string=True, limit=max_text_nodes):
            value = normalize_text(node)
            if value:
                preceding.append(value)

        for size in range(1, len(preceding) + 1):
            context = normalize_text(" ".join(reversed(preceding[:size])))
            if parse_ticketportal_date(context) and parse_time(context):
                return context
        return ""

    @staticmethod
    def _find_event_container(link):
        current = link
        best = None
        for _ in range(12):
            if current is None:
                break
            text = normalize_text(current.get_text(" ", strip=True))
            if parse_ticketportal_date(text) and parse_time(text):
                best = current
                event_links = current.find_all("a", href=re.compile(r"/event/", re.IGNORECASE))
                if len(event_links) <= 1:
                    return current
            current = current.parent
        return best

    @staticmethod
    def _find_title(container, original_link) -> str:
        for attr in ("title", "aria-label", "data-title"):
            value = normalize_text(original_link.get(attr))
            if value:
                return value
        for tag_name in ("h1", "h2", "h3", "h4", "h5", "strong"):
            for element in container.find_all(tag_name):
                value = normalize_text(element.get_text(" ", strip=True))
                if value and value.lower() not in {"koupit", "kd hronovická", "pardubice"}:
                    return value
        return ""
