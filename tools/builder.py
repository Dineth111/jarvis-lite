"""Autonomous full-stack project builder, XAMPP controller, and local project runner."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

from tools.developer import (
    _find_vscode_executable,
    _launch_process,
    _sanitize_relative_segment,
    get_projects_root,
)


def find_xampp_root() -> Path | None:
    """Locate a local XAMPP installation directory on Windows."""
    env_dir = os.getenv("XAMPP_DIR", "").strip()
    candidates = [Path(env_dir)] if env_dir else []
    candidates.extend([Path(r"C:\xampp"), Path(r"D:\xampp"), Path(r"E:\xampp")])
    for path in candidates:
        if path and path.is_dir() and (path / "htdocs").is_dir():
            return path.resolve()
    return None


def _is_port_open(port: int) -> bool:
    """Return True if localhost:<port> is currently accepting TCP connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            return sock.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def _wait_for_port(port: int, timeout_s: float = 6.0) -> bool:
    """Poll a local TCP port briefly until it starts listening."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _is_port_open(port):
            return True
        time.sleep(0.35)
    return _is_port_open(port)


def start_xampp(include_mysql: bool = True) -> str:
    """Start XAMPP Apache (port 80) and optionally MySQL (port 3306) on Windows."""
    try:
        xampp = find_xampp_root()
        if xampp is None:
            return (
                "XAMPP installation was not found (checked C:\\xampp, D:\\xampp, E:\\xampp). "
                "Install XAMPP or set XAMPP_DIR in .env."
            )

        status_parts: list[str] = []

        # Start Apache if not already listening on port 80
        if _is_port_open(80):
            status_parts.append("Apache (:80) already running")
        else:
            httpd = xampp / "apache" / "bin" / "httpd.exe"
            apache_bat = xampp / "apache_start.bat"
            if httpd.is_file():
                _launch_process([str(httpd)])
            elif apache_bat.is_file():
                _launch_process(["cmd.exe", "/c", str(apache_bat)])
            if _wait_for_port(80, timeout_s=6.0):
                status_parts.append("Apache (:80) started")
            else:
                status_parts.append("Apache start triggered (check XAMPP Control Panel if port 80 is busy)")

        # Start MySQL if requested and not already listening on port 3306
        if include_mysql:
            if _is_port_open(3306):
                status_parts.append("MySQL (:3306) already running")
            else:
                mysqld = xampp / "mysql" / "bin" / "mysqld.exe"
                mysql_bat = xampp / "mysql_start.bat"
                if mysqld.is_file():
                    my_ini = xampp / "mysql" / "bin" / "my.ini"
                    cmd = [str(mysqld), f"--defaults-file={my_ini}", "--standalone"] if my_ini.is_file() else [str(mysqld)]
                    _launch_process(cmd)
                elif mysql_bat.is_file():
                    _launch_process(["cmd.exe", "/c", str(mysql_bat)])
                if _wait_for_port(3306, timeout_s=6.0):
                    status_parts.append("MySQL (:3306) started")
                else:
                    status_parts.append("MySQL start triggered")

        return f"XAMPP ({xampp}): " + "; ".join(status_parts) + "."
    except Exception as exc:
        return f"Error starting XAMPP: {exc}"


def _safe_write_relative_file(project_dir: Path, rel_path: str, content: str) -> Path:
    """Safely write a relative file inside `project_dir`, blocking path traversal."""
    normalized = rel_path.replace("\\", "/").strip("/")
    parts = [
        _sanitize_relative_segment(seg, "file")
        for seg in normalized.split("/")
        if seg and seg not in {".", ".."}
    ]
    if not parts:
        parts = ["index.html"]

    full_path = (project_dir.joinpath(*parts)).resolve()
    if project_dir.resolve() not in full_path.parents:
        raise ValueError(f"Unsafe file path rejected: {rel_path}")

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content or "", encoding="utf-8")
    return full_path


def _resolve_project_dir(project_path: str) -> Path | None:
    """Find an existing project folder by full path, XAMPP htdocs name, or Jarvis-Projects name."""
    raw = (project_path or "").strip()
    if not raw:
        return None

    direct = Path(raw).expanduser()
    if direct.is_dir():
        return direct.resolve()

    xampp = find_xampp_root()
    search_bases: list[Path] = []
    if xampp:
        search_bases.append(xampp / "htdocs")
    search_bases.append(get_projects_root())

    for base in search_bases:
        candidate = base / raw
        if candidate.is_dir():
            return candidate.resolve()
    return None


def _detect_stack(project_dir: Path, hint: str = "auto") -> str:
    """Detect project stack from hint or directory contents."""
    h = (hint or "auto").strip().lower()
    if h and h != "auto":
        return h

    files = {p.name.lower() for p in project_dir.iterdir() if p.is_file()}
    if any(name.endswith(".php") for name in files):
        return "php"
    if "package.json" in files:
        return "node"
    if "app.py" in files:
        text = (project_dir / "app.py").read_text(encoding="utf-8", errors="ignore").lower()
        if "streamlit" in text:
            return "streamlit"
        if "flask" in text:
            return "flask"
        if "fastapi" in text:
            return "fastapi"
        return "python"
    if "main.py" in files:
        text = (project_dir / "main.py").read_text(encoding="utf-8", errors="ignore").lower()
        if "fastapi" in text:
            return "fastapi"
        return "python"
    if "index.html" in files:
        return "html"
    return "generic"


def run_project(project_path: str, stack: str = "auto") -> str:
    """Run a local project (starts XAMPP for PHP, launches dev server or opens browser preview)."""
    try:
        project_dir = _resolve_project_dir(project_path)
        if project_dir is None:
            return f"Project directory not found: '{project_path}'."

        detected = _detect_stack(project_dir, hint=stack)

        # PHP / XAMPP stack
        if detected in {"php", "xampp", "laravel"}:
            xampp = find_xampp_root()
            htdocs = (xampp / "htdocs").resolve() if xampp else None
            if htdocs and htdocs in project_dir.parents:
                xampp_msg = start_xampp(include_mysql=True)
                rel_url_path = project_dir.relative_to(htdocs).as_posix()
                url = f"http://localhost/{rel_url_path}/"
                webbrowser.open(url)
                return f"{xampp_msg} Opened live PHP app at {url}"

            # Fallback if PHP CLI is installed outside htdocs
            php_exe = shutil.which("php")
            if php_exe:
                _launch_process([php_exe, "-S", "127.0.0.1:8080", "-t", str(project_dir)])
                time.sleep(0.8)
                webbrowser.open("http://127.0.0.1:8080/")
                return f"Started PHP built-in server for `{project_dir.name}` at http://127.0.0.1:8080/"
            return f"Saved PHP project at `{project_dir}`, but neither XAMPP nor PHP CLI was found."

        # Static HTML / CSS / JS
        if detected in {"html", "static", "frontend"}:
            index_file = project_dir / "index.html"
            if index_file.is_file():
                webbrowser.open(index_file.as_uri())
                return f"Opened live HTML preview: {index_file.as_uri()}"
            return f"No index.html found in `{project_dir}`."

        # FastAPI
        if detected == "fastapi":
            entry = "main:app" if (project_dir / "main.py").is_file() else "app:app"
            if os.name == "nt":
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_dir}"; python -m uvicorn {entry} --reload --port 8000',
                    ]
                )
                time.sleep(1.5)
                webbrowser.open("http://127.0.0.1:8000/docs")
                return f"Launched FastAPI server for `{project_dir.name}` and opened http://127.0.0.1:8000/docs"

        # Streamlit
        if detected == "streamlit":
            entry_file = "app.py" if (project_dir / "app.py").is_file() else "main.py"
            if os.name == "nt":
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_dir}"; python -m streamlit run {entry_file} --server.port 8502',
                    ]
                )
                return f"Launched Streamlit app `{entry_file}` on http://localhost:8502"

        # Node / React / Vite
        if detected in {"node", "react", "vite", "nextjs"}:
            if os.name == "nt":
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_dir}"; npm install; npm run dev',
                    ]
                )
                return f"Opened terminal running `npm install && npm run dev` in `{project_dir}`."

        # Generic Python script / Flask
        if detected in {"python", "flask"}:
            entry_file = "app.py" if (project_dir / "app.py").is_file() else "main.py"
            if os.name == "nt" and (project_dir / entry_file).is_file():
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoExit",
                        "-Command",
                        f'Set-Location "{project_dir}"; python {entry_file}',
                    ]
                )
                return f"Running `{entry_file}` in a new PowerShell window for `{project_dir.name}`."

        return f"Project `{project_dir}` is ready (stack: {detected}). Open it in VS Code to run custom build steps."
    except Exception as exc:
        return f"Error running project: {exc}"


def init_project_workspace(project_name: str, stack: str = "html") -> str:
    """Create the project folder (XAMPP htdocs for PHP, else Jarvis-Projects) and open VS Code FIRST so the user can watch files appear live."""
    try:
        safe_name = _sanitize_relative_segment(project_name, "jarvis-app")
        stack_key = (stack or "html").strip().lower()
        xampp = find_xampp_root()
        if stack_key in {"php", "xampp", "laravel"} and xampp is not None:
            project_dir = (xampp / "htdocs" / safe_name).resolve()
        else:
            project_dir = (get_projects_root() / safe_name).resolve()

        project_dir.mkdir(parents=True, exist_ok=True)

        vscode = _find_vscode_executable()
        if vscode:
            _launch_process([vscode, str(project_dir)])
            return (
                f"Workspace ready at `{project_dir}` (stack: {stack_key}) and opened in VS Code. "
                "Now call write_project_file for each file so the user can watch them appear live."
            )
        return f"Workspace ready at `{project_dir}` (stack: {stack_key}). VS Code not found on PATH."
    except Exception as exc:
        return f"Error initializing project workspace: {exc}"


def build_full_project(
    project_name: str,
    stack: str,
    files: dict[str, str],
    open_in_vscode: bool = True,
    auto_run: bool = True,
) -> str:
    """Create a complete multi-file project in the right location (XAMPP htdocs for PHP, else Jarvis-Projects), open in VS Code, and run it."""
    try:
        safe_name = _sanitize_relative_segment(project_name, "jarvis-app")
        stack_key = (stack or "html").strip().lower()
        if not isinstance(files, dict) or not files:
            return "Error building project: `files` must be a non-empty object mapping relative paths to source code."

        # Automatically route PHP projects to XAMPP htdocs when available
        xampp = find_xampp_root()
        if stack_key in {"php", "xampp", "laravel"} and xampp is not None:
            project_dir = (xampp / "htdocs" / safe_name).resolve()
        else:
            project_dir = (get_projects_root() / safe_name).resolve()

        project_dir.mkdir(parents=True, exist_ok=True)

        written_paths: list[Path] = []
        for rel_path, content in files.items():
            written_paths.append(_safe_write_relative_file(project_dir, str(rel_path), str(content)))

        notes: list[str] = [
            f"Built `{stack_key}` project `{safe_name}` at `{project_dir}` ({len(written_paths)} file(s): "
            + ", ".join(p.relative_to(project_dir).as_posix() for p in written_paths[:10])
            + ")."
        ]

        # Open project folder + main entry file in VS Code
        if open_in_vscode:
            vscode = _find_vscode_executable()
            if vscode:
                entry = next(
                    (
                        p
                        for p in written_paths
                        if p.name.lower() in {"index.php", "index.html", "main.py", "app.py", "app.jsx"}
                    ),
                    written_paths[0],
                )
                _launch_process([vscode, str(project_dir), str(entry)])
                notes.append("Opened in VS Code.")
            else:
                notes.append("VS Code not found on PATH.")

        # Auto-start server / XAMPP / browser preview
        if auto_run:
            run_msg = run_project(str(project_dir), stack=stack_key)
            notes.append(run_msg)

        return " ".join(notes)
    except Exception as exc:
        return f"Error building full project: {exc}"


def write_project_file(
    project_path: str,
    relative_file_path: str,
    content: str,
    open_in_vscode: bool = True,
) -> str:
    """Add or update a file inside an existing project (in XAMPP htdocs or Jarvis-Projects)."""
    try:
        project_dir = _resolve_project_dir(project_path)
        if project_dir is None:
            return f"Project not found: '{project_path}'."

        saved = _safe_write_relative_file(project_dir, relative_file_path, content)
        msg = f"Updated `{saved}`."
        if open_in_vscode:
            vscode = _find_vscode_executable()
            if vscode:
                _launch_process([vscode, str(project_dir), str(saved)])
                msg += " Opened in VS Code."
        return msg
    except Exception as exc:
        return f"Error writing project file: {exc}"
