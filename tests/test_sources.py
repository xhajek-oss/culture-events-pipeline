from datetime import datetime, timezone

from models.venue import Venue
from sources.goout.source import GoOutSource
from sources.smsticket.source import SmsTicketSource
from sources.ticketportal.source import TicketportalSource


VENUE = Venue(id="kd_hronovicka", name="KD Hronovická Pardubice", city="Pardubice", sources={})
NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


def test_smsticket_parser_uses_stable_event_id():
    html = """
    <div>
      <a href="/vstupenky/67010-jiri-charvat-komik-ktery-neexistuje-kd-hronovicka-pardubice">
        Jiří Charvát - Komik, který neexistuje
      </a>
      <span>15.10.2026 19:00 Cena 490 Kč</span>
    </div>
    """
    events = SmsTicketSource()._parse(html, VENUE, NOW)
    assert len(events) == 1
    assert events[0].id == "smsticket:67010"
    assert events[0].title == "Jiří Charvát - Komik, který neexistuje"
    assert events[0].price == "490 Kč"


def test_ticketportal_parser_uses_stable_event_id():
    html = """
    <div>
      <span>4 Říj. 2026 15:00</span>
      <a href="/Event/12005807">Štístko a Poupěnka ...A KDE JE POUPĚNKA?</a>
    </div>
    """
    events = TicketportalSource()._parse(html, VENUE, NOW)
    assert len(events) == 1
    assert events[0].id == "ticketportal:12005807"
    assert events[0].start_at.hour == 15


def test_goout_parser_uses_schedule_id():
    payload = {
        "schedules": [
            {
                "id": 777,
                "attributes": {
                    "startAt": "2026-11-10T19:00:00+01:00",
                    "pricing": None,
                    "ticketingState": "available",
                },
                "relationships": {
                    "event": {"id": 55},
                    "venue": {"id": 65979},
                },
                "locales": {
                    "cs": {"siteUrl": "https://goout.net/cs/example/szabc/"}
                },
            }
        ],
        "included": {
            "events": [
                {
                    "id": 55,
                    "locales": {"cs": {"name": "Testovací akce"}},
                }
            ],
            "venues": [{"id": 65979}],
        },
    }
    events = GoOutSource()._parse(payload, VENUE, NOW)
    assert len(events) == 1
    assert events[0].id == "goout:777"
    assert events[0].source_event_id == "777"
