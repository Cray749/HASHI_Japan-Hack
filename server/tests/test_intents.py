"""Data checks: every request has all four labels, urgent ones are routed, banks are filled."""
import pytest

from hashi.intents import announcements, catalog, greetings

LANGS = tuple(catalog().langs) + ("ja",)  # every passenger language plus the crew language


def test_about_forty_intents():
    assert 38 <= len(catalog().intents) <= 46


@pytest.mark.parametrize("intent", list(catalog().intents.values()), ids=lambda i: i.id)
def test_every_intent_has_all_labels(intent):
    for lang in LANGS:
        assert intent.labels[lang].strip(), f"{intent.id} missing {lang}"
    assert intent.urgency in (1, 2, 3)
    assert intent.replies, f"{intent.id} has no reply options"


def test_reply_ids_exist():
    cat = catalog()
    for intent in cat.intents.values():
        for rid in intent.replies:
            assert rid in cat.replies, f"{intent.id} -> unknown reply {rid}"


def test_replies_have_all_languages():
    for reply in catalog().replies.values():
        for lang in LANGS:
            assert reply["text"][lang].strip()


def test_phrase_bank_covers_every_intent():
    cat = catalog()
    assert set(cat.phrases) == set(cat.intents)
    for intent_id, banks in cat.phrases.items():
        assert len(banks["rom"]) >= 5, intent_id
        assert len(banks["hi"]) >= 3 and len(banks["pa"]) >= 3, intent_id


def test_medical_looking_requests_are_urgent():
    cat = catalog().intents
    for key in ("help", "unwell", "chest_pain", "breathing", "dizzy", "injury", "smoke"):
        assert cat[key].urgency == 3


def test_home_grid_has_help_tile():
    tiles = [i.id for i in catalog().intents.values() if i.tile]
    assert "help" in tiles and 5 <= len(tiles) <= 8


def test_announcements_and_greetings_complete():
    for ann in announcements():
        for lang in LANGS:
            assert ann["text"][lang].strip()
    langs = {g["lang"] for g in greetings()}
    assert {"hi", "pa"} <= langs
    for g in greetings():
        for item in g["items"]:
            assert item["katakana"] and item["script"]


def test_language_packs_are_complete_and_marked_draft():
    cat = catalog()
    assert len(cat.languages) >= 17
    for lang in cat.languages:
        assert lang["status"] in ("draft", "reviewed")
    for code in cat.langs:
        for intent in cat.intents.values():
            assert intent.labels.get(code, "").strip(), f"{code} missing label for {intent.id}"
        for reply in cat.replies.values():
            assert reply["text"].get(code, "").strip(), f"{code} missing reply {reply['id']}"
        for ann in announcements():
            assert ann["text"].get(code, "").strip(), f"{code} missing announcement {ann['id']}"
    for code, ui in cat.ui.items():
        for key in ("askWhat", "understood", "helpBig", "consent1", "consent2", "start", "sent", "seen"):
            assert ui.get(key, "").strip(), f"{code} missing interface string {key}"
