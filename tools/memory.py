"""Long-term key-value fact memory tools backed by SQLite."""

from __future__ import annotations

from db import get_connection


def remember_fact(key: str, value: str) -> str:
    """Store or update a persistent user fact (e.g., name, preferences, routines)."""
    try:
        cleaned_key = (key or "").strip()
        cleaned_value = (value or "").strip()
        if not cleaned_key or not cleaned_value:
            return "Error remembering fact: both 'key' and 'value' must be non-empty."

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO facts (key, value, updated_at)
                VALUES (?, ?, datetime('now', 'localtime'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (cleaned_key, cleaned_value),
            )

        return f"Remembered fact — {cleaned_key}: {cleaned_value}"
    except Exception as exc:
        return f"Error remembering fact: {exc}"


def recall_facts() -> str:
    """Retrieve all stored long-term facts as a readable bullet list."""
    try:
        facts = get_all_facts()
        if not facts:
            return "No facts stored in long-term memory yet."

        return "\n".join(f"- {key}: {value}" for key, value in facts)
    except Exception as exc:
        return f"Error recalling facts: {exc}"


def get_all_facts() -> list[tuple[str, str]]:
    """Return all (key, value) pairs ordered alphabetically for prompt injection."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value FROM facts ORDER BY key ASC"
            ).fetchall()
        return [(str(row["key"]), str(row["value"])) for row in rows]
    except Exception:
        return []
