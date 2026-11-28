"""Gemini conversation loop with multi-step tool calling and automatic model fallback."""

from __future__ import annotations

import io
import os
import xml.etree.ElementTree as ET
import zipfile
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

DEFAULT_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS: tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
)
MAX_TOOL_ROUNDS = 15
MAX_OUTPUT_TOKENS = 8192
_FALLBACK_STATUS_CODES = {404, 429, 500, 503, 504}


def get_model_name() -> str:
    """Return the configured primary Gemini model name (defaults to gemini-3.5-flash-lite)."""
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    configured = os.getenv("GEMINI_MODEL", "").strip()
    return configured or DEFAULT_MODEL


def _build_model_chain(primary: str) -> list[str]:
    """Return an ordered, deduplicated list of models to try on transient failures."""
    chain = [primary]
    for candidate in FALLBACK_MODELS:
        if candidate not in chain:
            chain.append(candidate)
    return chain


def get_api_key() -> str:
    """Read GEMINI_API_KEY (or GOOGLE_API_KEY) from .env / environment."""
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key or key in {"your_gemini_api_key_here", "your_api_key_here"}:
        return ""
    return key


def get_client() -> genai.Client:
    """Instantiate a Google GenAI client with fast fail-over HTTP options."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Get a free key from https://aistudio.google.com/apikey "
            "and paste it into your `.env` file."
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=90_000,
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
    )


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


def _generate_with_fallback(
    client: Any,
    *,
    models: list[str],
    contents: list[types.Content],
    config: types.GenerateContentConfig,
) -> tuple[Any, str]:
    """Try each model in `models`, failing over on 503/429/504/404 or transient disconnects."""
    last_exc: Exception | None = None
    for candidate in models:
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=contents,
                config=config,
            )
            return response, candidate
        except genai_errors.APIError as exc:
            last_exc = exc
            if exc.code in _FALLBACK_STATUS_CODES:
                continue
            raise
        except Exception as exc:
            last_exc = exc
            err_msg = str(exc).lower()
            # Recover automatically from dropped HTTP/2 connections or read timeouts
            if any(
                token in err_msg
                for token in ("disconnected", "timeout", "timed out", "connection", "reset")
            ):
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No Gemini models were available to complete the request.")


_TEXT_FILE_EXTS = {
    ".txt", ".md", ".csv", ".json", ".py", ".html", ".htm", ".log",
    ".css", ".js", ".ts", ".tsx", ".jsx", ".sql", ".xml", ".yaml", ".yml",
    ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".php",
}


def _extract_office_text(data: bytes, suffix: str) -> str:
    """Extract plain text from .docx or .pptx archives using Python stdlib only."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            if suffix == ".docx":
                xml_names = [n for n in ("word/document.xml",) if n in zf.namelist()]
            elif suffix == ".pptx":
                xml_names = sorted(
                    n for n in zf.namelist()
                    if n.startswith("ppt/slides/slide") and n.endswith(".xml")
                )
            else:
                return ""

            paragraphs: list[str] = []
            for xml_name in xml_names:
                root = ET.fromstring(zf.read(xml_name))
                # Group text runs by paragraph (<w:p> for docx, <a:p> for pptx)
                for elem in root.iter():
                    if elem.tag.endswith("}p"):
                        line = "".join(
                            node.text for node in elem.iter()
                            if node.tag.endswith("}t") and node.text
                        ).strip()
                        if line:
                            paragraphs.append(line)
            return "\n".join(paragraphs)
    except Exception:
        return ""


def _build_attachment_parts(attachments: list[dict[str, Any]] | None) -> list[types.Part]:
    """Convert uploaded file attachments (images, PDFs, Word/PPT, code/text files) into Gemini Parts."""
    parts: list[types.Part] = []
    for att in attachments or []:
        name = str(att.get("name") or "file")
        mime = str(att.get("mime_type") or "").lower()
        data = att.get("data") or b""
        if not data:
            continue

        suffix = Path(name).suffix.lower()
        if suffix in {".docx", ".pptx"}:
            extracted = _extract_office_text(data, suffix)
            if not extracted:
                extracted = "(Could not extract text from this document.)"
            if len(extracted) > 60_000:
                extracted = extracted[:60_000] + "\n... [truncated]"
            parts.append(
                types.Part.from_text(
                    text=f"[Attached document: {name}]\n{extracted}"
                )
            )
        elif mime.startswith("text/") or suffix in _TEXT_FILE_EXTS:
            decoded = data.decode("utf-8", errors="replace")
            if len(decoded) > 60_000:
                decoded = decoded[:60_000] + "\n... [truncated]"
            parts.append(
                types.Part.from_text(
                    text=f"[Attached file: {name}]\n```\n{decoded}\n```"
                )
            )
        else:
            resolved_mime = mime or "application/octet-stream"
            parts.append(types.Part.from_bytes(data=data, mime_type=resolved_mime))
    return parts


def chat(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    *,
    attachments: list[dict[str, Any]] | None = None,
    system_prompt: str | None = None,
    session_facts: list[tuple[str, str]] | None = None,
    on_tool_call: Callable[[dict[str, Any]], None] | None = None,
    client: Any | None = None,
    model: str | None = None,
) -> str:
    """Send `user_message` (and optional file attachments) to Gemini with tool calling.

    Args:
        user_message: Natural-language prompt from the user.
        history: Mutable conversation list of serialized `types.Content` dicts; updated
            in-place only when the full turn succeeds so errors never corrupt state.
        attachments: Optional list of `{name, mime_type, data}` uploaded file dicts.
        system_prompt: Optional prebuilt system prompt; built automatically if omitted.
        session_facts: Optional `(key, value)` snapshot captured at session start.
        on_tool_call: Optional callback invoked with `{id, name, input, output}` per tool call.
        client: Optional pre-configured GenAI client (useful for testing).
        model: Optional model override (defaults to `gemini-3.5-flash-lite` with fallbacks).

    Returns:
        The assistant's final natural-language text response.
    """
    cleaned_input = (user_message or "").strip()
    attachment_parts = _build_attachment_parts(attachments)
    if not cleaned_input and not attachment_parts:
        return "Please enter a message or attach a file."
    if not cleaned_input and attachment_parts:
        cleaned_input = "Please analyze the attached file(s) and help me with them."

    init_db()
    active_client = client or get_client()
    model_chain = _build_model_chain(model or get_model_name())
    active_system = system_prompt or build_system_prompt(facts=session_facts)
    gemini_tools = _build_gemini_tools()

    # Rehydrate prior turns into Content objects on a working copy.
    working_contents: list[types.Content] = [
        types.Content.model_validate(item) if isinstance(item, dict) else item
        for item in (history or [])
    ]
    user_parts = [types.Part.from_text(text=cleaned_input), *attachment_parts]
    working_contents.append(types.Content(role="user", parts=user_parts))

    rounds = 0
    while True:
        rounds += 1
        response, used_model = _generate_with_fallback(
            active_client,
            models=model_chain,
            contents=working_contents,
            config=types.GenerateContentConfig(
                system_instruction=active_system,
                tools=gemini_tools,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
        # Prefer the working model for subsequent tool-result rounds in this turn.
        if used_model != model_chain[0]:
            model_chain = _build_model_chain(used_model)

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
