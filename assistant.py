"""Claude conversation loop with multi-step tool-use handling."""

from __future__ import annotations

import os
from typing import Any, Callable

from anthropic import Anthropic
from dotenv import load_dotenv

from db import init_db
from prompts import build_system_prompt
from tools import TOOLS, run_tool

# Load environment variables from .env (never hardcode API keys).
load_dotenv()

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 10


def get_model_name() -> str:
    """Return the configured Anthropic model name (defaults to claude-sonnet-5-5)."""
    configured = os.getenv("ANTHROPIC_MODEL", "").strip()
    return configured or DEFAULT_MODEL


def get_client() -> Anthropic:
    """Instantiate an Anthropic client using ANTHROPIC_API_KEY from the environment."""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing. Copy `.env.example` to `.env` and set your Anthropic API key."
        )
    return Anthropic(api_key=api_key)


def _serialize_content_blocks(content: list[Any]) -> list[dict[str, Any]]:
    """Convert Anthropic SDK content blocks into JSON-serializable dicts for session history."""
    serialized: list[dict[str, Any]] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            serialized.append({"type": "text", "text": block.text})
        elif block_type == "tool_use":
            serialized.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": dict(block.input) if isinstance(block.input, dict) else block.input,
                }
            )
        elif hasattr(block, "model_dump"):
            serialized.append(block.model_dump(exclude_none=True))
        elif isinstance(block, dict):
            serialized.append(block)
    return serialized


def chat(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    *,
    system_prompt: str | None = None,
    session_facts: list[tuple[str, str]] | None = None,
    on_tool_call: Callable[[dict[str, Any]], None] | None = None,
    client: Anthropic | None = None,
    model: str | None = None,
) -> str:
    """Send `user_message` to Claude and run tools until `stop_reason != "tool_use"`.

    Args:
        user_message: Natural-language prompt from the user.
        history: Mutable conversation list in Anthropic Messages format; updated in-place
            only once the full turn succeeds so errors never leave partial tool state.
        system_prompt: Optional prebuilt system prompt; built automatically if omitted.
        session_facts: Optional `(key, value)` snapshot captured at session start.
        on_tool_call: Optional callback invoked with `{name, input, output}` per tool call.
        client: Optional pre-configured `Anthropic` client (useful for testing).
        model: Optional model override (defaults to `claude-sonnet-5-5`).

    Returns:
        The assistant's final natural-language text response.
    """
    cleaned_input = (user_message or "").strip()
    if not cleaned_input:
        return "Please enter a message."

    init_db()
    active_client = client or get_client()
    active_model = model or get_model_name()
    active_system = system_prompt or build_system_prompt(facts=session_facts)

    # Work on a shallow copy so failed API calls never corrupt Streamlit session_state.
    working_messages: list[dict[str, Any]] = list(history) if history is not None else []
    working_messages.append({"role": "user", "content": cleaned_input})

    rounds = 0
    while True:
        rounds += 1
        response = active_client.messages.create(
            model=active_model,
            max_tokens=MAX_TOKENS,
            system=active_system,
            tools=TOOLS,
            messages=working_messages,
        )

        assistant_blocks = _serialize_content_blocks(response.content)
        working_messages.append({"role": "assistant", "content": assistant_blocks})

        # Keep calling the API until stop_reason != "tool_use".
        if response.stop_reason != "tool_use":
            reply_parts = [
                block.text
                for block in response.content
                if getattr(block, "type", None) == "text" and block.text
            ]
            final_reply = "\n\n".join(reply_parts).strip()

            if history is not None:
                history[:] = working_messages

            return final_reply or "Done."

        if rounds >= MAX_TOOL_ROUNDS:
            if history is not None:
                history[:] = working_messages
            return "Stopped after reaching the maximum number of consecutive tool calls."

        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue

            tool_input = dict(block.input) if isinstance(block.input, dict) else {}
            tool_output = run_tool(block.name, tool_input)

            if on_tool_call is not None:
                on_tool_call(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": tool_input,
                        "output": tool_output,
                    }
                )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_output,
                }
            )

        working_messages.append({"role": "user", "content": tool_results})
