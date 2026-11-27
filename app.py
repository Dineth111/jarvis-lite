"""Streamlit chat UI for Jarvis Lite (powered by Google Gemini)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from assistant import chat, get_api_key, get_model_name
from db import get_connection, init_db
from tools.memory import get_all_facts

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)
init_db()

st.set_page_config(
    page_title="Jarvis Lite",
    page_icon=":material/smart_toy:",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Session state initialization (long-term memory injected at session start)
# ---------------------------------------------------------------------------
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

if "session_facts" not in st.session_state:
    # Snapshot of persistent facts injected into the system prompt at session start.
    st.session_state.session_facts = get_all_facts()

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


def _fetch_pending_tasks() -> list[dict[str, Any]]:
    """Load pending tasks for the sidebar overview."""
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
                LIMIT 15
                """
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def _fetch_notes_count() -> int:
    """Return total number of saved notes."""
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM notes").fetchone()
        return int(row["total"]) if row else 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Sidebar: session controls and live SQLite state
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(":material/smart_toy: Jarvis Lite")
    st.caption(f"Model: `{get_model_name()}` (Google Gemini)")

    if st.button("Start new session", icon=":material/refresh:", width="stretch"):
        st.session_state.api_messages = []
        st.session_state.display_messages = []
        st.session_state.pending_prompt = None
        # Reload stored facts so newly remembered facts enter the new session prompt.
        st.session_state.session_facts = get_all_facts()
        st.rerun()

    pending_tasks = _fetch_pending_tasks()
    current_facts = get_all_facts()
    notes_count = _fetch_notes_count()

    with st.container(border=True):
        st.markdown(f"**:material/checklist: Pending tasks ({len(pending_tasks)})**")
        if pending_tasks:
            for item in pending_tasks[:8]:
                due_badge = f" · `{item['due_date']}`" if item["due_date"] else ""
                st.markdown(f"- `#{item['id']}` {item['title']}{due_badge}")
        else:
            st.caption("No pending tasks.")

    with st.container(border=True):
        st.markdown(f"**:material/psychology: Memory facts ({len(current_facts)})**")
        if current_facts:
            for key, value in current_facts[:8]:
                st.markdown(f"- **{key}**: {value}")
        else:
            st.caption("No facts stored yet.")

    st.caption(f":material/sticky_note_2: Saved notes: **{notes_count}**")


# ---------------------------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------------------------
st.title("Jarvis Lite")
st.caption(
    "Your personal AI assistant for tasks, notes, memory, and YouTube — "
    "chat naturally in English, සිංහල, or Singlish."
)

if not get_api_key():
    st.warning(
        "`GEMINI_API_KEY` is not set yet. Get a **free** key at "
        "https://aistudio.google.com/apikey, paste it into `.env`, save, and refresh this page.",
        icon=":material/key:",
    )

# Render conversation history
for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        if message.get("tool_calls"):
            label = f":material/build: Used {len(message['tool_calls'])} tool(s)"
            with st.expander(label, expanded=False):
                for call in message["tool_calls"]:
                    st.markdown(f"**`{call['name']}`**")
                    st.code(json.dumps(call["input"], ensure_ascii=False), language="json")
                    st.caption(call["output"])
        st.markdown(message["content"])

# Starter suggestion chips when chat is empty
SUGGESTIONS = {
    ":blue[:material/add_task:] Add task for tomorrow": "Add a task: submit report tomorrow",
    ":green[:material/checklist:] Check my tasks": "What are my tasks?",
    ":red[:material/smart_display:] Play Believer": "Go to YouTube and play Believer",
    ":violet[:material/psychology:] Remember a fact": "Remember that my favorite drink is iced latte",
    ":orange[:material/translate:] Try Singlish": "Machan heta ude gym yanna task ekak danna",
}

if not st.session_state.display_messages and st.session_state.pending_prompt is None:
    selected_chip = st.pills(
        "Starter prompts",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
    )
    if selected_chip:
        st.session_state.pending_prompt = SUGGESTIONS[selected_chip]
        st.rerun()

typed_prompt = st.chat_input(
    "Ask Jarvis Lite anything (e.g., 'add a task: submit report tomorrow')...",
    submit_mode="disable",
)

active_prompt = typed_prompt or st.session_state.pending_prompt
st.session_state.pending_prompt = None

if active_prompt:
    with st.chat_message("user"):
        st.markdown(active_prompt)

    tool_calls_this_turn: list[dict[str, Any]] = []

    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False) as status_box:

            def _handle_tool_call(event: dict[str, Any]) -> None:
                tool_calls_this_turn.append(event)
                status_box.update(
                    label=f"Running `{event['name']}`...",
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
                    f"Used {len(tool_calls_this_turn)} tool(s)"
                    if tool_calls_this_turn
                    else "Response ready"
                )
                status_box.update(label=done_label, state="complete", expanded=False)
            except Exception as exc:
                status_box.update(label="Request failed", state="error", expanded=True)
                st.error(f"Could not complete request: {exc}")
                st.stop()

        st.markdown(reply)

    st.session_state.display_messages.append({"role": "user", "content": active_prompt})
    st.session_state.display_messages.append(
        {
            "role": "assistant",
            "content": reply,
            "tool_calls": tool_calls_this_turn,
        }
    )
    st.rerun()
