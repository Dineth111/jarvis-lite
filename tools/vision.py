"""Live Desktop Screen Vision tool powered by Pillow ImageGrab + Gemini Vision."""

from __future__ import annotations

import io

from google.genai import types
from PIL import ImageGrab


def inspect_my_screen(
    question: str = "Look at my screen, describe what is visible, and help solve any error or coding issue shown.",
) -> str:
    """Capture the user's current Windows screen and analyze it with Gemini Vision."""
    try:
        screenshot = ImageGrab.grab(all_screens=False)
        # Resize large displays to keep upload fast and crisp
        screenshot.thumbnail((1600, 1000))
        if screenshot.mode != "RGB":
            screenshot = screenshot.convert("RGB")

        buf = io.BytesIO()
        screenshot.save(buf, format="JPEG", quality=82)
        jpeg_bytes = buf.getvalue()

        # Lazy import avoids circular dependency with tools/__init__.py
        from assistant import (
            _build_model_chain,
            _generate_with_fallback,
            get_client,
            get_model_name,
        )

        client = get_client()
        models = _build_model_chain(get_model_name())
        prompt_text = (question or "").strip() or (
            "Describe what is currently on my screen and help with any error or task visible."
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            f"The user shared a live capture of their computer screen. "
                            f"Answer concisely and practically: {prompt_text}"
                        )
                    ),
                    types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                ],
            )
        ]

        response, _ = _generate_with_fallback(
            client,
            models=models,
            contents=contents,
            config=types.GenerateContentConfig(max_output_tokens=1500),
        )
        analysis = (getattr(response, "text", None) or "").strip()
        return analysis or "Captured your screen, but could not generate a description."
    except Exception as exc:
        return f"Error capturing or analyzing screen: {exc}"
