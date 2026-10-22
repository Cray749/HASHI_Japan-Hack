"""Design guards that need no browser: colour contrast, icon coverage, touch-target sizes."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CSS = (ROOT / "web/src/shared/theme.css").read_text(encoding="utf-8")


def token(name: str) -> str:
    return re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", CSS).group(1)


def luminance(hex_colour: str) -> float:
    rgb = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# (text token, background token): every pair used for body-size text in the apps
PAIRS = [
    ("navy", "white"), ("navy", "soft"), ("muted", "white"), ("muted", "soft"),
    ("muted", "t-sky"), ("muted", "t-saffron"), ("muted", "t-green"), ("muted", "t-grey"),
    ("white", "navy"), ("white", "vermilion"), ("white", "green-ink"), ("white", "navy-2"),
    ("navy", "saffron"), ("saffron-ink", "t-saffron"), ("green-ink", "t-green"),
    ("sky-ink", "t-sky"), ("vermilion-ink", "t-vermilion"), ("vermilion-ink", "white"),
    ("navy", "t-vermilion"), ("navy", "t-saffron"), ("navy", "t-green"), ("navy", "t-sky"),
    ("sky-ink", "white"), ("green-ink", "white"),
]


def test_text_pairs_meet_wcag_aa():
    for fg, bg in PAIRS:
        ratio = contrast(token(fg), token(bg))
        assert ratio >= 4.5, f"{fg} on {bg} is only {ratio:.2f}:1"


def test_every_icon_in_the_data_is_bundled():
    icon_map = (ROOT / "web/src/shared/iconMap.ts").read_text(encoding="utf-8")
    for name in ("intents.yaml", "replies.yaml", "announcements.yaml"):
        rows = yaml.safe_load((ROOT / "data/intents" / name).read_text(encoding="utf-8"))
        for row in rows:
            assert re.search(rf"\b{row['icon']}\b", icon_map), f"{row['icon']} missing: run scripts/gen_icons.py"


def test_no_touch_target_below_48px():
    for css in (ROOT / "web/src").rglob("*.css"):
        for m in re.finditer(r"min-height:\s*(\d+)px", css.read_text(encoding="utf-8")):
            assert int(m.group(1)) >= 48, f"{css.name} has min-height {m.group(1)}px"
