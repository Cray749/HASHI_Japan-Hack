"""Per-flight state, kept in memory only. Nothing here is written to disk.

The store holds the rules (who is seated where, which requests are open, who has
confirmed an announcement). It knows nothing about sockets, so it is easy to test.
Everything is wiped when the crew press "landed".
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field

from .intents import announcements, catalog

SEAT_RE = re.compile(r"^(\d{1,2})([A-K])$")
DUPLICATE_WINDOW_S = 20  # a second tap of the same request inside this window is ignored
MAX_ACTIVE_STATES = ("new", "seen", "replied")


def now() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def parse_seat(seat: str) -> tuple[int, str] | None:
    m = SEAT_RE.match((seat or "").strip().upper())
    return (int(m.group(1)), m.group(2)) if m else None


def clean_seat(seat: str) -> str:
    parsed = parse_seat(seat)
    if not parsed:
        raise ValueError("bad seat")
    return f"{parsed[0]}{parsed[1]}"


@dataclass
class Passenger:
    seat: str
    lang: str = "pa"
    senior: bool = False
    first_time: bool = False
    pictures_first: bool = False
    needs: list[str] = field(default_factory=list)  # e.g. veg, hearing, mobility
    online: bool = False
    joined: float = field(default_factory=now)

    def public(self) -> dict:
        return {"seat": self.seat, "lang": self.lang, "senior": self.senior,
                "first_time": self.first_time, "pictures_first": self.pictures_first,
                "needs": self.needs, "online": self.online}


class Flight:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.passengers: dict[str, Passenger] = {}
        self.requests: dict[str, dict] = {}
        self.announcements: dict[str, dict] = {}
        self.exit_checks: dict[str, dict] = {}
        self.landed_at: float | None = None

    # ---- passengers ----------------------------------------------------------------
    def register(self, seat: str, **profile) -> Passenger:
        seat = clean_seat(seat)
        p = self.passengers.get(seat) or Passenger(seat=seat)
        if profile.get("lang") in catalog().langs:
            p.lang = profile["lang"]
        for key in ("senior", "first_time", "pictures_first"):
            if key in profile:
                setattr(p, key, bool(profile[key]))
        if "needs" in profile:
            p.needs = [str(n)[:24] for n in list(profile["needs"])[:8]]
        self.passengers[seat] = p
        self._attach_to_announcements(p)
        return p

    def _attach_to_announcements(self, p: Passenger) -> None:
        for ann in self.announcements.values():
            if self._targets(ann["target"], p.seat) and p.seat not in ann["acks"]:
                ann["acks"][p.seat] = {"state": "sent", "at": None}

    # ---- requests -----------------------------------------------------------------
    def create_request(self, seat: str, intent: str, via: str = "tap",
                       confidence: float | None = None) -> tuple[dict, bool]:
        """Return (request, is_new). A rapid repeat of the same tap returns the first one."""
        seat = clean_seat(seat)
        spec = catalog().intents.get(intent)
        if spec is None:
            raise ValueError("unknown intent")
        for r in self.requests.values():
            if (r["seat"] == seat and r["intent"] == intent and r["status"] in MAX_ACTIVE_STATES
                    and now() - r["created"] < DUPLICATE_WINDOW_S):
                return r, False
        req = {"id": new_id("r"), "seat": seat, "intent": intent, "urgency": spec.urgency,
               "via": via, "confidence": confidence, "status": "new", "created": now(),
               "seen_at": None, "replies": [], "understood_at": None, "done_at": None,
               "lang": self.passengers[seat].lang if seat in self.passengers else "pa"}
        self.requests[req["id"]] = req
        return req, True

    def get_request(self, req_id: str) -> dict:
        req = self.requests.get(req_id)
        if req is None:
            raise KeyError("no such request")
        return req

    def mark_seen(self, req_id: str) -> dict:
        req = self.get_request(req_id)
        if req["status"] == "new":
            req["status"] = "seen"
            req["seen_at"] = now()
        return req

    def add_reply(self, req_id: str, reply_id: str) -> dict:
        if reply_id not in catalog().replies:
            raise ValueError("unknown reply")
        req = self.get_request(req_id)
        if req["status"] in ("new", "seen"):
            req["seen_at"] = req["seen_at"] or now()
        if req["status"] != "done":
            req["status"] = "replied"
        req["replies"].append({"reply": reply_id, "at": now()})
        req["understood_at"] = None  # a fresh reply needs a fresh "understood"
        return req

    def understood(self, req_id: str, seat: str) -> dict:
        req = self.get_request(req_id)
        if req["seat"] != clean_seat(seat):
            raise PermissionError("not your request")
        req["understood_at"] = now()
        return req

    def finish(self, req_id: str) -> dict:
        req = self.get_request(req_id)
        req["status"] = "done"
        req["done_at"] = now()
        return req

    def cancel(self, req_id: str, seat: str) -> dict:
        req = self.get_request(req_id)
        if req["seat"] != clean_seat(seat):
            raise PermissionError("not your request")
        if req["status"] in ("new", "seen"):
            req["status"] = "cancelled"
            req["done_at"] = now()
        return req

    def open_requests(self) -> list[dict]:
        return [r for r in self.requests.values() if r["status"] in MAX_ACTIVE_STATES]

    # ---- announcements --------------------------------------------------------------
    @staticmethod
    def _targets(target: dict, seat: str) -> bool:
        if target.get("all"):
            return True
        row, col = parse_seat(seat) or (0, "")
        if row in target.get("rows", []):
            return True
        return seat in target.get("seats", [])

    def create_announcement(self, phrase_id: str | None, target: dict,
                            custom: str | None = None) -> dict:
        phrase = next((a for a in announcements() if a["id"] == phrase_id), None)
        if phrase is None and not (custom and custom.strip()):
            raise ValueError("unknown announcement")
        ann = {"id": new_id("a"), "phrase": phrase_id if phrase else None,
               "custom": custom.strip()[:300] if (custom and not phrase) else None,
               "kind": phrase["kind"] if phrase else "info",
               "icon": phrase["icon"] if phrase else "Megaphone",
               "target": {"all": bool(target.get("all")),
                          "rows": [int(r) for r in target.get("rows", [])][:60],
                          "seats": [clean_seat(s) for s in target.get("seats", [])][:300]},
               "created": now(), "acks": {}}
        for p in self.passengers.values():
            if self._targets(ann["target"], p.seat):
                ann["acks"][p.seat] = {"state": "sent", "at": None}
        self.announcements[ann["id"]] = ann
        return ann

    def ack_announcement(self, ann_id: str, seat: str) -> dict:
        ann = self.announcements.get(ann_id)
        if ann is None:
            raise KeyError("no such announcement")
        seat = clean_seat(seat)
        if seat in ann["acks"]:
            ann["acks"][seat] = {"state": "understood", "at": now()}
        return ann

    def pending_announcements(self, seat: str) -> list[dict]:
        return [a for a in self.announcements.values()
                if a["acks"].get(seat, {}).get("state") == "sent"]

    # ---- exit-row teach-back --------------------------------------------------------
    def start_exit_check(self, row: int) -> dict:
        seats = [s for s, p in self.passengers.items() if parse_seat(s)[0] == row]
        if not seats:
            raise ValueError("no passengers registered in that row")
        for chk in self.exit_checks.values():
            if chk["row"] == row and chk["open"]:
                chk["open"] = False
        chk = {"id": new_id("x"), "row": row, "created": now(), "open": True,
               "seats": {s: {"state": "waiting", "answer": None, "at": None} for s in seats}}
        self.exit_checks[chk["id"]] = chk
        return chk

    def answer_exit_check(self, check_id: str, seat: str, willing: bool, answer: str) -> dict:
        chk = self.exit_checks.get(check_id)
        seat = clean_seat(seat)
        if chk is None or seat not in chk["seats"]:
            raise KeyError("no such check")
        if not willing:
            state = "unwilling"
        elif answer == "when_told":
            state = "passed"
        else:
            state = "retry"
        chk["seats"][seat] = {"state": state, "answer": answer, "at": now()}
        return chk

    def resolve_exit_seat(self, check_id: str, seat: str, ok: bool) -> dict:
        """Crew confirm in person after a wrong answer or a 'not willing' reply."""
        chk = self.exit_checks.get(check_id)
        seat = clean_seat(seat)
        if chk is None or seat not in chk["seats"]:
            raise KeyError("no such check")
        chk["seats"][seat]["state"] = "passed" if ok else "reseat"
        chk["seats"][seat]["at"] = now()
        return chk

    def pending_exit_check(self, seat: str) -> dict | None:
        for chk in self.exit_checks.values():
            if chk["open"] and chk["seats"].get(seat, {}).get("state") == "waiting":
                return chk
        return None

    # ---- snapshots ------------------------------------------------------------------
    def snapshot(self) -> dict:
        return {"passengers": [p.public() for p in self.passengers.values()],
                "requests": sorted(self.requests.values(), key=lambda r: r["created"]),
                "announcements": sorted(self.announcements.values(), key=lambda a: a["created"]),
                "exit_checks": sorted(self.exit_checks.values(), key=lambda c: c["created"])}
