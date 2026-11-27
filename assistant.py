"""Gemini conversation loop with multi-step tool-use handling."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from db import init_db
from prompts import build_system_prompt
from tools import TOOLS, run_tool

_ENV_PATH = Path(__file__).resolve().parent / ".env"

# Load environment variables from .env (never hardcode API keys).
load_dotenv(dotenv_path=_ENV_PATH, override=True)

DEFAULT_MODEL = "gemini-3.8-flash"
MAX_TOOL_ROUNDS = 10
RETRY_DELAYS_SECONDS = (1.5, 3.0, 5.0)


def get_model_name() -> str:
    """Return the configured Gemini model name (defaults to gemini-3.8-flash)."""
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    configured = os.getenv("GEMINI_MODEL", "").strip()
    return configured or DEFAULT_MODEL


def get_api_key() -> str:
    """Read GEMINI_API_KEY (or GOOGLE_API_KEY) from .env / environment."""
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key or key in {"your_gemini_api_key_here", "your_api_key_here"}:
        return ""
    return key


def get_client() -> genai.Client:
    """Instantiate a Google GenAI client using GEMINI_API_KEY from .env."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Get a free key from https://aistudio.google.com/apikey "
            "and paste it into your `.env` file."
        )
    return genai.Client(api_key=api_key)


def _build_gemini_tools() -> list[types.Tool]:
    """Convert TOOLS JSON schemas into Google GenAI FunctionDeclarations."""
    declarations = [
        types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters_json_schema=tool["input_schema"],
        )
        for tool in TOOLS
    ]
    return [types.Tool(function_declarations=declarations)]


def _extract_function_calls(model_content: types.Content) -> list[types.FunctionCall]:
    """Extract all FunctionCall parts from a model response Content block."""
    calls: list[types.FunctionCall] = []
    for part in model_content.parts or []:
        if getattr(part, "function_call", None) is not None:
            calls.append(part.function_call)
    return calls


def _extract_text(model_content: types.Content) -> str:
    """Extract visible text parts (excluding internal thought parts) from Content."""
    chunks: list[str] = []
    for part in model_content.parts or []:
        if getattr(part, "thought", False):
            continue
        text = getattr(part, "text", None)
        if text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def _generate_with_retry(
    client: Any,
    *,
    model: str,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
) -> Any:
    """Call Gemini generate_content with automatic retry on temporary 503/429 spikes."""
    last_exc: Exception | None = None
    for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except genai_errors.APIError as exc:
            last_exc = exc
            if exc.code in (429, 503) and attempt < len(RETRY_DELAYS_SECONDS):
                time.sleep(RETRY_DELAYS_SECONDS[attempt])
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unexpected retry failure.")


def chat(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    *,
    system_prompt: str | None = None,
    session_facts: list[tuple[str, str]] | None = None,
    on_tool_call: Callable[[dict[str, Any]], None] | None = None,
    client: Any | None = None,
    model: str | None = None,
) -> str:
    """Send `user_message` to Gemini and run tools in a loop until no tool calls remain.

    Args:
        user_message: Natural-language prompt from the user.
        history: Mutable conversation list of serialized `types.Content` dicts; updated
            in-place only when the full turn succeeds so errors never corrupt state.
        system_prompt: Optional prebuilt system prompt; built automatically if omitted.
        session_facts: Optional `(key, value)` snapshot captured at session start.
        on_tool_call: Optional callback invoked with `{id, name, input, output}` per tool call.
        client: Optional pre-configured GenAI client (useful for testing).
        model: Optional model override (defaults to `gemini-2.5-flash`).

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
    gemini_tools = _build_gemini_tools()

    # Rehydrate prior turns into Content objects on a working copy.
    working_contents: list[types.Content] = [
        types.Content.model_validate(item) if isinstance(item, dict) else item
        for item in (history or [])
    ]
    working_contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=cleaned_input)])
    )

    rounds = 0
    while True:
        rounds += 1
        response = _generate_with_retry(
            active_client,
            model=active_model,
            contents=working_contents,
            config=types.GenerateContentConfig(
                system_instruction=active_system,
                tools=gemini_tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

        candidates = getattr(response, "candidates", None) or []
        if not candidates or getattr(candidates[0], "content", None) is None:
            raise RuntimeError("Model returned an empty response.")

        model_content: types.Content = candidates[0].content
        working_contents.append(model_content)

        function_calls = _extract_function_calls(model_content)

        # Keep calling the API until the model stops requesting tool calls.
        if not function_calls:
            final_reply = _extract_text(model_content)
            if history is not None:
                history[:] = [
                    item.model_dump(mode="json", exclude_none=True)
                    for item in working_contents
                ]
            return final_reply or "Done."

        if rounds >= MAX_TOOL_ROUNDS:
            if history is not None:
                history[:] = [
                    item.model_dump(mode="json", exclude_none=True)
                    for item in working_contents
                ]
            return "Stopped after reaching the maximum number of consecutive tool calls."

        response_parts: list[types.Part] = []
        for fc in function_calls:
            tool_name = fc.name or ""
            tool_input = dict(fc.args) if isinstance(fc.args, dict) else {}
            tool_output = run_tool(tool_name, tool_input)

            if on_tool_call is not None:
                on_tool_call(
                    {
                        "id": getattr(fc, "id", None) or tool_name,
                        "name": tool_name,
                        "input": tool_input,
                        "output": tool_output,
                    }
                )

            response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": tool_output},
                )
            )

        working_contents.append(types.Content(role="user", parts=response_parts))
