"""Match recognised text to the closed intent list.

Three signals are combined, all computed on the folded sound-alike form of the text
(see phonetic.py): character n-gram cosine, the same on consonants only, and a fuzzy
word-overlap score weighted by how rare each word is. The best phrase of each intent
gives that intent's score. No machine-learning model is needed, so it runs offline in
milliseconds and every decision can be explained.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from rapidfuzz import fuzz

from .intents import catalog
from .phonetic import phonetic_key, skeleton

ACCEPT_CONF = 0.62     # at or above this (with a clear margin) the request is sent directly
ACCEPT_MARGIN = 0.07
URGENT_CONF = 0.50     # urgent intents are sent at a lower bar: a false alarm is cheap
MIN_CONF = 0.30        # below this we show the picture tiles instead of guessing


def _grams(text: str, n_lo: int = 2, n_hi: int = 4) -> Counter:
    padded = f" {text} "
    c: Counter = Counter()
    for n in range(n_lo, n_hi + 1):
        for i in range(len(padded) - n + 1):
            c[padded[i:i + n]] += 1
    return c


def _norm(vec: dict) -> float:
    return math.sqrt(sum(v * v for v in vec.values())) or 1.0


@dataclass
class Candidate:
    intent: str
    score: float
    phrase: str

    def public(self) -> dict:
        return {"intent": self.intent, "score": round(self.score, 3), "phrase": self.phrase}


@dataclass
class Match:
    candidates: list[Candidate]
    confidence: float
    margin: float
    mode: str  # "send" | "confirm" | "tiles"

    def public(self) -> dict:
        return {"candidates": [c.public() for c in self.candidates],
                "confidence": round(self.confidence, 3), "margin": round(self.margin, 3),
                "mode": self.mode}


class IntentMatcher:
    def __init__(self) -> None:
        cat = catalog()
        self.rows: list[tuple[str, str, str, str, str]] = []   # intent, raw, key, skeleton, bank
        for intent_id, banks in cat.phrases.items():
            for bank, phrases in banks.items():
                for raw in phrases:
                    key = phonetic_key(raw)
                    self.rows.append((intent_id, raw, key, skeleton(key), bank))
        n = len(self.rows)
        df_full: Counter = Counter()
        df_skel: Counter = Counter()
        df_word: Counter = Counter()
        self.g_full, self.g_skel, self.words = [], [], []
        for _, _, key, skel, _ in self.rows:
            gf, gs, ws = _grams(key), _grams(skel, 2, 3), set(key.split())
            self.g_full.append(gf)
            self.g_skel.append(gs)
            self.words.append(ws)
            df_full.update(gf.keys())
            df_skel.update(gs.keys())
            df_word.update(ws)
        self.idf_full = {g: math.log((1 + n) / (1 + d)) + 1 for g, d in df_full.items()}
        self.idf_skel = {g: math.log((1 + n) / (1 + d)) + 1 for g, d in df_skel.items()}
        self.idf_word = {w: math.log((1 + n) / (1 + d)) + 1 for w, d in df_word.items()}
        self.v_full = [self._tfidf(g, self.idf_full) for g in self.g_full]
        self.v_skel = [self._tfidf(g, self.idf_skel) for g in self.g_skel]

    @staticmethod
    def _tfidf(grams: Counter, idf: dict) -> dict:
        vec = {g: (1 + math.log(c)) * idf.get(g, 1.0) for g, c in grams.items()}
        norm = _norm(vec)
        return {g: v / norm for g, v in vec.items()}

    @staticmethod
    def _cos(a: dict, b: dict) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(g, 0.0) for g, v in a.items())

    def _word_score(self, qwords: list[str], pwords: set[str]) -> float:
        if not qwords or not pwords:
            return 0.0
        idf = self.idf_word
        q_total = sum(idf.get(w, 2.0) for w in qwords)
        p_total = sum(idf.get(w, 2.0) for w in pwords)
        hit_q = hit_p = 0.0
        for w in qwords:
            best = max((fuzz.ratio(w, p) for p in pwords), default=0)
            if best >= 80:
                hit_q += idf.get(w, 2.0) * (best / 100)
        for p in pwords:
            best = max((fuzz.ratio(p, w) for w in qwords), default=0)
            if best >= 80:
                hit_p += idf.get(p, 2.0) * (best / 100)
        return 0.6 * hit_q / q_total + 0.4 * hit_p / p_total

    def match(self, text: str, top_k: int = 3, banks: tuple[str, ...] | None = None) -> Match:
        """banks limits the phrase banks used (e.g. ('en',)); the benchmark baseline uses it."""
        key = phonetic_key(text)
        if not key:
            return Match([], 0.0, 0.0, "tiles")
        skel = skeleton(key)
        qf = self._tfidf(_grams(key), self.idf_full)
        qs = self._tfidf(_grams(skel, 2, 3), self.idf_skel) if len(skel) >= 2 else {}
        qwords = key.split()
        best: dict[str, Candidate] = {}
        for i, (intent_id, raw, _, _, bank) in enumerate(self.rows):
            if banks and bank not in banks:
                continue
            s = (0.35 * self._cos(qf, self.v_full[i])
                 + 0.15 * (self._cos(qs, self.v_skel[i]) if qs else 0.0)
                 + 0.50 * self._word_score(qwords, self.words[i]))
            cur = best.get(intent_id)
            if cur is None or s > cur.score:
                best[intent_id] = Candidate(intent_id, s, raw)
        ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)[:top_k]
        top = ranked[0]
        second = ranked[1].score if len(ranked) > 1 else 0.0
        margin = top.score - second
        urgency = catalog().intents[top.intent].urgency
        if urgency == 3 and top.score >= URGENT_CONF:
            mode = "send"
        elif top.score >= ACCEPT_CONF and margin >= ACCEPT_MARGIN:
            mode = "send"
        elif top.score >= MIN_CONF:
            mode = "confirm"
        else:
            mode = "tiles"
        return Match(ranked, top.score, margin, mode)


_matcher: IntentMatcher | None = None


def get_matcher() -> IntentMatcher:
    global _matcher
    if _matcher is None:
        _matcher = IntentMatcher()
    return _matcher
