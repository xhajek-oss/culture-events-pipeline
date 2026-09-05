from pydantic import BaseModel


class Venue(BaseModel):
    id: str
    name: str
    city: str | None = None
    sources: dict[str, dict]
