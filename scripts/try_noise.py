"""Time each stage of one noisy clip: python scripts/try_noise.py [hi|pa] [snr_db]"""
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import yaml  # noqa: E402

from bench import audio_tools as at  # noqa: E402
from hashi import noise  # noqa: E402
from hashi.asr.whisper_backend import WhisperBackend  # noqa: E402

lang = sys.argv[1] if len(sys.argv) > 1 else "hi"
snr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
item = yaml.safe_load((ROOT / "bench" / "testset.yaml").read_text(encoding="utf-8"))[lang][1]
speech = at.synth(lang, list(at.SPEAKERS[lang])[0], item["text"], f"{lang}01")
rng = np.random.default_rng(1)
t = time.time()
nz = at.cabin_noise(len(speech) + at.SR, rng, [speech])
print(f"noise gen {time.time() - t:.2f}s")
noisy = at.mix_snr(speech, nz, snr)
t = time.time()
clean = noise.clean(noisy)
print(f"cleanup {time.time() - t:.2f}s ({len(noisy) / 16000:.1f}s audio)")
asr = WhisperBackend()
for name, pcm in (("noisy", noisy), ("cleaned", clean)):
    for task in ("transcribe", "translate"):
        r = asr.transcribe(pcm, lang, task=task)
        print(f"{name:8} {task:10} {r.seconds:5.1f}s -> {r.text!r}")
