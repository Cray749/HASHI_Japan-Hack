"""Live two-way conversation, tested with a stand-in translator (no model needed)."""
import os

os.environ["HASHI_ASR"] = "none"
os.environ["HASHI_ASR_PRELOAD"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from hashi import translate  # noqa: E402
from hashi.main import app, hub  # noqa: E402


class FakeMT:
    """Reversible fake: anything into Japanese gets a 'JA:' prefix, and Japanese back out removes it."""

    def translate(self, text, src, tgt):
        if src == "ja":
            return text[3:] if text.startswith("JA:") else f"[{tgt}] {text}"
        return f"JA:{text}"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(translate, "get_translator", lambda: FakeMT())
    translate._cache.clear()
    hub.flight.reset()
    with TestClient(app) as c:
        yield c


def test_passenger_message_is_checked_then_sent(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=24C") as pax:
            pax.send_json({"t": "hello", "lang": "ta"})
            pax.receive_json()
            crew.receive_json()
            pax.send_json({"t": "say", "text": "enakku thanni venum"})
            check = pax.receive_json()
            assert check["t"] == "say_check"
            assert check["msg"]["ja"] == "JA:enakku thanni venum"
            assert check["msg"]["score"] >= 90 and not check["msg"]["warn"]
            pax.send_json({"t": "say_confirm", "id": check["msg"]["id"]})
            assert pax.receive_json()["t"] == "say_sent"
            sent = crew.receive_json()
            assert sent["t"] == "say" and sent["msg"]["ja"].startswith("JA:")


def test_unconfirmed_message_never_reaches_crew(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=24C") as pax:
            pax.send_json({"t": "hello", "lang": "hi"})
            pax.receive_json()
            crew.receive_json()
            pax.send_json({"t": "say", "text": "pani chahiye"})
            check = pax.receive_json()
            pax.send_json({"t": "say_cancel", "id": check["msg"]["id"]})
            assert pax.receive_json()["msg"]["status"] == "cancelled"
            assert [m for m in hub.flight.threads["24C"] if m["status"] == "sent"] == []


def test_crew_reply_reaches_passenger_in_their_language(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=24C") as pax:
            pax.send_json({"t": "hello", "lang": "ta"})
            pax.receive_json()
            crew.receive_json()
            crew.send_json({"t": "crew_say", "seat": "24C", "text": "お席の周りに荷物はありませんか"})
            got = pax.receive_json()
            assert got["t"] == "crew_say" and got["msg"]["lane"] == "machine"
            assert got["msg"]["translated"].startswith("[ta]")


def test_pre_approved_wording_skips_machine_translation(client):
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=24C") as pax:
            pax.send_json({"t": "hello", "lang": "hi"})
            pax.receive_json()
            crew.receive_json()
            crew.send_json({"t": "crew_say", "seat": "24C", "text": "少々お待ちください。"})
            got = pax.receive_json()["msg"]
            assert got["lane"] == "vetted" and "इंतज़ार" in got["translated"]


def test_free_announcement_translated_once_per_language(client):
    calls = []
    real = FakeMT().translate

    class Counting(FakeMT):
        def translate(self, text, src, tgt):
            calls.append(tgt)
            return real(text, src, tgt)

    translate.get_translator = lambda: Counting()
    with client.websocket_connect("/ws/crew") as crew:
        crew.receive_json()
        with client.websocket_connect("/ws/passenger?seat=1A") as a, client.websocket_connect("/ws/passenger?seat=1B") as b, \
                client.websocket_connect("/ws/passenger?seat=1C") as c:
            for ws, lang in ((a, "ta"), (b, "ta"), (c, "th")):
                ws.send_json({"t": "hello", "lang": lang})
                ws.receive_json()
            for _ in range(3):
                crew.receive_json()
            crew.send_json({"t": "announce_text", "text": "ベルトをお締めください", "target": {"all": True}})
            assert crew.receive_json()["t"] == "announcement"
            for ws, lang in ((a, "ta"), (b, "ta"), (c, "th")):
                ann = ws.receive_json()["announcement"]
                assert ann["texts"][lang].startswith(f"[{lang}]")
            assert sorted(calls) == ["ta", "th"]  # two languages on board, so two translations, not three


def test_model_missing_is_reported_not_crashed(client, monkeypatch):
    monkeypatch.setattr(translate, "get_translator", lambda: None)
    with client.websocket_connect("/ws/passenger?seat=24C") as pax:
        pax.send_json({"t": "hello", "lang": "ta"})
        pax.receive_json()
        pax.send_json({"t": "say", "text": "hello"})
        assert pax.receive_json() == {"t": "say_error", "error": "model_not_ready"}
