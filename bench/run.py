"""Noise benchmark: plain speech-to-text then translation (A) versus HASHI intent matching (B).

    python -m bench.run                 # full run (about 20 requests x 3 voices x 2 languages)
    python -m bench.run --quick         # 6 requests, 1 voice, for a fast check
    python -m bench.run --model base    # use a lighter speech model

Metric: share of requests where the crew card would show the right request.
 A  Whisper translates the clip to English; the English text is matched against the English
    phrase bank only. This gives the baseline our own matcher, so it is a generous baseline.
 B  Whisper transcribes in the passenger's language; the text is matched against every bank.
See bench/README.md for how to add real recordings and for what this does not prove.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))

from bench import audio_tools as at  # noqa: E402
from bench.report import write_report  # noqa: E402

LEVELS = [("clean", None), ("10 dB", 10.0), ("0 dB", 0.0)]


def load_real(lang: str):
    """Team recordings: bench/real/manifest.csv with columns file,lang,speaker,gold."""
    path = ROOT / "bench" / "real" / "manifest.csv"
    if not path.exists():
        return []
    import csv
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["lang"] == lang:
                rows.append((r["speaker"], r["gold"], at.decode(path.parent / r["file"])))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--model", default="small")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    from hashi import noise as hashi_noise
    from hashi.asr.whisper_backend import WhisperBackend
    from hashi.matcher import get_matcher

    asr = WhisperBackend(args.model)
    matcher = get_matcher()
    testset = yaml.safe_load((ROOT / "bench" / "testset.yaml").read_text(encoding="utf-8"))
    rng = np.random.default_rng(args.seed)
    results: list[dict] = []
    t_start = time.time()

    for lang in ("hi", "pa"):
        items = testset[lang][: 6 if args.quick else None]
        speakers = list(at.SPEAKERS[lang])[: 1 if args.quick else None]
        clips: list[tuple[str, str, str, np.ndarray, str]] = []  # speaker, gold, text, pcm, kind
        for idx, item in enumerate(items):
            for sp in speakers:
                clips.append((sp, item["gold"], item["text"],
                              at.synth(lang, sp, item["text"], f"{lang}{idx:02d}"), "synthetic"))
        for sp, gold, pcm in load_real(lang):
            clips.append((sp, gold, "", pcm, "real"))
        babble_pool = [c[3] for c in clips[:: max(1, len(clips) // 6)]][:6]
        print(f"[{lang}] {len(clips)} clips", flush=True)

        for n, (sp, gold, text, speech, kind) in enumerate(clips):
            noise = at.cabin_noise(len(speech) + at.SR, rng, babble_pool)
            for level_name, snr in LEVELS:
                noisy = at.mix_snr(speech, noise, snr)
                # A: translate to English, then the English bank only
                tr = asr.transcribe(noisy, lang, task="translate")
                a = matcher.match(tr.text, banks=("en",))
                # B: transcribe in the passenger's language, all banks, with and without cleanup
                tx = asr.transcribe(noisy, lang)
                b = matcher.match(tx.text)
                cleaned = hashi_noise.clean(noisy)
                tc = asr.transcribe(cleaned, lang)
                bc = matcher.match(tc.text)
                results.append({
                    "lang": lang, "speaker": sp, "kind": kind, "level": level_name, "gold": gold,
                    "text": text, "A_text": tr.text, "A_pick": a.candidates[0].intent if a.candidates else None,
                    "B_text": tx.text, "B_pick": b.candidates[0].intent if b.candidates else None,
                    "B_top3": [c.intent for c in b.candidates], "B_mode": b.mode,
                    "C_text": tc.text, "C_pick": bc.candidates[0].intent if bc.candidates else None,
                    "C_top3": [c.intent for c in bc.candidates], "C_mode": bc.mode,
                    "asr_seconds": tx.seconds,
                })
            if (n + 1) % 10 == 0:
                print(f"  {lang} {n + 1}/{len(clips)}  elapsed {time.time() - t_start:.0f}s", flush=True)

    meta = {"model": f"faster-whisper {args.model} (int8, CPU)", "date": time.strftime("%Y-%m-%d"),
            "machine": f"{platform.processor() or platform.machine()} / {platform.system()}",
            "seconds": round(time.time() - t_start), "quick": args.quick}
    out = ROOT / "bench" / ("results.quick.json" if args.quick else "results.json")
    out.write_text(json.dumps({"meta": meta, "rows": results}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if not args.quick:
        write_report(meta, results, ROOT / "bench" / "REPORT.md")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
