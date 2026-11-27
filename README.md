# Jarvis Lite

A lightweight, day-to-day personal AI assistant built with **Python 3.11+**, the **Google GenAI SDK** (`gemini-3.8-flash`) with multi-step tool calling, **SQLite**, **yt-dlp**, and **Streamlit**.

Type natural language in **English**, **Sinhala (සිංහල)**, or **Singlish**, and Jarvis Lite automatically decides which tools to run—managing tasks, saving/searching notes, remembering long-term personal facts across sessions, and playing songs or videos on YouTube.

---

## Features

- **Conversational Streamlit UI** — Persistent chat history in `st.session_state`, live sidebar snapshots of pending tasks and memory, and collapsible tool-call inspection.
- **Multi-Step Tool Loop** — Calls the Gemini API in a loop until all requested function calls complete, allowing chained actions (such as listing tasks to find an ID before completing it).
- **SQLite Persistence (`jarvis.db`)**:
  - **Tasks**: `add_task(title, due_date?)`, `list_tasks()`, `complete_task(id)`
  - **Notes**: `save_note(text)`, `search_notes(keyword)`
  - **Long-Term Memory**: `remember_fact(key, value)`, `recall_facts()` — stored facts are injected into the system prompt at the start of every session.
- **YouTube Playback**: `play_youtube(query)` searches YouTube with `yt-dlp` (`ytsearch1:`), opens the top video in your default browser via `webbrowser.open()`, and returns the title + URL.
- **Multilingual Replies** — Replies concisely in the same language and tone as the user (English, Sinhala, or Singlish).
- **Safe Tool Execution** — Every tool and the central dispatcher are wrapped in `try/except` blocks that return clean, human-readable error messages.

---

## Project Structure

```text
jarvis-lite/
  app.py              # Streamlit chat UI
  assistant.py        # chat() loop with Gemini tool-use handling
  tools/
    __init__.py       # TOOLS list (JSON schemas) + run_tool() dispatcher
    tasks.py          # add_task, list_tasks, complete_task
    notes.py          # save_note, search_notes
    youtube.py        # play_youtube(query)
    memory.py         # remember_fact, recall_facts
  db.py               # SQLite setup (tasks, notes, facts tables)
  prompts.py          # SYSTEM prompt + session memory injection
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

### 2. Create and activate a virtual environment (optional, recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your environment variables

Copy `.env.example` to `.env` and add your Gemini API key:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=AIzaSy...
```

### 5. Launch the app

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal (typically `http://localhost:8501`).

---

## Example Commands

Try typing any of these in the chat input:

- **YouTube**
  - `"go to youtube and play Believer"`
  - `"play Lo-fi study beats on YouTube"`
- **Tasks**
  - `"add a task: submit report tomorrow"`
  - `"what are my tasks?"`
  - `"mark task 1 as done"`
- **Notes**
  - `"save a note: Wi-Fi router admin IP is 192.168.1.1"`
  - `"search my notes for router"`
- **Long-Term Memory**
  - `"remember that my name is Dineth and I prefer morning workouts"`
  - `"what facts do you remember about me?"`
- **Singlish & Sinhala**
  - `"Machan heta ude assignment eka submit karanna task ekak danna"`
  - `"මගේ ඉතිරි වැඩ මොනවද?"`

---

## Next Steps

1. **Telegram Bot Integration** — Wrap `assistant.chat()` with `python-telegram-bot` or `aiogram` (storing per-chat history in SQLite) so you can message Jarvis Lite from your phone on the go.
2. **Google Calendar Sync** — Add `list_calendar_events` and `create_calendar_event` tools using `google-api-python-client` with OAuth2 so deadlines and meetings sync directly with Google Calendar.
3. **Daily Morning Brief with APScheduler** — Schedule a daily morning job using `APScheduler` (`CronTrigger(hour=7, minute=30)`) that pulls today's due tasks, recent notes, and remembered preferences, generates a concise morning briefing with Gemini, and delivers it via Telegram or desktop notification.
