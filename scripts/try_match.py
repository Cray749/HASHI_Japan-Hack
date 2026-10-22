"""Quick manual check: python scripts/try_match.py "mujhe paani chahiye" "ਮੈਨੂੰ ਕੰਬਲ ਦਿਓ" """
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.stdout.reconfigure(encoding="utf-8")

from hashi.matcher import get_matcher  # noqa: E402

DEFAULT = ["mujhe pani chahiye", "पानी दे दो", "ਮੈਨੂੰ ਪਾਣੀ ਦਿਓ", "mainu kambal chahida",
           "seene me dard", "ਮੈਨੂੰ ਕੰਬਲ ਚਾਹੀਦਾ ਹੈ ਜੀ", "khana kab milega", "bachao",
           "मुझे चक्कर आ रहे", "tabiyat kharab hai", "pani", "asdf qwer",
           "dawai khani he mujhe", "mainu thand lagdi e", "toilet kidhar hai",
           "ਮੈਨੂੰ ਹਿੰਦੀ ਬੋਲਣ ਵਾਲਾ ਚਾਹੀਦਾ", "mera phone charge karna hai"]

if __name__ == "__main__":
    m = get_matcher()
    t = time.time()
    texts = sys.argv[1:] or DEFAULT
    for x in texts:
        r = m.match(x)
        print(f"{x!r:45} {[(c.intent, round(c.score, 2)) for c in r.candidates]} "
              f"{r.mode} m={r.margin:.2f}")
    print(f"avg {(time.time() - t) / len(texts) * 1000:.1f} ms")
