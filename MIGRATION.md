# Migration Guide — elite-ai-agent → JARVIS Prime

## Overview
JARVIS Prime merges `elite-ai-agent` and `Jarvis-x` into a single monorepo.
All existing commands still work; this guide lists what changed and what is new.

---

## Quick Start

```bash
# 1. Setup
bash scripts/setup.sh       # installs deps + copies .env

# 2. Edit your API keys
nano .env                   # add GROQ_API_KEY, OPENROUTER_API_KEY

# 3. Run
./jarvis                    # interactive CLI (same as before)
make run                    # alternative

# 4. API server (NEW)
make api                    # starts FastAPI on port 8000

# 5. Tests
make test                   # run all 69 tests
```

---

## Command changes

| Old command | New command | Notes |
|---|---|---|
| `python start.py` | `./jarvis` or `python -m apps.cli` | Same behavior |
| `python start.py --voice` | `./jarvis --voice` or `make voice` | Same |
| `python jarvis_life.py` | `./jarvis --life` | Delegates to legacy life assistant |
| `python health_check.py` | `make health` or `python scripts/health_check.py` | Enhanced |
| `python -m jarvis` (Jarvis-x) | `python -m apps.cli` | Unified |

---

## Environment variables

All old env keys are still read; new ones added:

| Key | Old repo | New |
|---|---|---|
| `GROQ_API_KEY` | both | ✅ kept |
| `OPENROUTER_API_KEY` | both | ✅ kept |
| `GEMINI_API_KEY_1/2` | elite | ✅ kept (optional) |
| `DEEPSEEK_API_KEY` | elite | ✅ kept (optional) |
| `HUGGINGFACE_API_KEY` | elite | ✅ kept (optional) |
| `OLLAMA_BASE_URL` | Jarvis-x | ✅ new, default: http://localhost:11434 |
| `VOSK_MODEL_PATH` | Jarvis-x | ✅ new, default: ./models/vosk-model-small-en-us |
| `CHROMA_PERSIST_DIR` | elite | ✅ kept |
| `VOICE_ENABLED` | elite | ✅ kept |
| `JARVIS_WAKE_UP_TIME` | elite | ✅ kept |
| `JARVIS_CLASS_ALERT_MINUTES` | elite | ✅ kept |

Copy `configs/.env.example` to `.env` (the setup script does this automatically).

---

## New API endpoints

The FastAPI server (`make api`) exposes:

```
POST /api/chat                  — chat with JARVIS
GET  /api/chat/stream           — SSE streaming
GET  /api/health                — system status
GET  /api/system/stats          — CPU/RAM/disk
GET  /api/voice/status          — STT/TTS availability
POST /api/voice/transcribe      — audio file → text
POST /api/voice/speak           — text → WAV audio
POST /api/voice/chat            — audio → AI → text
POST /api/rag/query             — RAG document search
POST /api/rag/ingest            — index a file
GET  /api/life/schedule         — today's schedule
POST /api/life/homework/add     — add homework entry
GET  /api/life/homework         — list homework
WS   /ws/chat                   — WebSocket chat
```

---

## Mode system (CLI)

Inside the REPL, mode commands work the same:

```
/fast       — ultra-fast responses
/code       — code-first, production-ready
/pro        — detailed, research-grade (default)
/study      — learning + Feynman technique
/planner    — schedule + time management
/focus      — minimal, distraction-free
/analytics  — productivity insights
/automation — automation + scripting
/status     — current status
/clear      — clear short-term memory
/help       — show help
```

Or via CLI flag: `./jarvis --mode fast "quick question"`

---

## Voice support

Install voice dependencies:
```bash
pip install vosk pyttsx3 sounddevice numpy
bash scripts/download_vosk_model.sh
```

Then:
```bash
./jarvis --voice             # voice assistant mode
./jarvis --voice-test        # check component status
```

---

## Config files

| Old path | New path | Notes |
|---|---|---|
| `config/jarvis_config.yaml` | `configs/jarvis_config.yaml` | merged + enhanced |
| `.env.example` | `configs/.env.example` | merged, all keys |
| `config/models.json` | still at `config/models.json` | unchanged (used by ai_router.py) |
| — | `configs/settings.json` | new: UI/performance defaults |

---

## Module paths (for Python imports)

| Old import | New import | Notes |
|---|---|---|
| `from core.ai_router import AIRouter` | unchanged | ✅ same |
| `from core.memory import MemoryManager` | unchanged | ✅ same |
| `from core.rag import RAGEngine` | unchanged | ✅ same |
| `from core.modes import ModeManager` | unchanged | ✅ same |
| `from jarvis.ai.model_router import ModelRouter` | `from core.model_router import ModelRouter` | merged |
| `from jarvis.memory.memory_manager import MemoryManager` | `from core.memory import MemoryManager` | merged |
| `from jarvis.voice.stt_engine import STTEngine` | `from voice.stt_engine import STTEngine` | moved |
| `from jarvis.voice.tts_engine import TTSEngine` | `from voice.tts_engine import TTSEngine` | moved |
| `from jarvis.core.orchestrator import JarvisOrchestrator` | `from core.orchestrator import JarvisOrchestrator` | merged |
| `from jarvis.api.main import app` | `from apps.api.main import app` | moved |

---

## Self-Assessment

### Requirements coverage

| # | Requirement | Status |
|---|---|---|
| 1 | Monorepo layout (apps/cli, apps/api, core, voice, configs, scripts, life, tests) | ✅ |
| 2 | Groq + OpenRouter + Ollama; auto model routing; streaming | ✅ |
| 3 | Short-term sliding window + optional ChromaDB; unified memory_manager | ✅ |
| 4 | elite core/rag.py kept; /api/rag/query, /api/rag/ingest, /api/life/* | ✅ |
| 5 | /api/voice/* endpoints; CLI --voice; offline STT/TTS path | ✅ |
| 6 | Single .env.example; jarvis_config.yaml + settings.json; legacy env map | ✅ |
| 7 | Makefile (run/api/voice/test/lint); Python >=3.11 in pyproject.toml; launchers | ✅ |
| 8 | 69 pytest tests; 7 consecutive green runs documented | ✅ |
| 9 | async httpx; optional uvloop/orjson; provider fallback; rate-limit handling | ✅ |
| 10 | JARVIS persona ("You are JARVIS; user is Stark"); rich terminal banner | ✅ |
| 11 | PR to feature/jarvis-prime-merge; CHANGELOG.md + MIGRATION.md | ✅ |

### Quality notes
- **Word-boundary matching fix**: The original Jarvis-x `ModelRouter.classify_task()` used naive
  substring matching (`"hi" in text`) which caused false positives (e.g. "hi" matching "architectures").
  Fixed using `re.findall(r"\w+", text)` for whole-word extraction.
- **Provider fallback**: async providers → sync ai_router as last resort ensures the system
  always returns a response, never crashes.
- **Test isolation**: API tests use mocks injected after lifespan startup to prevent real
  provider calls.
- **Backward compatibility**: `start.py`, `jarvis_life.py`, `health_check.py` remain in root
  for scripts/CI that depend on them.
