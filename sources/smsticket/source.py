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
from sources.parsing import local_datetime, make_content_hash, normalize_text, parse_numeric_date, parse_time


class SmsTicketSource(CultureSource):
    name = "smsticket"
    base_url = "https://www.smsticket.cz"

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

        for link in soup.find_all("a", href=True):
            href = str(link.get("href") or "")
            match = re.search(r"/vstupenky/(\d+)-", href, flags=re.IGNORECASE)
            if not match:
                continue

            source_id = match.group(1)
            full_url = urljoin(self.base_url, href)
            container = self._find_event_container(link)
            if container is None:
                continue
            block = normalize_text(container.get_text(" ", strip=True))
            event_date = parse_numeric_date(block)
            event_time = parse_time(block)
            if not event_date or not event_time:
                continue

            title = normalize_text(link.get_text(" ", strip=True))
            if not title or title.lower() in {"více informací", "koupit vstupenky", "vstupenky", "detail akce"}:
                title = self._title_from_slug(href)
            if not title:
                continue

            price_match = re.search(r"(\d[\d\s]*)\s*Kč", block, flags=re.IGNORECASE)
            price = f"{normalize_text(price_match.group(1))} Kč" if price_match else None
            lower = block.lower()
            availability = "Vyprodáno" if "vyprodáno" in lower else None

            event = CultureEvent(
                id=f"smsticket:{source_id}",
                source="smsticket",
                source_event_id=source_id,
                venue_id=venue.id,
                title=title,
                start_at=local_datetime(event_date, event_time),
                price=price,
                availability=availability,
                url=full_url,
                fetched_at=fetched_at,
                content_hash=make_content_hash(
                    title=title,
                    start_at=local_datetime(event_date, event_time),
                    price=price,
                    availability=availability,
                    url=full_url,
                ),
            )
            result[event.id] = event

        return sorted(result.values(), key=lambda e: (e.start_at or datetime.max.replace(tzinfo=timezone.utc), e.title.lower()))

    @staticmethod
    def _find_event_container(link):
        current = link
        for _ in range(8):
            if current is None:
                return None
            text = normalize_text(current.get_text(" ", strip=True))
            if parse_numeric_date(text) and parse_time(text):
                return current
            current = current.parent
        return None

    @staticmethod
    def _title_from_slug(href: str) -> str:
        match = re.search(r"/vstupenky/\d+-(.+?)(?:[/?#]|$)", href, flags=re.IGNORECASE)
        if not match:
            return ""
        title = match.group(1)
        title = re.sub(r"-kd-hronovicka-pardubice$", "", title, flags=re.IGNORECASE)
        return normalize_text(title.replace("-", " "))
