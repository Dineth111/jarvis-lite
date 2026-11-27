"""Tool schemas for Claude tool calling and the run_tool() dispatcher."""

from __future__ import annotations

from typing import Any

from tools.memory import recall_facts, remember_fact
from tools.notes import save_note, search_notes
from tools.tasks import add_task, complete_task, list_tasks
from tools.youtube import play_youtube

TOOLS: list[dict[str, Any]] = [
    {
        "name": "add_task",
        "description": (
            "Add a new to-do task to the user's task list. "
            "Convert relative dates like 'tomorrow' or 'next Friday' into ISO YYYY-MM-DD format "
            "using the current date in the system prompt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Concise description of the task to perform.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Optional due date in YYYY-MM-DD format.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List the user's tasks. By default returns pending (incomplete) tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_completed": {
                    "type": "boolean",
                    "description": "Set to true only if the user also wants to see completed tasks.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark an existing task as completed using its integer task ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "Numeric ID of the task to mark complete.",
                }
            },
            "required": ["id"],
        },
    },
    {
        "name": "save_note",
        "description": "Save a quick note, thought, snippet, or piece of information for later retrieval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Full text content of the note to save.",
                }
            },
            "required": ["text"],
        },
    },
    {
        "name": "search_notes",
        "description": "Search previously saved notes using a keyword or phrase. Pass an empty string to list recent notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Keyword or phrase to search for in saved notes.",
                }
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "remember_fact",
        "description": (
            "Save or update a persistent fact about the user in long-term memory "
            "(for example: name, city, study/work details, favorite music, preferences)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short snake_case or descriptive label for the fact (e.g., 'user_name', 'favorite_drink').",
                },
                "value": {
                    "type": "string",
                    "description": "The fact value to remember.",
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_facts",
        "description": "Retrieve all facts currently stored in long-term memory.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "play_youtube",
        "description": (
            "Search YouTube for the top matching video, open it immediately in the user's browser, "
            "and return the video title and URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song title, artist, or YouTube search query (e.g., 'Believer').",
                }
            },
            "required": ["query"],
        },
    },
]

_TOOL_DISPATCH = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "save_note": save_note,
    "search_notes": search_notes,
    "remember_fact": remember_fact,
    "recall_facts": recall_facts,
    "play_youtube": play_youtube,
}


def run_tool(name: str, tool_input: dict[str, Any] | None = None) -> str:
    """Safely execute a registered tool by name and return its string result."""
    try:
        func = _TOOL_DISPATCH.get(name)
        if func is None:
            return f"Error: unknown tool '{name}'."

        kwargs = tool_input if isinstance(tool_input, dict) else {}
        result = func(**kwargs)
        return str(result)
    except TypeError as exc:
        return f"Error calling tool '{name}' with invalid arguments: {exc}"
    except Exception as exc:
        return f"Error executing tool '{name}': {exc}"
