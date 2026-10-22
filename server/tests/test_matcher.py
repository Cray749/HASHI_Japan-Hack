import pytest

from hashi.matcher import get_matcher
from hashi.phonetic import phonetic_key


def test_scripts_fold_to_the_same_sound():
    assert phonetic_key("पानी") == phonetic_key("ਪਾਣੀ") == phonetic_key("paani") == "pani"
    assert phonetic_key("मदद करो") == phonetic_key("ਮਦਦ ਕਰੋ") == phonetic_key("madad karo")


CASES = [
    ("mujhe pani chahiye", "water"),
    ("पानी दे दो", "water"),
    ("ਮੈਨੂੰ ਪਾਣੀ ਦਿਓ", "water"),
    ("mainu kambal chahida", "blanket"),
    ("ਮੈਨੂੰ ਕੰਬਲ ਚਾਹੀਦਾ ਹੈ ਜੀ", "blanket"),
    ("dawai khani hai", "medicine"),
    ("seene me dard", "chest_pain"),
    ("bachao", "help"),
    ("mujhe chakkar aa rahe hain", "dizzy"),
    ("mainu thand lagdi e", "too_cold"),
    ("khana kab milega", "meal_time"),
    ("mera phone charge karna hai", "charger"),
    ("मुझे अभी मदद चाहिए", "help"),
    ("ਸਾਹ ਲੈਣ ਵਿੱਚ ਤਕਲੀਫ਼ ਹੈ", "breathing"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_top_match(text, expected):
    assert get_matcher().match(text).candidates[0].intent == expected


def test_returns_top_three_with_scores():
    m = get_matcher().match("mujhe paani chahiye")
    assert len(m.candidates) == 3
    assert m.candidates[0].score >= m.candidates[1].score >= m.candidates[2].score


def test_gibberish_falls_back_to_tiles():
    m = get_matcher().match("asdf qwer zxcv")
    assert m.mode == "tiles"


def test_empty_text_is_safe():
    assert get_matcher().match("   ").mode == "tiles"


def test_urgent_request_is_sent_without_waiting():
    assert get_matcher().match("seene me dard").mode == "send"


def test_unsure_match_asks_for_confirmation():
    # two intents share these words, so the matcher must not guess
    m = get_matcher().match("light")
    assert m.mode in ("confirm", "tiles")


def test_collapse_repeats():
    from hashi.phonetic import collapse_repeats
    assert collapse_repeats("a a a a".split()) == ["a"]
    assert collapse_repeats("a b a b a b c".split()) == ["a", "b", "c"]
    assert collapse_repeats("mujhe pani do".split()) == ["mujhe", "pani", "do"]


def test_engine_loop_is_never_sent_without_confirmation():
    loop = "तबीयत नहीं है, " * 6
    m = get_matcher().match(loop)
    assert m.suspect and m.mode != "send"


def test_real_repeated_plea_still_goes_through():
    assert get_matcher().match("bachao bachao bachao").mode == "send"
