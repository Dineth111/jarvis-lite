"""Jarvis Dev — Clean, handcrafted local developer assistant workspace."""

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

st.set_page_config(
    page_title="Jarvis",
    page_icon=":material/terminal:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Minimal, restrained desktop-app styling (Linear / Raycast inspired)
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      .block-container {
        padding-top: 0.75rem;
        padding-bottom: 1.25rem;
        max-width: 1460px;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      @keyframes voice-bar {
        0%, 100% { height: 5px; opacity: 0.45; }
        50% { height: 22px; opacity: 1; }
      }
      @keyframes ring-speak {
        0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.35); }
        50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0.0); }
      }

      /* Top App Bar */
      .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 16px;
        margin-bottom: 14px;
        border-radius: 10px;
        background: #12151C;
        border: 1px solid #222733;
      }
      .app-header-left {
        display: flex;
        align-items: baseline;
        gap: 10px;
      }
      .app-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: #F3F4F6;
        letter-spacing: -0.01em;
        margin: 0;
      }
      .app-tag {
        font-size: 0.78rem;
        color: #7D8798;
        margin: 0;
      }
      .app-meta {
        display: flex;
        align-items: center;
        gap: 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #8B94A5;
      }
      .status-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
      }
      .dot-ok { background: #22C55E; }
      .dot-warn { background: #F59E0B; }

      /* Center Assistant Stage */
      .assistant-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 22px 20px 18px 20px;
        margin-bottom: 12px;
        border-radius: 12px;
        background: #12151C;
        border: 1px solid #222733;
      }
      .avatar-frame {
        width: 310px;
        height: 310px;
        border-radius: 50%;
        border: 1.5px solid #283040;
        background: #0B0D11;
        overflow: hidden;
        margin-bottom: 14px;
        transition: border-color 0.25s ease;
      }
      .avatar-frame-speaking {
        border-color: #3B82F6;
        animation: ring-speak 1.5s ease-out infinite;
      }
      .avatar-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transform: scale(1.32);
        display: block;
      }

      /* Subtle 7-bar audio level indicator */
      .voice-meter {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        height: 24px;
        margin-bottom: 12px;
      }
      .voice-meter-bar {
        width: 3px;
        height: 6px;
        border-radius: 3px;
        background: #2C3445;
      }
      .voice-meter-active .voice-meter-bar {
        background: #3B82F6;
        animation: voice-bar 0.55s ease-in-out infinite;
      }

      /* Clean Reply Box */
      .reply-card {
        width: 100%;
        max-width: 660px;
        padding: 14px 18px;
        border-radius: 8px;
        background: #0E1117;
        border: 1px solid #1F2430;
        text-align: left;
      }
      .reply-text {
        font-size: 0.96rem;
        line-height: 1.6;
        color: #E5E7EB;
        margin: 0;
        white-space: pre-wrap;
      }
      .reply-tools {
        margin-top: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #6B7689;
      }

      .section-heading {
        font-size: 0.80rem;
        font-weight: 600;
        color: #9CA3AF;
        letter-spacing: 0.02em;
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


def _render_center_assistant(
    *,
    speaking: bool,
    latest_reply: str,
    latest_tools: list[dict[str, Any]],
) -> None:
    frame_cls = "avatar-frame avatar-frame-speaking" if speaking else "avatar-frame"
    meter_cls = "voice-meter voice-meter-active" if speaking else "voice-meter"
    delays = [0.0, 0.1, 0.2, 0.08, 0.18, 0.26, 0.12]
    bars = "".join(
        f'<div class="voice-meter-bar" style="animation-delay: {d}s;"></div>' for d in delays
    )

    avatar_uri = _load_avatar_data_uri()
    img_html = (
        f'<img class="avatar-img" src="{avatar_uri}" alt="Jarvis" />'
        if avatar_uri
        else ""
    )

    safe_reply = html.escape(latest_reply)
    tools_line = ""
    if latest_tools:
        names = ", ".join(t["name"] for t in latest_tools)
        tools_line = f'<div class="reply-tools">Ran: {html.escape(names)}</div>'

    st.html(
        f"""
        <div class="assistant-stage">
          <div class="{frame_cls}">
            {img_html}
          </div>
          <div class="{meter_cls}">
            {bars}
          </div>
          <div class="reply-card">
            <p class="reply-text">{safe_reply}</p>
            {tools_line}
          </div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Minimal Top App Bar
# ---------------------------------------------------------------------------
now_label = datetime.now().strftime("%a, %d %b · %H:%M")
api_ready = bool(get_api_key())
dot_cls = "status-dot dot-ok" if api_ready else "status-dot dot-warn"
status_label = "Ready" if api_ready else "API key missing"

st.html(
    f"""
    <div class="app-header">
      <div class="app-header-left">
        <p class="app-name">Jarvis</p>
        <p class="app-tag">Local developer workspace</p>
      </div>
      <div class="app-meta">
        <span><span class="{dot_cls}"></span>{status_label}</span>
        <span>{get_model_name()}</span>
        <span>{now_label}</span>
      </div>
    </div>
    """
)

if not api_ready:
    st.warning(
        "`GEMINI_API_KEY` is not set. Add your key from https://aistudio.google.com/apikey to `.env` and refresh.",
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
subtitle_text = (
    latest_assistant_msg["content"]
    if latest_assistant_msg
    else "Ready. Speak, attach a file, or type a command — I can inspect your screen, manage Git repos, build projects in VS Code/XAMPP, or handle tasks and notes."
)
subtitle_tools = (latest_assistant_msg or {}).get("tool_calls") or []

# ---------------------------------------------------------------------------
# 3-Column Workspace Layout
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([0.95, 2.15, 1.0], gap="medium")

# LEFT PANEL: Tasks, Notes, Memory
with col_left:
    with st.container(border=True):
        st.html('<div class="section-heading">Tasks</div>')
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
        st.html('<div class="section-heading">Notes</div>')
        if recent_notes:
            for note in recent_notes[:5]:
                snippet = note["text"] if len(note["text"]) <= 68 else f"{note['text'][:65]}..."
                st.markdown(f"- `#{note['id']}` {snippet}")
        else:
            st.caption("No saved notes.")

    with st.container(border=True):
        st.html('<div class="section-heading">Memory</div>')
        if current_facts:
            for key, value in current_facts[:6]:
                st.markdown(f"- **{key}**: {value}")
        else:
            st.caption("No saved facts.")

# RIGHT PANEL: Voice Settings & Persistent Chat History
with col_right:
    with st.container(border=True):
        st.html('<div class="section-heading">Voice</div>')
        voice_enabled = st.toggle("Spoken replies", value=True, key="voice_enabled")
        selected_voice = st.selectbox(
            "Voice",
            options=list(VOICE_PRESETS.keys()),
            index=0,
            label_visibility="collapsed",
            key="voice_profile",
        )
        if audio_to_play:
            st.audio(audio_to_play, format="audio/mp3", autoplay=True)

        if st.button("New chat", icon=":material/add:", width="stretch"):
            st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")
            st.session_state.api_messages = []
            st.session_state.display_messages = []
            st.session_state.pending_prompt = None
            st.session_state.last_audio = None
            st.session_state.session_facts = get_all_facts()
            st.rerun()

    with st.container(border=True):
        st.html('<div class="section-heading">History</div>')
        tab_current, tab_history = st.tabs(["Current", "Saved"])

        with tab_current:
            with st.container(height=310, border=False):
                if st.session_state.display_messages:
                    for msg in st.session_state.display_messages:
                        role_tag = "You" if msg["role"] == "user" else "Jarvis"
                        st.markdown(f"**{role_tag}**  \n{msg['content']}")
                        if msg.get("tool_calls"):
                            with st.expander(
                                f"Tools ({len(msg['tool_calls'])})",
                                expanded=False,
                            ):
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
                        f"{((s['preview'] or 'Chat')[:26])}"
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
                with st.container(height=225, border=False):
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
                st.caption("No saved sessions yet.")

# CENTER PANEL: Large Assistant Face + Quick Actions + Input Bar
with col_center:
    _render_center_assistant(
        speaking=bool(audio_to_play),
        latest_reply=subtitle_text,
        latest_tools=subtitle_tools,
    )

    SUGGESTIONS = {
        ":material/visibility: Inspect screen": "Look at my screen and tell me what you see or help with any error shown",
        ":material/commit: Git status": "Check git status of jarvis-lite",
        ":material/code: Build HTML page": "Open VS Code and write a modern HTML portfolio page",
        ":material/search: Search Google": "Go to Google and search Python FastAPI tutorial",
        ":material/lan: Dev ports": "Check which local dev ports are running right now",
    }

    selected_chip = st.pills(
        "Quick actions",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
        key="quick_pills",
    )
    if selected_chip and selected_chip != st.session_state.last_pill:
        st.session_state.last_pill = selected_chip
        st.session_state.pending_prompt = SUGGESTIONS[selected_chip]
    elif not selected_chip:
        st.session_state.last_pill = None

    chat_submission = st.chat_input(
        "Message Jarvis, record voice, or attach files...",
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
            f"{prompt_text}  *(attached: {', '.join(file_names)})*"
            if file_names
            else prompt_text
        )

        tool_calls_this_turn: list[dict[str, Any]] = []
        with st.status(f"Working on: {prompt_text[:60]}", expanded=True) as status_box:

            def _handle_tool_call(event: dict[str, Any]) -> None:
                tool_calls_this_turn.append(event)
                step_num = len(tool_calls_this_turn)
                tool_name = event["name"]
                tool_input = event.get("input") or {}
                if tool_name == "init_project_workspace":
                    label = f"Opening VS Code workspace: {tool_input.get('project_name', '')}"
                elif tool_name == "write_project_file":
                    label = f"Writing {tool_input.get('relative_file_path', '')}"
                elif tool_name in {"run_project", "start_xampp"}:
                    label = "Starting local server..."
                else:
                    label = f"Running {tool_name}..."
                status_box.update(label=label, state="running", expanded=True)
                status_box.markdown(f"**{step_num}. `{tool_name}`** — {event['output']}")

            try:
                reply = chat(
                    prompt_text,
                    st.session_state.api_messages,
                    attachments=attachments or None,
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
