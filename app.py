"""Jarvis — 3-Column Modern Cockpit with Mode Switcher (Dev / Academic / Personal / Research) & 60fps JS Face."""

from __future__ import annotations

import base64
import html
import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

import assistant as _assistant_mod
import db as _db_mod
import prompts as _prompts_mod
import tools as _tools_mod
import tools.builder as _builder_tools_mod
import tools.developer as _dev_tools_mod
import tools.vision as _vision_tools_mod
from components import render_jarvis_hero
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
    page_title="Jarvis",
    page_icon=str(_FAVICON_PATH) if _FAVICON_PATH.exists() else ":material/auto_awesome:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Mode Configurations — each mode shows ONLY its own relevant actions & copy
# ---------------------------------------------------------------------------
MODE_CONFIG: dict[str, dict[str, Any]] = {
    "Dev": {
        "key": "dev",
        "subtitle": "Code, Git, VS Code, XAMPP & Screen Debugging",
        "greeting": "Dev mode active. Inspect your screen, build projects live in VS Code/XAMPP, check localhost ports, or manage Git repos.",
        "placeholder": "Dev command (e.g., 'build PHP LMS in XAMPP', 'git status', 'look at my screen')...",
        "suggestions": {
            ":material/visibility: Inspect screen": "Look at my screen and help fix any error or code shown",
            ":material/commit: Git status": "Check git status of jarvis-lite",
            ":material/code: Build HTML in VS Code": "Open VS Code and write a modern HTML portfolio page",
            ":material/rocket_launch: Scaffold FastAPI": "Create a new FastAPI project called api-demo and open it in VS Code",
            ":material/lan: Dev ports": "Check which local dev ports are running right now",
        },
        "left_tasks_title": "Dev Sprint Tasks",
        "left_notes_title": "Code Snippets & Notes",
    },
    "Academic": {
        "key": "academic",
        "subtitle": "Lectures, Assignments, Exam Prep & Study Notes",
        "greeting": "Academic mode active. Attach lecture PDFs or Word docs to summarize, generate practice MCQs, explain CS/IT concepts, or track assignment deadlines.",
        "placeholder": "Study command (attach PDF/Word slides or ask 'make 5 MCQs on...')...",
        "suggestions": {
            ":material/school: Open SLIIT": "Open SLIIT",
            ":material/menu_book: Open W3Schools": "Open W3Schools",
            ":material/quiz: Practice MCQs": "Give me 5 quick interview & exam MCQs on Python and SQL with answers",
            ":material/add_task: Add assignment": "Add a task: submit university assignment tomorrow",
            ":material/visibility: Explain my screen": "Look at my screen and explain the concept or question shown",
        },
        "left_tasks_title": "Assignments & Deadlines",
        "left_notes_title": "Study Notes",
    },
    "Personal": {
        "key": "personal",
        "subtitle": "Daily Tasks, YouTube, WhatsApp & Personal Memory",
        "greeting": "Personal mode active. Ask me to play songs on YouTube, open WhatsApp, remember personal facts, or organize your day in English, සිංහල, or Singlish.",
        "placeholder": "Message Jarvis (e.g., 'play Believer on YouTube', 'open WhatsApp', 'heta gym yanna')...",
        "suggestions": {
            ":material/smart_display: Play Believer": "Go to YouTube and play Believer",
            ":material/chat: Open WhatsApp": "Open WhatsApp",
            ":material/checklist: My tasks": "What are my tasks?",
            ":material/psychology: What you remember": "What facts do you remember about me?",
            ":material/translate: Singlish task": "Machan heta ude gym yanna task ekak danna",
        },
        "left_tasks_title": "Daily Tasks",
        "left_notes_title": "Personal Notes",
    },
    "Research": {
        "key": "research",
        "subtitle": "Deep Document Analysis, Google Search & Comparisons",
        "greeting": "Research mode active. Attach SRS/PDF/Word documents for structured analysis, search Google, compare technologies, and save key findings.",
        "placeholder": "Research query or attach a document to analyze...",
        "suggestions": {
            ":material/search: Search Google": "Go to Google and search latest AI agent frameworks 2026",
            ":material/compare_arrows: Compare stacks": "Compare FastAPI vs Node.js Express for an AI backend in a clean table",
            ":material/open_in_new: Open GitHub": "Open GitHub",
            ":material/sticky_note_2: Search my notes": "Search my notes for recent findings",
            ":material/visibility: Read my screen": "Look at my screen and summarize the article or document shown",
        },
        "left_tasks_title": "Research Queue",
        "left_notes_title": "Research Findings",
    },
}

# ---------------------------------------------------------------------------
# Modern 3-Column Glass Cockpit CSS
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      .stApp {
        background:
          radial-gradient(ellipse 65% 42% at 50% -6%, rgba(99, 102, 241, 0.14), transparent 60%),
          radial-gradient(ellipse 46% 36% at 50% 24%, rgba(56, 189, 248, 0.10), transparent 58%),
          #090A0F;
      }
      .block-container {
        padding-top: 0.7rem;
        padding-bottom: 1.2rem;
        max-width: 1500px;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      div[data-testid="stChatInput"] > div {
        border-radius: 18px !important;
        background: rgba(18, 21, 31, 0.88) !important;
        border: 1px solid rgba(255, 255, 255, 0.11) !important;
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.42);
        backdrop-filter: blur(14px);
      }
      div[data-testid="stChatInput"] > div:focus-within {
        border-color: rgba(129, 140, 248, 0.55) !important;
      }
      .top-brand-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-top: 4px;
      }
      .brand-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: linear-gradient(135deg, #38BDF8, #818CF8);
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.7);
      }
      .brand-name {
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #F8FAFC;
        margin: 0;
      }
      .brand-sub {
        font-size: 0.78rem;
        color: #94A3B8;
        margin: 0;
      }
      .top-status-strip {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        padding-top: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        color: #94A3B8;
      }
      .live-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 999px;
        background: rgba(52, 211, 153, 0.10);
        border: 1px solid rgba(52, 211, 153, 0.25);
        color: #6EE7B7;
      }
      .live-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #34D399;
      }
      .reply-glass-card {
        width: 100%;
        padding: 14px 18px;
        margin: 2px 0 12px 0;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
      }
      .reply-glass-text {
        font-size: 0.96rem;
        line-height: 1.6;
        color: #E2E8F0;
        margin: 0;
        white-space: pre-wrap;
      }
      .reply-tool-chip {
        display: inline-block;
        margin-top: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.71rem;
        padding: 2px 8px;
        border-radius: 6px;
        background: rgba(56, 189, 248, 0.10);
        border: 1px solid rgba(56, 189, 248, 0.24);
        color: #7DD3FC;
      }
      .wing-heading {
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin-bottom: 8px;
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

if "last_pill" not in st.session_state:
    st.session_state.last_pill = None


def _fetch_pending_tasks() -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, due_date
                FROM tasks
                WHERE completed = 0
                ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END ASC,
                         due_date ASC,
                         id ASC
                LIMIT 10
                """
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def _fetch_recent_notes() -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, text, created_at FROM notes ORDER BY id DESC LIMIT 6"
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def _load_avatar_data_uri() -> str:
    avatar_path = Path(__file__).resolve().parent / "assets" / "jarvis_face.jpg"
    if not avatar_path.exists():
        return ""
    encoded = base64.b64encode(avatar_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


# ---------------------------------------------------------------------------
# Top Bar with Interactive Mode Switcher (Dev | Academic | Personal | Research)
# ---------------------------------------------------------------------------
now_label = datetime.now().strftime("%a %d %b · %H:%M")
api_ready = bool(get_api_key())
status_html = (
    '<span class="live-pill"><span class="live-dot"></span>Online</span>'
    if api_ready
    else '<span>API key missing</span>'
)

with st.container(border=True):
    tb_left, tb_mid, tb_right = st.columns([1.6, 1.0, 1.6], vertical_alignment="center")

    with tb_mid:
        mode_names = list(MODE_CONFIG.keys())
        chosen_mode = st.selectbox(
            "Workspace mode",
            options=mode_names,
            index=mode_names.index(st.session_state.active_mode),
            format_func=lambda m: f"Mode: {m}",
            label_visibility="collapsed",
            key="mode_dropdown",
        )
        if chosen_mode != st.session_state.active_mode:
            st.session_state.active_mode = chosen_mode
            st.session_state.last_pill = None
            st.rerun()

    current_mode_name = st.session_state.active_mode
    mode_cfg = MODE_CONFIG[current_mode_name]

    with tb_left:
        st.html(
            f"""
            <div class="top-brand-strip">
              <span class="brand-dot"></span>
              <div>
                <p class="brand-name">Jarvis</p>
                <p class="brand-sub">{html.escape(mode_cfg['subtitle'])}</p>
              </div>
            </div>
            """
        )

    with tb_right:
        st.html(
            f"""
            <div class="top-status-strip">
              {status_html}
              <span>{get_model_name()}</span>
              <span>{now_label}</span>
            </div>
            """
        )

if not api_ready:
    st.warning(
        "`GEMINI_API_KEY` is missing. Add your free key from https://aistudio.google.com/apikey to `.env` and refresh.",
        icon=":material/key:",
    )

pending_tasks = _fetch_pending_tasks()
current_facts = get_all_facts()
recent_notes = _fetch_recent_notes()

audio_to_play = st.session_state.last_audio
st.session_state.last_audio = None

latest_assistant_msg = next(
    (m for m in reversed(st.session_state.display_messages) if m["role"] == "assistant"),
    None,
)
reply_text = latest_assistant_msg["content"] if latest_assistant_msg else mode_cfg["greeting"]
reply_tools = (latest_assistant_msg or {}).get("tool_calls") or []

# ---------------------------------------------------------------------------
# 3-Column Modern Cockpit Layout (Left Wing | Wide Center JS Face | Right Wing)
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([0.82, 2.55, 0.88], gap="medium")

# LEFT WING: Tasks, Notes, Memory (contextual titles per mode)
with col_left:
    with st.container(border=True):
        st.html(f'<div class="wing-heading">{html.escape(mode_cfg["left_tasks_title"])}</div>')
        if pending_tasks:
            for item in pending_tasks[:7]:
                due_badge = f" · `{item['due_date']}`" if item["due_date"] else ""
                t_left, t_right = st.columns([5, 1], vertical_alignment="center")
                t_left.markdown(f"`#{item['id']}` {item['title']}{due_badge}")
                if t_right.button(
                    "",
                    key=f"done_task_{item['id']}",
                    icon=":material/check:",
                    help=f"Complete task #{item['id']}",
                ):
                    complete_task(item["id"])
                    st.rerun()
        else:
            st.caption("No open tasks.")

    with st.container(border=True):
        st.html(f'<div class="wing-heading">{html.escape(mode_cfg["left_notes_title"])}</div>')
        if recent_notes:
            for note in recent_notes[:5]:
                snippet = note["text"] if len(note["text"]) <= 68 else f"{note['text'][:65]}..."
                st.markdown(f"- `#{note['id']}` {snippet}")
        else:
            st.caption("No saved notes yet.")

    with st.container(border=True):
        st.html('<div class="wing-heading">Long-Term Memory</div>')
        if current_facts:
            for key, value in current_facts[:6]:
                st.markdown(f"- **{key}**: {value}")
        else:
            st.caption("No saved facts yet.")

# RIGHT WING: Voice Controls + Telemetry + Persistent Chat History
with col_right:
    with st.container(border=True):
        st.html('<div class="wing-heading">Voice & Session</div>')
        voice_enabled = st.toggle("Spoken replies", value=True, key="voice_enabled")
        selected_voice = st.selectbox(
            "Voice profile",
            options=list(VOICE_PRESETS.keys()),
            index=0,
            label_visibility="collapsed",
            key="voice_profile",
        )
        if audio_to_play:
            st.audio(audio_to_play, format="audio/mp3", autoplay=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks", len(pending_tasks))
        m2.metric("Memory", len(current_facts))
        m3.metric("Notes", len(recent_notes))

        if st.button("New chat", icon=":material/add:", width="stretch"):
            st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")
            st.session_state.api_messages = []
            st.session_state.display_messages = []
            st.session_state.pending_prompt = None
            st.session_state.last_audio = None
            st.session_state.session_facts = get_all_facts()
            st.rerun()

    with st.container(border=True):
        st.html('<div class="wing-heading">Chat History</div>')
        tab_current, tab_history = st.tabs(["Current", "Saved"])

        with tab_current:
            with st.container(height=290, border=False):
                if st.session_state.display_messages:
                    for msg in st.session_state.display_messages:
                        role_tag = "You" if msg["role"] == "user" else "Jarvis"
                        st.markdown(f"**{role_tag}**  \n{msg['content']}")
                        if msg.get("tool_calls"):
                            with st.expander(f"Tools ({len(msg['tool_calls'])})", expanded=False):
                                for call in msg["tool_calls"]:
                                    st.code(
                                        f"{call['name']}({json.dumps(call['input'], ensure_ascii=False)})\n-> {call['output']}",
                                        language="text",
                                    )
                else:
                    st.caption("Messages from this session appear here.")

        with tab_history:
            saved_sessions = list_chat_sessions(limit=20)
            if saved_sessions:
                session_labels = {
                    s["session_id"]: (
                        f"{(s['last_at'] or '')[5:16]} · "
                        f"{((s['preview'] or 'Chat')[:24])}"
                        f" ({s['message_count']})"
                    )
                    for s in saved_sessions
                }
                chosen_sid = st.selectbox(
                    "Past sessions",
                    options=list(session_labels.keys()),
                    format_func=lambda sid: session_labels[sid],
                    label_visibility="collapsed",
                    key="history_session_select",
                )
                past_msgs = get_session_messages(chosen_sid)
                with st.container(height=210, border=False):
                    for msg in past_msgs:
                        role_tag = "You" if msg["role"] == "user" else "Jarvis"
                        ts = (msg.get("created_at") or "")[11:16]
                        st.markdown(f"**{role_tag}** `{ts}`  \n{msg['content']}")

                b1, b2 = st.columns(2)
                if b1.button("Load", icon=":material/history:", width="stretch", key="load_hist_btn"):
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
                if b2.button("Delete", icon=":material/delete:", width="stretch", key="del_hist_btn"):
                    delete_chat_session(chosen_sid)
                    if st.session_state.session_id == chosen_sid:
                        st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")
                        st.session_state.display_messages = []
                        st.session_state.api_messages = []
                    st.rerun()
            else:
                st.caption("No saved chats yet.")

# CENTER STAGE: Large 60fps JS Face + Live Speech Card + Mode-Specific Quick Actions + Input
with col_center:
    render_jarvis_hero(
        avatar_uri=_load_avatar_data_uri(),
        speaking=bool(audio_to_play),
        compact=False,
        heading="",
        subtitle="",
    )

    tool_chip_html = ""
    if reply_tools:
        names = ", ".join(t["name"] for t in reply_tools)
        tool_chip_html = f'<div><span class="reply-tool-chip">Ran: {html.escape(names)}</span></div>'

    st.html(
        f"""
        <div class="reply-glass-card">
          <p class="reply-glass-text">{html.escape(reply_text)}</p>
          {tool_chip_html}
        </div>
        """
    )

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
            with st.spinner("Transcribing audio..."):
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
        with st.status(f"[{current_mode_name}] Working on: {prompt_text[:55]}", expanded=True) as status_box:

            def _handle_tool_call(event: dict[str, Any]) -> None:
                tool_calls_this_turn.append(event)
                step_num = len(tool_calls_this_turn)
                tool_name = event["name"]
                tool_input = event.get("input") or {}
                if tool_name == "init_project_workspace":
                    label = f"Opening VS Code: {tool_input.get('project_name', '')}"
                elif tool_name == "write_project_file":
                    label = f"Writing {tool_input.get('relative_file_path', '')}"
                elif tool_name in {"run_project", "start_xampp"}:
                    label = "Launching local server..."
                else:
                    label = f"Running {tool_name}..."
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
                status_box.update(label="Done", state="complete", expanded=False)
            except Exception as exc:
                status_box.update(label="Failed", state="error", expanded=True)
                st.error(f"Request failed: {exc}")
                st.stop()

        if voice_enabled:
            with st.spinner("Generating audio..."):
                st.session_state.last_audio = synthesize_speech(
                    reply,
                    voice_id=VOICE_PRESETS[selected_voice],
                )

        save_chat_message(st.session_state.session_id, "user", display_user_text)
        save_chat_message(
            st.session_state.session_id,
            "assistant",
            reply,
            tool_calls=tool_calls_this_turn,
        )

        st.session_state.display_messages.append({"role": "user", "content": display_user_text})
        st.session_state.display_messages.append(
            {
                "role": "assistant",
                "content": reply,
                "tool_calls": tool_calls_this_turn,
            }
        )
        st.rerun()
