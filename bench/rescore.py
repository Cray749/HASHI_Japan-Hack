"""Re-score saved transcripts with the current phrase bank, without running speech recognition again.

    python -m bench.rescore

bench.run stores what the speech engine heard for every clip. If the phrase bank or the matcher
changes, this rebuilds bench/REPORT.md from those transcripts in seconds. Do not tune the phrase
bank on the test sentences; the point of the held-out set is to avoid that.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))

from bench.report import write_report  # noqa: E402
from hashi.matcher import get_matcher  # noqa: E402


def main() -> int:
    path = ROOT / "bench" / "results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    matcher = get_matcher()
    for r in data["rows"]:
        a = matcher.match(r["A_text"], banks=("en",))
        b = matcher.match(r["B_text"])
        c = matcher.match(r["C_text"])
        r["A_pick"] = a.candidates[0].intent if a.candidates else None
        r["B_pick"], r["B_top3"], r["B_mode"] = (b.candidates[0].intent if b.candidates else None,
                                                 [x.intent for x in b.candidates], b.mode)
        r["C_pick"], r["C_top3"], r["C_mode"] = (c.candidates[0].intent if c.candidates else None,
                                                 [x.intent for x in c.candidates], c.mode)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(data["meta"], data["rows"], ROOT / "bench" / "REPORT.md")
    print("rescored", len(data["rows"]), "rows ->", ROOT / "bench" / "REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
