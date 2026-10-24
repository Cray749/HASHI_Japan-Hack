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
# language code -> neural voice locale; the first female voice found for the locale is used
EDGE_LOCALE = {"ta": "ta-IN", "te": "te-IN", "bn": "bn-IN", "gu": "gu-IN", "mr": "mr-IN", "kn": "kn-IN",
               "ml": "ml-IN", "th": "th-TH", "vi": "vi-VN", "id": "id-ID", "fil": "fil-PH",
               "ms": "ms-MY", "km": "km-KH", "my": "my-MM"}


def jobs() -> list[tuple[str, str, str]]:
    """(file name, language, text)"""
    out: list[tuple[str, str, str]] = []
    langs = [x for x in catalog().langs]
    for r in catalog().replies.values():
        for lang in langs:
            if lang in r["text"]:
                out.append((f"reply_{r['id']}_{lang}.mp3", lang, r["text"][lang]))
    for a in announcements():
        for lang in langs:
            if lang in a["text"]:
                out.append((f"ann_{a['id']}_{lang}.mp3", lang, a["text"][lang]))
    for g in greetings():
        for item in g["items"]:
            out.append((f"greet_{g['lang']}_{item['id']}.mp3", g["lang"], item["script"]))
    return out


async def pick_voices() -> None:
    """Find a neural voice for each extra language from the service's own list."""
    import edge_tts
    voices = await edge_tts.list_voices()
    for lang, locale in EDGE_LOCALE.items():
        pool = [v for v in voices if v["Locale"] == locale] or [v for v in voices if v["Locale"].startswith(locale[:2])]
        pool.sort(key=lambda v: v["Gender"] != "Female")
        if pool:
            EDGE_VOICE[lang] = pool[0]["ShortName"]


async def edge_one(path: Path, lang: str, text: str, slow: bool = True) -> None:
    import edge_tts
    # slightly slower speech for seniors; some voices reject the rate setting, so retries drop it
    kwargs = {"rate": "-12%"} if slow else {}
    await edge_tts.Communicate(text, EDGE_VOICE[lang], **kwargs).save(str(path))


def gtts_one(path: Path, lang: str, text: str) -> None:
    from gtts import gTTS
    gTTS(text=text, lang=lang, slow=False).save(str(path))


async def make_one(sem: asyncio.Semaphore, name: str, lang: str, text: str, force: bool) -> str:
    path = OUT / name
    if path.exists() and path.stat().st_size > 500 and not force:
        return "skipped"
    async with sem:
        for attempt in range(4):  # the online voices fail now and then; retry before giving up
            try:
                if lang == "pa" or lang not in EDGE_VOICE:
                    await asyncio.to_thread(gtts_one, path, lang, text)
                else:
                    await edge_one(path, lang, text, slow=attempt < 2)
                return "made"
            except Exception as exc:
                last = exc
                await asyncio.sleep(1 + attempt)
        print(f"failed {name}: {last}")
        return "failed"


async def main(force: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    await pick_voices()
    sem = asyncio.Semaphore(4)
    results = await asyncio.gather(*(make_one(sem, n, lang, t, force) for n, lang, t in jobs()))
    made, skipped, failed = (results.count(k) for k in ("made", "skipped", "failed"))
    print(f"audio: {made} made, {skipped} already there, {failed} failed -> {OUT}")
    return 1 if failed and not made else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    raise SystemExit(asyncio.run(main(ap.parse_args().force)))
