"""End-to-end over real WebSockets using the FastAPI test client."""
import os

os.environ["HASHI_ASR"] = "none"
os.environ["HASHI_ASR_PRELOAD"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from hashi.main import app, hub  # noqa: E402


@pytest.fixture()
def client():
    hub.flight.reset()
    with TestClient(app) as c:
        yield c


def test_health(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True


def test_catalog_endpoint(client):
    body = client.get("/api/catalog").json()
    assert len(body["intents"]) >= 38 and body["replies"] and body["announcements"]


def test_match_endpoint(client):
    out = client.post("/api/match", json={"text": "mujhe pani chahiye"}).json()
    assert out["candidates"][0]["intent"] == "water"


def test_bad_seat_rejected(client):
    from starlette.websockets import WebSocketDisconnect
    with client.websocket_connect("/ws/passenger?seat=ZZ") as ws:
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_request_reply_understood_flow(client):
    with client.websocket_connect("/ws/crew") as crew:
        assert crew.receive_json()["t"] == "snapshot"
        with client.websocket_connect("/ws/passenger?seat=24C") as pax:
            pax.send_json({"t": "hello", "lang": "pa", "senior": True})
            assert pax.receive_json()["t"] == "welcome"
            assert crew.receive_json()["t"] == "passenger"

            pax.send_json({"t": "request", "intent": "water", "via": "tap"})
            assert pax.receive_json()["t"] == "request"
            msg = crew.receive_json()
            assert msg["t"] == "request" and msg["request"]["seat"] == "24C"
            req_id = msg["request"]["id"]

            crew.send_json({"t": "seen", "req_id": req_id})
            assert pax.receive_json()["request"]["status"] == "seen"
            crew.receive_json()

            crew.send_json({"t": "reply", "req_id": req_id, "reply_id": "bringing"})
            got = pax.receive_json()["request"]
            assert got["status"] == "replied" and got["replies"][0]["reply"] == "bringing"
            crew.receive_json()

            pax.send_json({"t": "understood", "req_id": req_id})
            assert pax.receive_json()["request"]["understood_at"] is not None
            assert crew.receive_json()["request"]["understood_at"] is not None


def test_announcement_reaches_passenger_and_ack_returns(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=10A") as pax:
            pax.send_json({"t": "hello", "lang": "hi"})
            pax.receive_json()
            crew.receive_json()
            crew.send_json({"t": "announce", "phrase_id": "seatbelt_on", "target": {"all": True}})
            assert crew.receive_json()["t"] == "announcement"
            ann = pax.receive_json()["announcement"]
            pax.send_json({"t": "ack", "ann_id": ann["id"]})
            updated = crew.receive_json()["announcement"]
            assert updated["acks"]["10A"]["state"] == "understood"


def test_landing_wipes_state(client):
    with client.websocket_connect("/ws/passenger?seat=5A") as pax:
        pax.send_json({"t": "hello", "lang": "pa"})
        pax.receive_json()
        assert hub.flight.passengers
        assert client.post("/api/landing").json()["ok"]
        assert pax.receive_json()["t"] == "landed"
    assert not hub.flight.passengers


def test_voice_without_engine_falls_back_to_tiles(client):
    out = client.post("/api/voice", files={"audio": ("a.wav", b"RIFF....", "audio/wav")},
                      data={"lang": "pa"}).json()
    assert out["ok"] is False and out["mode"] == "tiles"


def test_exit_check_flow(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=24A") as pax:
            pax.send_json({"t": "hello", "lang": "hi"})
            pax.receive_json()
            crew.receive_json()
            crew.send_json({"t": "exit_start", "row": 24})
            chk = crew.receive_json()["exit"]
            assert pax.receive_json()["t"] == "exit_check"
            pax.send_json({"t": "exit_answer", "check_id": chk["id"], "willing": True,
                           "answer": "right_away"})
            assert pax.receive_json()["state"] == "retry"
            assert crew.receive_json()["exit"]["seats"]["24A"]["state"] == "retry"
            crew.send_json({"t": "exit_resolve", "check_id": chk["id"], "seat": "24A", "ok": True})
            assert crew.receive_json()["exit"]["seats"]["24A"]["state"] == "passed"


def test_urgent_request_is_flagged_new_to_crew(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=12F") as pax:
            pax.send_json({"t": "request", "intent": "unwell", "via": "tap"})
            pax.receive_json()
            msg = crew.receive_json()
            assert msg["new"] is True and msg["request"]["urgency"] == 3


def test_tap_reaches_crew_well_inside_two_seconds(client):
    import time
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=8A") as pax:
            started = time.perf_counter()
            pax.send_json({"t": "request", "intent": "water", "via": "tap"})
            crew.receive_json()
            assert time.perf_counter() - started < 0.5


def test_crew_pin_protects_crew_socket_and_landing(client, monkeypatch):
    from starlette.websockets import WebSocketDisconnect

    import hashi.main as main
    monkeypatch.setattr(main, "CREW_PIN", "4321")
    assert client.get("/api/health").json()["crew_pin_required"] is True
    with client.websocket_connect("/ws/crew?pin=0000") as ws:
        with pytest.raises(WebSocketDisconnect) as err:
            ws.receive_json()
        assert err.value.code == 4401
    with client.websocket_connect("/ws/crew?pin=4321") as ws:
        assert ws.receive_json()["t"] == "snapshot"
    assert client.post("/api/landing").status_code == 401
    assert client.post("/api/landing", headers={"X-Crew-Pin": "4321"}).status_code == 200
