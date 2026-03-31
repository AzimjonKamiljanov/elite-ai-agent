"""Voice assistant loop — listen → transcribe → AI → speak."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.orchestrator import JarvisOrchestrator

from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .audio_stream import AudioStream


class VoiceAssistant:
    """End-to-end voice interaction loop using Vosk STT + pyttsx3 TTS."""

    def __init__(self, orchestrator: "JarvisOrchestrator", config: dict | None = None) -> None:
        cfg = config or {}
        model_path = cfg.get("stt_model_path", None)
        tts_rate = int(cfg.get("tts_rate", 175))
        self._stt = STTEngine(model_path=model_path)
        self._tts = TTSEngine(rate=tts_rate)
        self._audio = AudioStream()
        self._orchestrator = orchestrator

    def is_available(self) -> bool:
        return (
            self._stt.is_available()
            and self._tts.is_available()
            and self._audio.is_available()
        )

    def get_status(self) -> dict:
        return {
            "stt": self._stt.is_available(),
            "tts": self._tts.is_available(),
            "microphone": self._audio.is_available(),
        }

    async def run_voice_loop(self) -> None:
        """Continuous listen-respond loop until KeyboardInterrupt."""
        from rich.console import Console
        console = Console()
        console.print("[bold cyan]Voice mode active. Speak or press Ctrl+C to exit.[/bold cyan]")

        session_id = "voice-session"
        while True:
            try:
                console.print("[dim]Listening…[/dim]")
                pcm = self._audio.record(duration=5.0)
                result = self._stt.transcribe_audio(pcm)
                text = result.get("text", "").strip()
                if not text:
                    continue

                console.print(f"[cyan]You:[/cyan] {text}")

                # Get AI response
                ai_result = await self._orchestrator.process_message(  # type: ignore[union-attr]
                    user_input=text, session_id=session_id
                )
                response = ai_result["response"]
                console.print(f"[green]JARVIS:[/green] {response}")
                self._tts.speak_async(response)

            except KeyboardInterrupt:
                console.print("\n[dim]Voice mode deactivated.[/dim]")
                break
            except Exception as exc:
                console.print(f"[red]Voice error:[/red] {exc}")
                await asyncio.sleep(0.5)
