#!/usr/bin/env python3
"""JARVIS Prime health-check script — checks providers, memory, voice, API."""

from __future__ import annotations

import os
import sys
import time

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_providers() -> dict[str, bool]:
    results: dict[str, bool] = {}
    try:
        from core.providers.groq_provider import GroqProvider
        results["groq"] = GroqProvider().is_available()
    except Exception:
        results["groq"] = False
    try:
        from core.providers.openrouter_provider import OpenRouterProvider
        results["openrouter"] = OpenRouterProvider().is_available()
    except Exception:
        results["openrouter"] = False
    try:
        from core.providers.ollama_provider import OllamaProvider
        results["ollama"] = OllamaProvider().is_available()
    except Exception:
        results["ollama"] = False
    return results


def check_memory() -> dict:
    try:
        from core.memory import MemoryManager
        mm = MemoryManager()
        stats = mm.get_stats()
        return {"ok": True, "backend": stats.get("storage_backend", "?"), "stats": stats}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_voice() -> dict[str, bool]:
    results: dict[str, bool] = {}
    try:
        from voice.stt_engine import STTEngine
        results["stt"] = STTEngine().is_available()
    except Exception:
        results["stt"] = False
    try:
        from voice.tts_engine import TTSEngine
        results["tts"] = TTSEngine().is_available()
    except Exception:
        results["tts"] = False
    try:
        from voice.audio_stream import AudioStream
        results["microphone"] = AudioStream().is_available()
    except Exception:
        results["microphone"] = False
    return results


def check_rag() -> dict:
    try:
        from core.rag import RAGEngine
        rag = RAGEngine()
        stats = rag.get_stats()
        return {"ok": True, "stats": stats}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> None:
    print("\n" + "=" * 60)
    print("  JARVIS Prime — Health Check")
    print("=" * 60)

    ok_icon = "✅"
    fail_icon = "❌"

    # Providers
    print("\n[AI Providers]")
    providers = check_providers()
    for name, ok in providers.items():
        icon = ok_icon if ok else fail_icon
        print(f"  {icon} {name}")

    # Memory
    print("\n[Memory]")
    mem = check_memory()
    if mem["ok"]:
        print(f"  {ok_icon} Memory OK — backend: {mem.get('backend', '?')}")
    else:
        print(f"  {fail_icon} Memory error: {mem.get('error')}")

    # RAG
    print("\n[RAG]")
    rag = check_rag()
    if rag["ok"]:
        print(f"  {ok_icon} RAG OK — {rag.get('stats', {})}")
    else:
        print(f"  {fail_icon} RAG error: {rag.get('error')}")

    # Voice
    print("\n[Voice]")
    voice = check_voice()
    for name, ok in voice.items():
        icon = ok_icon if ok else fail_icon
        print(f"  {icon} {name}")

    # Summary
    all_ok = all(providers.values()) and mem["ok"]
    print("\n" + "=" * 60)
    if all_ok:
        print("  ✅ All systems operational — JARVIS Prime ready.")
    else:
        print("  ⚠  Some systems offline — check your API keys and dependencies.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
