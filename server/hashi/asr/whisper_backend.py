"""Local Whisper-family engine through faster-whisper (CPU, int8). Works with no internet
once the model has been downloaded by scripts/get_models.py."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import numpy as np

from .base import ASRBackend, ASRResult

MODELS_DIR = Path(os.environ.get("HASHI_MODELS", Path(__file__).resolve().parents[3] / "models"))

# No vocabulary prompt on purpose. A cabin-words prompt looked helpful on clean audio, but in loud
# noise Whisper repeated the prompt itself ("तबीयत नहीं है" many times), which the matcher then read as
# "I feel unwell". A Gurmukhi prompt made Punjabi loop outright. The benchmark caught both.


# our codes that differ from Whisper's; any other supported code is passed straight through
_WHISPER_LANG = {"fil": "tl"}


class WhisperBackend(ASRBackend):
    name = "faster-whisper"

    def __init__(self, size: str | None = None) -> None:
        from faster_whisper import WhisperModel  # imported late: optional dependency

        self.size = size or os.environ.get("HASHI_ASR_MODEL", "small")
        local = MODELS_DIR / f"whisper-{self.size}"
        source = str(local) if local.exists() else self.size
        self._lock = threading.Lock()  # one clip at a time; others wait their turn
        threads = int(os.environ.get("HASHI_ASR_THREADS", min(8, max(4, (os.cpu_count() or 8) // 2))))
        self.model = WhisperModel(source, device="cpu", compute_type="int8", cpu_threads=threads,
                                  download_root=str(MODELS_DIR) if not local.exists() else None,
                                  local_files_only=os.environ.get("HASHI_OFFLINE", "") == "1")

    def transcribe(self, pcm: np.ndarray, lang: str, task: str = "transcribe") -> ASRResult:
        with self._lock:
            return self._run(pcm, lang, task)

    def _run(self, pcm: np.ndarray, lang: str, task: str) -> ASRResult:
        t0 = time.time()
        segments, info = self.model.transcribe(
            pcm.astype(np.float32), language=_WHISPER_LANG.get(lang, lang),
            task=task, beam_size=3, vad_filter=False, condition_on_previous_text=False,
            # requests are one short sentence: no retry loop on noisy audio, and a hard cap
            # on length so a hallucinated run-on cannot stall the passenger's phone
            temperature=0.0, max_new_tokens=64, no_speech_threshold=0.9,
            no_repeat_ngram_size=3,
            )
        text = " ".join(s.text.strip() for s in segments).strip()
        return ASRResult(text=text, language=info.language, seconds=time.time() - t0)
