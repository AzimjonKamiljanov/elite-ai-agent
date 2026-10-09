"""
Ovoz tizimi — STT (Whisper) va TTS (piper/sistem).
Bog'liqliklar yo'q bo'lsa, graceful fallback.
"""

from __future__ import annotations


class VoiceEngine:
    """Ovoz kiritish va chiqarish tizimi."""

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled
        self._whisper_model: object | None = None
        self._tts_engine: str | None = None
        if enabled:
            self._init_stt()
            self._init_tts()

    def _init_stt(self) -> None:
        """Whisper STT ni ishga tushirish."""
        try:
            import whisper  # type: ignore

            self._whisper_model = whisper.load_model("base")
        except ImportError:
            self._whisper_model = None
        except Exception:
            self._whisper_model = None

    def _init_tts(self) -> None:
        """TTS ni ishga tushirish."""
        # piper ni tekshirish
        try:
            import subprocess

            result = subprocess.run(["piper", "--version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                self._tts_engine = "piper"
                return
        except Exception:
            pass

        # Tizim TTS ni tekshirish (espeak)
        try:
            import subprocess

            result = subprocess.run(["espeak", "--version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                self._tts_engine = "espeak"
                return
        except Exception:
            pass

        # macOS say
        try:
            import subprocess

            result = subprocess.run(["say", "--version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                self._tts_engine = "say"
                return
        except Exception:
            pass

        self._tts_engine = None

    def listen(self) -> str:
        """Mikrofon orqali ovoz kiritishni tinglash (5 sekund).

        Returns:
            Transkriptlangan matn yoki bo'sh satr
        """
        if not self._enabled:
            return ""

        if self._whisper_model is None:
            return ""

        try:
            import tempfile

            import sounddevice as sd  # type: ignore
            import soundfile as sf  # type: ignore

            samplerate = 16000
            duration = 5  # sekund
            audio = sd.rec(
                int(duration * samplerate),
                samplerate=samplerate,
                channels=1,
                dtype="float32",
            )
            sd.wait()

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, samplerate)
                result = self._whisper_model.transcribe(tmp.name)  # type: ignore
                return result.get("text", "").strip()
        except Exception:
            return ""

    def speak(self, text: str) -> None:
        """Matnni ovozga aylantirish va o'qish."""
        if not self._enabled or not self._tts_engine or not text.strip():
            return

        try:
            import subprocess

            if self._tts_engine == "espeak":
                subprocess.run(["espeak", text], timeout=30, capture_output=True)
            elif self._tts_engine == "say":
                subprocess.run(["say", text], timeout=30, capture_output=True)
            elif self._tts_engine == "piper":
                # piper stdin orqali qabul qiladi
                subprocess.run(
                    ["piper", "--output-raw"],
                    input=text.encode(),
                    timeout=30,
                    capture_output=True,
                )
        except Exception:
            pass

    @property
    def is_available(self) -> bool:
        """Ovoz tizimi ishga tayyor ekanligini tekshirish."""
        return self._enabled and self._tts_engine is not None

    @property
    def stt_available(self) -> bool:
        """STT mavjudligini tekshirish."""
        return self._enabled and self._whisper_model is not None
