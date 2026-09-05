import hashlib
import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_time(text: str) -> tuple[int, int] | None:
    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def parse_numeric_date(text: str) -> date | None:
    match = re.search(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{2,4})\b", text)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_ticketportal_date(text: str) -> date | None:
    direct = parse_numeric_date(text)
    if direct:
        return direct

    months = {
        "led": 1, "ún": 2, "un": 2, "bře": 3, "bre": 3,
        "dub": 4, "kvě": 5, "kve": 5, "čvn": 6, "cvn": 6,
        "čvc": 7, "cvc": 7, "srp": 8, "zář": 9, "zar": 9,
        "říj": 10, "rij": 10, "lis": 11, "pro": 12,
    }
    match = re.search(
        r"\b(\d{1,2})\s+(Led\.?|Ún\.?|Un\.?|Bře\.?|Bre\.?|Dub\.?|Kvě\.?|Kve\.?|Čvn\.?|Cvn\.?|Čvc\.?|Cvc\.?|Srp\.?|Zář\.?|Zar\.?|Říj\.?|Rij\.?|Lis\.?|Pro\.?)\s+(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    day = int(match.group(1))
    month = months.get(match.group(2).lower().rstrip("."))
    year = int(match.group(3))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def local_datetime(event_date: date, event_time: tuple[int, int]) -> datetime:
    hour, minute = event_time
    return datetime(event_date.year, event_date.month, event_date.day, hour, minute, tzinfo=PRAGUE)


def make_content_hash(**values: object) -> str:
    raw = json.dumps(values, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
