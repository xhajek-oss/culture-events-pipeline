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
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

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
              sent_at TEXT,
              attempts INTEGER NOT NULL DEFAULT 0,
              last_error TEXT
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
            CREATE TABLE IF NOT EXISTS metadata (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            """)

    def get_metadata(self, key: str) -> str | None:
        with self.connect() as con:
            row = con.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def is_initialized(self) -> bool:
        return self.get_metadata("baseline_initialized") == "1"

    def mark_initialized(self) -> None:
        self.set_metadata("baseline_initialized", "1")

    def upsert_event(self, event: CultureEvent) -> bool:
        with self.connect() as con:
            row = con.execute("SELECT id FROM events WHERE id = ?", (event.id,)).fetchone()
            if row is None:
                con.execute(
                    "INSERT INTO events (id,source,source_event_id,venue_id,title,start_at,price,availability,url,first_seen_at,last_seen_at,content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event.id,
                        event.source,
                        event.source_event_id,
                        event.venue_id,
                        event.title,
                        event.start_at.isoformat() if event.start_at else None,
                        event.price,
                        event.availability,
                        event.url,
                        event.fetched_at.isoformat(),
                        event.fetched_at.isoformat(),
                        event.content_hash,
                    ),
                )
                return True
            con.execute(
                "UPDATE events SET title=?, start_at=?, price=?, availability=?, url=?, last_seen_at=?, content_hash=? WHERE id=?",
                (
                    event.title,
                    event.start_at.isoformat() if event.start_at else None,
                    event.price,
                    event.availability,
                    event.url,
                    event.fetched_at.isoformat(),
                    event.content_hash,
                    event.id,
                ),
            )
            return False

    def enqueue_notification(self, event_id: str) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO notifications(event_id,status) VALUES (?, 'pending')",
                (event_id,),
            )

    def pending_events(self) -> list[CultureEvent]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT e.* FROM notifications n
                JOIN events e ON e.id = n.event_id
                WHERE n.status = 'pending'
                ORDER BY n.created_at, e.id
                """
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def mark_notification_sent(self, event_id: str, sent_at: datetime) -> None:
        with self.connect() as con:
            con.execute(
                "UPDATE notifications SET status='sent', sent_at=?, attempts=attempts+1, last_error=NULL WHERE event_id=?",
                (sent_at.isoformat(), event_id),
            )

    def mark_notification_failed(self, event_id: str, error: str) -> None:
        with self.connect() as con:
            con.execute(
                "UPDATE notifications SET attempts=attempts+1, last_error=? WHERE event_id=?",
                (error[:1000], event_id),
            )

    def record_source_run(self, result: SourceResult) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO source_runs(source,venue_id,status,transport,fetched_at,duration_ms,error) VALUES (?,?,?,?,?,?,?)",
                (
                    result.source,
                    result.venue_id,
                    result.status,
                    result.transport,
                    result.fetched_at.isoformat(),
                    result.duration_ms,
                    result.error,
                ),
            )

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> CultureEvent:
        return CultureEvent(
            id=row["id"],
            source=row["source"],
            source_event_id=row["source_event_id"],
            venue_id=row["venue_id"],
            title=row["title"],
            start_at=datetime.fromisoformat(row["start_at"]) if row["start_at"] else None,
            price=row["price"],
            availability=row["availability"],
            url=row["url"],
            fetched_at=datetime.fromisoformat(row["last_seen_at"]),
            content_hash=row["content_hash"],
        )
