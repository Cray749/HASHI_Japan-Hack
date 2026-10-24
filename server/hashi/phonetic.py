"""Fold Devanagari, Gurmukhi and roman spellings into one rough sound-alike form.

Speech recognisers spell the same Hindi/Punjabi word in different scripts or with
different roman spellings ("paani", "pani", "पानी", "ਪਾਣੀ"). If we compare words in
this folded form, one phrase bank serves all of them. The result is not linguistically
exact; it only has to make near-identical sounds look near-identical.
"""
import re
import unicodedata

# Devanagari block (U+0900) and Gurmukhi block (U+0A00) share the same layout, so one
# table keyed by the offset from the block start serves both scripts.
_VOWEL_INDEP = {0x05: "a", 0x06: "a", 0x07: "i", 0x08: "i", 0x09: "u", 0x0A: "u",
                0x0F: "e", 0x10: "e", 0x13: "o", 0x14: "o", 0x0B: "ri"}
_MATRA = {0x3E: "a", 0x3F: "i", 0x40: "i", 0x41: "u", 0x42: "u", 0x47: "e", 0x48: "e",
          0x4B: "o", 0x4C: "o", 0x43: "ri"}
_CONS = {
    0x15: "k", 0x16: "k", 0x17: "g", 0x18: "g", 0x19: "n",
    0x1A: "C", 0x1B: "C", 0x1C: "j", 0x1D: "j", 0x1E: "n",
    0x1F: "t", 0x20: "t", 0x21: "d", 0x22: "d", 0x23: "n",
    0x24: "t", 0x25: "t", 0x26: "d", 0x27: "d", 0x28: "n",
    0x2A: "p", 0x2B: "p", 0x2C: "b", 0x2D: "b", 0x2E: "m",
    0x2F: "y", 0x30: "r", 0x32: "l", 0x35: "v", 0x36: "s", 0x38: "s", 0x39: "h",
    0x33: "l", 0x5E: "p",  # Gurmukhi ਲ਼ and ਫ਼ share offsets with Devanagari ळ and फ़
}
_NASAL = {0x01, 0x02}          # chandrabindu / anusvara (Gurmukhi tippi U+0A02)
_VIRAMA = 0x4D
_IGNORE = {0x3C, 0x03, 0x70, 0x71}  # nukta, visarga, Gurmukhi tippi-like marks, addak


def _indic_to_latin(text: str) -> str:
    out: list[str] = []
    pending_schwa = False
    for ch in text:
        cp = ord(ch)
        # Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam: 128-wide blocks
        # that share one layout, so the same table works for all of them
        base = (cp & ~0x7F) if 0x0900 <= cp < 0x0D80 else None
        if base is None:
            if pending_schwa:
                out.append("a")
                pending_schwa = False
            out.append(ch)
            continue
        off = cp - base
        if off in _CONS:
            if pending_schwa:
                out.append("a")
            out.append(_CONS[off])
            pending_schwa = True
        elif off in _MATRA:
            out.append(_MATRA[off])
            pending_schwa = False
        elif off == _VIRAMA:
            pending_schwa = False
        elif off in _VOWEL_INDEP:
            if pending_schwa:
                out.append("a")
            out.append(_VOWEL_INDEP[off])
            pending_schwa = False
        elif off in _NASAL:
            if pending_schwa:
                out.append("a")
                pending_schwa = False
            out.append("n")
        elif off in _IGNORE:
            continue
        else:
            if pending_schwa:
                out.append("a")
                pending_schwa = False
    # a word-final inherent vowel is silent in Hindi/Punjabi, so pending_schwa is dropped
    return "".join(out)


_ROMAN_RULES = [
    (re.compile(r"chh|ch"), "C"), (re.compile(r"sh"), "s"), (re.compile(r"([kgtdbpj])h"), r"\1"),
    (re.compile(r"ai|ei"), "e"), (re.compile(r"au"), "o"),
    (re.compile(r"aa+"), "a"), (re.compile(r"ee+|ii+"), "i"), (re.compile(r"oo+|uu+"), "u"),
]
_ROMAN_MAP = str.maketrans({"z": "j", "f": "p", "w": "v", "q": "k", "c": "k", "x": "k"})


_RAW_SCRIPTS = re.compile("[฀-๿ក-៿က-႟]")


def _fold_roman(word: str) -> str:
    # "C" stands for the "ch" sound; indic text is converted straight to it
    for pat, rep in _ROMAN_RULES:
        word = pat.sub(rep, word)
    word = word.translate(_ROMAN_MAP)
    return re.sub(r"(.)\1+", r"\1", word)  # collapse doubled letters


def phonetic_words(text: str) -> list[str]:
    """Split text into folded words. Punctuation and case are ignored."""
    text = unicodedata.normalize("NFC", text)
    words: list[str] = []
    for raw in re.split(r"[\s,.;:!?\"'()\-।|/]+", text):
        if not raw:
            continue
        if _RAW_SCRIPTS.search(raw):
            words.append(raw.lower())  # Thai, Khmer, Burmese: compared as written (character n-grams)
            continue
        if not raw.isascii():
            stripped = "".join(c for c in unicodedata.normalize("NFD", raw) if not unicodedata.combining(c))
            if stripped.isascii():  # Vietnamese and other Latin text with accents
                raw = stripped.replace("đ", "d").replace("Đ", "D")
        if raw.isascii():
            raw = raw.lower()
        converted = _indic_to_latin(raw)
        folded = _fold_roman(converted)
        folded = re.sub(r"[^a-zC]", "", folded)
        if folded:
            words.append(folded)
    return words


def phonetic_key(text: str) -> str:
    return " ".join(phonetic_words(text))


def skeleton(key: str) -> str:
    """Consonants only. Survives vowel mishearings ('pani' vs 'puni')."""
    return re.sub(r"[aeiou]", "", key)


def collapse_repeats(words: list[str]) -> list[str]:
    """Squash stuck-record output ("a b a b a b" or "a a a a") into a single pass.

    Speech engines sometimes loop on noise. One pass of the loop carries all the information,
    and counting the repeats would make the match look stronger than it is.
    """
    out = list(words)
    changed = True
    while changed:
        changed = False
        for n in (1, 2, 3, 4):
            i = 0
            res: list[str] = []
            while i < len(out):
                res.append(out[i])
                i += 1
                if len(res) >= n and out[i:i + n] == res[-n:]:
                    while out[i:i + n] == res[-n:]:
                        i += n
                        changed = True
            out = res
    return out
