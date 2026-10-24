"""Optional free-text translation with NLLB-200 (distilled 600M, int8, CTranslate2).

This is NOT the request-matching path (that is the closed list, with Japanese written in advance).
It powers the live translator page for open-ended speech and text, and is always labelled as
machine translation. Licence of the model is CC-BY-NC 4.0 (non-commercial). It is loaded only if
models/nllb-600m-ct2 exists (python scripts/get_nllb.py).
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

MODEL_DIR = Path(os.environ.get("HASHI_NLLB", Path(__file__).resolve().parents[2] / "models" / "nllb-600m-ct2"))

NLLB_CODE = {
    "en": "eng_Latn", "ja": "jpn_Jpan", "hi": "hin_Deva", "pa": "pan_Guru", "ta": "tam_Taml",
    "te": "tel_Telu", "bn": "ben_Beng", "gu": "guj_Gujr", "mr": "mar_Deva", "kn": "kan_Knda",
    "ml": "mal_Mlym", "th": "tha_Thai", "vi": "vie_Latn", "id": "ind_Latn", "fil": "tgl_Latn",
    "ms": "zsm_Latn", "km": "khm_Khmr", "my": "mya_Mymr",
}


class Translator:
    def __init__(self) -> None:
        import ctranslate2
        import sentencepiece as spm

        threads = min(8, max(4, (os.cpu_count() or 8) // 2))
        self.ct = ctranslate2.Translator(str(MODEL_DIR), device="cpu", compute_type="int8",
                                         intra_threads=threads)
        self.sp = spm.SentencePieceProcessor(str(MODEL_DIR / "sentencepiece.bpe.model"))
        self._lock = threading.Lock()

    def translate(self, text: str, src: str, tgt: str) -> str:
        if src == tgt or not text.strip():
            return text
        tokens = [NLLB_CODE[src]] + self.sp.encode(text.strip(), out_type=str) + ["</s>"]
        with self._lock:
            res = self.ct.translate_batch([tokens], target_prefix=[[NLLB_CODE[tgt]]], beam_size=4,
                                          max_decoding_length=160, repetition_penalty=1.1)
        out = res[0].hypotheses[0][1:]
        return self.sp.decode(out)


_translator: Translator | None = None
_failed = False


def available() -> bool:
    return (MODEL_DIR / "model.bin").exists() and not _failed


def get_translator() -> Translator | None:
    global _translator, _failed
    if _translator is None and available():
        try:
            _translator = Translator()
        except Exception:
            _failed = True
    return _translator
