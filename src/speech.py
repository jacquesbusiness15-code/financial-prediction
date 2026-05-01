"""OpenAI speech-to-text wrapper for the copilot mic input."""
from __future__ import annotations

import base64
import binascii
import io
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

_MODEL = "gpt-4o-mini-transcribe"
_FALLBACK_MODEL = "whisper-1"


def _client() -> "OpenAI | None":
    if OpenAI is None:
        return None
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _ext_for_mime(mime: str) -> str:
    m = (mime or "").lower()
    if "webm" in m:
        return "webm"
    if "ogg" in m:
        return "ogg"
    if "wav" in m:
        return "wav"
    if "mp4" in m or "m4a" in m or "aac" in m:
        return "m4a"
    if "mpeg" in m or "mp3" in m:
        return "mp3"
    return "webm"


def transcribe(audio_b64: str, mime: str = "audio/webm",
               lang: str | None = None) -> str:
    """Transcribe a base64-encoded audio blob via OpenAI.

    Returns the transcript text, or raises RuntimeError on failure.
    """
    if not audio_b64:
        raise RuntimeError("No audio data received.")
    try:
        raw = base64.b64decode(audio_b64, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(f"Invalid audio payload: {exc}") from exc
    if not raw:
        raise RuntimeError("Empty audio recording.")

    client = _client()
    if client is None:
        raise RuntimeError(
            "OpenAI API not configured - set OPENAI_API_KEY in .env "
            "and install the 'openai' package.",
        )

    buf = io.BytesIO(raw)
    buf.name = f"recording.{_ext_for_mime(mime)}"

    kwargs: dict = {"model": _MODEL, "file": buf}
    if lang:
        # Whisper expects ISO-639-1; map our two-letter codes through.
        kwargs["language"] = lang[:2].lower()

    try:
        resp = client.audio.transcriptions.create(**kwargs)
    except Exception:  # noqa: BLE001 - try the older model if the new one is unavailable
        buf.seek(0)
        kwargs["model"] = _FALLBACK_MODEL
        resp = client.audio.transcriptions.create(**kwargs)

    text = getattr(resp, "text", None) or ""
    return text.strip()
