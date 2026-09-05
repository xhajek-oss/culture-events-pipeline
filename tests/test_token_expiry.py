from datetime import date

import pytest

from monitoring.token_expiry import build_expiry_alert, days_until_expiry, parse_expiry


def test_parse_expiry_requires_iso_date():
    assert parse_expiry("2026-10-05") == date(2026, 10, 5)
    with pytest.raises(ValueError):
        parse_expiry("05.10.2026")


def test_days_until_expiry():
    assert days_until_expiry(date(2026, 10, 5), today=date(2026, 9, 5)) == 30


def test_alert_thresholds_match_sports_repo():
    expiry = date(2026, 10, 5)
    assert build_expiry_alert(expiry, 30) is not None
    assert build_expiry_alert(expiry, 14) is not None
    assert build_expiry_alert(expiry, 7) is not None
    assert build_expiry_alert(expiry, 3) is not None
    assert build_expiry_alert(expiry, 1) is not None
    assert build_expiry_alert(expiry, 0) is not None
    assert build_expiry_alert(expiry, 29) is None


def test_expired_token_alerts_every_day():
    message = build_expiry_alert(date(2026, 9, 4), -1)
    assert message is not None
    assert "po expiraci" in message
