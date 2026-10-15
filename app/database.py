from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_default_db_path = str(Path(tempfile.gettempdir()) / "flyrank.db") if os.getenv("VERCEL") else "data/flyrank.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", _default_db_path))


def _connect():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10, prepare_threshold=None)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection() -> Iterator[Any]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    statements = [
        """CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY, subject TEXT NOT NULL, category TEXT NOT NULL,
            attributes_json TEXT NOT NULL, caption TEXT NOT NULL, confidence DOUBLE PRECISION NOT NULL,
            filename TEXT, content_type TEXT, image_path TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS suggestions (
            suggestion_id TEXT PRIMARY KEY, post_id TEXT NOT NULL, image_id TEXT NOT NULL,
            score DOUBLE PRECISION NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE
        )""",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_post ON suggestions(post_id)",
    ]
    with connection() as conn:
        for statement in statements:
            conn.execute(statement)


def save_image(image: dict[str, Any]) -> None:
    values = (
        image["id"], image["subject"], image["category"],
        json.dumps(image.get("attributes", [])), image["caption"], image["confidence"],
        image.get("filename"), image.get("content_type"), image.get("image_path"),
    )
    with connection() as conn:
        if DATABASE_URL:
            conn.execute(
                """INSERT INTO images
                (id, subject, category, attributes_json, caption, confidence, filename, content_type, image_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(id) DO UPDATE SET subject=EXCLUDED.subject, category=EXCLUDED.category,
                attributes_json=EXCLUDED.attributes_json, caption=EXCLUDED.caption,
                confidence=EXCLUDED.confidence, filename=EXCLUDED.filename,
                content_type=EXCLUDED.content_type, image_path=EXCLUDED.image_path""", values
            )
        else:
            conn.execute(
                """INSERT OR REPLACE INTO images
                (id, subject, category, attributes_json, caption, confidence, filename, content_type, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", values
            )


def load_images() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM images ORDER BY created_at, id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["attributes"] = json.loads(item.pop("attributes_json"))
        result.append(item)
    return result


def count_images() -> int:
    """Return the persisted image count from the configured database."""
    with connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS image_count FROM images").fetchone()
    return int(row["image_count"])


def save_suggestions(items: list[dict[str, Any]]) -> None:
    with connection() as conn:
        for item in items:
            if DATABASE_URL:
                conn.execute(
                    """INSERT INTO suggestions
                    (suggestion_id, post_id, image_id, score, decision, reason, review_status)
                    VALUES (%s, %s, %s, %s, %s, %s, COALESCE(
                        (SELECT review_status FROM suggestions WHERE suggestion_id = %s), 'pending'))
                    ON CONFLICT(suggestion_id) DO UPDATE SET
                    score=EXCLUDED.score, decision=EXCLUDED.decision, reason=EXCLUDED.reason""",
                    (item["suggestion_id"], item["post_id"], item["image_id"], item["score"],
                     item["decision"], item["reason"], item["suggestion_id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO suggestions
                    (suggestion_id, post_id, image_id, score, decision, reason, review_status)
                    VALUES (?, ?, ?, ?, ?, ?, COALESCE(
                        (SELECT review_status FROM suggestions WHERE suggestion_id = ?), 'pending'))
                    ON CONFLICT(suggestion_id) DO UPDATE SET
                    score=excluded.score, decision=excluded.decision, reason=excluded.reason""",
                    (item["suggestion_id"], item["post_id"], item["image_id"], item["score"],
                     item["decision"], item["reason"], item["suggestion_id"]),
                )


def get_suggestion(suggestion_id: str) -> dict[str, Any] | None:
    placeholder = "%s" if DATABASE_URL else "?"
    with connection() as conn:
        row = conn.execute(f"SELECT * FROM suggestions WHERE suggestion_id = {placeholder}", (suggestion_id,)).fetchone()  # nosec B608: placeholder is a fixed driver-specific parameter marker
    return dict(row) if row else None


def set_review(suggestion_id: str, status: str) -> bool:
    placeholder = "%s" if DATABASE_URL else "?"
    with connection() as conn:
        cursor = conn.execute(
            f"UPDATE suggestions SET review_status = {placeholder} WHERE suggestion_id = {placeholder}",  # nosec B608: placeholders are fixed driver-specific parameter markers
            (status, suggestion_id),
        )
        return cursor.rowcount > 0


def clear_demo_state() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM suggestions")
        conn.execute("DELETE FROM images")
