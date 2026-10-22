"""HASHI cabin server: one process serves the API, the WebSockets and both web apps."""
from __future__ import annotations

import logging
import os
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

from . import asr, voice
from .demo import seed as seed_demo
from .hub import Hub
from .intents import DATA_DIR, LANGS, announcements, catalog, greetings
from .matcher import get_matcher
from .netinfo import candidate_ips, lan_ip

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
    return {"langs": list(LANGS), "intents": [i.public() for i in cat.intents.values()],
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
                  cleanup: str = Form("1")):
    data = audio.file.read(4_000_000)
    try:
        return voice.process_audio(data, lang if lang in ("hi", "pa", "en") else "hi",
                                   cleanup == "1")
    except Exception as exc:  # any failure: the passenger app shows the picture tiles
        log.warning("voice failed: %s", exc)
        return JSONResponse({"ok": False, "error": "failed", "mode": "tiles",
                             "candidates": []})


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
    svg = segno.make(url, error="m").svg_inline(scale=6, border=2, dark="#0E1A3A")
    return Response(svg, media_type="image/svg+xml")


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
