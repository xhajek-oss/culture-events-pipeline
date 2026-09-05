from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from models.culture_event import CultureEvent


class SourceResult(BaseModel):
    source: str
    venue_id: str
    status: Literal["ok", "error"]
    transport: str
    fetched_at: datetime
    duration_ms: int
    events: list[CultureEvent] = Field(default_factory=list)
    error: str | None = None
