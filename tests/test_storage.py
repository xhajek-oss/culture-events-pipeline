from datetime import date, datetime, timezone

from models.culture_event import CultureEvent
from storage.sqlite import Database


def test_new_event_is_new_only_once(tmp_path):
    db = Database(str(tmp_path / "events.db"))
    db.init()
    event = CultureEvent(id="smsticket:abc", source="smsticket", source_event_id="abc", venue_id="venue", title="Test", url="https://example.test/abc", fetched_at=datetime.now(timezone.utc), content_hash="hash")
    assert db.upsert_event(event) is True
    assert db.upsert_event(event) is False


def test_metadata_roundtrip(tmp_path):
    db = Database(str(tmp_path / "events.db"))
    db.init()
    assert db.get_metadata("health:goout:venue") is None
    db.set_metadata("health:goout:venue", "down")
    assert db.get_metadata("health:goout:venue") == "down"
    db.set_metadata("health:goout:venue", "ok")
    assert db.get_metadata("health:goout:venue") == "ok"


def test_prune_past_events_removes_only_old_rows(tmp_path):
    db = Database(str(tmp_path / "events.db"))
    db.init()
    old = CultureEvent(
        id="ticketportal:old",
        source="ticketportal",
        source_event_id="old",
        venue_id="venue",
        title="Old",
        start_at=datetime(2017, 5, 10, 15, 0, tzinfo=timezone.utc),
        url="https://example.test/old",
        fetched_at=datetime.now(timezone.utc),
        content_hash="old",
    )
    future = CultureEvent(
        id="ticketportal:future",
        source="ticketportal",
        source_event_id="future",
        venue_id="venue",
        title="Future",
        start_at=datetime(2026, 12, 2, 19, 0, tzinfo=timezone.utc),
        url="https://example.test/future",
        fetched_at=datetime.now(timezone.utc),
        content_hash="future",
    )
    db.upsert_event(old)
    db.upsert_event(future)

    assert db.prune_past_events(date(2026, 9, 5)) == 1
    assert db.upsert_event(future) is False
    assert db.upsert_event(old) is True
