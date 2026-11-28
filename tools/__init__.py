"""Tool schemas for Claude tool calling and the run_tool() dispatcher."""

from __future__ import annotations

from typing import Any

from tools.builder import (
    build_full_project,
    init_project_workspace,
    run_project,
    start_xampp,
    write_project_file,
)
from tools.developer import (
    check_dev_ports,
    create_code_file,
    create_github_repo,
    create_project_template,
    git_commit_and_push,
    git_status,
    google_search,
    list_my_projects,
    open_app,
    open_in_vscode,
    open_website,
)
from tools.memory import recall_facts, remember_fact
from tools.notes import save_note, search_notes
from tools.tasks import add_task, complete_task, list_tasks
from tools.vision import inspect_my_screen
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
    {
        "name": "open_app",
        "description": (
            "Open a desktop application on the user's PC (such as WhatsApp, VS Code, Chrome, "
            "Edge, Terminal, Notepad, Calculator, File Explorer, Spotify, or Discord)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the app to open (e.g., 'WhatsApp', 'VS Code', 'Terminal').",
                }
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "open_website",
        "description": (
            "Open a website URL or developer shortcut (e.g., 'github', 'whatsapp web', "
            "'stackoverflow', 'localhost:3000', or any full URL) in the browser."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url_or_name": {
                    "type": "string",
                    "description": "Website name or URL to open.",
                }
            },
            "required": ["url_or_name"],
        },
    },
    {
        "name": "create_code_file",
        "description": (
            "Create a complete, ready-to-run code file (e.g., a decorated HTML/CSS page, JS app, "
            "or Python script) inside Desktop/Jarvis-Projects, open it directly in VS Code, and "
            "optionally open HTML files in the browser for instant live preview."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "File name including extension (e.g., 'index.html', 'app.py').",
                },
                "content": {
                    "type": "string",
                    "description": "Full, clean, well-formatted source code to write into the file.",
                },
                "folder": {
                    "type": "string",
                    "description": "Optional subfolder name inside Desktop/Jarvis-Projects (e.g., 'portfolio-site').",
                },
                "open_in_vscode": {
                    "type": "boolean",
                    "description": "Whether to open the folder and file in VS Code immediately (default true).",
                },
                "open_in_browser": {
                    "type": "boolean",
                    "description": "Set to true for HTML pages so the user sees the styled page live in their browser.",
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "open_in_vscode",
        "description": "Open an existing file or project folder in Visual Studio Code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path or folder name inside Desktop / Desktop/Jarvis-Projects.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "git_status",
        "description": "Check the current Git branch, modified/untracked files, and last 3 commits for a local repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Optional repo folder name or path (defaults to current jarvis-lite repo).",
                }
            },
            "required": [],
        },
    },
    {
        "name": "git_commit_and_push",
        "description": "Stage non-ignored changes, create a Git commit with `message`, and optionally push to remote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Clear Git commit message.",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Optional repo folder name or path (defaults to current jarvis-lite repo).",
                },
                "push": {
                    "type": "boolean",
                    "description": "Whether to push after committing (default true).",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "create_project_template",
        "description": (
            "Scaffold a complete multi-file developer starter project inside Desktop/Jarvis-Projects "
            "and open it in VS Code. Templates: 'fastapi', 'html-portfolio', 'python-cli', 'react-vite'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Folder name for the new project (e.g., 'my-api', 'portfolio-v2').",
                },
                "template": {
                    "type": "string",
                    "description": "Template name: 'fastapi', 'html-portfolio', 'python-cli', or 'react-vite'.",
                },
                "open_in_vscode": {
                    "type": "boolean",
                    "description": "Whether to open the scaffolded project in VS Code (default true).",
                },
            },
            "required": ["project_name", "template"],
        },
    },
    {
        "name": "list_my_projects",
        "description": "List the developer's local project folders on Desktop/Jarvis-Projects and Desktop/Project.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_dev_ports",
        "description": "Check which common localhost developer server ports (3000, 5173, 8000, 8501, 11434, etc.) are active.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "init_project_workspace",
        "description": (
            "Step 1 of live project building: create the project folder (C:\\xampp\\htdocs\\<name> for PHP, "
            "or Desktop\\Jarvis-Projects\\<name> for other stacks) and open VS Code immediately so the user "
            "can watch files being created live."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Clean folder slug (e.g., 'simple-lms', 'portfolio').",
                },
                "stack": {
                    "type": "string",
                    "description": "Primary stack: 'php', 'html', 'python', 'fastapi', 'flask', 'streamlit', 'node', or 'react'.",
                },
            },
            "required": ["project_name", "stack"],
        },
    },
    {
        "name": "build_full_project",
        "description": (
            "Build a COMPLETE multi-file project in ANY language/stack (php, html, python, fastapi, flask, "
            "streamlit, node, react). For PHP projects, automatically saves inside XAMPP htdocs "
            "(C:\\xampp\\htdocs\\<project_name>), opens it in VS Code, starts XAMPP Apache/MySQL, and opens "
            "http://localhost/<project_name>/ in the browser. For other stacks, saves in Desktop/Jarvis-Projects, "
            "opens VS Code, and runs the app."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Clean folder slug for the project (e.g., 'simple-lms', 'shop-php', 'portfolio').",
                },
                "stack": {
                    "type": "string",
                    "description": "Primary stack: 'php', 'html', 'python', 'fastapi', 'flask', 'streamlit', 'node', or 'react'.",
                },
                "files": {
                    "type": "object",
                    "description": "Object mapping relative file paths (e.g., 'index.php', 'css/style.css', 'schema.sql') to full source code strings.",
                    "additionalProperties": {"type": "string"},
                },
                "open_in_vscode": {
                    "type": "boolean",
                    "description": "Open the built project directly in VS Code (default true).",
                },
                "auto_run": {
                    "type": "boolean",
                    "description": "Automatically start XAMPP/dev server and open the live app in the browser (default true).",
                },
            },
            "required": ["project_name", "stack", "files"],
        },
    },
    {
        "name": "write_project_file",
        "description": (
            "Add or edit a specific file inside an existing project (in XAMPP htdocs or Desktop/Jarvis-Projects) "
            "and open it in VS Code. Use this to iteratively add features or fix bugs until the project is 100% complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Project folder name (e.g., 'simple-lms') or full path.",
                },
                "relative_file_path": {
                    "type": "string",
                    "description": "Relative file path inside the project (e.g., 'login.php', 'css/style.css').",
                },
                "content": {
                    "type": "string",
                    "description": "Complete updated file contents.",
                },
                "open_in_vscode": {
                    "type": "boolean",
                    "description": "Open the updated file in VS Code (default true).",
                },
            },
            "required": ["project_path", "relative_file_path", "content"],
        },
    },
    {
        "name": "run_project",
        "description": (
            "Start and open a local project: for PHP starts XAMPP Apache/MySQL and opens http://localhost/<project>/; "
            "for HTML opens browser preview; for FastAPI/Python/Streamlit/Node launches the dev server."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Project folder name (in XAMPP htdocs or Jarvis-Projects) or full path.",
                },
                "stack": {
                    "type": "string",
                    "description": "Optional stack override ('auto', 'php', 'html', 'fastapi', 'python', 'streamlit', 'node').",
                },
            },
            "required": ["project_path"],
        },
    },
    {
        "name": "start_xampp",
        "description": "Start local XAMPP Apache (:80) and MySQL (:3306) services on Windows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_mysql": {
                    "type": "boolean",
                    "description": "Also start MySQL (:3306) in addition to Apache (:80) (default true).",
                }
            },
            "required": [],
        },
    },
    {
        "name": "inspect_my_screen",
        "description": (
            "Capture a live screenshot of the user's current computer screen and analyze it with Vision AI. "
            "Use whenever the user says 'look at my screen', 'check this error on my screen', or 'mage screen eka balanna'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "What to look for or solve on the user's screen.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "google_search",
        "description": "Open Google Search in the browser for any query (e.g., 'go to google and search ...').",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to look up on Google.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_github_repo",
        "description": (
            "Initialize Git in a local project folder, commit all non-ignored files, create a brand-new "
            "GitHub repository, and push the code automatically."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Name for the new GitHub repository (e.g., 'simple-lms').",
                },
                "project_path": {
                    "type": "string",
                    "description": "Optional local project folder name or path (defaults to current workspace).",
                },
                "private": {
                    "type": "boolean",
                    "description": "Set to true to create a private GitHub repo (default false = public).",
                },
                "commit_message": {
                    "type": "string",
                    "description": "Initial commit message (default 'Initial commit').",
                },
            },
            "required": ["repo_name"],
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
    "open_app": open_app,
    "open_website": open_website,
    "create_code_file": create_code_file,
    "open_in_vscode": open_in_vscode,
    "git_status": git_status,
    "git_commit_and_push": git_commit_and_push,
    "create_project_template": create_project_template,
    "list_my_projects": list_my_projects,
    "check_dev_ports": check_dev_ports,
    "init_project_workspace": init_project_workspace,
    "build_full_project": build_full_project,
    "write_project_file": write_project_file,
    "run_project": run_project,
    "start_xampp": start_xampp,
    "inspect_my_screen": inspect_my_screen,
    "google_search": google_search,
    "create_github_repo": create_github_repo,
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
