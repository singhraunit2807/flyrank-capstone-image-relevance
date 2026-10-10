from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# Vercel's deployed source filesystem is read-only. /tmp is writable but ephemeral.
_default_db_path = "/tmp/flyrank.db" if os.getenv("VERCEL") else "data/flyrank.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", _default_db_path))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
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
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            attributes_json TEXT NOT NULL,
            caption TEXT NOT NULL,
            confidence REAL NOT NULL,
            filename TEXT,
            content_type TEXT,
            image_path TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS suggestions (
            suggestion_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            image_id TEXT NOT NULL,
            score REAL NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_suggestions_post ON suggestions(post_id);
        """)


def save_image(image: dict[str, Any]) -> None:
    with connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO images
            (id, subject, category, attributes_json, caption, confidence, filename, content_type, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (image["id"], image["subject"], image["category"],
             json.dumps(image.get("attributes", [])), image["caption"], image["confidence"],
             image.get("filename"), image.get("content_type"), image.get("image_path")),
        )


def load_images() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM images ORDER BY created_at, id").fetchall()
    return [{
        "id": row["id"], "subject": row["subject"], "category": row["category"],
        "attributes": json.loads(row["attributes_json"]), "caption": row["caption"],
        "confidence": row["confidence"], "filename": row["filename"],
        "content_type": row["content_type"], "image_path": row["image_path"],
    } for row in rows]


def save_suggestions(items: list[dict[str, Any]]) -> None:
    with connection() as conn:
        for item in items:
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
    with connection() as conn:
        row = conn.execute("SELECT * FROM suggestions WHERE suggestion_id = ?", (suggestion_id,)).fetchone()
    return dict(row) if row else None


def set_review(suggestion_id: str, status: str) -> bool:
    with connection() as conn:
        cursor = conn.execute("UPDATE suggestions SET review_status = ? WHERE suggestion_id = ?",
                              (status, suggestion_id))
        return cursor.rowcount > 0


def clear_demo_state() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM suggestions")
        conn.execute("DELETE FROM images")
