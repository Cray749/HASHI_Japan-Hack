import pytest

from hashi.store import Flight, clean_seat


def test_seat_validation():
    assert clean_seat(" 24c ") == "24C"
    with pytest.raises(ValueError):
        clean_seat("ZZ99")


def test_request_lifecycle():
    f = Flight()
    f.register("24C", lang="pa")
    req, is_new = f.create_request("24C", "water")
    assert is_new and req["status"] == "new" and req["lang"] == "pa"
    f.mark_seen(req["id"])
    assert req["status"] == "seen"
    f.add_reply(req["id"], "bringing")
    assert req["status"] == "replied" and req["understood_at"] is None
    f.understood(req["id"], "24C")
    assert req["understood_at"] is not None
    f.finish(req["id"])
    assert req["status"] == "done"


def test_double_tap_is_ignored():
    f = Flight()
    first, new1 = f.create_request("12F", "help")
    second, new2 = f.create_request("12F", "help")
    assert new1 and not new2 and first["id"] == second["id"]


def test_cannot_touch_someone_elses_request():
    f = Flight()
    req, _ = f.create_request("12F", "water")
    with pytest.raises(PermissionError):
        f.understood(req["id"], "13A")


def test_unknown_intent_rejected():
    with pytest.raises(ValueError):
        Flight().create_request("12F", "teleport")


def test_announcement_ack_tracking():
    f = Flight()
    for seat in ("24A", "24B", "30C"):
        f.register(seat)
    ann = f.create_announcement("seatbelt_on", {"rows": [24]})
    assert set(ann["acks"]) == {"24A", "24B"}
    f.ack_announcement(ann["id"], "24A")
    assert ann["acks"]["24A"]["state"] == "understood"
    assert ann["acks"]["24B"]["state"] == "sent"
    assert [a["id"] for a in f.pending_announcements("24B")] == [ann["id"]]
    # a passenger who joins later still gets a flight-wide announcement
    ann_all = f.create_announcement("meal_service", {"all": True})
    f.register("40A")
    assert ann_all["acks"]["40A"]["state"] == "sent"


def test_exit_row_check_states():
    f = Flight()
    for seat in ("24A", "24B", "24C"):
        f.register(seat)
    chk = f.start_exit_check(24)
    f.answer_exit_check(chk["id"], "24A", True, "when_told")
    f.answer_exit_check(chk["id"], "24B", True, "right_away")
    f.answer_exit_check(chk["id"], "24C", False, "")
    assert chk["seats"]["24A"]["state"] == "passed"
    assert chk["seats"]["24B"]["state"] == "retry"
    assert chk["seats"]["24C"]["state"] == "unwilling"
    f.resolve_exit_seat(chk["id"], "24B", True)
    assert chk["seats"]["24B"]["state"] == "passed"


def test_reset_wipes_everything():
    f = Flight()
    f.register("1A")
    f.create_request("1A", "water")
    f.reset()
    assert not f.passengers and not f.requests
