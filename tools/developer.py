"""Developer & Windows PC automation tools (apps, VS Code, code file scaffolding, websites)."""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import urllib.parse
import urllib.request
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
    "claude": "https://claude.ai",
    "deepseek": "https://chat.deepseek.com",
    "linkedin": "https://www.linkedin.com",
    "google": "https://www.google.com",
    "google maps": "https://maps.google.com",
    "maps": "https://maps.google.com",
    "google translate": "https://translate.google.com",
    "translate": "https://translate.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "w3schools": "https://www.w3schools.com",
    "sliit": "https://courseweb.sliit.lk",
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


def _resolve_repo_dir(repo_path: str | None = None) -> Path:
    """Resolve a git repository directory from an explicit path, project name, or current workspace."""
    workspace_root = Path(__file__).resolve().parent.parent
    raw = (repo_path or "").strip()
    if not raw or raw.lower() in {".", "current", "here", "jarvis-lite", "this"}:
        return workspace_root

    candidate = Path(raw).expanduser()
    if candidate.is_dir():
        return candidate.resolve()

    search_roots = [
        get_projects_root(),
        _get_desktop_dir() / "Project",
        _get_desktop_dir() / "Project" / "AI-ML project",
        _get_desktop_dir(),
    ]
    for base in search_roots:
        alt = base / raw
        if alt.is_dir():
            return alt.resolve()

    return candidate.resolve()


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a git command safely without shell=True."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=25,
    )


def git_status(repo_path: str | None = None) -> str:
    """Check current Git branch, working tree changes, and last 3 commits."""
    try:
        repo = _resolve_repo_dir(repo_path)
        if not repo.is_dir():
            return f"Repository folder not found: `{repo}`."

        branch_res = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
        if branch_res.returncode != 0:
            return f"`{repo}` is not a Git repository ({branch_res.stderr.strip()})."

        branch = branch_res.stdout.strip()
        status_res = _run_git(["status", "--short"], repo)
        log_res = _run_git(["log", "-n", "3", "--oneline"], repo)

        changes = status_res.stdout.strip() or "(working tree clean)"
        commits = log_res.stdout.strip() or "(no commits yet)"

        return (
            f"Repo: {repo.name} (branch: {branch})\n"
            f"Changes:\n{changes}\n\n"
            f"Recent commits:\n{commits}"
        )
    except Exception as exc:
        return f"Error checking git status: {exc}"


def git_commit_and_push(
    message: str,
    repo_path: str | None = None,
    push: bool = True,
) -> str:
    """Stage tracked/untracked non-ignored changes, commit, and optionally push."""
    try:
        commit_msg = (message or "").strip()
        if not commit_msg:
            return "Error: commit message cannot be empty."

        repo = _resolve_repo_dir(repo_path)
        if not repo.is_dir():
            return f"Repository folder not found: `{repo}`."

        add_res = _run_git(["add", "."], repo)
        if add_res.returncode != 0:
            return f"Error staging files: {add_res.stderr.strip()}"

        diff_res = _run_git(["diff", "--cached", "--name-only"], repo)
        staged = [line for line in diff_res.stdout.splitlines() if line.strip()]
        if not staged:
            return f"Nothing to commit in `{repo.name}` — working tree is already clean."

        commit_res = _run_git(["commit", "-m", commit_msg], repo)
        if commit_res.returncode != 0:
            return f"Git commit failed: {(commit_res.stderr or commit_res.stdout).strip()}"

        summary = f"Committed {len(staged)} file(s) in `{repo.name}`: \"{commit_msg}\"."
        if push:
            push_res = _run_git(["push"], repo)
            if push_res.returncode != 0:
                return f"{summary} Push failed: {(push_res.stderr or push_res.stdout).strip()}"
            summary += " Pushed to remote."
        return summary
    except Exception as exc:
        return f"Error during git commit/push: {exc}"


_PROJECT_TEMPLATES: dict[str, dict[str, str]] = {
    "fastapi": {
        "main.py": (
            'from fastapi import FastAPI\n\n'
            'app = FastAPI(title="FastAPI Starter")\n\n\n'
            '@app.get("/")\n'
            'def health_check():\n'
            '    return {"status": "online", "message": "Hello from J.A.R.V.I.S. DEV!"}\n'
        ),
        "requirements.txt": "fastapi>=0.115.0\nuvicorn[standard]>=0.30.0\n",
        ".gitignore": "__pycache__/\nvenv/\n.env\n",
        "README.md": "# FastAPI Starter\n\nRun with:\n```bash\npip install -r requirements.txt\nuvicorn main:app --reload\n```\n",
    },
    "python-cli": {
        "main.py": (
            'import argparse\n\n\n'
            'def main() -> None:\n'
            '    parser = argparse.ArgumentParser(description="Python CLI Starter")\n'
            '    parser.add_argument("--name", default="Developer")\n'
            '    args = parser.parse_args()\n'
            '    print(f"Hello, {args.name}!")\n\n\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        ),
        ".gitignore": "__pycache__/\nvenv/\n.env\n",
        "README.md": "# Python CLI Starter\n\nRun with `python main.py --name Dineth`.\n",
    },
    "html-portfolio": {
        "index.html": (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "  <meta charset=\"UTF-8\" />\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n"
            "  <title>Developer Portfolio</title>\n"
            "  <link rel=\"stylesheet\" href=\"styles.css\" />\n"
            "</head>\n<body>\n"
            "  <main class=\"hero\">\n"
            "    <span class=\"badge\">AVAILABLE FOR PROJECTS</span>\n"
            "    <h1>Hi, I'm a Full-Stack & AI Developer</h1>\n"
            "    <p>Building fast web apps, intelligent agents, and clean developer tools.</p>\n"
            "    <button id=\"pingBtn\">Say Hello</button>\n"
            "  </main>\n"
            "  <script src=\"app.js\"></script>\n"
            "</body>\n</html>\n"
        ),
        "styles.css": (
            "* { box-sizing: border-box; margin: 0; padding: 0; }\n"
            "body { min-height: 100vh; display: grid; place-items: center; font-family: system-ui, sans-serif; "
            "background: radial-gradient(circle at top, #0c2340, #050a14 70%); color: #e6f7ff; }\n"
            ".hero { max-width: 680px; padding: 48px; text-align: center; border-radius: 20px; "
            "background: rgba(10, 24, 46, 0.78); border: 1px solid rgba(0, 212, 255, 0.35); "
            "box-shadow: 0 0 40px rgba(0, 200, 255, 0.16); }\n"
            ".badge { display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: 12px; "
            "letter-spacing: 0.14em; color: #66ffd1; border: 1px solid rgba(102, 255, 209, 0.45); margin-bottom: 18px; }\n"
            "h1 { font-size: 2.3rem; margin-bottom: 14px; }\n"
            "p { color: #9ad7f0; line-height: 1.6; margin-bottom: 24px; }\n"
            "button { padding: 12px 26px; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; "
            "background: linear-gradient(90deg, #00c8ff, #00e6a8); color: #03101d; }\n"
        ),
        "app.js": (
            'document.getElementById("pingBtn").addEventListener("click", () => {\n'
            '  alert("Scaffolded by J.A.R.V.I.S. DEV!");\n'
            '});\n'
        ),
    },
    "react-vite": {
        "package.json": (
            '{\n'
            '  "name": "jarvis-react-starter",\n'
            '  "private": true,\n'
            '  "version": "0.1.0",\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "vite",\n'
            '    "build": "vite build"\n'
            '  },\n'
            '  "dependencies": {\n'
            '    "react": "^19.0.0",\n'
            '    "react-dom": "^19.0.0"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "@vitejs/plugin-react": "^4.3.0",\n'
            '    "vite": "^6.0.0"\n'
            '  }\n'
            '}\n'
        ),
        "index.html": (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '  <meta charset="UTF-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            '  <title>React Starter</title>\n'
            '</head>\n<body>\n'
            '  <div id="root"></div>\n'
            '  <script type="module" src="/src/main.jsx"></script>\n'
            '</body>\n</html>\n'
        ),
        "src/main.jsx": (
            'import React from "react";\n'
            'import ReactDOM from "react-dom/client";\n'
            'import App from "./App.jsx";\n\n'
            'ReactDOM.createRoot(document.getElementById("root")).render(<App />);\n'
        ),
        "src/App.jsx": (
            'export default function App() {\n'
            '  return (\n'
            '    <main style={{ fontFamily: "system-ui", padding: 40 }}>\n'
            '      <h1>React + Vite Starter</h1>\n'
            '      <p>Scaffolded by J.A.R.V.I.S. DEV.</p>\n'
            '    </main>\n'
            '  );\n'
            '}\n'
        ),
    },
}


def create_project_template(
    project_name: str,
    template: str = "fastapi",
    open_in_vscode: bool = True,
) -> str:
    """Scaffold a complete multi-file starter project (fastapi, html-portfolio, python-cli, react-vite)."""
    try:
        safe_name = _sanitize_relative_segment(project_name, "new-project")
        tpl_key = (template or "fastapi").strip().lower()
        files = _PROJECT_TEMPLATES.get(tpl_key)
        if files is None:
            available = ", ".join(sorted(_PROJECT_TEMPLATES.keys()))
            return f"Unknown template '{template}'. Available templates: {available}."

        target_dir = (get_projects_root() / safe_name).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        created_files: list[str] = []
        for rel_path, content in files.items():
            full_path = target_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            created_files.append(rel_path)

        msg = f"Scaffolded `{tpl_key}` project at `{target_dir}` with files: {', '.join(created_files)}."
        if open_in_vscode:
            vscode = _find_vscode_executable()
            if vscode:
                _launch_process([vscode, str(target_dir)])
                msg += " Opened in VS Code."
        return msg
    except Exception as exc:
        return f"Error scaffolding project: {exc}"


def list_my_projects() -> str:
    """List local project folders from Desktop/Jarvis-Projects and Desktop/Project."""
    try:
        roots = [
            get_projects_root(),
            _get_desktop_dir() / "Project",
            _get_desktop_dir() / "Project" / "AI-ML project",
        ]
        found: list[str] = []
        seen: set[Path] = set()
        for root in roots:
            if not root.is_dir():
                continue
            for entry in sorted(root.iterdir()):
                if entry.is_dir() and not entry.name.startswith(".") and entry.resolve() not in seen:
                    seen.add(entry.resolve())
                    is_git = " [git]" if (entry / ".git").exists() else ""
                    found.append(f"- {entry.name}{is_git} ({entry.resolve()})")

        if not found:
            return f"No projects found yet. New projects are created in `{get_projects_root()}`."
        return "Local projects:\n" + "\n".join(found[:25])
    except Exception as exc:
        return f"Error listing projects: {exc}"


def check_dev_ports() -> str:
    """Check common local developer ports to see which servers are currently running."""
    try:
        common_ports = {
            3000: "React / Next.js / Node",
            3001: "Node / Express",
            4200: "Angular",
            5000: "Flask / Python",
            5173: "Vite",
            8000: "FastAPI / Django",
            8080: "HTTP / Java / Spring",
            8501: "Streamlit (Jarvis)",
            8502: "Streamlit (alt)",
            11434: "Ollama Local LLM",
        }
        active: list[str] = []
        for port, label in common_ports.items():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.15)
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    active.append(f"- localhost:{port} — ACTIVE ({label})")

        if not active:
            return "No common local dev servers are currently listening on ports 3000-11434."
        return "Active local dev ports:\n" + "\n".join(active)
    except Exception as exc:
        return f"Error checking dev ports: {exc}"


def google_search(query: str) -> str:
    """Open Google Search in the default browser for the given query."""
    try:
        cleaned = (query or "").strip()
        if not cleaned:
            webbrowser.open("https://www.google.com")
            return "Opened Google (https://www.google.com)."

        encoded = urllib.parse.quote_plus(cleaned)
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return f'Opened Google search for "{cleaned}" ({url}).'
    except Exception as exc:
        return f"Error opening Google search: {exc}"


def create_github_repo(
    repo_name: str,
    project_path: str | None = None,
    private: bool = False,
    commit_message: str = "Initial commit",
) -> str:
    """Initialize git if needed, commit files, create a new GitHub repo, and push."""
    try:
        safe_repo = _sanitize_relative_segment(repo_name, "new-repo").replace(" ", "-")
        repo_dir = _resolve_repo_dir(project_path)
        if not repo_dir.is_dir():
            return f"Project folder not found: `{repo_dir}`."

        # Ensure .gitignore protects .env and databases
        gitignore = repo_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(".env\n*.db\nvenv/\n__pycache__/\nnode_modules/\n", encoding="utf-8")

        # Initialize git repo if not already one
        if not (repo_dir / ".git").exists():
            init_res = _run_git(["init", "-b", "main"], repo_dir)
            if init_res.returncode != 0:
                return f"Failed to initialize git repo: {init_res.stderr.strip()}"

        _run_git(["add", "."], repo_dir)
        commit_res = _run_git(["commit", "-m", commit_message or "Initial commit"], repo_dir)
        commit_note = (
            "Committed files."
            if commit_res.returncode == 0
            else "Using existing commit (nothing new to stage)."
        )

        # Path 1: Use GitHub CLI (`gh`) if installed & authenticated
        gh_exe = shutil.which("gh")
        if gh_exe:
            vis_flag = "--private" if private else "--public"
            gh_res = subprocess.run(
                [gh_exe, "repo", "create", safe_repo, vis_flag, "--source=.", "--remote=origin", "--push"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=35,
            )
            if gh_res.returncode == 0:
                return f"{commit_note} Created GitHub repo `{safe_repo}` and pushed! {gh_res.stdout.strip()}"

        # Path 2: Use GITHUB_TOKEN from .env via GitHub REST API
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if token:
            payload = json.dumps({"name": safe_repo, "private": bool(private)}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.github.com/user/repos",
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "Content-Type": "application/json",
                    "User-Agent": "jarvis-dev",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            clone_url = data.get("clone_url") or ""
            html_url = data.get("html_url") or clone_url
            if clone_url:
                _run_git(["remote", "remove", "origin"], repo_dir)
                _run_git(["remote", "add", "origin", clone_url], repo_dir)
                push_res = _run_git(["push", "-u", "origin", "main"], repo_dir)
                if push_res.returncode == 0:
                    return f"{commit_note} Created GitHub repo and pushed to {html_url}"
                return f"Created GitHub repo {html_url}, but push failed: {push_res.stderr.strip()}"

        # Fallback: Local repo is committed; open github.com/new for 1-click creation
        webbrowser.open("https://github.com/new")
        return (
            f"{commit_note} Local Git repo is ready at `{repo_dir}`. "
            "To auto-create GitHub repos by voice, install GitHub CLI (`gh auth login`) "
            "or add `GITHUB_TOKEN=ghp_...` to `.env`. Opened https://github.com/new for you."
        )
    except Exception as exc:
        return f"Error creating GitHub repo: {exc}"

