from abc import ABC, abstractmethod

from models.source_result import SourceResult
from models.venue import Venue


class CultureSource(ABC):
    name: str

    @abstractmethod
    async def fetch(self, venue: Venue, config: dict) -> SourceResult:
        raise NotImplementedError
