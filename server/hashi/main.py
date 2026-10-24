"""HASHI cabin server: one process serves the API, the WebSockets and both web apps."""
from __future__ import annotations

import io
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import segno
from fastapi import (
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import asr, noise, translate, voice
from .demo import seed as seed_demo
from .hub import Hub
from .intents import DATA_DIR, announcements, catalog, greetings
from .matcher import get_matcher
from .netinfo import candidate_ips, lan_ip
from .phonetic import phonetic_key
from .store import clean_seat

log = logging.getLogger("hashi")
ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = Path(os.environ.get("HASHI_WEB", ROOT / "web" / "dist"))
VERSION = "0.1.0"
CREW_PIN = os.environ.get("HASHI_CREW_PIN", "")  # optional: protects the crew tablet

hub = Hub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_matcher()  # build the index once at start
    if os.environ.get("HASHI_DEMO") == "1":
        seed_demo(hub.flight)
    if os.environ.get("HASHI_ASR_PRELOAD", "1") == "1":
        asr.preload()
    yield


app = FastAPI(title="HASHI cabin server", version=VERSION, lifespan=lifespan)


# ---- REST ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    backend = asr._backend  # may still be loading
    return {"ok": True, "version": VERSION, "asr": backend.name if backend else "loading",
            "asr_ready": bool(backend and backend.ready), "crew_pin_required": bool(CREW_PIN),
            "passengers": len(hub.flight.passengers),
            "crew_connected": len(hub.crew)}


@app.get("/api/catalog")
def get_catalog():
    cat = catalog()
    return {"langs": cat.langs, "languages": cat.languages, "ui": cat.ui, "intents": [i.public() for i in cat.intents.values()],
            "replies": list(cat.replies.values()), "announcements": announcements(),
            "greetings": greetings()}


class MatchIn(BaseModel):
    text: str


@app.post("/api/match")
def match_text(body: MatchIn):
    """Text to intent. Used by tests, the benchmark and the 'type instead' fallback."""
    return voice.understand(body.text[:300])


@app.post("/api/voice")
def voice_request(audio: UploadFile = File(...), lang: str = Form("hi"),
                  cleanup: str = Form("0")):
    data = audio.file.read(4_000_000)
    try:
        return voice.process_audio(data, lang if lang in catalog().langs else "hi", cleanup == "1")
    except Exception as exc:  # any failure: the passenger app shows the picture tiles
        log.warning("voice failed: %s", exc)
        return JSONResponse({"ok": False, "error": "failed", "mode": "tiles",
                             "candidates": []})


class TranslateIn(BaseModel):
    text: str
    src: str
    tgt: str


def _translate(text: str, src: str, tgt: str) -> str | None:
    if src not in translate.NLLB_CODE or tgt not in translate.NLLB_CODE:
        return None
    tr = translate.get_translator()
    return tr.translate(text[:400], src, tgt) if tr else None


@app.get("/api/live/info")
def live_info():
    """What the live translator page can do on this machine."""
    return {"translate": translate.available(), "languages": list(translate.NLLB_CODE)}


@app.post("/api/translate")
def translate_text(body: TranslateIn):
    out = _translate(body.text, body.src, body.tgt)
    if out is None:
        raise HTTPException(503, "translation model not installed (python scripts/get_nllb.py)")
    return {"text": out, "note": "machine translation, unverified"}


@app.post("/api/live")
def live_audio(audio: UploadFile = File(...), src: str = Form("hi"), tgt: str = Form("ja"),
               cleanup: str = Form("0")):
    """Speak, see every step of what the system did. Audio is processed in memory only."""
    t_all = time.time()
    data = audio.file.read(4_000_000)
    steps: dict = {}
    try:
        pcm = voice.decode_wav(data)
        backend = asr.get_backend()
        if not backend.ready or len(pcm) < 4800:
            return {"ok": False, "error": "no_speech"}
        steps["received"] = {"seconds": round(len(pcm) / voice.TARGET_SR, 1)}
        use_cleanup = cleanup == "1"
        t = time.time()
        if use_cleanup:
            pcm = noise.clean(pcm)
        steps["noise"] = {"applied": use_cleanup, "ms": int((time.time() - t) * 1000)}
        t = time.time()
        res = backend.transcribe(pcm, src)
        heard = res.text
        steps["asr"] = {"engine": backend.name, "ms": int((time.time() - t) * 1000)}
        english = None
        if tgt == "en" and src != "en" and heard.strip():
            english = backend.transcribe(pcm, src, task="translate").text  # Whisper's own translate task
    except Exception as exc:
        log.warning("live failed: %s", exc)
        return {"ok": False, "error": "failed"}
    del pcm, data  # the recording is dropped here; nothing was written to disk
    out = {"ok": True, "heard": heard, "tgt": tgt, "translation": None, "translator": None, "match": None,
           "steps": steps}
    if heard.strip():
        t = time.time()
        words = phonetic_key(heard)
        steps["fold"] = {"sound_form": words}
        m = voice.understand(heard)
        steps["match"] = {"ms": int((time.time() - t) * 1000), "mode": m["mode"], "suspect": m.get("suspect", False),
                          "candidates": [{"intent": c["intent"], "score": c["score"],
                                          "ja": catalog().intents[c["intent"]].labels["ja"],
                                          "en": catalog().intents[c["intent"]].labels["en"]}
                                         for c in m["candidates"]]}
        top = m["candidates"][0] if m["candidates"] else None
        if top and m["mode"] != "tiles":
            intent = catalog().intents[top["intent"]]
            mode = m["mode"] if src in voice.VALIDATED_VOICE or m["mode"] == "tiles" else "confirm"
            out["match"] = {"intent": intent.id, "ja": intent.labels["ja"], "en": intent.labels["en"],
                            "confidence": m["confidence"], "mode": mode}
        t = time.time()
        tr = _translate(heard, src, tgt)
        if tr:
            out["translation"], out["translator"] = tr, "NLLB-200 600M"
        elif english:
            out["translation"], out["translator"] = english, "Whisper translate (to English)"
        steps["translate"] = {"ms": int((time.time() - t) * 1000), "model": out["translator"]}
    steps["discarded"] = True
    steps["total_ms"] = int((time.time() - t_all) * 1000)
    return out


class SendIn(BaseModel):
    seat: str
    intent: str


@app.post("/api/live/send")
async def live_send(body: SendIn):
    """Send a recognised request to the crew tablet as if the passenger had confirmed it."""
    try:
        await hub.handle_passenger(clean_seat(body.seat), {"t": "request", "intent": body.intent, "via": "voice"})
    except (ValueError, KeyError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True}


@app.get("/api/join")
def join_info(request_host: str | None = None):
    port = int(os.environ.get("HASHI_PORT", "8000"))
    scheme = os.environ.get("HASHI_SCHEME", "http")
    url = f"{scheme}://{lan_ip()}:{port}/p/"
    return {"url": url, "crew_url": f"{scheme}://{lan_ip()}:{port}/crew/",
            "others": [f"{scheme}://{ip}:{port}/p/" for ip in candidate_ips() if ip != lan_ip()]}


@app.get("/api/qr.svg")
def qr(seat: str = ""):
    port = int(os.environ.get("HASHI_PORT", "8000"))
    scheme = os.environ.get("HASHI_SCHEME", "http")
    url = f"{scheme}://{lan_ip()}:{port}/p/" + (f"?seat={seat}" if seat else "")
    buf = io.BytesIO()
    # svgns=True writes the xmlns attribute; without it the browser will not draw the file in an <img>
    segno.make(url, error="m").save(buf, kind="svg", scale=6, border=2, dark="#0E1A3A", xmldecl=False, svgns=True)
    return Response(buf.getvalue(), media_type="image/svg+xml")


@app.post("/api/landing")
async def landing(x_crew_pin: str = Header("")):
    if CREW_PIN and x_crew_pin != CREW_PIN:
        raise HTTPException(401, "crew PIN needed")
    await hub.land()
    return {"ok": True}


# ---- WebSockets ---------------------------------------------------------------------
@app.websocket("/ws/passenger")
async def ws_passenger(ws: WebSocket, seat: str = ""):
    await ws.accept()
    try:
        seat = await hub.passenger_connect(ws, seat)
    except ValueError:
        await ws.close(code=4400)
        return
    try:
        while True:
            msg = await ws.receive_json()
            try:
                await hub.handle_passenger(seat, msg)
            except (ValueError, KeyError, PermissionError) as exc:
                await ws.send_json({"t": "error", "error": str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.passenger_disconnect(ws, seat)


@app.websocket("/ws/crew")
async def ws_crew(ws: WebSocket, pin: str = ""):
    await ws.accept()
    if CREW_PIN and pin != CREW_PIN:
        await ws.close(code=4401)  # the tablet sees this code and asks for the PIN again
        return
    await hub.crew_connect(ws)
    try:
        while True:
            msg = await ws.receive_json()
            try:
                await hub.handle_crew(msg)
            except (ValueError, KeyError, PermissionError) as exc:
                await ws.send_json({"t": "error", "error": str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        hub.crew_disconnect(ws)


# ---- static files -------------------------------------------------------------------
@app.get("/")
def home():
    return RedirectResponse("/p/")


(DATA_DIR / "audio").mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=DATA_DIR / "audio"), name="audio")

if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:
    @app.get("/p/")
    @app.get("/crew/")
    def not_built():
        raise HTTPException(503, "Web apps are not built yet. Run: cd web && npm run build")
