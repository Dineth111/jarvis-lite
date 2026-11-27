"""YouTube search and browser playback tool powered by yt-dlp."""

from __future__ import annotations

import webbrowser
from typing import Any

import yt_dlp


def play_youtube(query: str) -> str:
    """Find the top YouTube result for `query`, open it in the default browser, and return title + URL."""
    try:
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return "Error playing YouTube video: search query cannot be empty."

        # If the user just asked to open YouTube itself, open the homepage directly.
        if cleaned_query.lower() in {"youtube", "my youtube", "youtube home", "youtube homepage"}:
            webbrowser.open("https://www.youtube.com")
            return "Opened YouTube homepage (https://www.youtube.com)"

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{cleaned_query}", download=False)

        entries = (info or {}).get("entries") or []
        # Filter out any None entries
        entries = [entry for entry in entries if entry]
        if not entries:
            return f'No YouTube results found for "{cleaned_query}".'

        top_video = entries[0]
        title = top_video.get("title") or cleaned_query
        video_id = top_video.get("id")
        raw_url = top_video.get("webpage_url") or top_video.get("url") or ""

        if raw_url.startswith(("http://", "https://")):
            video_url = raw_url
        elif video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            return f'Found "{title}", but could not resolve a valid YouTube URL.'

        webbrowser.open(video_url)
        return f"Opened on YouTube: {title} ({video_url})"
    except Exception as exc:
        return f"Error playing YouTube video: {exc}"
