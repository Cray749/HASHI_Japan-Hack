"""Send a synthetic spoken sentence to the running server's /api/live: python scripts/try_live.py ta "text" """
import asyncio
import io
import sys
import wave
from pathlib import Path

import edge_tts
import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
from bench.audio_tools import decode  # noqa: E402

lang, text = sys.argv[1], sys.argv[2]
tgt = sys.argv[3] if len(sys.argv) > 3 else "ja"


async def voice_for(code: str) -> str:
    voices = await edge_tts.list_voices()
    loc = {"ta": "ta-IN", "te": "te-IN", "bn": "bn-IN", "gu": "gu-IN", "mr": "mr-IN", "kn": "kn-IN",
           "ml": "ml-IN", "th": "th-TH", "vi": "vi-VN", "id": "id-ID", "fil": "fil-PH", "ms": "ms-MY",
           "km": "km-KH", "my": "my-MM", "hi": "hi-IN", "ja": "ja-JP", "en": "en-IN"}[code]
    return sorted([v for v in voices if v["Locale"] == loc], key=lambda v: v["Gender"] != "Female")[0]["ShortName"]


async def main() -> None:
    path = Path("bench/.cache") / f"live-{lang}.mp3"
    await edge_tts.Communicate(text, await voice_for(lang)).save(str(path))
    pcm = decode(path)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes((np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())
    r = requests.post("http://127.0.0.1:8000/api/live", files={"audio": ("v.wav", buf.getvalue(), "audio/wav")},
                      data={"src": lang, "tgt": tgt}).json()
    print("heard:", r.get("heard"))
    print("sound form:", r.get("steps", {}).get("fold"))
    print("match:", r.get("match"))
    print("translation:", r.get("translator"), "|", r.get("translation"))
    print("total ms:", r.get("steps", {}).get("total_ms"))


asyncio.run(main())
