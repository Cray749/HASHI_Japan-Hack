"""Message hub: keeps the open WebSockets and turns messages into store changes.

Two kinds of clients connect: passenger phones (one per seat) and crew tablets. Every
change is pushed straight to whoever needs it, so a request shows on the crew tablet
within a fraction of a second on the local network.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket

from . import translate
from .intents import catalog
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
                "exit_check": f.pending_exit_check(seat),
                "checkin": f.pending_checkin(seat),
                "thread": f.threads.get(seat, [])[-30:]}

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
        elif kind == "say":
            await self._passenger_say(seat, str(msg.get("text", "")))
        elif kind == "say_confirm":
            m = f.get_message(seat, msg.get("id", ""))
            if m["status"] == "pending":
                m["status"] = "sent"
                await self.to_seat(seat, {"t": "say_sent", "msg": m})
                await self.to_crew({"t": "say", "msg": m})
        elif kind == "say_cancel":
            m = f.get_message(seat, msg.get("id", ""))
            if m["status"] == "pending":
                m["status"] = "cancelled"
                await self.to_seat(seat, {"t": "say_sent", "msg": m})
        elif kind == "checkin_answer":
            c = f.answer_checkin(seat, str(msg.get("answer", "")))
            await self.to_seat(seat, {"t": "checkin_done", "checkin": c})
            await self.to_crew({"t": "checkin", "checkin": c})
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
        elif kind == "crew_say":
            await self._crew_say(msg.get("seat", ""), str(msg.get("text", "")), str(msg.get("src", "ja")))
        elif kind == "announce_text":
            await self._announce_text(str(msg.get("text", "")), msg.get("target") or {"all": True})
        elif kind == "checkin":
            c = f.start_checkin(msg.get("seat", ""))
            await self.to_crew({"t": "checkin", "checkin": c})
            await self.to_seat(c["seat"], {"t": "checkin", "checkin": c})
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


    # ---- live two-way conversation (machine translation lane) -------------------------
    async def _passenger_say(self, seat: str, text: str) -> None:
        """Passenger text (typed or recognised) -> Japanese for the crew, checked by translating it back."""
        text = text.strip()[:300]
        if not text:
            raise ValueError("empty message")
        lang = self.flight.passengers[seat].lang if seat in self.flight.passengers else "en"
        try:
            ja = await asyncio.to_thread(translate.translate_text, text, lang, "ja")
            back = await asyncio.to_thread(translate.translate_text, ja, "ja", lang)
        except translate.NotReady:
            await self.to_seat(seat, {"t": "say_error", "error": "model_not_ready"})
            return
        score = translate.round_trip_score(text, back)
        m = self.flight.add_message(seat, "passenger", original=text, lang=lang, ja=ja, back=back,
                                    score=score, warn=score < 55, lane="machine", status="pending")
        await self.to_seat(seat, {"t": "say_check", "msg": m})

    async def _crew_say(self, seat: str, text: str, src: str) -> None:
        """Crew text (Japanese by default) -> the passenger's language. Pre-approved wording is used when it matches."""
        seat = clean_seat(seat)
        text = text.strip()[:300]
        if not text or seat not in self.flight.passengers:
            raise ValueError("nothing to send")
        lang = self.flight.passengers[seat].lang
        wanted = text.rstrip("\u3002.")
        vetted = next((r for r in catalog().replies.values() if r["text"]["ja"].rstrip("\u3002.") == wanted), None)
        if vetted is not None and lang in vetted["text"]:
            translated, back, lane = vetted["text"][lang], "", "vetted"
        else:
            try:
                translated = await asyncio.to_thread(translate.translate_text, text, src, lang)
                back = await asyncio.to_thread(translate.translate_text, translated, lang, src)
            except translate.NotReady:
                await self.to_crew({"t": "say_error", "error": "model_not_ready"})
                return
            lane = "machine"
        m = self.flight.add_message(seat, "crew", original=text, lang=lang, translated=translated, back=back, lane=lane)
        await self.to_seat(seat, {"t": "crew_say", "msg": m})
        await self.to_crew({"t": "say", "msg": m})

    async def _announce_text(self, text: str, target: dict) -> None:
        """A free announcement: translated once per language that is on board, then sent to each seat."""
        text = text.strip()[:300]
        if not text:
            raise ValueError("empty announcement")
        f = self.flight
        spec = {"all": bool(target.get("all")), "rows": [int(r) for r in target.get("rows", [])],
                "seats": target.get("seats", [])}
        langs = {p.lang for p in f.passengers.values() if f._targets(spec, p.seat)}
        texts = {"ja": text}
        try:
            for lang in langs:
                texts[lang] = await asyncio.to_thread(translate.translate_text, text, "ja", lang)
        except translate.NotReady:
            await self.to_crew({"t": "say_error", "error": "model_not_ready"})
            return
        ann = f.create_announcement(None, target, custom=text, texts=texts)
        await self.to_crew({"t": "announcement", "announcement": ann})
        for seat in ann["acks"]:
            await self.to_seat(seat, {"t": "announce", "announcement": ann})
