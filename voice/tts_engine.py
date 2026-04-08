"""Text-to-Speech engine using pyttsx3 (fully offline, no model download)."""

from __future__ import annotations

import threading
from typing import Any


class TTSEngine:
    """Offline TTS powered by pyttsx3."""

    def __init__(self, rate: int = 175, voice_id: str | None = None) -> None:
        self._rate = rate
        self._voice_id = voice_id
        self._engine: Any = None

    def _load(self) -> None:
        """Lazy-load pyttsx3 engine."""
        if self._engine is not None:
            return
        try:
            import pyttsx3  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "pyttsx3 is not installed. Run: pip install pyttsx3"
            ) from exc

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", self._rate)
        if self._voice_id:
            self._engine.setProperty("voice", self._voice_id)

    def is_available(self) -> bool:
        """Return True if pyttsx3 can be imported."""
        try:
            import pyttsx3  # type: ignore[import]  # noqa: F401
            return True
        except ImportError:
            return False

    def speak(self, text: str) -> None:
        """Speak text through speakers (blocking)."""
        self._load()
        assert self._engine is not None
        self._engine.say(text)
        self._engine.runAndWait()

    def speak_async(self, text: str) -> None:
        """Speak text in a background thread (non-blocking)."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def save_to_file(self, text: str, output_path: str) -> str:
        """Save speech audio to WAV file. Returns output_path."""
        self._load()
        assert self._engine is not None
        self._engine.save_to_file(text, output_path)
        self._engine.runAndWait()
        return output_path

    def set_rate(self, rate: int) -> None:
        self._rate = rate
        if self._engine is not None:
            self._engine.setProperty("rate", rate)

    def list_voices(self) -> list[dict]:
        """Return available voices as [{id, name, language}]."""
        self._load()
        assert self._engine is not None
        result = []
        for v in self._engine.getProperty("voices"):
            lang = ""
            if v.languages:
                raw = v.languages[0]
                lang = raw.decode() if isinstance(raw, bytes) else str(raw)
            result.append({"id": v.id, "name": v.name, "language": lang})
        return result
