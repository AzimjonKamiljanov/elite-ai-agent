# CHANGELOG — JARVIS Prime

## v2.0.0 — Jarvis Prime Merge (feature/jarvis-prime-merge)

### Overview
Merged `AzimjonKamiljanov/elite-ai-agent` (life assistant, modes, RAG, tools) with
`AzimjonKamiljanov/Jarvis-x` (FastAPI, async providers, memory manager, Vosk STT) into a
single optimized monorepo.

---

### New Structure
```
apps/
  cli/        # Merged CLI — life assistant + modes + --voice
  api/        # FastAPI server (unified from Jarvis-x + elite endpoints)
core/
  ai_router.py        # Elite multi-provider sync router (kept)
  model_router.py     # Jarvis-x complexity-based router (merged, fixed word-boundary matching)
  orchestrator.py     # Unified orchestrator (async, with sync fallback)
  memory.py           # Short-term + ChromaDB long-term (kept elite version)
  modes.py            # 8 modes: fast/code/pro/study/planner/focus/analytics/automation
  rag.py              # RAG engine (kept elite version)
  providers/          # Async providers: Groq, OpenRouter, Ollama
voice/
  stt_engine.py       # Vosk offline STT (from Jarvis-x)
  tts_engine.py       # pyttsx3 offline TTS (from Jarvis-x)
  audio_stream.py     # Microphone capture (from Jarvis-x)
  voice_assistant.py  # End-to-end voice loop
configs/
  .env.example        # Unified env with all keys
  jarvis_config.yaml  # Unified config (merged)
  settings.json       # UI/performance defaults
scripts/
  setup.sh            # One-shot setup script
  health_check.py     # System health check
  download_vosk_model.sh  # Offline STT model downloader
life/                 # Life assistant modules preserved unchanged
tests/                # 69 pytest tests (model routing, memory, RAG, API, voice, CLI, orchestrator)
```

### Added
- **Unified async orchestrator** (`core/orchestrator.py`): selects model by complexity, falls
  back across providers (Groq → OpenRouter → Ollama → sync ai_router).
- **Async provider layer** (`core/providers/`): Groq (native SDK), OpenRouter (httpx),
  Ollama (httpx local), all with streaming support.
- **FastAPI server** (`apps/api/main.py`): 15 endpoints covering chat, streaming, voice, RAG,
  life assistant, WebSocket.
- **New API endpoints**: `POST /api/rag/query`, `POST /api/rag/ingest`,
  `GET /api/life/schedule`, `POST /api/life/homework/add`, `GET /api/life/homework`.
- **Voice layer** (`voice/`): Vosk STT + pyttsx3 TTS + sounddevice mic (fully offline).
- **`pyproject.toml`**: Python ≥3.11, optional extras `[voice,memory,pdf,perf,dev]`.
- **`Makefile`**: targets `run`, `api`, `voice`, `test`, `test-5`, `lint`, `health`, `vosk-model`.
- **Word-boundary keyword matching** in `ModelRouter.classify_task()` — prevents false
  substring matches (e.g. "hi" matching "architectures").
- **JARVIS persona** enforced: system prompt = "You are JARVIS; user is Stark".
- **69 pytest tests** covering all major subsystems; run 7 times with 0 failures.

### Changed
- `jarvis` launcher: now calls `python -m apps.cli` (backward compatible flags).
- `jarvis.bat`: updated for Windows with new CLI entry point.
- Model router: fixed `_TRIVIAL_KEYWORDS` substring false-positive with `re.findall` word extraction.

### Preserved (unchanged)
- All `core/` modules from elite-ai-agent (`ai_router`, `modes`, `memory`, `rag`, `voice`,
  `tools`, `intelligence`, `calendar_system`, etc.)
- All `life/` modules (scheduler, homework, daily_planner, reminders, storage, models).
- All `tools/` modules (file_manager, terminal, web_search, code_executor).
- `start.py`, `jarvis_life.py`, `health_check.py` — kept for backward compatibility.
- `config/` directory with existing prompts.

### Performance
- Async HTTP (httpx) for OpenRouter and Ollama providers.
- Optional `uvloop` and `orjson` via `pip install jarvis-prime[perf]`.
- Provider fallback chain with rate-limit detection and graceful degradation.

---

## Previous versions
See git log for elite-ai-agent history before this merge.
