"""Developer & Windows PC automation tools (apps, VS Code, code file scaffolding, websites)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path

try:
    import winreg
except ImportError:  # Non-Windows platforms
    winreg = None


def _get_desktop_dir() -> Path:
    """Resolve the user's real Desktop folder (handles OneDrive Desktop on Windows)."""
    home = Path.home()
    for candidate in (home / "OneDrive" / "Desktop", home / "Desktop"):
        if candidate.is_dir():
            return candidate
    return home


def get_projects_root() -> Path:
    """Return the root folder where Jarvis creates new code files/projects."""
    custom = os.getenv("JARVIS_PROJECTS_DIR", "").strip()
    if custom:
        root = Path(custom).expanduser().resolve()
    else:
        root = (_get_desktop_dir() / "Jarvis-Projects").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _find_vscode_executable() -> str | None:
    """Locate the VS Code CLI or executable on Windows/macOS/Linux."""
    for cmd in ("code.cmd", "code"):
        found = shutil.which(cmd)
        if found:
            return found

    local_app_data = os.getenv("LOCALAPPDATA", "")
    program_files = os.getenv("ProgramFiles", r"C:\Program Files")
    candidates = [
        Path(local_app_data) / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd",
        Path(local_app_data) / "Programs" / "Microsoft VS Code" / "Code.exe",
        Path(program_files) / "Microsoft VS Code" / "bin" / "code.cmd",
        Path(program_files) / "Microsoft VS Code" / "Code.exe",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def _protocol_registered(scheme: str) -> bool:
    """Check whether a Windows URI protocol handler (e.g., 'whatsapp') is installed."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, scheme):
            return True
    except OSError:
        return False


def _launch_process(args: list[str]) -> None:
    """Launch a detached GUI process safely without blocking Streamlit."""
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )


_WEB_SHORTCUTS: dict[str, str] = {
    "whatsapp web": "https://web.whatsapp.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
    "linkedin": "https://www.linkedin.com",
    "google": "https://www.google.com",
}


def open_app(app_name: str) -> str:
    """Open a common desktop app (VS Code, WhatsApp, Chrome, Terminal, Notepad, etc.)."""
    try:
        raw = (app_name or "").strip()
        if not raw:
            return "Error opening app: app name cannot be empty."

        key = raw.lower()

        # VS Code
        if key in {"vs code", "vscode", "code", "visual studio code"}:
            vscode = _find_vscode_executable()
            if vscode:
                _launch_process([vscode])
                return "Opened Visual Studio Code."
            return "Could not find VS Code installed on this PC."

        # WhatsApp (Desktop app if registered, otherwise WhatsApp Web)
        if key in {"whatsapp", "whats app", "whtsapp", "wa"}:
            if os.name == "nt" and _protocol_registered("whatsapp"):
                os.startfile("whatsapp:")
                return "Opened WhatsApp Desktop app."
            webbrowser.open("https://web.whatsapp.com")
            return "Opened WhatsApp Web in your browser (https://web.whatsapp.com)."

        # Spotify
        if key == "spotify":
            if os.name == "nt" and _protocol_registered("spotify"):
                os.startfile("spotify:")
                return "Opened Spotify."
            webbrowser.open("https://open.spotify.com")
            return "Opened Spotify Web Player (https://open.spotify.com)."

        # Discord
        if key == "discord":
            if os.name == "nt" and _protocol_registered("discord"):
                os.startfile("discord:")
                return "Opened Discord."
            webbrowser.open("https://discord.com/app")
            return "Opened Discord Web (https://discord.com/app)."

        # Windows built-in / developer apps
        windows_apps: dict[str, list[str]] = {
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "calc": ["calc.exe"],
            "explorer": ["explorer.exe"],
            "file explorer": ["explorer.exe"],
            "terminal": ["wt.exe"] if shutil.which("wt.exe") else ["powershell.exe"],
            "powershell": ["powershell.exe"],
            "cmd": ["cmd.exe"],
            "command prompt": ["cmd.exe"],
            "chrome": ["chrome.exe"],
            "google chrome": ["chrome.exe"],
            "edge": ["msedge.exe"],
            "task manager": ["taskmgr.exe"],
        }
        if key in windows_apps:
            cmd = windows_apps[key]
            exe = shutil.which(cmd[0])
            if exe:
                _launch_process([exe, *cmd[1:]])
                return f"Opened {raw}."
            if os.name == "nt":
                os.startfile(cmd[0])
                return f"Opened {raw}."

        # Web shortcuts fallback
        if key in _WEB_SHORTCUTS:
            url = _WEB_SHORTCUTS[key]
            webbrowser.open(url)
            return f"Opened {raw} ({url})."

        # Try launching by executable on PATH
        direct_exe = shutil.which(raw)
        if direct_exe:
            _launch_process([direct_exe])
            return f"Opened {raw}."

        return (
            f"Could not find an installed app named '{raw}'. "
            "Supported examples: VS Code, WhatsApp, Chrome, Edge, Terminal, Notepad, Spotify, Discord, GitHub."
        )
    except Exception as exc:
        return f"Error opening '{app_name}': {exc}"


def open_website(url_or_name: str) -> str:
    """Open a website URL or common developer shortcut in the default browser."""
    try:
        raw = (url_or_name or "").strip()
        if not raw:
            return "Error opening website: URL or site name cannot be empty."

        lower = raw.lower()
        if lower in _WEB_SHORTCUTS:
            url = _WEB_SHORTCUTS[lower]
        elif raw.startswith(("http://", "https://")):
            url = raw
        elif lower.startswith("localhost"):
            url = f"http://{raw}"
        elif "." in raw and " " not in raw:
            url = f"https://{raw}"
        else:
            url = f"https://www.google.com/search?q={raw.replace(' ', '+')}"

        webbrowser.open(url)
        return f"Opened {url} in your browser."
    except Exception as exc:
        return f"Error opening website: {exc}"


def _sanitize_relative_segment(name: str, fallback: str) -> str:
    """Sanitize a filename or folder segment to prevent path traversal."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (name or "").strip())
    cleaned = cleaned.strip(". ")
    return cleaned or fallback


def create_code_file(
    filename: str,
    content: str,
    folder: str | None = None,
    open_in_vscode: bool = True,
    open_in_browser: bool = False,
) -> str:
    """Create a code file (HTML/CSS/JS/Python/etc.) in Desktop/Jarvis-Projects and open it in VS Code."""
    try:
        safe_filename = _sanitize_relative_segment(filename, "index.html")
        root = get_projects_root()

        if folder and folder.strip():
            safe_folder = _sanitize_relative_segment(folder, "project")
            target_dir = (root / safe_folder).resolve()
        else:
            target_dir = root

        # Guard against escaping the projects root
        if root not in target_dir.parents and target_dir != root:
            return "Error creating file: invalid folder path."

        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = (target_dir / safe_filename).resolve()
        file_path.write_text(content or "", encoding="utf-8")

        actions: list[str] = [f"Created `{file_path}`"]

        if open_in_vscode:
            vscode = _find_vscode_executable()
            if vscode:
                _launch_process([vscode, str(target_dir), str(file_path)])
                actions.append("opened in VS Code")
            else:
                actions.append("VS Code was not found on PATH")

        if open_in_browser and file_path.suffix.lower() in {".html", ".htm"}:
            webbrowser.open(file_path.as_uri())
            actions.append("opened live preview in browser")

        return " and ".join(actions) + "."
    except Exception as exc:
        return f"Error creating code file: {exc}"


def open_in_vscode(path: str) -> str:
    """Open an existing file or project folder in VS Code."""
    try:
        vscode = _find_vscode_executable()
        if not vscode:
            return "Error: Visual Studio Code was not found on this PC."

        raw = (path or "").strip()
        if not raw:
            _launch_process([vscode])
            return "Opened Visual Studio Code."

        candidate = Path(raw).expanduser()
        if not candidate.exists():
            # Also check inside Desktop/Jarvis-Projects and Desktop
            for base in (get_projects_root(), _get_desktop_dir()):
                alt = base / raw
                if alt.exists():
                    candidate = alt
                    break

        if not candidate.exists():
            return f"Path not found: '{raw}'."

        _launch_process([vscode, str(candidate.resolve())])
        return f"Opened `{candidate.resolve()}` in VS Code."
    except Exception as exc:
        return f"Error opening in VS Code: {exc}"
