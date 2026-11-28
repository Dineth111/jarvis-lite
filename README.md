# J.A.R.V.I.S. DEV (`jarvis-lite`)

> **Perplexity** is for Research. **Cursor** is for inside the Editor. **J.A.R.V.I.S. DEV** is your **Voice-First Local Developer Command Center**.

A futuristic, Iron Man-inspired **Holographic Cockpit AI Assistant** built specifically for developers using **Python 3.11+**, **Google GenAI SDK** (`gemini-3.5-flash-lite` with automatic model fallback), **SQLite**, **edge-tts** Neural Voice, **yt-dlp**, and **Streamlit**.

Speak, attach error screenshots/code files, or type in **English**, **Sinhala (සිංහල)**, or **Singlish** — J.A.R.V.I.S. DEV controls your local Git repos, scaffolds starter projects straight into VS Code, inspects active localhost dev ports, launches apps, and tracks your sprint tasks & long-term developer memory.

---

## Key Features

- **Cinematic 3-Column Hologram Cockpit UI** — Centered glowing 3D holographic AI face avatar, 17-bar voice waveform equalizer, live speech subtitle bar, and symmetrical HUD wings.
- **Two-Way Voice & Multimodal Debugging**:
  - **Voice Input:** Click the microphone in the chat bar to speak commands in English, Sinhala, or Singlish (transcribed natively by Gemini).
  - **Neural Voice Output:** Realistic British J.A.R.V.I.S. voice (`en-GB-RyanNeural`) and automatic Sinhala neural voice (`si-LK-SameeraNeural`) via `edge-tts`.
  - **File & Screenshot Attachments:** Attach error screenshots, PDFs, or `.py/.html/.js/.css/.json` files for instant root-cause debugging.
- **17 Developer & Productivity Tools**:
  - **Git Voice Copilot:** `git_status`, `git_commit_and_push`
  - **VS Code & Project Scaffolding:** `create_project_template` (`fastapi`, `html-portfolio`, `python-cli`, `react-vite`), `create_code_file` (with instant VS Code + browser preview), `open_in_vscode`, `list_my_projects`
  - **Local Dev Environment:** `check_dev_ports` (`3000`, `5173`, `8000`, `8501`, `11434`), `open_app` (VS Code, WhatsApp, Terminal, Chrome, Spotify, Discord), `open_website`, `play_youtube`
  - **SQLite Persistence (`jarvis.db`):** Sprint tasks (`add_task`, `list_tasks`, `complete_task`), Snippet/Note Vault (`save_note`, `search_notes`), Long-Term Dev Memory (`remember_fact`, `recall_facts` injected at session start), and **Saved Chat History** across sessions.

---

## Project Structure

```text
jarvis-lite/
  .streamlit/
    config.toml       # Cyber-cyan dark HUD theme & Orbitron/Space Grotesk fonts
  assets/
    jarvis_face.jpg   # 3D holographic AI face avatar
  tools/
    __init__.py       # 17 tool schemas + safe run_tool() dispatcher
    developer.py      # Git, VS Code, scaffolding, ports, desktop apps & websites
    tasks.py          # add_task, list_tasks, complete_task
    notes.py          # save_note, search_notes
    memory.py         # remember_fact, recall_facts
    youtube.py        # play_youtube(query)
  app.py              # 3-Column J.A.R.V.I.S. Hologram Cockpit UI
  assistant.py        # Multi-step Gemini tool loop + automatic model fallback
  voice.py            # Gemini voice transcription + edge-tts neural speech
  db.py               # SQLite storage (tasks, notes, facts, chat_history)
  prompts.py          # J.A.R.V.I.S. DEV system prompt + session memory injection
  requirements.txt
  .env.example
  .gitignore
  README.md
```

---

## Setup

### 1. Prerequisites
- **Python 3.11+**
- A **free Google Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) (no credit card required)

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure `.env`

```powershell
Copy-Item .env.example .env
```

Paste your key inside `.env`:
```env
GEMINI_API_KEY=AIzaSy...
```

### 4. Launch J.A.R.V.I.S. DEV

```powershell
streamlit run app.py
```

---

## Example Developer Commands

- `"Check git status of jarvis-lite"`
- `"Commit and push jarvis-lite with message 'update navbar'"`
- `"Create a new FastAPI project called api-demo and open it in VS Code"`
- `"Open VS Code and write a modern decorated HTML portfolio page"`
- `"Check which local dev ports are running right now"`
- `"Open WhatsApp"` / `"Open GitHub"` / `"Go to YouTube and play Believer"`
- `"Machan heta deploy karanna task ekak danna"`
- *(Attach an error screenshot)* `"Explain why this error is happening and fix it"`

---

## Next Steps

1. **Telegram Bot Integration** — Wrap `assistant.chat()` with `python-telegram-bot` or `aiogram` so you can check builds, tasks, and notes from your phone.
2. **Google Calendar Sync** — Connect `google-api-python-client` to sync sprint deadlines and standup meetings.
3. **Daily Morning Dev Brief with APScheduler** — Run a scheduled morning job (`APScheduler`) summarizing today's tasks, git repo status, and remembered priorities.
