"""Generate the reply, announcement and greeting audio files into data/audio/.

Run once with internet (the cabin server never needs it afterwards):
    python scripts/gen_audio.py            # only missing files
    python scripts/gen_audio.py --force    # regenerate everything

Hindi and English use neural voices through edge-tts; Punjabi uses gTTS because no
Punjabi neural voice is offered there. The files are small, but their voices are not
open-licence, so they are git-ignored and rebuilt by this script instead of committed.
"""
import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.stdout.reconfigure(encoding="utf-8")

from hashi.intents import DATA_DIR, announcements, catalog, greetings  # noqa: E402

OUT = DATA_DIR / "audio"
EDGE_VOICE = {"hi": "hi-IN-SwaraNeural", "en": "en-IN-NeerjaNeural", "ja": "ja-JP-NanamiNeural"}


def jobs() -> list[tuple[str, str, str]]:
    """(file name, language, text)"""
    out: list[tuple[str, str, str]] = []
    for r in catalog().replies.values():
        for lang in ("hi", "pa", "en"):
            out.append((f"reply_{r['id']}_{lang}.mp3", lang, r["text"][lang]))
    for a in announcements():
        for lang in ("hi", "pa", "en"):
            out.append((f"ann_{a['id']}_{lang}.mp3", lang, a["text"][lang]))
    for g in greetings():
        for item in g["items"]:
            out.append((f"greet_{g['lang']}_{item['id']}.mp3", g["lang"], item["script"]))
    return out


async def edge_one(path: Path, lang: str, text: str) -> None:
    import edge_tts
    await edge_tts.Communicate(text, EDGE_VOICE[lang], rate="-12%").save(str(path))


def gtts_one(path: Path, lang: str, text: str) -> None:
    from gtts import gTTS
    gTTS(text=text, lang=lang, slow=False).save(str(path))


async def main(force: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = skipped = failed = 0
    for name, lang, text in jobs():
        path = OUT / name
        if path.exists() and path.stat().st_size > 500 and not force:
            skipped += 1
            continue
        try:
            if lang == "pa":
                await asyncio.to_thread(gtts_one, path, lang, text)
            else:
                await edge_one(path, lang, text)
            made += 1
        except Exception as exc:  # keep going; the app falls back to the phone's own voice
            failed += 1
            print(f"failed {name}: {exc}")
    print(f"audio: {made} made, {skipped} already there, {failed} failed -> {OUT}")
    return 1 if failed and not made else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    raise SystemExit(asyncio.run(main(ap.parse_args().force)))
