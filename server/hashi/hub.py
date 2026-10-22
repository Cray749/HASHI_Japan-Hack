"""Message hub: keeps the open WebSockets and turns messages into store changes.

Two kinds of clients connect: passenger phones (one per seat) and crew tablets. Every
change is pushed straight to whoever needs it, so a request shows on the crew tablet
within a fraction of a second on the local network.
"""
from __future__ import annotations

import json
import logging

from fastapi import WebSocket

from .store import Flight, clean_seat

log = logging.getLogger("hashi.hub")


class Hub:
    def __init__(self, flight: Flight | None = None) -> None:
        self.flight = flight or Flight()
        self.passengers: dict[str, set[WebSocket]] = {}
        self.crew: set[WebSocket] = set()

    # ---- sending -------------------------------------------------------------------
    @staticmethod
    async def _send(ws: WebSocket, msg: dict) -> bool:
        try:
            await ws.send_text(json.dumps(msg, ensure_ascii=False))
            return True
        except Exception:  # the socket died; the caller drops it
            return False

    async def to_crew(self, msg: dict) -> None:
        for ws in list(self.crew):
            if not await self._send(ws, msg):
                self.crew.discard(ws)

    async def to_seat(self, seat: str, msg: dict) -> None:
        for ws in list(self.passengers.get(seat, ())):
            if not await self._send(ws, msg):
                self.passengers[seat].discard(ws)

    async def push_passenger(self, seat: str) -> None:
        p = self.flight.passengers.get(seat)
        if p:
            p.online = bool(self.passengers.get(seat))
            await self.to_crew({"t": "passenger", "passenger": p.public()})

    # ---- passenger side ------------------------------------------------------------
    async def passenger_connect(self, ws: WebSocket, seat: str) -> str:
        seat = clean_seat(seat)
        self.passengers.setdefault(seat, set()).add(ws)
        return seat

    async def passenger_disconnect(self, ws: WebSocket, seat: str) -> None:
        self.passengers.get(seat, set()).discard(ws)
        await self.push_passenger(seat)

    def passenger_state(self, seat: str) -> dict:
        f = self.flight
        return {"t": "welcome", "passenger": f.passengers[seat].public(),
                "requests": [r for r in f.requests.values() if r["seat"] == seat
                             and r["status"] in ("new", "seen", "replied")],
                "announcements": f.pending_announcements(seat),
                "exit_check": f.pending_exit_check(seat)}

    async def handle_passenger(self, seat: str, msg: dict) -> None:
        f = self.flight
        kind = msg.get("t")
        if kind == "hello" or kind == "profile":
            f.register(seat, **{k: msg[k] for k in
                                ("lang", "senior", "first_time", "pictures_first", "needs")
                                if k in msg})
            await self.to_seat(seat, self.passenger_state(seat))
            await self.push_passenger(seat)
        elif kind == "request":
            if seat not in f.passengers:
                f.register(seat)
            req, is_new = f.create_request(seat, msg.get("intent", ""), msg.get("via", "tap"),
                                           msg.get("confidence"))
            await self.to_seat(seat, {"t": "request", "request": req})
            if is_new:
                await self.to_crew({"t": "request", "request": req, "new": True})
        elif kind == "cancel":
            req = f.cancel(msg.get("req_id", ""), seat)
            await self.to_seat(seat, {"t": "request", "request": req})
            await self.to_crew({"t": "request", "request": req})
        elif kind == "understood":
            req = f.understood(msg.get("req_id", ""), seat)
            await self.to_seat(seat, {"t": "request", "request": req})
            await self.to_crew({"t": "request", "request": req})
        elif kind == "ack":
            ann = f.ack_announcement(msg.get("ann_id", ""), seat)
            await self.to_crew({"t": "announcement", "announcement": ann})
        elif kind == "exit_answer":
            chk = f.answer_exit_check(msg.get("check_id", ""), seat,
                                      bool(msg.get("willing")), str(msg.get("answer", "")))
            await self.to_seat(seat, {"t": "exit_done", "state": chk["seats"][seat]["state"]})
            await self.to_crew({"t": "exit", "exit": chk})
        elif kind == "ping":
            await self.to_seat(seat, {"t": "pong"})

    # ---- crew side -----------------------------------------------------------------
    async def crew_connect(self, ws: WebSocket) -> None:
        self.crew.add(ws)
        await self._send(ws, {"t": "snapshot", **self.flight.snapshot()})

    def crew_disconnect(self, ws: WebSocket) -> None:
        self.crew.discard(ws)

    async def handle_crew(self, msg: dict) -> None:
        f = self.flight
        kind = msg.get("t")
        if kind == "seen":
            req = f.mark_seen(msg.get("req_id", ""))
            await self._request_changed(req)
        elif kind == "reply":
            req = f.add_reply(msg.get("req_id", ""), msg.get("reply_id", ""))
            await self._request_changed(req)
        elif kind == "done":
            req = f.finish(msg.get("req_id", ""))
            await self._request_changed(req)
        elif kind == "announce":
            ann = f.create_announcement(msg.get("phrase_id"), msg.get("target") or {"all": True},
                                        msg.get("custom"))
            await self.to_crew({"t": "announcement", "announcement": ann})
            for seat in ann["acks"]:
                await self.to_seat(seat, {"t": "announce", "announcement": ann})
        elif kind == "exit_start":
            chk = f.start_exit_check(int(msg.get("row", 0)))
            await self.to_crew({"t": "exit", "exit": chk})
            for seat in chk["seats"]:
                await self.to_seat(seat, {"t": "exit_check", "check": chk})
        elif kind == "exit_resolve":
            chk = f.resolve_exit_seat(msg.get("check_id", ""), msg.get("seat", ""),
                                      bool(msg.get("ok")))
            await self.to_crew({"t": "exit", "exit": chk})
        elif kind == "landing":
            await self.land()

    async def _request_changed(self, req: dict) -> None:
        await self.to_crew({"t": "request", "request": req})
        await self.to_seat(req["seat"], {"t": "request", "request": req})

    async def land(self) -> None:
        """Wipe everything for this flight and tell every device."""
        self.flight.reset()
        await self.to_crew({"t": "snapshot", **self.flight.snapshot(), "landed": True})
        for seat in list(self.passengers):
            await self.to_seat(seat, {"t": "landed"})
