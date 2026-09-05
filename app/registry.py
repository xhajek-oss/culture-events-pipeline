from dataclasses import dataclass
from typing import Callable

from sources.goout.source import GoOutSource
from sources.smsticket.source import SmsTicketSource
from sources.ticketportal.source import TicketportalSource


@dataclass(frozen=True)
class SourceSpec:
    name: str
    factory: Callable[[], object]
    allow_empty: bool = False


SOURCES = {
    "goout": SourceSpec("goout", GoOutSource),
    "smsticket": SourceSpec("smsticket", SmsTicketSource),
    "ticketportal": SourceSpec("ticketportal", TicketportalSource),
}
