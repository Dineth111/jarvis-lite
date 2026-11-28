"""J.A.R.V.I.S. — Tactical Stark-Style HUD Dashboard with 4 Workspace Modes & 60fps JS Radar Face."""

from __future__ import annotations

import base64
import html
import importlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

import assistant as _assistant_mod
import components as _components_mod
import db as _db_mod
import prompts as _prompts_mod
import tools as _tools_mod
import tools.builder as _builder_tools_mod
import tools.developer as _dev_tools_mod
import tools.vision as _vision_tools_mod
from tools.memory import get_all_facts
from tools.tasks import complete_task
from voice import VOICE_PRESETS, synthesize_speech, transcribe_audio

importlib.reload(_db_mod)
importlib.reload(_dev_tools_mod)
importlib.reload(_builder_tools_mod)
importlib.reload(_vision_tools_mod)
importlib.reload(_tools_mod)
importlib.reload(_prompts_mod)
importlib.reload(_assistant_mod)
if not hasattr(_components_mod, "render_jarvis_voice_aura"):
    importlib.reload(_components_mod)

render_jarvis_voice_aura = _components_mod.render_jarvis_voice_aura

chat = _assistant_mod.chat
get_api_key = _assistant_mod.get_api_key
get_model_name = _assistant_mod.get_model_name
delete_chat_session = _db_mod.delete_chat_session
get_connection = _db_mod.get_connection
get_session_messages = _db_mod.get_session_messages
init_db = _db_mod.init_db
list_chat_sessions = _db_mod.list_chat_sessions
save_chat_message = _db_mod.save_chat_message

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)
init_db()

_FAVICON_PATH = Path(__file__).resolve().parent / "assets" / "favicon.png"

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon=str(_FAVICON_PATH) if _FAVICON_PATH.exists() else ":material/terminal:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Workspace Mode Definitions (Dev | Academic | Personal | Research)
# ---------------------------------------------------------------------------
MODE_CONFIG: dict[str, dict[str, Any]] = {
    "Dev": {
        "key": "dev",
        "code": "DEV-OPS",
        "greeting": "DEV CORE OPTIMAL. Ready for VS Code/XAMPP live builds, Git operations, screen debugging, and port monitoring.",
        "placeholder": "jarvis --dev (e.g. 'build PHP LMS in XAMPP', 'git status', 'look at my screen')...",
        "suggestions": {
            ":material/visibility: Screen Debug": "Look at my screen and help fix any error or code shown",
            ":material/commit: Git Status": "Check git status of jarvis-lite",
            ":material/code: Build HTML": "Open VS Code and write a modern HTML portfolio page",
            ":material/lan: Dev Ports": "Check which local dev ports are running right now",
        },
        "tasks_tag": "SPRINT QUEUE",
    },
    "Academic": {
        "key": "academic",
        "code": "STUDY-CORE",
        "greeting": "ACADEMIC MODULE ONLINE. Attach lecture PDFs or Word docs for summaries, MCQs, concept explanations, or deadline tracking.",
        "placeholder": "jarvis --study (attach PDF/Word slides or ask 'make 5 MCQs on...')...",
        "suggestions": {
            ":material/school: Open SLIIT": "Open SLIIT",
            ":material/menu_book: W3Schools": "Open W3Schools",
            ":material/quiz: Practice MCQs": "Give me 5 quick exam MCQs on Python and SQL with answers",
            ":material/visibility: Explain Screen": "Look at my screen and explain the concept or question shown",
        },
        "tasks_tag": "ASSIGNMENTS",
    },
    "Personal": {
        "key": "personal",
        "code": "PERSONAL-OS",
        "greeting": "PERSONAL SYSTEMS OPTIMAL. Play YouTube music, open WhatsApp, manage daily tasks, or chat in English, සිංහල, or Singlish.",
        "placeholder": "jarvis --personal (e.g. 'play Believer on YouTube', 'open WhatsApp', 'heta gym')...",
        "suggestions": {
            ":material/smart_display: Play Believer": "Go to YouTube and play Believer",
            ":material/chat: WhatsApp": "Open WhatsApp",
            ":material/checklist: My Tasks": "What are my tasks?",
            ":material/translate: Singlish Task": "Machan heta ude gym yanna task ekak danna",
        },
        "tasks_tag": "DAILY TASKS",
    },
    "Research": {
        "key": "research",
        "code": "INTEL-NET",
        "greeting": "RESEARCH ENGINE ACTIVE. Attach SRS/PDF/Word files for deep analysis, run Google searches, or compare tech stacks.",
        "placeholder": "jarvis --research (attach a report or enter a research query)...",
        "suggestions": {
            ":material/search: Google Search": "Go to Google and search latest AI agent frameworks 2026",
            ":material/compare_arrows: Compare Stacks": "Compare FastAPI vs Node.js Express in a clean summary",
            ":material/open_in_new: GitHub": "Open GitHub",
            ":material/visibility: Read Screen": "Look at my screen and summarize the document shown",
        },
        "tasks_tag": "RESEARCH QUEUE",
    },
}

# ---------------------------------------------------------------------------
# Reference-Matched Tactical HUD CSS (#02080D + #00E5FF + Corner L-Brackets)
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      .stApp {
        background: #02080D;
      }
      .block-container {
        padding-top: 1.4rem;
        padding-bottom: 1.0rem;
        max-width: 1560px;
      }
      header[data-testid="stHeader"] {
        background: transparent;
        pointer-events: none;
      }
      header[data-testid="stHeader"] button,
      header[data-testid="stHeader"] a {
        pointer-events: auto;
      }

      /* Tactical Corner-Bracketed Panel Frame */
      .hud-card {
        position: relative;
        background: rgba(4, 16, 24, 0.88);
        border: 1px solid #0C3242;
        border-radius: 3px;
        padding: 12px 14px;
        margin-bottom: 10px;
      }
      .hud-card::before,
      .hud-card::after {
        content: "";
        position: absolute;
        width: 10px;
        height: 10px;
        pointer-events: none;
      }
      .hud-card::before {
        top: -1px;
        left: -1px;
        border-top: 2px solid #00E5FF;
        border-left: 2px solid #00E5FF;
      }
      .hud-card::after {
        bottom: -1px;
        right: -1px;
        border-bottom: 2px solid #00E5FF;
        border-right: 2px solid #00E5FF;
      }
      .hud-card-hdr {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid rgba(0, 229, 255, 0.14);
        padding-bottom: 6px;
        margin-bottom: 10px;
      }
      .hud-sys-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        color: #2E7C91;
        text-transform: uppercase;
      }
      .hud-sys-title {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.96rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #5CEEFF;
        text-transform: uppercase;
        margin: 1px 0 0 0;
      }
      .hud-sys-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.64rem;
        letter-spacing: 0.10em;
        color: #2E7C91;
        text-transform: uppercase;
      }

      /* Tactical Cyan Progress Bars (matching CPU / Memory / Storage in reference) */
      .hud-bar-row {
        margin-bottom: 9px;
      }
      .hud-bar-meta {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #7AC4D6;
        margin-bottom: 4px;
      }
      .hud-bar-val {
        color: #00E5FF;
        font-weight: 600;
      }
      .hud-bar-track {
        width: 100%;
        height: 4px;
        background: #082330;
        border-radius: 2px;
        overflow: hidden;
      }
      .hud-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #00A6C8, #00E5FF);
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.65);
      }

      /* Top Tactical Header */
      .hud-top-left {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      .hud-diamond {
        width: 13px;
        height: 13px;
        border: 1.5px solid #00E5FF;
        transform: rotate(45deg);
        background: rgba(0, 229, 255, 0.16);
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.45);
        flex-shrink: 0;
      }
      .hud-wordmark {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.32rem;
        font-weight: 700;
        letter-spacing: 0.28em;
        color: #6AF1FF;
        margin: 0;
        line-height: 1.05;
      }
      .hud-tagline {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        letter-spacing: 0.14em;
        color: #2E7C91;
        margin: 2px 0 0 0;
        text-transform: uppercase;
      }
      .hud-top-status {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 18px;
        font-family: 'JetBrains Mono', monospace;
      }
      .hud-kv-label {
        font-size: 0.58rem;
        letter-spacing: 0.14em;
        color: #2E7C91;
        text-transform: uppercase;
      }
      .hud-kv-val {
        font-size: 0.78rem;
        color: #5CEEFF;
        font-weight: 600;
      }
      .hud-user-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 10px;
        border: 1px solid #0E3A4C;
        border-radius: 999px;
        background: #04131D;
        color: #7EEFFF;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
      }
      .hud-user-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 1.5px solid #00E5FF;
        background: rgba(0, 229, 255, 0.2);
      }

      /* System Log Lines */
      .hud-log-line {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        line-height: 1.55;
        color: #8DE8F7;
        margin-bottom: 5px;
        word-break: break-word;
      }
      .hud-log-ts {
        color: #2C788C;
        margin-right: 6px;
      }
      .hud-log-role {
        color: #00E5FF;
        font-weight: 600;
        margin-right: 5px;
      }

      /* Terminal Box */
      .hud-terminal {
        background: #02090F;
        border: 1px solid #0B2D3C;
        padding: 10px 12px;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        color: #4CE8FF;
        line-height: 1.5;
      }
      .hud-term-sub {
        color: #367E92;
        font-size: 0.70rem;
        margin-top: 4px;
      }

      /* Center Transmission Readout */
      .hud-reply-box {
        background: rgba(4, 16, 24, 0.85);
        border: 1px solid #0E384A;
        border-left: 3px solid #00E5FF;
        border-radius: 3px;
        padding: 12px 15px;
        margin: 4px 0 10px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.84rem;
        line-height: 1.6;
        color: #D2F6FC;
        white-space: pre-wrap;
      }

      /* Chat input tactical border */
      div[data-testid="stChatInput"] > div {
        background: #041018 !important;
        border: 1px solid #134C63 !important;
        border-radius: 4px !important;
      }
      div[data-testid="stChatInput"] > div:focus-within {
        border-color: #00E5FF !important;
        box-shadow: 0 0 14px rgba(0, 229, 255, 0.22);
      }
    </style>
    """
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")

if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Dev"

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

if "session_facts" not in st.session_state:
    st.session_state.session_facts = get_all_facts()

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = ""

if "last_pill" not in st.session_state:
    st.session_state.last_pill = None


def _fetch_task_stats() -> tuple[list[dict[str, Any]], int, int]:
    try:
        with get_connection() as conn:
            pending = conn.execute(
                """
                SELECT id, title, due_date
                FROM tasks
                WHERE completed = 0
                ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END ASC,
                         due_date ASC,
                         id ASC
                LIMIT 8
                """
            ).fetchall()
            done_cnt = conn.execute("SELECT COUNT(*) AS c FROM tasks WHERE completed = 1").fetchone()["c"]
            total_cnt = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
        return [dict(r) for r in pending], int(done_cnt), int(total_cnt)
    except Exception:
        return [], 0, 0


def _fetch_recent_notes() -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, text, created_at FROM notes ORDER BY id DESC LIMIT 5"
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def _get_disk_usage_pct() -> tuple[int, str]:
    try:
        usage = shutil.disk_usage(Path.home())
        pct = int((usage.used / usage.total) * 100)
        free_gb = usage.free / (1024**3)
        return pct, f"{pct}% ({free_gb:.0f} GB free)"
    except Exception:
        return 50, "N/A"


@st.cache_data(show_spinner=False)
def _load_avatar_data_uri() -> str:
    avatar_path = Path(__file__).resolve().parent / "assets" / "jarvis_face.jpg"
    if not avatar_path.exists():
        return ""
    encoded = base64.b64encode(avatar_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


# ---------------------------------------------------------------------------
# Top Tactical Header Bar (JARVIS | Mode Dropdown | STATUS • TIME | DINETH)
# ---------------------------------------------------------------------------
now_time = datetime.now().strftime("%H:%M:%S")
api_ready = bool(get_api_key())
status_word = "● OPTIMAL" if api_ready else "● KEY NEEDED"

def _on_mode_change() -> None:
    st.session_state.last_pill = None
    st.toast(f"Switched to {st.session_state.active_mode} mode", icon=":material/tune:")


with st.container(border=True):
    tb_left, tb_mid, tb_right = st.columns([1.5, 0.95, 1.75], vertical_alignment="center")

    with tb_mid:
        mode_names = list(MODE_CONFIG.keys())
        st.selectbox(
            "Workspace mode",
            options=mode_names,
            format_func=lambda m: f"MODE // {m.upper()}",
            label_visibility="collapsed",
            key="active_mode",
            on_change=_on_mode_change,
        )

    current_mode_name = st.session_state.active_mode
    mode_cfg = MODE_CONFIG[current_mode_name]

    with tb_left:
        st.html(
            """
            <div class="hud-top-left">
              <div class="hud-diamond"></div>
              <div>
                <p class="hud-wordmark">J A R V I S</p>
                <p class="hud-tagline">JUST A RATHER VERY INTELLIGENT SYSTEM</p>
              </div>
            </div>
            """
        )

    with tb_right:
        st.html(
            f"""
            <div class="hud-top-status">
              <div>
                <div class="hud-kv-label">SYSTEM STATUS</div>
                <div class="hud-kv-val">{status_word}</div>
              </div>
              <div>
                <div class="hud-kv-label">LOCAL TIME</div>
                <div class="hud-kv-val">{now_time}</div>
              </div>
              <div class="hud-user-badge">
                <span>DINETH</span>
                <span class="hud-user-dot"></span>
              </div>
            </div>
            """
        )

if not api_ready:
    st.warning(
        "`GEMINI_API_KEY` is missing. Add your free key from https://aistudio.google.com/apikey to `.env` and refresh.",
        icon=":material/key:",
    )

pending_tasks, done_tasks_cnt, total_tasks_cnt = _fetch_task_stats()
current_facts = get_all_facts()
recent_notes = _fetch_recent_notes()
disk_pct, disk_label = _get_disk_usage_pct()

audio_to_play = st.session_state.last_audio
audio_play_id = st.session_state.last_audio_id
st.session_state.last_audio = None
audio_data_uri = (
    f"data:audio/mp3;base64,{base64.b64encode(audio_to_play).decode('ascii')}"
    if audio_to_play
    else ""
)

latest_assistant_msg = next(
    (m for m in reversed(st.session_state.display_messages) if m["role"] == "assistant"),
    None,
)
reply_text = latest_assistant_msg["content"] if latest_assistant_msg else mode_cfg["greeting"]
reply_tools = (latest_assistant_msg or {}).get("tool_calls") or []

# ---------------------------------------------------------------------------
# Reference-Matched 3-Column Tactical HUD Grid
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([0.96, 1.98, 1.02], gap="medium")

# LEFT COLUMN: 3 Corner-Bracketed HUD Modules
with col_left:
    # 1. Tasks / Mission Queue
    completion_pct = int((done_tasks_cnt / total_tasks_cnt) * 100) if total_tasks_cnt else 100
    st.html(
        f"""
        <div class="hud-card">
          <div class="hud-card-hdr">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">{html.escape(mode_cfg['tasks_tag'])}</div>
            </div>
            <div class="hud-sys-tag">{len(pending_tasks)} OPEN</div>
          </div>
          <div class="hud-bar-row">
            <div class="hud-bar-meta">
              <span>COMPLETION</span>
              <span class="hud-bar-val">{completion_pct}%</span>
            </div>
            <div class="hud-bar-track">
              <div class="hud-bar-fill" style="width: {completion_pct}%;"></div>
            </div>
          </div>
        </div>
        """
    )
    if pending_tasks:
        for item in pending_tasks[:5]:
            due_badge = f" · `{item['due_date']}`" if item["due_date"] else ""
            t_l, t_r = st.columns([5, 1], vertical_alignment="center")
            t_l.markdown(f"`#{item['id']}` {item['title']}{due_badge}")
            if t_r.button("", key=f"done_task_{item['id']}", icon=":material/check:"):
                complete_task(item["id"])
                st.rerun()
    else:
        st.caption("ALL MISSIONS CLEARED")

    # 2. System Resources (exact cyan progress bars from reference)
    tools_pct = 100
    mem_pct = min(100, max(12, len(current_facts) * 12))
    st.html(
        f"""
        <div class="hud-card">
          <div class="hud-card-hdr">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">SYSTEM RESOURCES</div>
            </div>
            <div class="hud-sys-tag">RT-MONITOR</div>
          </div>
          <div class="hud-bar-row">
            <div class="hud-bar-meta">
              <span>AI CORE ({html.escape(get_model_name())})</span>
              <span class="hud-bar-val">{tools_pct}%</span>
            </div>
            <div class="hud-bar-track">
              <div class="hud-bar-fill" style="width: {tools_pct}%;"></div>
            </div>
          </div>
          <div class="hud-bar-row">
            <div class="hud-bar-meta">
              <span>NEURAL MEMORY</span>
              <span class="hud-bar-val">{len(current_facts)} FACTS</span>
            </div>
            <div class="hud-bar-track">
              <div class="hud-bar-fill" style="width: {mem_pct}%;"></div>
            </div>
          </div>
          <div class="hud-bar-row" style="margin-bottom: 2px;">
            <div class="hud-bar-meta">
              <span>LOCAL STORAGE</span>
              <span class="hud-bar-val">{disk_label}</span>
            </div>
            <div class="hud-bar-track">
              <div class="hud-bar-fill" style="width: {disk_pct}%;"></div>
            </div>
          </div>
        </div>
        """
    )

    # 3. Neural Memory & Notes Vault
    facts_html = "".join(
        f'<div class="hud-log-line"><span class="hud-log-role">{html.escape(k)}:</span>{html.escape(v)}</div>'
        for k, v in current_facts[:4]
    ) or '<div class="hud-log-line" style="color:#367E92;">NO FACTS RECORDED</div>'
    notes_html = "".join(
        f'<div class="hud-log-line"><span class="hud-log-ts">#{n["id"]}</span>{html.escape(n["text"][:52])}</div>'
        for n in recent_notes[:3]
    ) or '<div class="hud-log-line" style="color:#367E92;">VAULT EMPTY</div>'

    st.html(
        f"""
        <div class="hud-card">
          <div class="hud-card-hdr">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">MEMORY &amp; NOTES</div>
            </div>
            <div class="hud-sys-tag">SQLITE-DB</div>
          </div>
          {facts_html}
          <div style="border-top:1px solid rgba(0,229,255,0.12); margin:8px 0;"></div>
          {notes_html}
        </div>
        """
    )

# RIGHT COLUMN: 3 Corner-Bracketed HUD Modules
with col_right:
    # 1. Core Status + Mode-Specific Tactical Action Tiles
    active_tool_count = len(_tools_mod.get_tools_for_mode(mode_cfg["key"]))
    st.html(
        f"""
        <div class="hud-card">
          <div class="hud-card-hdr">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">CORE CONTROLS</div>
            </div>
            <div class="hud-sys-tag">{mode_cfg['code']}</div>
          </div>
          <div style="display:flex; gap:14px; margin-bottom:2px;">
            <div style="flex:1;">
              <div class="hud-bar-meta"><span>MODE TOOLS</span><span class="hud-bar-val">{active_tool_count}</span></div>
              <div class="hud-bar-track"><div class="hud-bar-fill" style="width:100%;"></div></div>
            </div>
            <div style="flex:1;">
              <div class="hud-bar-meta"><span>VOICE</span><span class="hud-bar-val">NEURAL</span></div>
              <div class="hud-bar-track"><div class="hud-bar-fill" style="width:98%;"></div></div>
            </div>
          </div>
        </div>
        """
    )
    voice_enabled = st.toggle("VOICE SYNTHESIS", value=True, key="voice_enabled")
    selected_voice = st.selectbox(
        "Voice profile",
        options=list(VOICE_PRESETS.keys()),
        index=0,
        label_visibility="collapsed",
        key="voice_profile",
    )

    # 4 Mode-Specific Tactical Icon Tiles (strictly scoped to the active mode)
    mode_tiles: dict[str, list[tuple[str, str, str]]] = {
        "dev": [
            (":material/visibility:", "Screen Debug", "Look at my screen and help fix any code error shown"),
            (":material/commit:", "Git Status", "Check git status of jarvis-lite"),
            (":material/lan:", "Dev Ports", "Check which local dev ports are running right now"),
        ],
        "academic": [
            (":material/visibility:", "Explain Screen", "Look at my screen and explain the study topic shown"),
            (":material/school:", "Open SLIIT", "Open SLIIT"),
            (":material/menu_book:", "Open W3Schools", "Open W3Schools"),
        ],
        "personal": [
            (":material/smart_display:", "Play YouTube", "Go to YouTube and play Believer"),
            (":material/chat:", "Open WhatsApp", "Open WhatsApp"),
            (":material/checklist:", "My Tasks", "What are my tasks?"),
        ],
        "research": [
            (":material/visibility:", "Read Screen", "Look at my screen and summarize the article shown"),
            (":material/search:", "Google Search", "Go to Google and search latest AI research trends"),
            (":material/sticky_note_2:", "Search Notes", "Search my notes for recent findings"),
        ],
    }
    tiles_for_mode = mode_tiles.get(mode_cfg["key"], mode_tiles["dev"])
    ic1, ic2, ic3, ic4 = st.columns(4, gap="small")
    for idx, (col_btn, (t_icon, t_help, t_prompt)) in enumerate(zip((ic1, ic2, ic3), tiles_for_mode)):
        if col_btn.button("", icon=t_icon, help=t_help, key=f"tile_{mode_cfg['key']}_{idx}", width="stretch"):
            st.session_state.pending_prompt = t_prompt
            st.rerun()
    if ic4.button("", icon=":material/restart_alt:", help="New session", key="tile_reset", width="stretch"):
        st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")
        st.session_state.api_messages = []
        st.session_state.display_messages = []
        st.session_state.pending_prompt = None
        st.session_state.last_audio = None
        st.session_state.session_facts = get_all_facts()
        st.rerun()

    # 2. System Logs & Saved History (matching [HH:MM:SS] reference log panel!)
    st.html(
        """
        <div class="hud-card" style="margin-top:10px; margin-bottom:6px; padding-bottom:8px;">
          <div class="hud-card-hdr" style="margin-bottom:0; border-bottom:none; padding-bottom:0;">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">SYSTEM LOGS</div>
            </div>
            <div class="hud-sys-tag">RT-LOG</div>
          </div>
        </div>
        """
    )
    tab_log, tab_saved = st.tabs(["LIVE LOG", "SAVED HISTORY"])

    with tab_log:
        with st.container(height=215, border=True):
            if st.session_state.display_messages:
                for msg in st.session_state.display_messages:
                    role_lbl = "USER" if msg["role"] == "user" else "JARVIS"
                    ts = (msg.get("created_at") or now_time)[-8:]
                    st.html(
                        f'<div class="hud-log-line">'
                        f'<span class="hud-log-ts">[{html.escape(ts)}]</span>'
                        f'<span class="hud-log-role">{role_lbl}:</span>'
                        f'{html.escape(msg["content"][:220])}'
                        f'</div>'
                    )
            else:
                st.html(
                    f"""
                    <div class="hud-log-line"><span class="hud-log-ts">[{now_time}]</span> SYSTEM INTEGRITY CHECK COMPLETE</div>
                    <div class="hud-log-line"><span class="hud-log-ts">[{now_time}]</span> MODE LOCKED: {mode_cfg['code']}</div>
                    <div class="hud-log-line"><span class="hud-log-ts">[{now_time}]</span> 25 LOCAL DEV TOOLS ONLINE</div>
                    <div class="hud-log-line"><span class="hud-log-ts">[{now_time}]</span> AWAITING USER INPUT...</div>
                    """
                )

    with tab_saved:
        saved_sessions = list_chat_sessions(limit=20)
        if saved_sessions:
            session_labels = {
                s["session_id"]: f"{(s['last_at'] or '')[5:16]} · {(s['preview'] or 'Chat')[:20]}"
                for s in saved_sessions
            }
            chosen_sid = st.selectbox(
                "Saved sessions",
                options=list(session_labels.keys()),
                format_func=lambda sid: session_labels[sid],
                label_visibility="collapsed",
                key="history_session_select",
            )
            past_msgs = get_session_messages(chosen_sid)
            with st.container(height=130, border=True):
                for m in past_msgs[-6:]:
                    r_lbl = "USER" if m["role"] == "user" else "JARVIS"
                    st.html(
                        f'<div class="hud-log-line"><span class="hud-log-role">{r_lbl}:</span>'
                        f'{html.escape(m["content"][:120])}</div>'
                    )
            b1, b2 = st.columns(2)
            if b1.button("LOAD", icon=":material/history:", width="stretch", key="load_hist_btn"):
                st.session_state.session_id = chosen_sid
                st.session_state.display_messages = past_msgs
                st.session_state.api_messages = [
                    {
                        "role": "user" if m["role"] == "user" else "model",
                        "parts": [{"text": m["content"]}],
                    }
                    for m in past_msgs
                ]
                st.rerun()
            if b2.button("DELETE", icon=":material/delete:", width="stretch", key="del_hist_btn"):
                delete_chat_session(chosen_sid)
                st.rerun()
        else:
            st.caption("NO SAVED SESSIONS")

    # 3. Terminal Box (matching bottom-right ROOT@JARVIS panel in reference!)
    last_tool_cmd = (
        f"jarvis --exec {reply_tools[-1]['name']}"
        if reply_tools
        else f"jarvis --mode {mode_cfg['key']} --ready"
    )
    last_tool_out = (
        reply_tools[-1]["output"][:95]
        if reply_tools
        else "Environment active. Voice, Vision & File Attach ready."
    )
    st.html(
        f"""
        <div class="hud-card" style="margin-top:8px;">
          <div class="hud-card-hdr">
            <div>
              <div class="hud-sys-label">SYSTEM //</div>
              <div class="hud-sys-title">TERMINAL</div>
            </div>
            <div class="hud-sys-tag">ROOT@JARVIS</div>
          </div>
          <div class="hud-terminal">
            &gt;_ {html.escape(last_tool_cmd)}
            <div class="hud-term-sub">{html.escape(last_tool_out)}</div>
          </div>
        </div>
        """
    )

# CENTER STAGE: 60fps JS Tactical Radar + 360° Voice Spectrum & Ripples + Waveform
with col_center:
    render_jarvis_voice_aura(
        avatar_uri=_load_avatar_data_uri(),
        audio_uri=audio_data_uri,
        audio_id=audio_play_id,
    )

    st.html(f'<div class="hud-reply-box">{html.escape(reply_text)}</div>')

    mode_suggestions: dict[str, str] = mode_cfg["suggestions"]
    selected_chip = st.pills(
        f"{current_mode_name} quick actions",
        list(mode_suggestions.keys()),
        label_visibility="collapsed",
        key=f"quick_pills_{mode_cfg['key']}",
    )
    if selected_chip and selected_chip != st.session_state.last_pill:
        st.session_state.last_pill = selected_chip
        st.session_state.pending_prompt = mode_suggestions[selected_chip]
    elif not selected_chip:
        st.session_state.last_pill = None

    chat_submission = st.chat_input(
        mode_cfg["placeholder"],
        accept_audio=True,
        accept_file="multiple",
        file_type=[
            "png", "jpg", "jpeg", "webp",
            "pdf", "docx", "pptx", "txt", "md", "csv", "json", "log",
            "py", "html", "css", "js", "ts", "sql", "xml", "yaml", "yml",
            "java", "c", "cpp", "cs", "go", "rs", "php",
        ],
        submit_mode="disable",
    )

    active_prompt: str | None = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    attachments: list[dict[str, Any]] = []

    if chat_submission:
        if getattr(chat_submission, "files", None):
            for uploaded in chat_submission.files:
                attachments.append(
                    {
                        "name": uploaded.name,
                        "mime_type": getattr(uploaded, "type", None) or "",
                        "data": uploaded.read(),
                    }
                )

        if chat_submission.audio is not None:
            with st.spinner("TRANSCRIBING AUDIO..."):
                try:
                    raw_audio = chat_submission.audio.read()
                    mime = getattr(chat_submission.audio, "type", None) or "audio/wav"
                    spoken_text = transcribe_audio(raw_audio, mime_type=mime)
                except Exception as exc:
                    st.error(f"Could not transcribe audio: {exc}")
                    spoken_text = ""
            if spoken_text:
                active_prompt = spoken_text
        elif chat_submission.text:
            active_prompt = chat_submission.text
        elif attachments:
            active_prompt = "Analyze the attached file(s)."

    if active_prompt or attachments:
        prompt_text = active_prompt or "Analyze the attached file(s)."
        file_names = [a["name"] for a in attachments]
        display_user_text = (
            f"{prompt_text}  (attached: {', '.join(file_names)})"
            if file_names
            else prompt_text
        )

        tool_calls_this_turn: list[dict[str, Any]] = []
        with st.status(f"[{mode_cfg['code']}] EXECUTING: {prompt_text[:50]}", expanded=True) as status_box:

            def _handle_tool_call(event: dict[str, Any]) -> None:
                tool_calls_this_turn.append(event)
                step_num = len(tool_calls_this_turn)
                tool_name = event["name"]
                tool_input = event.get("input") or {}
                if tool_name == "init_project_workspace":
                    label = f"OPENING VS CODE: {tool_input.get('project_name', '')}"
                elif tool_name == "write_project_file":
                    label = f"WRITING: {tool_input.get('relative_file_path', '')}"
                elif tool_name in {"run_project", "start_xampp"}:
                    label = "LAUNCHING LOCAL SERVER..."
                else:
                    label = f"RUNNING: {tool_name}..."
                status_box.update(label=label, state="running", expanded=True)
                status_box.markdown(f"**{step_num}. `{tool_name}`** — {event['output']}")

            try:
                reply = chat(
                    prompt_text,
                    st.session_state.api_messages,
                    attachments=attachments or None,
                    mode=mode_cfg["key"],
                    session_facts=st.session_state.session_facts,
                    on_tool_call=_handle_tool_call,
                )
                status_box.update(label="EXECUTION COMPLETE", state="complete", expanded=False)
            except Exception as exc:
                status_box.update(label="COMMAND FAILED", state="error", expanded=True)
                st.error(f"Request failed: {exc}")
                st.stop()

        if voice_enabled:
            with st.spinner("SYNTHESIZING VOICE..."):
                st.session_state.last_audio = synthesize_speech(
                    reply,
                    voice_id=VOICE_PRESETS[selected_voice],
                )
                st.session_state.last_audio_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

        now_ts = datetime.now().strftime("%H:%M:%S")
        save_chat_message(st.session_state.session_id, "user", display_user_text)
        save_chat_message(
            st.session_state.session_id,
            "assistant",
            reply,
            tool_calls=tool_calls_this_turn,
        )

        st.session_state.display_messages.append(
            {"role": "user", "content": display_user_text, "created_at": now_ts}
        )
        st.session_state.display_messages.append(
            {
                "role": "assistant",
                "content": reply,
                "tool_calls": tool_calls_this_turn,
                "created_at": now_ts,
            }
        )
        st.rerun()
