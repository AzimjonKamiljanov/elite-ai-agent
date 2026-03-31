"""JARVIS Prime — unified CLI entry point.

Usage:
    python -m apps.cli                      # interactive REPL
    python -m apps.cli "Your message"       # single message
    python -m apps.cli --mode fast "Hi"     # choose mode
    python -m apps.cli --offline "Hi"       # offline (Ollama only)
    python -m apps.cli --stream "Explain X" # streaming output
    python -m apps.cli --voice              # voice assistant mode
    python -m apps.cli --voice-test         # test voice components
    python -m apps.cli --api                # start FastAPI server
    python -m apps.cli --life               # launch life assistant

Modes: fast | code | pro | study | planner | focus | analytics | automation
Mode commands inside REPL: /fast /code /pro /study /planner /focus /analytics /auto
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Ensure repo root is on path when running as __main__
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.orchestrator import JarvisOrchestrator

console = Console()

_BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██████╗ ██████╗ ██╗███╗   ███╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██╔══██╗██╔══██╗██║████╗ ████║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗    ██████╔╝██████╔╝██║██╔████╔██║█████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██╔═══╝ ██╔══██╗██║██║╚██╔╝██║██╔══╝
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ██║     ██║  ██║██║██║ ╚═╝ ██║███████╗
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝
"""

_MODE_COMMANDS: dict[str, str] = {
    "/fast": "fast",
    "/code": "code",
    "/pro": "pro",
    "/study": "study",
    "/planner": "planner",
    "/focus": "focus",
    "/analytics": "analytics",
    "/automation": "automation",
    "/auto": "automation",  # /auto → automation mode
    "/default": "pro",
}

VERSION = "2.0.0"


def _print_banner() -> None:
    console.print(Text(_BANNER, style="bold cyan"))
    console.print(
        Panel(
            f"[bold green]JARVIS Prime v{VERSION}[/bold green] — "
            "You are Stark. I am JARVIS.\n"
            "[dim]Type /fast /code /pro to switch modes. 'exit' to quit.[/dim]",
            border_style="cyan",
        )
    )


async def _send_message(
    orchestrator: JarvisOrchestrator,
    message: str,
    session_id: str,
    force_offline: bool,
    stream: bool = False,
) -> None:
    """Send a message and print the response."""
    if stream:
        console.print()
        chunks: list[str] = []
        with console.status("[bold cyan]Streaming…[/bold cyan]", spinner="dots"):
            async for chunk in orchestrator.process_stream(
                user_input=message,
                session_id=session_id,
                force_offline=force_offline,
            ):
                chunks.append(chunk)
        console.print(
            Panel(Text("".join(chunks), style="green"), title="[dim]streamed[/dim]", border_style="green")
        )
    else:
        with console.status("[bold cyan]Thinking…[/bold cyan]", spinner="dots"):
            result = await orchestrator.process_message(
                user_input=message,
                session_id=session_id,
                force_offline=force_offline,
            )
        console.print()
        console.print(
            Panel(
                Text(result["response"], style="green"),
                title=(
                    f"[dim]mode: {result.get('mode', '?')} | "
                    f"model: {result['model_used']} | "
                    f"{result['response_time']:.2f}s[/dim]"
                ),
                border_style="green",
            )
        )


async def _repl(orchestrator: JarvisOrchestrator, force_offline: bool) -> None:
    """Interactive REPL with mode switching."""
    _print_banner()
    session_id = str(uuid.uuid4())
    current_mode = "pro"

    while True:
        try:
            prompt = f"[bold cyan][{current_mode.upper()}] You:[/bold cyan] "
            user_input = console.input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye, Mr. Stark.[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "chiqish", "bye"}:
            console.print("[dim]Goodbye, Mr. Stark.[/dim]")
            break

        # Mode switching commands
        if user_input.lower() in _MODE_COMMANDS:
            new_mode = _MODE_COMMANDS[user_input.lower()]
            if orchestrator.set_mode(new_mode):
                current_mode = new_mode
                console.print(f"[bold cyan]Mode switched to {new_mode.upper()}[/bold cyan]")
            continue

        # /status command
        if user_input.lower() == "/status":
            providers = orchestrator.get_available_providers()
            memory = orchestrator.get_memory_count()
            console.print(
                Panel(
                    f"Mode: [bold]{current_mode}[/bold]\n"
                    f"Providers: {', '.join(providers) or 'none'}\n"
                    f"Memory entries: {memory}",
                    title="JARVIS Status",
                    border_style="cyan",
                )
            )
            continue

        # /clear
        if user_input.lower() == "/clear":
            orchestrator._memory.clear_short_term()
            console.print("[dim]Short-term memory cleared.[/dim]")
            continue

        # /help
        if user_input.lower() in {"/help", "/?"}:
            console.print(
                Panel(
                    "Commands:\n"
                    "  /fast /code /pro /study /planner /focus /analytics /automation — switch mode\n"
                    "  /status — show current status\n"
                    "  /clear  — clear short-term memory\n"
                    "  exit    — quit JARVIS",
                    title="Help",
                    border_style="dim",
                )
            )
            continue

        await _send_message(orchestrator, user_input, session_id, force_offline)


def _voice_test() -> None:
    from voice.audio_stream import AudioStream
    from voice.stt_engine import STTEngine
    from voice.tts_engine import TTSEngine

    stt = STTEngine()
    tts = TTSEngine()
    audio = AudioStream()

    console.print("\n[bold cyan]Voice Component Status[/bold cyan]")
    ok, no = "[green]✅ available[/green]", "[red]❌ unavailable[/red]"
    console.print(f"  STT (Vosk):    {ok if stt.is_available() else no}")
    console.print(f"  TTS (pyttsx3): {ok if tts.is_available() else no}")
    console.print(f"  Microphone:    {ok if audio.is_available() else no}")
    if not (stt.is_available() and tts.is_available() and audio.is_available()):
        console.print(
            "\n[yellow]To install voice dependencies:[/yellow]\n"
            "  pip install vosk pyttsx3 sounddevice numpy\n"
            "  bash scripts/download_vosk_model.sh"
        )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jarvis-prime",
        description="JARVIS Prime — unified AI assistant",
    )
    p.add_argument("message", nargs="?", help="Single message (omit for REPL)")
    p.add_argument("--mode", "-m", default="pro", help="Mode: fast|code|pro|study|… (default: pro)")
    p.add_argument("--offline", action="store_true", help="Use only offline (Ollama) models")
    p.add_argument("--stream", action="store_true", help="Stream responses")
    p.add_argument("--voice", action="store_true", help="Start voice assistant")
    p.add_argument("--voice-test", dest="voice_test", action="store_true", help="Test voice components")
    p.add_argument("--api", action="store_true", help="Start FastAPI server")
    p.add_argument("--life", action="store_true", help="Start life assistant (jarvis_life.py)")
    p.add_argument("--port", type=int, default=8000, help="API server port (default: 8000)")
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ── API server ────────────────────────────────────────────────────────────
    if args.api:
        try:
            import uvicorn  # type: ignore[import]
        except ImportError:
            console.print("[red]uvicorn missing: pip install uvicorn[standard][/red]")
            sys.exit(1)
        uvicorn.run("apps.api.main:app", host="0.0.0.0", port=args.port, reload=False)
        return

    # ── Voice test ────────────────────────────────────────────────────────────
    if args.voice_test:
        _voice_test()
        return

    # ── Life assistant ────────────────────────────────────────────────────────
    if args.life:
        # Delegate to legacy life assistant
        life_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "jarvis_life.py",
        )
        os.execv(sys.executable, [sys.executable, life_path])
        return

    # ── Orchestrator setup ────────────────────────────────────────────────────
    orchestrator = JarvisOrchestrator(default_mode=args.mode)

    # ── Voice assistant ───────────────────────────────────────────────────────
    if args.voice:
        from voice.voice_assistant import VoiceAssistant

        async def _run_voice() -> None:
            await orchestrator.initialize()
            va = VoiceAssistant(orchestrator=orchestrator)
            if not va.is_available():
                status = va.get_status()
                console.print("[red]Voice system unavailable:[/red]")
                for comp, ok in status.items():
                    icon = "[green]✅[/green]" if ok else "[red]❌[/red]"
                    console.print(f"  {comp}: {icon}")
                return
            await va.run_voice_loop()

        try:
            asyncio.run(_run_voice())
        except KeyboardInterrupt:
            console.print("\n[dim]Voice mode deactivated.[/dim]")
        return

    # ── Single message or REPL ────────────────────────────────────────────────
    async def _run() -> None:
        await orchestrator.initialize()
        if args.message:
            sid = str(uuid.uuid4())
            await _send_message(
                orchestrator,
                args.message,
                sid,
                force_offline=args.offline,
                stream=args.stream,
            )
        else:
            await _repl(orchestrator, force_offline=args.offline)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye, Mr. Stark.[/dim]")


if __name__ == "__main__":
    main()
