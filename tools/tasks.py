"""Task management tools backed by SQLite."""

from __future__ import annotations

from db import get_connection


def add_task(title: str, due_date: str | None = None) -> str:
    """Add a new task with an optional due date (YYYY-MM-DD)."""
    try:
        cleaned_title = (title or "").strip()
        if not cleaned_title:
            return "Error adding task: task title cannot be empty."

        cleaned_due = due_date.strip() if isinstance(due_date, str) and due_date.strip() else None

        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
                (cleaned_title, cleaned_due),
            )
            task_id = cursor.lastrowid

        due_suffix = f" (due: {cleaned_due})" if cleaned_due else ""
        return f'Added task #{task_id}: "{cleaned_title}"{due_suffix}.'
    except Exception as exc:
        return f"Error adding task: {exc}"


def list_tasks(include_completed: bool = False) -> str:
    """List pending tasks (or all tasks when include_completed is True)."""
    try:
        with get_connection() as conn:
            if include_completed:
                rows = conn.execute(
                    """
                    SELECT id, title, due_date, completed
                    FROM tasks
                    ORDER BY completed ASC,
                             CASE WHEN due_date IS NULL THEN 1 ELSE 0 END ASC,
                             due_date ASC,
                             id ASC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, title, due_date, completed
                    FROM tasks
                    WHERE completed = 0
                    ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END ASC,
                             due_date ASC,
                             id ASC
                    """
                ).fetchall()

        if not rows:
            return "No tasks found." if include_completed else "You have no pending tasks."

        lines: list[str] = []
        for row in rows:
            status = "[x]" if row["completed"] else "[ ]"
            due_part = f" (due: {row['due_date']})" if row["due_date"] else ""
            lines.append(f"{status} #{row['id']}: {row['title']}{due_part}")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error listing tasks: {exc}"


def complete_task(id: int) -> str:
    """Mark a task as completed by its numeric ID."""
    try:
        task_id = int(id)
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, title, completed FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

            if row is None:
                return f"Task #{task_id} was not found."

            if row["completed"]:
                return f'Task #{task_id} ("{row["title"]}") is already completed.'

            conn.execute(
                """
                UPDATE tasks
                SET completed = 1,
                    completed_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (task_id,),
            )

        return f'Completed task #{task_id}: "{row["title"]}".'
    except ValueError:
        return f"Error completing task: invalid task ID '{id}' (must be an integer)."
    except Exception as exc:
        return f"Error completing task: {exc}"
