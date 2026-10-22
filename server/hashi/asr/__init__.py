"""Pick a speech engine. HASHI_ASR=auto|whisper|none (default auto)."""
from __future__ import annotations

import logging
import os
import threading

from .base import ASRBackend, ASRResult, NullBackend

__all__ = ["ASRBackend", "ASRResult", "get_backend", "preload"]

log = logging.getLogger("hashi.asr")
_backend: ASRBackend | None = None
_lock = threading.Lock()


def get_backend() -> ASRBackend:
    global _backend
    with _lock:
        if _backend is None:
            _backend = _build()
        return _backend


def _build() -> ASRBackend:
    choice = os.environ.get("HASHI_ASR", "auto").lower()
    if choice == "none":
        return NullBackend()
    try:
        from .whisper_backend import WhisperBackend
        backend = WhisperBackend()
        log.info("speech engine ready: %s (%s)", backend.name, backend.size)
        return backend
    except Exception as exc:  # missing package or missing model: degrade to tiles
        log.warning("no speech engine (%s); voice falls back to picture tiles", exc)
        return NullBackend()


def preload() -> None:
    """Load the engine in the background so the first voice request is not slow."""
    threading.Thread(target=get_backend, daemon=True).start()
