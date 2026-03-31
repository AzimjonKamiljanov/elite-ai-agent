"""Tests for voice components — STT, TTS, AudioStream availability checks."""

from __future__ import annotations

from voice.stt_engine import STTEngine
from voice.tts_engine import TTSEngine
from voice.audio_stream import AudioStream


def test_stt_engine_is_available_returns_bool() -> None:
    stt = STTEngine()
    assert isinstance(stt.is_available(), bool)


def test_stt_engine_custom_model_path_not_available() -> None:
    stt = STTEngine(model_path="/nonexistent/path/to/model")
    assert stt.is_available() is False


def test_tts_engine_is_available_returns_bool() -> None:
    tts = TTSEngine()
    assert isinstance(tts.is_available(), bool)


def test_audio_stream_is_available_returns_bool() -> None:
    audio = AudioStream()
    assert isinstance(audio.is_available(), bool)


def test_tts_engine_default_rate() -> None:
    tts = TTSEngine(rate=200)
    assert tts._rate == 200


def test_tts_engine_set_rate() -> None:
    tts = TTSEngine()
    tts.set_rate(150)
    assert tts._rate == 150


def test_stt_engine_sample_rate() -> None:
    stt = STTEngine(sample_rate=44100)
    assert stt._sample_rate == 44100
