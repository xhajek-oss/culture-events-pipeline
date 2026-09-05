import time
from datetime import datetime, timezone

from models.source_result import SourceResult
from models.venue import Venue
from sources.base import CultureSource


class SmsTicketSource(CultureSource):
    name = "smsticket"

    async def fetch(self, venue: Venue, config: dict) -> SourceResult:
        started = time.perf_counter()
        fetched_at = datetime.now(timezone.utc)
        return SourceResult(source=self.name, venue_id=venue.id, status="error", transport="discovery_required", fetched_at=fetched_at, duration_ms=int((time.perf_counter() - started) * 1000), error="API/XHR endpoint discovery not implemented yet")
