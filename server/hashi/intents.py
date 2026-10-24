"""Load the closed list of cabin requests, crew replies and phrase banks from data/."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

DATA_DIR = Path(os.environ.get("HASHI_DATA", Path(__file__).resolve().parents[2] / "data"))
CORE_LANGS = ("en", "ja", "hi", "pa")  # labels written inside the core data files
LANGS = CORE_LANGS  # kept for older imports; the full list is catalog().langs


def _load(name: str):
    with open(DATA_DIR / "intents" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class Intent:
    id: str
    cat: str
    urgency: int
    icon: str
    tile: bool
    labels: dict[str, str]
    replies: list[str]

    def public(self) -> dict:
        return {"id": self.id, "cat": self.cat, "urgency": self.urgency, "icon": self.icon,
                "tile": self.tile, "labels": self.labels, "replies": self.replies}


@dataclass
class Catalog:
    intents: dict[str, Intent] = field(default_factory=dict)
    replies: dict[str, dict] = field(default_factory=dict)
    phrases: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    languages: list[dict] = field(default_factory=list)   # passenger languages with metadata
    ui: dict[str, dict[str, str]] = field(default_factory=dict)  # interface strings from packs

    @property
    def langs(self) -> list[str]:
        return [x["code"] for x in self.languages]


@lru_cache(maxsize=1)
def catalog() -> Catalog:
    cat = Catalog()
    for row in _load("intents.yaml"):
        cat.intents[row["id"]] = Intent(
            id=row["id"], cat=row["cat"], urgency=int(row["urgency"]), icon=row["icon"],
            tile=bool(row.get("tile", False)), labels={k: row[k] for k in CORE_LANGS},
            replies=list(row.get("replies", [])))
    for row in _load("replies.yaml"):
        cat.replies[row["id"]] = {"id": row["id"], "icon": row["icon"],
                                  "text": {k: row[k] for k in CORE_LANGS}}
    cat.phrases = _load("phrases.yaml")
    cat.languages = [
        {"code": "pa", "name": "ਪੰਜਾਬੀ", "voice": True, "status": "draft"},
        {"code": "hi", "name": "हिन्दी", "voice": True, "status": "draft"},
        {"code": "en", "name": "English", "voice": True, "status": "draft"},
    ]
    _merge_packs(cat)
    return cat


def _merge_packs(cat: Catalog) -> None:
    """Extra languages live in data/intents/translations/<code>.yaml, one file each."""
    folder = DATA_DIR / "intents" / "translations"
    anns = {a["id"]: {"id": a["id"], "icon": a["icon"], "kind": a.get("kind", "info"),
                      "text": {k: a[k] for k in CORE_LANGS}} for a in _load("announcements.yaml")}
    for path in sorted(folder.glob("*.yaml")) if folder.exists() else []:
        with open(path, encoding="utf-8") as f:
            pack = yaml.safe_load(f)
        code = pack["code"]
        cat.languages.append({"code": code, "name": pack["name"], "voice": bool(pack.get("voice", False)),
                              "status": pack.get("status", "draft")})
        cat.ui[code] = pack.get("ui", {})
        for iid, text in pack.get("intents", {}).items():
            if iid in cat.intents:
                cat.intents[iid].labels[code] = text
        for rid, text in pack.get("replies", {}).items():
            if rid in cat.replies:
                cat.replies[rid]["text"][code] = text
        for aid, text in pack.get("announcements", {}).items():
            if aid in anns:
                anns[aid]["text"][code] = text
    # announcements() reads the same file; keep the merged copy for it
    cat_announcements.clear()
    cat_announcements.update(anns)


cat_announcements: dict[str, dict] = {}


@lru_cache(maxsize=1)
def announcements() -> list[dict]:
    catalog()  # makes sure the packs were merged
    rows = cat_announcements.values()
    return [dict(r) for r in rows]


@lru_cache(maxsize=1)
def greetings() -> list[dict]:
    return _load("greetings.yaml")
