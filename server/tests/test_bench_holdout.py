"""The benchmark must not grade the matcher on sentences it was built from."""
from pathlib import Path

import yaml

from hashi.intents import catalog
from hashi.phonetic import phonetic_key

TESTSET = Path(__file__).resolve().parents[2] / "bench" / "testset.yaml"


def test_testset_sentences_are_not_in_the_phrase_bank():
    bank = {phonetic_key(p) for banks in catalog().phrases.values()
            for phrases in banks.values() for p in phrases}
    data = yaml.safe_load(TESTSET.read_text(encoding="utf-8"))
    leaked = [row["text"] for rows in data.values() for row in rows if phonetic_key(row["text"]) in bank]
    assert not leaked, f"test sentences also in the phrase bank: {leaked}"


def test_testset_gold_labels_exist():
    data = yaml.safe_load(TESTSET.read_text(encoding="utf-8"))
    intents = catalog().intents
    for lang, rows in data.items():
        assert len(rows) >= 20, lang
        for row in rows:
            assert row["gold"] in intents
