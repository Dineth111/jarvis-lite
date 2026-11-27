"""SQLite storage setup and connection helpers for Jarvis Lite."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# Default database lives in the project root (ignored via *.db in .gitignore).
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    due_date TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed, due_date);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id, id);
"""

_initialized_paths: set[Path] = set()


def get_db_path() -> Path:
    """Return the configured SQLite database file path."""
    custom_path = os.getenv("JARVIS_DB_PATH")
    if custom_path:
        return Path(custom_path).expanduser().resolve()
    return DEFAULT_DB_PATH


def init_db(db_path: Path | None = None) -> None:
    """Create the tasks, notes, facts, and chat_history tables if they do not exist."""
    target = (db_path or get_db_path()).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
        _initialized_paths.add(target)
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a short-lived, thread-safe SQLite connection with Row access."""
    target = (db_path or get_db_path()).resolve()
    if target not in _initialized_paths or not target.exists():
        init_db(target)

    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_chat_message(
    session_id: str,
    role: str,
    content: str,
    tool_calls: list[dict[str, Any]] | None = None,
) -> None:
    """Persist a single chat turn into SQLite chat_history."""
    payload = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_history (session_id, role, content, tool_calls_json)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, payload),
        )


def list_chat_sessions(limit: int = 20) -> list[dict[str, Any]]:
    """Return recent chat sessions with their first user prompt preview and message count."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                session_id,
                COUNT(*) AS message_count,
                MIN(created_at) AS started_at,
                MAX(created_at) AS last_at,
                (
                    SELECT content FROM chat_history ch2
                    WHERE ch2.session_id = ch1.session_id AND ch2.role = 'user'
                    ORDER BY ch2.id ASC LIMIT 1
                ) AS preview
            FROM chat_history ch1
            GROUP BY session_id
            ORDER BY MAX(id) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Load all persisted messages for a given chat session."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, tool_calls_json, created_at
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    messages: list[dict[str, Any]] = []
    for row in rows:
        tool_calls = []
        if row["tool_calls_json"]:
            try:
                tool_calls = json.loads(row["tool_calls_json"])
            except Exception:
                tool_calls = []
        messages.append(
            {
                "role": row["role"],
                "content": row["content"],
                "tool_calls": tool_calls,
                "created_at": row["created_at"],
            }
        )
    return messages


def delete_chat_session(session_id: str) -> None:
    """Delete a single chat session from persistent history."""
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
