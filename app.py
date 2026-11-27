"""Futuristic J.A.R.V.I.S. Holographic HUD with AI Face Avatar & Two-Way Voice."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from assistant import chat, get_api_key, get_model_name
from db import get_connection, init_db
from tools.memory import get_all_facts
from tools.tasks import complete_task
from voice import VOICE_PRESETS, synthesize_speech, transcribe_audio

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)
init_db()

st.set_page_config(
    page_title="J.A.R.V.I.S. Lite — HUD",
    page_icon=":material/neurology:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Futuristic HUD Styling & Holographic Face Animations
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at 20% 14%, rgba(0, 200, 255, 0.12), transparent 42%),
          radial-gradient(circle at 82% 20%, rgba(0, 120, 255, 0.10), transparent 40%),
          linear-gradient(180deg, #040811 0%, #050c19 55%, #030710 100%);
      }
      .block-container {
        padding-top: 1.3rem;
        padding-bottom: 1.4rem;
        max-width: 1380px;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      div[data-testid="stChatMessage"] {
        background: rgba(10, 22, 42, 0.66);
        border: 1px solid rgba(0, 200, 255, 0.18);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        backdrop-filter: blur(8px);
      }
      div[data-testid="stChatInput"] > div {
        border: 1px solid rgba(0, 200, 255, 0.38) !important;
        box-shadow: 0 0 20px rgba(0, 200, 255, 0.14);
      }
      @keyframes jarvis-spin-cw {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      @keyframes jarvis-spin-ccw {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
      }
      @keyframes jarvis-blink {
        0%, 92%, 100% { transform: scaleY(1); }
        96% { transform: scaleY(0.08); }
      }
      @keyframes jarvis-scan {
        0% { transform: translateY(-48px); opacity: 0; }
        20% { opacity: 0.55; }
        80% { opacity: 0.55; }
        100% { transform: translateY(56px); opacity: 0; }
      }
      @keyframes jarvis-eq-idle {
        0%, 100% { height: 6px; opacity: 0.55; }
        50% { height: 14px; opacity: 0.9; }
      }
      @keyframes jarvis-eq-talk {
        0%, 100% { height: 7px; opacity: 0.7; }
        50% { height: 30px; opacity: 1; }
      }
      .jarvis-hud-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 12px 18px;
        margin-bottom: 14px;
        border-radius: 12px;
        background: linear-gradient(90deg, rgba(8, 22, 44, 0.94), rgba(6, 15, 31, 0.88));
        border: 1px solid rgba(0, 200, 255, 0.30);
        box-shadow: 0 0 24px rgba(0, 200, 255, 0.09), inset 0 0 24px rgba(0, 200, 255, 0.04);
      }
      .jarvis-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        color: #dff6ff;
        text-shadow: 0 0 12px rgba(0, 200, 255, 0.5);
        margin: 0;
      }
      .jarvis-sub {
        font-size: 0.76rem;
        letter-spacing: 0.08em;
        color: #7cc9e8;
        margin: 2px 0 0 0;
        text-transform: uppercase;
      }
      .jarvis-pill-row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }
      .jarvis-chip {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(0, 200, 255, 0.35);
        background: rgba(0, 200, 255, 0.08);
        color: #9beeff;
        white-space: nowrap;
      }
      .jarvis-chip-online {
        border-color: rgba(0, 230, 168, 0.45);
        background: rgba(0, 230, 168, 0.1);
        color: #5ef5ca;
      }
      .jarvis-face-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 16px 14px 14px 14px;
        margin-bottom: 14px;
        border-radius: 14px;
        background:
          radial-gradient(circle at 50% 42%, rgba(0, 212, 255, 0.16), rgba(6, 15, 31, 0.92) 68%);
        border: 1px solid rgba(0, 200, 255, 0.28);
        box-shadow: 0 0 28px rgba(0, 200, 255, 0.10), inset 0 0 36px rgba(0, 200, 255, 0.07);
        text-align: center;
      }
      .jarvis-ring-outer {
        transform-origin: 120px 115px;
        animation: jarvis-spin-cw 26s linear infinite;
      }
      .jarvis-ring-inner {
        transform-origin: 120px 115px;
        animation: jarvis-spin-ccw 18s linear infinite;
      }
      .jarvis-eye {
        transform-box: fill-box;
        transform-origin: center;
        animation: jarvis-blink 4.6s ease-in-out infinite;
      }
      .jarvis-scan-line {
        animation: jarvis-scan 3.4s ease-in-out infinite;
      }
      @keyframes jarvis-avatar-breathe {
        0%, 100% {
          box-shadow: 0 0 22px rgba(0, 212, 255, 0.35), 0 0 46px rgba(0, 140, 255, 0.18);
          transform: scale(1);
        }
        50% {
          box-shadow: 0 0 34px rgba(0, 224, 255, 0.6), 0 0 64px rgba(0, 180, 255, 0.28);
          transform: scale(1.02);
        }
      }
      @keyframes jarvis-avatar-speak {
        0%, 100% {
          box-shadow: 0 0 28px rgba(0, 230, 168, 0.55), 0 0 58px rgba(0, 212, 255, 0.38);
          transform: scale(1.01);
        }
        50% {
          box-shadow: 0 0 44px rgba(0, 245, 196, 0.85), 0 0 78px rgba(0, 212, 255, 0.55);
          transform: scale(1.04);
        }
      }
      .jarvis-avatar-wrap {
        width: 210px;
        height: 210px;
        border-radius: 50%;
        padding: 4px;
        border: 2px solid rgba(0, 216, 255, 0.55);
        background: radial-gradient(circle, rgba(0, 212, 255, 0.22), #040811 72%);
        overflow: hidden;
        margin-bottom: 10px;
        animation: jarvis-avatar-breathe 3.4s ease-in-out infinite;
      }
      .jarvis-avatar-wrap-speaking {
        border-color: rgba(0, 230, 168, 0.85);
        animation: jarvis-avatar-speak 0.85s ease-in-out infinite;
      }
      .jarvis-avatar-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
        display: block;
      }
      .jarvis-eq {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        height: 32px;
        margin-top: 4px;
      }
      .jarvis-eq-bar {
        width: 4px;
        border-radius: 4px;
        background: linear-gradient(180deg, #9cf4ff, #00c8ff);
        box-shadow: 0 0 8px rgba(0, 200, 255, 0.7);
      }
      .jarvis-eq-idle .jarvis-eq-bar {
        animation: jarvis-eq-idle 1.8s ease-in-out infinite;
      }
      .jarvis-eq-talk .jarvis-eq-bar {
        background: linear-gradient(180deg, #80ffdb, #00d4ff);
        box-shadow: 0 0 12px rgba(0, 230, 168, 0.85);
        animation: jarvis-eq-talk 0.55s ease-in-out infinite;
      }
      .jarvis-face-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        color: #7ee8ff;
        margin-top: 6px;
        text-transform: uppercase;
      }
      .jarvis-panel-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 0.14em;
        color: #66dcff;
        text-transform: uppercase;
        margin-bottom: 6px;
      }
    </style>
    """
)

# ---------------------------------------------------------------------------
# Session state initialization (long-term memory injected at session start)
# ---------------------------------------------------------------------------
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


def _fetch_pending_tasks() -> list[dict[str, Any]]:
    """Load pending tasks for the HUD mission queue."""
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
                LIMIT 12
                """
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def _fetch_recent_notes() -> list[dict[str, Any]]:
    """Load recent notes for the HUD vault panel."""
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
    """Load the holographic Jarvis face image as a base64 data URI."""
    avatar_path = Path(__file__).resolve().parent / "assets" / "jarvis_face.jpg"
    if not avatar_path.exists():
        return ""
    encoded = base64.b64encode(avatar_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _render_holographic_face(speaking: bool = False) -> None:
    """Render the 3D holographic J.A.R.V.I.S. AI face avatar + animated voice visualizer."""
    eq_class = "jarvis-eq jarvis-eq-talk" if speaking else "jarvis-eq jarvis-eq-idle"
    wrap_class = (
        "jarvis-avatar-wrap jarvis-avatar-wrap-speaking" if speaking else "jarvis-avatar-wrap"
    )
    status_label = "VOICE SYNTHESIS • SPEAKING" if speaking else "HOLOGRAPHIC CORE • READY"
    delays = [0.0, 0.12, 0.24, 0.08, 0.18, 0.30, 0.10, 0.22, 0.05]
    bars_html = "".join(
        f'<div class="jarvis-eq-bar" style="animation-delay: {d}s;"></div>' for d in delays
    )
    avatar_uri = _load_avatar_data_uri()
    img_html = (
        f'<img class="jarvis-avatar-img" src="{avatar_uri}" alt="J.A.R.V.I.S. Holographic Face" />'
        if avatar_uri
        else ""
    )

    st.html(
        f"""
        <div class="jarvis-face-card">
          <div class="{wrap_class}">
            {img_html}
          </div>
          <div class="{eq_class}">
            {bars_html}
          </div>
          <div class="jarvis-face-status">{status_label}</div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Top Holographic HUD Status Bar
# ---------------------------------------------------------------------------
now_label = datetime.now().strftime("%a %d %b • %H:%M")
api_ready = bool(get_api_key())
status_badge = "● ONLINE" if api_ready else "● KEY REQUIRED"
status_class = "jarvis-chip jarvis-chip-online" if api_ready else "jarvis-chip"

st.html(
    f"""
    <div class="jarvis-hud-bar">
      <div>
        <p class="jarvis-title">J.A.R.V.I.S. LITE</p>
        <p class="jarvis-sub">Holographic Voice & Neural Assistant • English / සිංහල / Singlish</p>
      </div>
      <div class="jarvis-pill-row">
        <span class="{status_class}">{status_badge}</span>
        <span class="jarvis-chip">MODEL: {get_model_name()}</span>
        <span class="jarvis-chip">{now_label}</span>
      </div>
    </div>
    """
)

if not api_ready:
    st.warning(
        "`GEMINI_API_KEY` is not set yet. Get a **free** key at "
        "https://aistudio.google.com/apikey, paste it into `.env`, save, and refresh this page.",
        icon=":material/key:",
    )

pending_tasks = _fetch_pending_tasks()
current_facts = get_all_facts()
recent_notes = _fetch_recent_notes()

# Grab any queued TTS audio once so it auto-plays and activates the speaking face animation
audio_to_play = st.session_state.last_audio
st.session_state.last_audio = None

# ---------------------------------------------------------------------------
# Wide 2-Column Command Center Layout
# ---------------------------------------------------------------------------
col_console, col_hud = st.columns([2.2, 1.05], gap="large")

with col_hud:
    _render_holographic_face(speaking=bool(audio_to_play))

    if audio_to_play:
        st.audio(audio_to_play, format="audio/mp3", autoplay=True)

    # Voice & Session Controls
    with st.container(border=True):
        st.html('<div class="jarvis-panel-label">Voice & Neural Core</div>')
        voice_enabled = st.toggle("Jarvis voice output", value=True, key="voice_enabled")
        selected_voice = st.selectbox(
            "Voice profile",
            options=list(VOICE_PRESETS.keys()),
            index=0,
            key="voice_profile",
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks", len(pending_tasks))
        m2.metric("Memory", len(current_facts))
        m3.metric("Notes", len(recent_notes))

        if st.button("Reset session", icon=":material/restart_alt:", width="stretch"):
            st.session_state.api_messages = []
            st.session_state.display_messages = []
            st.session_state.pending_prompt = None
            st.session_state.last_audio = None
            st.session_state.session_facts = get_all_facts()
            st.rerun()

    # Interactive Mission Queue (Pending Tasks)
    with st.container(border=True):
        st.html('<div class="jarvis-panel-label">Mission Queue</div>')
        if pending_tasks:
            for item in pending_tasks[:7]:
                due_badge = f" · `{item['due_date']}`" if item["due_date"] else ""
                row_left, row_right = st.columns([5, 1], vertical_alignment="center")
                row_left.markdown(f"`#{item['id']}` {item['title']}{due_badge}")
                if row_right.button(
                    "",
                    key=f"done_task_{item['id']}",
                    icon=":material/check:",
                    help=f"Complete task #{item['id']}",
                ):
                    complete_task(item["id"])
                    st.rerun()
        else:
            st.caption("All clear — no pending missions.")

    # Neural Memory Bank
    with st.container(border=True):
        st.html('<div class="jarvis-panel-label">Neural Memory</div>')
        if current_facts:
            for key, value in current_facts[:8]:
                st.markdown(f"- **{key}**: {value}")
        else:
            st.caption("No long-term facts stored yet.")

    # Notes Vault
    with st.container(border=True):
        st.html('<div class="jarvis-panel-label">Notes Vault</div>')
        if recent_notes:
            for note in recent_notes[:4]:
                snippet = note["text"] if len(note["text"]) <= 70 else f"{note['text'][:67]}..."
                st.markdown(f"- `#{note['id']}` {snippet}")
        else:
            st.caption("No notes archived yet.")

with col_console:
    SUGGESTIONS = {
        ":blue[:material/add_task:] Schedule task for tomorrow": "Add a task: submit report tomorrow",
        ":green[:material/checklist:] Mission status": "What are my tasks?",
        ":red[:material/smart_display:] Play Believer": "Go to YouTube and play Believer",
        ":violet[:material/psychology:] Store memory": "Remember that I prefer concise replies and dark mode",
        ":orange[:material/translate:] Singlish command": "Machan heta ude gym yanna task ekak danna",
    }

    if not st.session_state.display_messages and st.session_state.pending_prompt is None:
        st.caption(
            "Click the **mic icon** in the input bar to talk, or choose a quick command below:"
        )
        selected_chip = st.pills(
            "Quick commands",
            list(SUGGESTIONS.keys()),
            label_visibility="collapsed",
        )
        if selected_chip:
            st.session_state.pending_prompt = SUGGESTIONS[selected_chip]
            st.rerun()

    # Conversation stream
    for message in st.session_state.display_messages:
        avatar = ":material/person:" if message["role"] == "user" else ":material/neurology:"
        with st.chat_message(message["role"], avatar=avatar):
            if message.get("tool_calls"):
                label = f":material/terminal: Executed {len(message['tool_calls'])} tool(s)"
                with st.expander(label, expanded=False):
                    for call in message["tool_calls"]:
                        st.markdown(f"**`{call['name']}`**")
                        st.code(json.dumps(call["input"], ensure_ascii=False), language="json")
                        st.caption(call["output"])
            st.markdown(message["content"])

    chat_submission = st.chat_input(
        "Speak (mic) or type a command to J.A.R.V.I.S. ...",
        accept_audio=True,
        submit_mode="disable",
    )

    active_prompt: str | None = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    if chat_submission:
        if chat_submission.audio is not None:
            with st.spinner("Listening & transcribing voice command..."):
                try:
                    raw_audio = chat_submission.audio.read()
                    mime = getattr(chat_submission.audio, "type", None) or "audio/wav"
                    spoken_text = transcribe_audio(raw_audio, mime_type=mime)
                except Exception as exc:
                    st.error(f"Could not transcribe voice command: {exc}")
                    spoken_text = ""
            if spoken_text:
                active_prompt = spoken_text
        elif chat_submission.text:
            active_prompt = chat_submission.text

    if active_prompt:
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(active_prompt)

        tool_calls_this_turn: list[dict[str, Any]] = []

        with st.chat_message("assistant", avatar=":material/neurology:"):
            with st.status("Processing neural request...", expanded=False) as status_box:

                def _handle_tool_call(event: dict[str, Any]) -> None:
                    tool_calls_this_turn.append(event)
                    status_box.update(
                        label=f"Executing `{event['name']}`...",
                        state="running",
                    )
                    status_box.markdown(f"**`{event['name']}`**")
                    status_box.code(
                        json.dumps(event["input"], ensure_ascii=False),
                        language="json",
                    )
                    status_box.caption(event["output"])

                try:
                    reply = chat(
                        active_prompt,
                        st.session_state.api_messages,
                        session_facts=st.session_state.session_facts,
                        on_tool_call=_handle_tool_call,
                    )
                    done_label = (
                        f"Executed {len(tool_calls_this_turn)} tool(s)"
                        if tool_calls_this_turn
                        else "Response ready"
                    )
                    status_box.update(label=done_label, state="complete", expanded=False)
                except Exception as exc:
                    status_box.update(label="Command failed", state="error", expanded=True)
                    st.error(f"Could not complete request: {exc}")
                    st.stop()

            st.markdown(reply)

            if voice_enabled:
                with st.spinner("Synthesizing J.A.R.V.I.S. voice..."):
                    st.session_state.last_audio = synthesize_speech(
                        reply,
                        voice_id=VOICE_PRESETS[selected_voice],
                    )

        st.session_state.display_messages.append({"role": "user", "content": active_prompt})
        st.session_state.display_messages.append(
            {
                "role": "assistant",
                "content": reply,
                "tool_calls": tool_calls_this_turn,
            }
        )
        st.rerun()
