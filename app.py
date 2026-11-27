"""Cinematic 3-Column J.A.R.V.I.S. Holographic Cockpit HUD with Centerpiece 3D Face & Voice."""

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
from tools.memory import get_all_facts
from tools.tasks import complete_task
from voice import VOICE_PRESETS, synthesize_speech, transcribe_audio

importlib.reload(_db_mod)
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
    page_title="J.A.R.V.I.S. Lite — Hologram Cockpit",
    page_icon=":material/neurology:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Cinematic Iron Man / J.A.R.V.I.S. Cockpit CSS
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at 50% 34%, rgba(0, 212, 255, 0.16), transparent 46%),
          radial-gradient(circle at 12% 18%, rgba(0, 110, 255, 0.10), transparent 36%),
          radial-gradient(circle at 88% 18%, rgba(0, 230, 168, 0.08), transparent 36%),
          linear-gradient(180deg, #030710 0%, #050d1c 52%, #02060e 100%);
      }
      .block-container {
        padding-top: 0.9rem;
        padding-bottom: 1.2rem;
        max-width: 1520px;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      div[data-testid="stChatInput"] > div {
        border: 1px solid rgba(0, 216, 255, 0.48) !important;
        background: rgba(6, 16, 33, 0.88) !important;
        box-shadow: 0 0 26px rgba(0, 200, 255, 0.18);
      }
      @keyframes jarvis-spin-cw {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      @keyframes jarvis-spin-ccw {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
      }
      @keyframes jarvis-breathe {
        0%, 100% {
          box-shadow: 0 0 32px rgba(0, 212, 255, 0.42), 0 0 72px rgba(0, 140, 255, 0.22);
          transform: scale(1);
        }
        50% {
          box-shadow: 0 0 48px rgba(0, 228, 255, 0.68), 0 0 96px rgba(0, 180, 255, 0.34);
          transform: scale(1.018);
        }
      }
      @keyframes jarvis-speak-glow {
        0%, 100% {
          box-shadow: 0 0 40px rgba(0, 235, 175, 0.65), 0 0 88px rgba(0, 212, 255, 0.45);
          transform: scale(1.01);
        }
        50% {
          box-shadow: 0 0 64px rgba(0, 255, 204, 0.95), 0 0 120px rgba(0, 212, 255, 0.65);
          transform: scale(1.035);
        }
      }
      @keyframes jarvis-eq-idle {
        0%, 100% { height: 7px; opacity: 0.48; }
        50% { height: 17px; opacity: 0.9; }
      }
      @keyframes jarvis-eq-talk {
        0%, 100% { height: 8px; opacity: 0.72; }
        50% { height: 38px; opacity: 1; }
      }

      /* Top HUD Bar */
      .jarvis-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 10px 18px;
        margin-bottom: 14px;
        border-radius: 12px;
        background: linear-gradient(90deg, rgba(6, 18, 38, 0.94), rgba(4, 12, 26, 0.88), rgba(6, 18, 38, 0.94));
        border: 1px solid rgba(0, 208, 255, 0.32);
        box-shadow: 0 0 28px rgba(0, 200, 255, 0.10), inset 0 0 20px rgba(0, 200, 255, 0.05);
      }
      .jarvis-brand-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        color: #e2f8ff;
        text-shadow: 0 0 14px rgba(0, 212, 255, 0.55);
        margin: 0;
      }
      .jarvis-brand-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.10em;
        color: #79cbe8;
        margin: 2px 0 0 0;
        text-transform: uppercase;
      }
      .jarvis-chip-row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }
      .jarvis-chip {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(0, 208, 255, 0.36);
        background: rgba(0, 208, 255, 0.09);
        color: #9ef0ff;
        white-space: nowrap;
      }
      .jarvis-chip-live {
        border-color: rgba(0, 235, 170, 0.55);
        background: rgba(0, 235, 170, 0.12);
        color: #66ffd1;
      }

      /* Center Holographic Face Stage */
      .jarvis-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 26px 20px 22px 20px;
        margin-bottom: 14px;
        border-radius: 18px;
        background:
          radial-gradient(circle at 50% 40%, rgba(0, 212, 255, 0.18), rgba(4, 11, 24, 0.90) 68%);
        border: 1px solid rgba(0, 212, 255, 0.30);
        box-shadow: 0 0 42px rgba(0, 200, 255, 0.12), inset 0 0 48px rgba(0, 200, 255, 0.08);
        position: relative;
        overflow: hidden;
      }
      .jarvis-orbital-frame {
        position: relative;
        width: 336px;
        height: 336px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
      }
      .jarvis-orbit-outer {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        border: 2px dashed rgba(0, 216, 255, 0.45);
        animation: jarvis-spin-cw 28s linear infinite;
        pointer-events: none;
      }
      .jarvis-orbit-mid {
        position: absolute;
        inset: 12px;
        border-radius: 50%;
        border: 2px dotted rgba(0, 235, 175, 0.40);
        animation: jarvis-spin-ccw 19s linear infinite;
        pointer-events: none;
      }
      .jarvis-portal {
        width: 292px;
        height: 292px;
        border-radius: 50%;
        padding: 5px;
        border: 2.5px solid rgba(0, 224, 255, 0.72);
        background: radial-gradient(circle, rgba(0, 216, 255, 0.25), #030812 72%);
        overflow: hidden;
        animation: jarvis-breathe 3.4s ease-in-out infinite;
      }
      .jarvis-portal-speaking {
        border-color: rgba(0, 250, 190, 0.92);
        animation: jarvis-speak-glow 0.8s ease-in-out infinite;
      }
      .jarvis-portal-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
        transform: scale(1.22);
        display: block;
      }

      /* 17-Bar Voice Waveform Equalizer */
      .jarvis-wave {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        height: 40px;
        margin-bottom: 8px;
      }
      .jarvis-wave-bar {
        width: 4.5px;
        border-radius: 5px;
        background: linear-gradient(180deg, #b8f8ff, #00c8ff);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.75);
      }
      .jarvis-wave-idle .jarvis-wave-bar {
        animation: jarvis-eq-idle 1.9s ease-in-out infinite;
      }
      .jarvis-wave-talk .jarvis-wave-bar {
        background: linear-gradient(180deg, #9effe4, #00d8ff);
        box-shadow: 0 0 14px rgba(0, 240, 185, 0.92);
        animation: jarvis-eq-talk 0.48s ease-in-out infinite;
      }
      .jarvis-state-tag {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.74rem;
        letter-spacing: 0.22em;
        color: #7eeeff;
        text-transform: uppercase;
        margin-bottom: 14px;
      }

      /* Live Holographic Speech Subtitle Box */
      .jarvis-subtitle-box {
        width: 100%;
        max-width: 640px;
        padding: 14px 18px;
        border-radius: 12px;
        background: rgba(5, 16, 34, 0.82);
        border: 1px solid rgba(0, 212, 255, 0.30);
        box-shadow: inset 0 0 18px rgba(0, 212, 255, 0.06);
        text-align: center;
      }
      .jarvis-subtitle-who {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        letter-spacing: 0.16em;
        color: #5ee6ff;
        text-transform: uppercase;
        margin-bottom: 6px;
      }
      .jarvis-subtitle-text {
        font-size: 1.02rem;
        line-height: 1.55;
        color: #e8faff;
        margin: 0;
        white-space: pre-wrap;
      }
      .jarvis-tool-pill {
        display: inline-block;
        margin-top: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid rgba(0, 230, 168, 0.42);
        background: rgba(0, 230, 168, 0.10);
        color: #6ef7cf;
      }

      .jarvis-wing-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.74rem;
        letter-spacing: 0.15em;
        color: #6ce0ff;
        text-transform: uppercase;
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


def _render_center_hologram(
    *,
    speaking: bool,
    latest_reply: str,
    latest_tools: list[dict[str, Any]],
) -> None:
    """Render the giant centered 3D holographic face + equalizer + live speech subtitle."""
    portal_class = "jarvis-portal jarvis-portal-speaking" if speaking else "jarvis-portal"
    wave_class = "jarvis-wave jarvis-wave-talk" if speaking else "jarvis-wave jarvis-wave-idle"
    state_text = "VOICE LINK ACTIVE • SPEAKING" if speaking else "HOLOGRAPHIC CORE • LISTENING"

    delays = [0.0, 0.08, 0.16, 0.24, 0.12, 0.28, 0.04, 0.20, 0.32, 0.18, 0.06, 0.26, 0.14, 0.22, 0.10, 0.05, 0.15]
    bars_html = "".join(
        f'<div class="jarvis-wave-bar" style="animation-delay: {d}s;"></div>' for d in delays
    )

    avatar_uri = _load_avatar_data_uri()
    img_html = (
        f'<img class="jarvis-portal-img" src="{avatar_uri}" alt="J.A.R.V.I.S." />'
        if avatar_uri
        else ""
    )

    safe_reply = html.escape(latest_reply)
    tool_html = ""
    if latest_tools:
        names = ", ".join(t["name"] for t in latest_tools)
        tool_html = f'<div class="jarvis-tool-pill">⚡ EXECUTED: {html.escape(names)}</div>'

    st.html(
        f"""
        <div class="jarvis-stage">
          <div class="jarvis-orbital-frame">
            <div class="jarvis-orbit-outer"></div>
            <div class="jarvis-orbit-mid"></div>
            <div class="{portal_class}">
              {img_html}
            </div>
          </div>
          <div class="{wave_class}">
            {bars_html}
          </div>
          <div class="jarvis-state-tag">{state_text}</div>
          <div class="jarvis-subtitle-box">
            <div class="jarvis-subtitle-who">J.A.R.V.I.S. LIVE TRANSMISSION</div>
            <p class="jarvis-subtitle-text">{safe_reply}</p>
            {tool_html}
          </div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Top Holographic Status Bar
# ---------------------------------------------------------------------------
now_label = datetime.now().strftime("%a %d %b • %H:%M")
api_ready = bool(get_api_key())
status_text = "● SYSTEMS ONLINE" if api_ready else "● API KEY REQUIRED"
status_css = "jarvis-chip jarvis-chip-live" if api_ready else "jarvis-chip"

st.html(
    f"""
    <div class="jarvis-topbar">
      <div>
        <p class="jarvis-brand-title">J.A.R.V.I.S. LITE</p>
        <p class="jarvis-brand-sub">Developer Neural Cockpit • Voice / English / සිංහල / Singlish</p>
      </div>
      <div class="jarvis-chip-row">
        <span class="{status_css}">{status_text}</span>
        <span class="jarvis-chip">{get_model_name()}</span>
        <span class="jarvis-chip">{now_label}</span>
      </div>
    </div>
    """
)

if not api_ready:
    st.warning(
        "`GEMINI_API_KEY` is not set yet. Get a **free** key at "
        "https://aistudio.google.com/apikey, paste it into `.env`, save, and refresh.",
        icon=":material/key:",
    )

pending_tasks = _fetch_pending_tasks()
current_facts = get_all_facts()
recent_notes = _fetch_recent_notes()

# Grab queued TTS audio once so it auto-plays and activates the speaking hologram state
audio_to_play = st.session_state.last_audio
st.session_state.last_audio = None

# Latest assistant reply for the live centered speech subtitle
latest_assistant_msg = next(
    (m for m in reversed(st.session_state.display_messages) if m["role"] == "assistant"),
    None,
)
subtitle_text = (
    latest_assistant_msg["content"]
    if latest_assistant_msg
    else "All systems online. Click the microphone or type a command — I can open VS Code, build decorated HTML pages, launch WhatsApp, manage tasks, or play YouTube."
)
subtitle_tools = (latest_assistant_msg or {}).get("tool_calls") or []

# ---------------------------------------------------------------------------
# Symmetrical 3-Column Hologram Cockpit Layout
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1.0, 2.05, 1.05], gap="medium")

# LEFT WING: Mission Queue + Notes Vault
with col_left:
    with st.container(border=True):
        st.html('<div class="jarvis-wing-title">Mission Queue</div>')
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
            st.caption("All clear — no pending missions.")

    with st.container(border=True):
        st.html('<div class="jarvis-wing-title">Notes Vault</div>')
        if recent_notes:
            for note in recent_notes[:5]:
                snippet = note["text"] if len(note["text"]) <= 68 else f"{note['text'][:65]}..."
                st.markdown(f"- `#{note['id']}` {snippet}")
        else:
            st.caption("No notes archived yet.")

    with st.container(border=True):
        st.html('<div class="jarvis-wing-title">Neural Memory</div>')
        if current_facts:
            for key, value in current_facts[:6]:
                st.markdown(f"- **{key}**: {value}")
        else:
            st.caption("No facts stored yet.")

# RIGHT WING: Voice Controls + Telemetry + Scrollable Chat Log
with col_right:
    with st.container(border=True):
        st.html('<div class="jarvis-wing-title">Voice & Core</div>')
        voice_enabled = st.toggle("Jarvis voice output", value=True, key="voice_enabled")
        selected_voice = st.selectbox(
            "Voice profile",
            options=list(VOICE_PRESETS.keys()),
            index=0,
            key="voice_profile",
        )
        if audio_to_play:
            st.audio(audio_to_play, format="audio/mp3", autoplay=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks", len(pending_tasks))
        m2.metric("Mem", len(current_facts))
        m3.metric("Notes", len(recent_notes))

        if st.button("New chat session", icon=":material/add_comment:", width="stretch"):
            st.session_state.session_id = datetime.now().strftime("session-%Y%m%d-%H%M%S")
            st.session_state.api_messages = []
            st.session_state.display_messages = []
            st.session_state.pending_prompt = None
            st.session_state.last_audio = None
            st.session_state.session_facts = get_all_facts()
            st.rerun()

    with st.container(border=True):
        st.html('<div class="jarvis-wing-title">Comm Log & History</div>')
        tab_current, tab_history = st.tabs(["Current", "Saved History"])

        with tab_current:
            with st.container(height=280, border=False):
                if st.session_state.display_messages:
                    for msg in st.session_state.display_messages:
                        role_tag = "YOU" if msg["role"] == "user" else "J.A.R.V.I.S."
                        st.markdown(f"**`{role_tag}`** {msg['content']}")
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
                    st.caption("Current session conversation will appear here.")

        with tab_history:
            saved_sessions = list_chat_sessions(limit=20)
            if saved_sessions:
                session_labels = {
                    s["session_id"]: (
                        f"{(s['last_at'] or '')[5:16]} · "
                        f"{((s['preview'] or 'Chat')[:28])}"
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
                with st.container(height=205, border=False):
                    for msg in past_msgs:
                        role_tag = "YOU" if msg["role"] == "user" else "J.A.R.V.I.S."
                        ts = (msg.get("created_at") or "")[11:16]
                        st.markdown(f"**`{role_tag}`** `{ts}` {msg['content']}")

                b1, b2 = st.columns(2)
                if b1.button("Load", icon=":material/history:", width="stretch", key="load_hist_btn"):
                    st.session_state.session_id = chosen_sid
                    st.session_state.display_messages = past_msgs
                    # Rebuild clean text-only Gemini context for continuing the loaded chat
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
                st.caption("No saved chat history yet.")

# CENTER STAGE: Giant 3D Holographic Face + Quick Commands + Voice/Text Input
with col_center:
    _render_center_hologram(
        speaking=bool(audio_to_play),
        latest_reply=subtitle_text,
        latest_tools=subtitle_tools,
    )

    SUGGESTIONS = {
        ":blue[:material/code:] Build HTML page in VS Code": "Open VS Code and write a modern decorated HTML portfolio page",
        ":green[:material/chat:] Open WhatsApp": "Open WhatsApp",
        ":blue[:material/add_task:] Task for tomorrow": "Add a task: submit report tomorrow",
        ":red[:material/smart_display:] Play Believer": "Go to YouTube and play Believer",
        ":orange[:material/translate:] Singlish": "Machan mage tasks monawada?",
    }

    selected_chip = st.pills(
        "Quick commands",
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
        "Speak (mic), attach files (clip), or command J.A.R.V.I.S. ...",
        accept_audio=True,
        accept_file="multiple",
        file_type=[
            "png", "jpg", "jpeg", "webp",
            "pdf", "txt", "md", "csv", "json",
            "py", "html", "css", "js", "ts", "sql", "xml", "yaml", "yml",
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
            with st.spinner("Listening & transcribing voice..."):
                try:
                    raw_audio = chat_submission.audio.read()
                    mime = getattr(chat_submission.audio, "type", None) or "audio/wav"
                    spoken_text = transcribe_audio(raw_audio, mime_type=mime)
                except Exception as exc:
                    st.error(f"Could not transcribe voice: {exc}")
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
        with st.status(f"Executing: {prompt_text[:60]}...", expanded=False) as status_box:

            def _handle_tool_call(event: dict[str, Any]) -> None:
                tool_calls_this_turn.append(event)
                status_box.update(label=f"Running `{event['name']}`...", state="running")
                status_box.markdown(f"**`{event['name']}`**")
                status_box.caption(event["output"])

            try:
                reply = chat(
                    prompt_text,
                    st.session_state.api_messages,
                    attachments=attachments or None,
                    session_facts=st.session_state.session_facts,
                    on_tool_call=_handle_tool_call,
                )
                status_box.update(label="Transmission ready", state="complete", expanded=False)
            except Exception as exc:
                status_box.update(label="Command failed", state="error", expanded=True)
                st.error(f"Could not complete request: {exc}")
                st.stop()

        if voice_enabled:
            with st.spinner("Synthesizing J.A.R.V.I.S. voice..."):
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
