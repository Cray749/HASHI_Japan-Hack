"""Speech recognition interface. Engines are swappable behind this one class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class ASRResult:
    text: str
    language: str = ""
    seconds: float = 0.0   # time the engine took, for the benchmark


class ASRBackend(ABC):
    name = "base"

    @abstractmethod
    def transcribe(self, pcm: np.ndarray, lang: str, task: str = "transcribe") -> ASRResult:
        """pcm: float32 mono 16 kHz in [-1, 1]. lang: 'hi', 'pa' or 'en'.
        task: 'transcribe' (original language) or 'translate' (to English, used by the
        benchmark baseline)."""

    @property
    def ready(self) -> bool:
        return True


class NullBackend(ASRBackend):
    """Used when no engine is installed. The app then falls back to picture tiles."""

    name = "none"

    def transcribe(self, pcm: np.ndarray, lang: str, task: str = "transcribe") -> ASRResult:
        raise RuntimeError("no speech engine installed")

    @property
    def ready(self) -> bool:
        return False
