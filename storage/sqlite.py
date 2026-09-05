import sqlite3
from datetime import datetime
from pathlib import Path

from models.culture_event import CultureEvent
from models.source_result import SourceResult


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def init(self) -> None:
        with self.connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              source_event_id TEXT,
              venue_id TEXT NOT NULL,
              title TEXT NOT NULL,
              start_at TEXT,
              price TEXT,
              availability TEXT,
              url TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              content_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
              event_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              sent_at TEXT
            );
            CREATE TABLE IF NOT EXISTS source_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT NOT NULL,
              venue_id TEXT NOT NULL,
              status TEXT NOT NULL,
              transport TEXT NOT NULL,
              fetched_at TEXT NOT NULL,
              duration_ms INTEGER NOT NULL,
              error TEXT
            );
            """)

    def upsert_event(self, event: CultureEvent) -> bool:
        with self.connect() as con:
            row = con.execute("SELECT id FROM events WHERE id = ?", (event.id,)).fetchone()
            if row is None:
                con.execute("INSERT INTO events (id,source,source_event_id,venue_id,title,start_at,price,availability,url,first_seen_at,last_seen_at,content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (event.id, event.source, event.source_event_id, event.venue_id, event.title, event.start_at.isoformat() if event.start_at else None, event.price, event.availability, event.url, event.fetched_at.isoformat(), event.fetched_at.isoformat(), event.content_hash))
                return True
            con.execute("UPDATE events SET title=?, start_at=?, price=?, availability=?, url=?, last_seen_at=?, content_hash=? WHERE id=?", (event.title, event.start_at.isoformat() if event.start_at else None, event.price, event.availability, event.url, event.fetched_at.isoformat(), event.content_hash, event.id))
            return False

    def enqueue_notification(self, event_id: str) -> None:
        with self.connect() as con:
            con.execute("INSERT OR IGNORE INTO notifications(event_id,status) VALUES (?, 'pending')", (event_id,))

    def mark_notification_sent(self, event_id: str, sent_at: datetime) -> None:
        with self.connect() as con:
            con.execute("UPDATE notifications SET status='sent', sent_at=? WHERE event_id=?", (sent_at.isoformat(), event_id))

    def record_source_run(self, result: SourceResult) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO source_runs(source,venue_id,status,transport,fetched_at,duration_ms,error) VALUES (?,?,?,?,?,?,?)", (result.source, result.venue_id, result.status, result.transport, result.fetched_at.isoformat(), result.duration_ms, result.error))
