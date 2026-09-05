from datetime import datetime, timezone

from models.culture_event import CultureEvent


def test_source_local_identity_is_stable():
    event = CultureEvent(id="goout:123", source="goout", source_event_id="123", venue_id="venue", title="Test", url="https://example.test/123", fetched_at=datetime.now(timezone.utc), content_hash="x")
    assert event.id == "goout:123"
