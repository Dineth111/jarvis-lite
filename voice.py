"""Voice input (Gemini audio transcription) and neural TTS output (edge-tts) for Jarvis Lite."""

from __future__ import annotations

import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

from google.genai import types

from assistant import _build_model_chain, _generate_with_fallback, get_client, get_model_name

VOICE_PRESETS: dict[str, str] = {
    "Jarvis (British Male)": "en-GB-RyanNeural",
    "Friday (British Female)": "en-GB-SoniaNeural",
    "Jarvis (US Male)": "en-US-AndrewNeural",
    "Sinhala (Male)": "si-LK-SameeraNeural",
    "Sinhala (Female)": "si-LK-ThiliniNeural",
}

_SINHALA_RE = re.compile(r"[\u0D80-\u0DFF]")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_URL_RE = re.compile(r"https?://\S+")


def _clean_for_speech(text: str) -> str:
    """Strip Markdown symbols and URLs so TTS sounds natural."""
    cleaned = _MD_LINK_RE.sub(r"\1", text or "")
    cleaned = _URL_RE.sub("", cleaned)
    cleaned = re.sub(r"[`*_#>~]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 700:
        cleaned = cleaned[:700].rsplit(" ", 1)[0] + "."
    return cleaned


def _pick_voice(text: str, preferred_voice: str) -> str:
    """Auto-switch to Sinhala neural voice when the reply contains Sinhala script."""
    if _SINHALA_RE.search(text) and not preferred_voice.startswith("si-LK-"):
        if "Sonia" in preferred_voice or "Thilini" in preferred_voice:
            return "si-LK-ThiliniNeural"
        return "si-LK-SameeraNeural"
    return preferred_voice


async def _edge_tts_bytes(text: str, voice: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+4%")
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def synthesize_speech(text: str, voice_id: str = "en-GB-RyanNeural") -> bytes | None:
    """Convert assistant reply text into MP3 audio bytes using Microsoft Neural TTS."""
    try:
        spoken = _clean_for_speech(text)
        if not spoken:
            return None

        target_voice = _pick_voice(spoken, voice_id)

        def _runner() -> bytes:
            return asyncio.run(_edge_tts_bytes(spoken, target_voice))

        # Run in a dedicated thread so it never conflicts with Streamlit's event loop.
        with ThreadPoolExecutor(max_workers=1) as pool:
            audio_bytes = pool.submit(_runner).result(timeout=20)
        return audio_bytes or None
    except Exception:
        return None


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Transcribe a voice command using Gemini's native audio understanding."""
    if not audio_bytes:
        return ""

    client = get_client()
    models = _build_model_chain(get_model_name())
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=(
                        "Transcribe this spoken command accurately in the speaker's original "
                        "language (English, Sinhala, or Romanized Singlish). "
                        "Return ONLY the transcribed text with no extra commentary."
                    )
                ),
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )
    ]
    response, _ = _generate_with_fallback(
        client,
        models=models,
        contents=contents,
        config=types.GenerateContentConfig(),
    )
    return (getattr(response, "text", None) or "").strip()
