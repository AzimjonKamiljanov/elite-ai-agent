"""JARVIS Prime — unified FastAPI server.

Endpoints:
  POST /api/chat                   — single-turn chat
  GET  /api/chat/stream            — server-sent events streaming
  GET  /api/health                 — health & provider status
  GET  /api/system/stats           — CPU/RAM/disk stats
  GET  /api/voice/status           — voice component availability
  POST /api/voice/transcribe       — upload WAV → text
  POST /api/voice/speak            — text → WAV audio
  POST /api/voice/chat             — audio → AI → text
  POST /api/rag/query              — RAG document query
  POST /api/rag/ingest             — ingest file into RAG index
  GET  /api/life/schedule          — today's schedule
  POST /api/life/homework/add      — add homework entry
  GET  /api/life/homework          — list homework
  WS   /ws/chat                    — WebSocket streaming chat
"""

from __future__ import annotations

import io
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.orchestrator import JarvisOrchestrator
from core.rag import RAGEngine

_orchestrator: JarvisOrchestrator | None = None
_rag: RAGEngine | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI):  # noqa: ANN001
    global _orchestrator, _rag
    _orchestrator = JarvisOrchestrator()
    await _orchestrator.initialize()
    _rag = RAGEngine()
    yield


app = FastAPI(
    title="JARVIS Prime API",
    version="2.0.0",
    description="Unified AI assistant API — elite-ai-agent + Jarvis-x merged.",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _orc() -> JarvisOrchestrator:
    assert _orchestrator is not None, "Orchestrator not initialized"
    return _orchestrator


def _rag_engine() -> RAGEngine:
    assert _rag is not None, "RAG engine not initialized"
    return _rag


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    force_offline: bool = False
    mode: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    model_used: str
    response_time: float
    mode: str


class RAGQueryRequest(BaseModel):
    question: str
    k: int = 5


class RAGIngestRequest(BaseModel):
    path: str
    # Restrict ingestion to files within the specified base directory.
    # Set to empty string to use the default data directory restriction.
    allowed_base: str | None = None


class HomeworkEntry(BaseModel):
    subject: str
    task: str
    due_date: str | None = None


# ── Chat endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    orc = _orc()
    if req.mode:
        orc.set_mode(req.mode)
    session_id = req.session_id or str(uuid.uuid4())
    result = await orc.process_message(
        user_input=req.message,
        session_id=session_id,
        force_offline=req.force_offline,
    )
    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        model_used=result["model_used"],
        response_time=result["response_time"],
        mode=result.get("mode", "pro"),
    )


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    session_id: str | None = None,
) -> StreamingResponse:
    orc = _orc()
    sid = session_id or str(uuid.uuid4())

    async def _gen() -> Any:
        async for chunk in orc.process_stream(user_input=message, session_id=sid):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict:
    orc = _orc()
    return {
        "status": "operational",
        "version": "2.0.0",
        "providers": orc.get_available_providers(),
        "memory_entries": orc.get_memory_count(),
        "current_mode": orc.get_mode(),
    }


# ── System stats ───────────────────────────────────────────────────────────────

@app.get("/api/system/stats")
async def system_stats() -> dict:
    try:
        import psutil  # type: ignore[import]
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        return {"error": "psutil not installed"}


# ── Voice endpoints ────────────────────────────────────────────────────────────

class VoiceStatusResponse(BaseModel):
    stt: bool
    tts: bool
    microphone: bool


class TranscribeResponse(BaseModel):
    text: str
    confidence: float


class VoiceChatResponse(BaseModel):
    user_text: str
    response: str
    model_used: str
    audio_url: str | None = None


@app.get("/api/voice/status", response_model=VoiceStatusResponse)
async def voice_status() -> VoiceStatusResponse:
    from voice.audio_stream import AudioStream
    from voice.stt_engine import STTEngine
    from voice.tts_engine import TTSEngine

    return VoiceStatusResponse(
        stt=STTEngine().is_available(),
        tts=TTSEngine().is_available(),
        microphone=AudioStream().is_available(),
    )


@app.post("/api/voice/transcribe", response_model=TranscribeResponse)
async def voice_transcribe(file: UploadFile = File(...)) -> TranscribeResponse:
    from voice.stt_engine import STTEngine

    stt = STTEngine()
    if not stt.is_available():
        raise HTTPException(
            status_code=503,
            detail="STT unavailable. Install vosk and download the model.",
        )

    audio_bytes = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = stt.transcribe_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    return TranscribeResponse(
        text=str(result.get("text", "")),
        confidence=float(result.get("confidence", 0.0)),
    )


@app.post("/api/voice/speak")
async def voice_speak(text: str) -> StreamingResponse:
    from voice.tts_engine import TTSEngine

    tts = TTSEngine()
    if not tts.is_available():
        raise HTTPException(status_code=503, detail="TTS unavailable. Install pyttsx3.")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tts.save_to_file(text, tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
    finally:
        os.unlink(tmp_path)

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=speech.wav"},
    )


@app.post("/api/voice/chat", response_model=VoiceChatResponse)
async def voice_chat(file: UploadFile = File(...)) -> VoiceChatResponse:
    from voice.stt_engine import STTEngine

    stt = STTEngine()
    if not stt.is_available():
        raise HTTPException(status_code=503, detail="STT unavailable.")

    audio_bytes = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        stt_result = stt.transcribe_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    user_text = str(stt_result.get("text", "")).strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio.")

    orc = _orc()
    ai_result = await orc.process_message(
        user_input=user_text,
        session_id=str(uuid.uuid4()),
    )

    return VoiceChatResponse(
        user_text=user_text,
        response=ai_result["response"],
        model_used=ai_result["model_used"],
    )


# ── RAG endpoints ──────────────────────────────────────────────────────────────

@app.post("/api/rag/query")
async def rag_query(req: RAGQueryRequest) -> dict:
    results = _rag_engine().query(req.question, k=req.k)
    return {"results": results, "count": len(results)}


@app.post("/api/rag/ingest")
async def rag_ingest(req: RAGIngestRequest) -> dict:
    import logging
    logger = logging.getLogger("jarvis.api")
    # Default: restrict to ./data directory to prevent path traversal via API
    allowed_base = req.allowed_base or os.path.abspath("./data")
    try:
        chunks = _rag_engine().ingest_file(req.path, allowed_base=allowed_base)
        return {"status": "ok", "chunks_added": chunks, "path": req.path}
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="File not found.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Unsupported file type or invalid path.")
    except Exception:
        logger.exception("RAG ingest error")
        raise HTTPException(status_code=500, detail="Failed to ingest file.")


# ── Life assistant endpoints ───────────────────────────────────────────────────

@app.get("/api/life/schedule")
async def life_schedule() -> dict:
    try:
        from life.scheduler import Scheduler
        s = Scheduler()
        return {"schedule": s.get_today(), "date": s.today_str()}
    except ImportError:
        return {"schedule": [], "date": "", "error": "life module not available"}


@app.post("/api/life/homework/add")
async def life_homework_add(entry: HomeworkEntry) -> dict:
    try:
        from life.homework import HomeworkTracker
        tracker = HomeworkTracker()
        tracker.add(
            subject=entry.subject,
            task=entry.task,
            due_date=entry.due_date,
        )
        return {"status": "added", "subject": entry.subject}
    except ImportError:
        raise HTTPException(status_code=503, detail="life module not available")


@app.get("/api/life/homework")
async def life_homework_list() -> dict:
    try:
        from life.homework import HomeworkTracker
        tracker = HomeworkTracker()
        return {"homework": tracker.list_all()}
    except ImportError:
        return {"homework": [], "error": "life module not available"}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    orc = _orc()
    session_id = str(uuid.uuid4())
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            stream = data.get("stream", False)

            if stream:
                async for chunk in orc.process_stream(user_input=message, session_id=session_id):
                    await websocket.send_json({"type": "chunk", "content": chunk})
                await websocket.send_json({"type": "done", "content": ""})
            else:
                result = await orc.process_message(user_input=message, session_id=session_id)
                await websocket.send_json({"type": "response", "content": result["response"]})
    except WebSocketDisconnect:
        pass
