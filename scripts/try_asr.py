"""Time the speech engine on one synthetic clip: python scripts/try_asr.py [hi|pa]"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import yaml  # noqa: E402

from bench import audio_tools as at  # noqa: E402
from hashi.asr.whisper_backend import WhisperBackend  # noqa: E402
from hashi.matcher import get_matcher  # noqa: E402

lang = sys.argv[1] if len(sys.argv) > 1 else "hi"
item = yaml.safe_load((ROOT / "bench" / "testset.yaml").read_text(encoding="utf-8"))[lang][0]
speaker = list(at.SPEAKERS[lang])[0]
pcm = at.synth(lang, speaker, item["text"], f"{lang}00")
t = time.time()
asr = WhisperBackend()
print(f"model load {time.time() - t:.1f}s, clip {len(pcm) / 16000:.1f}s")
for task in ("transcribe", "translate"):
    r = asr.transcribe(pcm, lang, task=task)
    print(f"{task}: {r.seconds:.1f}s -> {r.text!r}")
print(get_matcher().match(asr.transcribe(pcm, lang).text).public())
