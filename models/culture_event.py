from datetime import datetime

from pydantic import BaseModel


class CultureEvent(BaseModel):
    id: str
    source: str
    source_event_id: str | None = None
    venue_id: str
    title: str
    start_at: datetime | None = None
    price: str | None = None
    availability: str | None = None
    url: str
    fetched_at: datetime
    content_hash: str
