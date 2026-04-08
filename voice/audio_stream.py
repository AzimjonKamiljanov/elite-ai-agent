"""Audio stream — microphone capture via sounddevice."""

from __future__ import annotations


class AudioStream:
    """Checks microphone availability and captures audio."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self._sample_rate = sample_rate
        self._channels = channels

    def is_available(self) -> bool:
        """Return True if sounddevice is installed and a mic is available."""
        try:
            import sounddevice as sd  # type: ignore[import]
            devices = sd.query_devices()
            return any(d["max_input_channels"] > 0 for d in devices)
        except Exception:
            return False

    def record(self, duration: float = 5.0) -> bytes:
        """Record audio for *duration* seconds and return raw PCM bytes."""
        try:
            import numpy as np  # type: ignore[import]
            import sounddevice as sd  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice/numpy is not installed. Run: pip install sounddevice numpy"
            ) from exc

        audio = sd.rec(
            int(duration * self._sample_rate),
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
        )
        sd.wait()
        return audio.tobytes()
