"""Load the closed list of cabin requests, crew replies and phrase banks from data/."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

DATA_DIR = Path(os.environ.get("HASHI_DATA", Path(__file__).resolve().parents[2] / "data"))
LANGS = ("en", "ja", "hi", "pa")


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


@lru_cache(maxsize=1)
def catalog() -> Catalog:
    cat = Catalog()
    for row in _load("intents.yaml"):
        cat.intents[row["id"]] = Intent(
            id=row["id"], cat=row["cat"], urgency=int(row["urgency"]), icon=row["icon"],
            tile=bool(row.get("tile", False)), labels={k: row[k] for k in LANGS},
            replies=list(row.get("replies", [])))
    for row in _load("replies.yaml"):
        cat.replies[row["id"]] = {"id": row["id"], "icon": row["icon"],
                                  "text": {k: row[k] for k in LANGS}}
    cat.phrases = _load("phrases.yaml")
    return cat


@lru_cache(maxsize=1)
def announcements() -> list[dict]:
    rows = _load("announcements.yaml")
    return [{"id": r["id"], "icon": r["icon"], "kind": r.get("kind", "info"),
             "text": {k: r[k] for k in LANGS}} for r in rows]


@lru_cache(maxsize=1)
def greetings() -> list[dict]:
    return _load("greetings.yaml")
