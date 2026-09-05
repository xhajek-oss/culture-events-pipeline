from datetime import datetime, timezone

from models.culture_event import CultureEvent
from storage.sqlite import Database


def test_new_event_is_new_only_once(tmp_path):
    db = Database(str(tmp_path / "events.db"))
    db.init()
    event = CultureEvent(id="smsticket:abc", source="smsticket", source_event_id="abc", venue_id="venue", title="Test", url="https://example.test/abc", fetched_at=datetime.now(timezone.utc), content_hash="hash")
    assert db.upsert_event(event) is True
    assert db.upsert_event(event) is False
