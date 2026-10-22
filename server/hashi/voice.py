"""Voice request pipeline: WAV bytes -> noise cleanup -> speech engine -> intent match.

Audio is handled in memory only. Nothing is written to disk and nothing is kept after the
reply is built.
"""
from __future__ import annotations

import io
import time
import wave

import numpy as np

from . import noise
from .asr import get_backend
from .matcher import get_matcher

TARGET_SR = 16000
MAX_SECONDS = 15


def decode_wav(data: bytes) -> np.ndarray:
    """16-bit PCM WAV (the browser sends 16 kHz mono) to float32 mono at 16 kHz."""
    with wave.open(io.BytesIO(data)) as w:
        if w.getsampwidth() != 2:
            raise ValueError("expected 16-bit audio")
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(min(w.getnframes(), sr * MAX_SECONDS))
    pcm = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        pcm = pcm.reshape(-1, ch).mean(axis=1)
    if sr != TARGET_SR:
        n = int(len(pcm) * TARGET_SR / sr)
        pcm = np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm)
        pcm = pcm.astype(np.float32)
    return pcm


def understand(text: str) -> dict:
    return get_matcher().match(text).public()


def process_audio(data: bytes, lang: str, cleanup: bool = True) -> dict:
    t0 = time.time()
    backend = get_backend()
    if not backend.ready:
        return {"ok": False, "error": "asr_unavailable", "mode": "tiles", "candidates": []}
    pcm = decode_wav(data)
    if len(pcm) < TARGET_SR * 0.3:
        return {"ok": False, "error": "too_short", "mode": "tiles", "candidates": []}
    if float(np.sqrt(np.mean(pcm ** 2))) < 0.003:
        return {"ok": False, "error": "silence", "mode": "tiles", "candidates": []}
    if cleanup:
        pcm = noise.clean(pcm)
    result = backend.transcribe(pcm, lang)
    out = {"ok": True, "heard": result.text, "engine": backend.name}
    out.update(understand(result.text))
    out["ms"] = int((time.time() - t0) * 1000)
    return out
