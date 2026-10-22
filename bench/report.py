"""Turn raw benchmark rows into bench/REPORT.md. Every number comes from the rows."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

LEVELS = ["clean", "10 dB", "0 dB"]
LANG_NAME = {"hi": "Hindi", "pa": "Punjabi"}


def _pct(hit: int, n: int) -> str:
    return f"{100 * hit / n:.0f}% ({hit}/{n})" if n else "n/a"


def _acc(rows: list[dict], key: str) -> tuple[int, int]:
    return sum(1 for r in rows if r[key] == r["gold"]), len(rows)


def write_report(meta: dict, rows: list[dict], path: Path) -> None:
    by = defaultdict(list)
    for r in rows:
        by[(r["lang"], r["level"])].append(r)

    out: list[str] = ["# Noise benchmark report", ""]
    out += [f"Run on {meta['date']} · {meta['model']} · {meta['machine']} · took {meta['seconds']} s", ""]
    kinds = sorted({r["kind"] for r in rows})
    speakers = sorted({r["speaker"] for r in rows})
    out += [f"Clip sources: **{', '.join(kinds)}**. Speakers: {', '.join(speakers)}.", ""]
    out += ["## Question",
            "How often does the crew card show the right request when the passenger speaks in cabin noise?",
            "",
            "* **A: plain speech-to-text then translation.** The speech engine translates the clip to English; "
            "the English text is matched to a request using the English phrase bank only "
            "(this hands the baseline our own matcher, which is generous to it).",
            "* **B: HASHI.** The engine transcribes in the passenger's language and the text is matched to the "
            "closed request list. **B+** is the same with the spectral-gating cleanup applied first.",
            "",
            "Success means the top request equals the request the speaker meant.", ""]

    out += ["## Results", "",
            "| Language | Noise | A: speech-to-text + translation | B: HASHI | B+: HASHI with cleanup | B: right request in top 3 |",
            "| --- | --- | --- | --- | --- | --- |"]
    for lang in ("hi", "pa"):
        for lv in LEVELS:
            rs = by.get((lang, lv), [])
            if not rs:
                continue
            a = _acc(rs, "A_pick")
            b = _acc(rs, "B_pick")
            c = _acc(rs, "C_pick")
            top3 = sum(1 for r in rs if r["gold"] in r["B_top3"])
            out.append(f"| {LANG_NAME[lang]} | {lv} | {_pct(*a)} | {_pct(*b)} | {_pct(*c)} | {_pct(top3, len(rs))} |")
    out += [""]

    out += ["### Overall by noise level (both languages)", "",
            "| Noise | A | B | B+ |", "| --- | --- | --- | --- |"]
    for lv in LEVELS:
        rs = [r for r in rows if r["level"] == lv]
        if rs:
            out.append(f"| {lv} | {_pct(*_acc(rs, 'A_pick'))} | {_pct(*_acc(rs, 'B_pick'))} | {_pct(*_acc(rs, 'C_pick'))} |")
    out += [""]

    out += ["### Reading the numbers", ""]
    for lv in LEVELS:
        rs = [r for r in rows if r["level"] == lv]
        if not rs:
            continue
        a, b, c = (_acc(rs, k)[0] / len(rs) * 100 for k in ("A_pick", "B_pick", "C_pick"))
        out.append(f"* **{lv}:** HASHI (B) is {b - a:+.0f} points against plain speech-to-text plus "
                   f"translation (A); the cleanup step (B+) is {c - b:+.0f} points against B.")
    loops = sum(1 for r in rows if r.get("B_suspect"))
    if loops:
        out.append(f"* The matcher flagged {loops} of {len(rows)} B transcripts as a stuck, repeating engine "
                   "and refused to send them without the passenger confirming.")
    out += [""]

    out += ["### What the passenger would see (B, the shipped setting)", "",
            "HASHI only sends straight away when it is confident; otherwise it shows the top pictures to confirm.",
            "",
            "| Noise | Sent directly and right | Sent directly but wrong | Asked to confirm | Fell back to tiles |",
            "| --- | --- | --- | --- | --- |"]
    for lv in LEVELS:
        rs = [r for r in rows if r["level"] == lv]
        if not rs:
            continue
        sent = [r for r in rs if r["B_mode"] == "send"]
        ok = sum(1 for r in sent if r["B_pick"] == r["gold"])
        out.append(f"| {lv} | {ok} | {len(sent) - ok} | {sum(1 for r in rs if r['B_mode'] == 'confirm')} "
                   f"| {sum(1 for r in rs if r['B_mode'] == 'tiles')} |")
    out += [""]

    out += ["### By speaker (B, all noise levels)", "", "| Speaker | Right request |", "| --- | --- |"]
    for sp in speakers:
        rs = [r for r in rows if r["speaker"] == sp]
        out.append(f"| {sp} | {_pct(*_acc(rs, 'B_pick'))} |")
    out += [""]

    secs = [r["asr_seconds"] for r in rows if r.get("asr_seconds")]
    if secs:
        out += [f"Speech engine time per clip on this machine: median {sorted(secs)[len(secs) // 2]:.1f} s.", ""]

    out += ["## Failures at 0 dB (B), for inspection", "",
            "| Language | Meant | HASHI picked | Engine heard |", "| --- | --- | --- | --- |"]
    fails = [r for r in rows if r["level"] == "0 dB" and r["B_pick"] != r["gold"]][:25]
    for r in fails:
        heard = (r["B_text"] or "(nothing)").replace("|", "/")
        out.append(f"| {LANG_NAME[r['lang']]} | {r['gold']} | {r['B_pick']} | {heard} |")
    if not fails:
        out.append("| none | | | |")
    out += [""]

    out += ["## Sample of baseline A output (0 dB)", "",
            "| Meant | English the crew would have read |", "| --- | --- |"]
    seen = set()
    for r in rows:
        if r["level"] == "0 dB" and r["gold"] not in seen and len(seen) < 12:
            seen.add(r["gold"])
            out.append(f"| {r['gold']} ({LANG_NAME[r['lang']]}) | {(r['A_text'] or '(nothing)').replace('|', '/')} |")
    out += [""]

    out += ["## Limits (read before quoting any number)", "",
            "* Clips are **synthetic** (text-to-speech voices, with simple speed/pitch variants as extra "
            "\"speakers\") unless the source line above also lists `real`. Synthetic voices are cleaner and more "
            "regular than frightened or elderly people with accents, so real-world accuracy will be lower.",
            "* Noise is **synthetic** cabin noise (steady engine rumble and tones plus faint background voices) mixed at "
            "the stated signal-to-noise ratios. It is not a recording from an aircraft.",
            "* The test sentences are one per request per language, 20 per language. Small samples: treat a difference "
            "of a few clips as noise.",
            "* The request list is closed (about 40 requests). Free speech outside the list falls back to tiles by design.",
            "* Baseline A uses our own matcher on the English text, so it is a stronger baseline than a human reading "
            "raw machine translation would be, but it does not model how well a crew member would guess the meaning.",
            "* To add real recordings see `bench/README.md` and re-run `make bench`.", ""]
    path.write_text("\n".join(out), encoding="utf-8")
