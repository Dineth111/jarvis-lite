"""SQLite storage setup and connection helpers for Jarvis Lite."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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

CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed, due_date);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
"""

_initialized_paths: set[Path] = set()


def get_db_path() -> Path:
    """Return the configured SQLite database file path."""
    custom_path = os.getenv("JARVIS_DB_PATH")
    if custom_path:
        return Path(custom_path).expanduser().resolve()
    return DEFAULT_DB_PATH


def init_db(db_path: Path | None = None) -> None:
    """Create the tasks, notes, and facts tables if they do not exist."""
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
