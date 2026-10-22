"""Compare speech-engine settings on Punjabi clips: python scripts/try_pa.py [model_size]"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from bench import audio_tools as at  # noqa: E402
from hashi.asr.whisper_backend import WhisperBackend  # noqa: E402
from hashi.matcher import get_matcher  # noqa: E402

size = sys.argv[1] if len(sys.argv) > 1 else "small"
asr = WhisperBackend(size)
m = get_matcher()
items = yaml.safe_load((ROOT / "bench" / "testset.yaml").read_text(encoding="utf-8"))["pa"][:8]
clips = [(it["gold"], at.synth("pa", "pa-gtts", it["text"], f"pa{i:02d}")) for i, it in enumerate(items)]

VARIANTS = {
    "pa+prompt": dict(language="pa", prompt=True, extra={}),
    "pa no prompt": dict(language="pa", prompt=False, extra={}),
    "pa guards": dict(language="pa", prompt=False, extra={"repetition_penalty": 1.3, "no_repeat_ngram_size": 3}),
    "hi on pa audio": dict(language="hi", prompt=False, extra={"repetition_penalty": 1.3, "no_repeat_ngram_size": 3}),
    "auto": dict(language=None, prompt=False, extra={"repetition_penalty": 1.3, "no_repeat_ngram_size": 3}),
}
for name, v in VARIANTS.items():
    hits, t0, heard = 0, time.time(), []
    for gold, pcm in clips:
        segs, info = asr.model.transcribe(
            pcm.astype(np.float32), language=v["language"], task="transcribe", beam_size=3,
            vad_filter=False, condition_on_previous_text=False, temperature=0.0, max_new_tokens=64,
            initial_prompt=("ਪਾਣੀ, ਕੰਬਲ, ਖਾਣਾ, ਦਵਾਈ, ਪਖਾਨਾ" if v["prompt"] else None), **v["extra"])
        text = " ".join(s.text.strip() for s in segs)
        heard.append(text)
        hits += m.match(text).candidates[0].intent == gold
    print(f"{name:16} {hits}/{len(clips)}  {time.time() - t0:.0f}s   e.g. {heard[0]!r} | {heard[3]!r}")
