"""Note-taking and keyword search tools backed by SQLite."""

from __future__ import annotations

from db import get_connection


def save_note(text: str) -> str:
    """Save a free-form note to SQLite."""
    try:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return "Error saving note: note text cannot be empty."

        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (text) VALUES (?)",
                (cleaned_text,),
            )
            note_id = cursor.lastrowid

        preview = cleaned_text if len(cleaned_text) <= 80 else f"{cleaned_text[:77]}..."
        return f'Saved note #{note_id}: "{preview}".'
    except Exception as exc:
        return f"Error saving note: {exc}"


def search_notes(keyword: str) -> str:
    """Search saved notes by keyword (case-insensitive across Unicode text)."""
    try:
        cleaned_keyword = (keyword or "").strip()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, text, created_at FROM notes ORDER BY id DESC"
            ).fetchall()

        if not rows:
            return "No notes have been saved yet."

        if cleaned_keyword:
            needle = cleaned_keyword.casefold()
            matches = [row for row in rows if needle in row["text"].casefold()]
        else:
            matches = list(rows[:20])

        if not matches:
            return f'No notes found matching "{cleaned_keyword}".'

        lines = [
            f"[#{row['id']} | {row['created_at']}] {row['text']}"
            for row in matches[:25]
        ]
        return "\n".join(lines)
    except Exception as exc:
        return f"Error searching notes: {exc}"
