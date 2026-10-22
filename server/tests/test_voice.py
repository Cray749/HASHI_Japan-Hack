import io
import wave

import numpy as np
import pytest

from hashi import asr, noise, voice
from hashi.asr.base import ASRBackend, ASRResult
from hashi.demo import seed
from hashi.store import Flight


def wav_bytes(pcm: np.ndarray, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


class FakeASR(ASRBackend):
    name = "fake"

    def __init__(self, text):
        self.text = text

    def transcribe(self, pcm, lang, task="transcribe"):
        return ASRResult(text=self.text, language=lang)


@pytest.fixture()
def fake_engine(monkeypatch):
    def use(text):
        monkeypatch.setattr(asr, "_backend", FakeASR(text))
    return use


def tone(seconds=1.0, rate=16000, amp=0.3):
    t = np.arange(int(seconds * rate)) / rate
    return (amp * np.sin(2 * np.pi * 300 * t)).astype(np.float32)


def test_wav_roundtrip_and_resample():
    pcm = voice.decode_wav(wav_bytes(tone(1.0, 8000), 8000))
    assert abs(len(pcm) - 16000) < 5


def test_voice_pipeline_matches_intent(fake_engine):
    fake_engine("मुझे पानी चाहिए")
    out = voice.process_audio(wav_bytes(tone()), "hi")
    assert out["ok"] and out["candidates"][0]["intent"] == "water"
    assert out["mode"] == "send"


def test_voice_too_short_and_silent(fake_engine):
    fake_engine("pani")
    assert voice.process_audio(wav_bytes(tone(0.1)), "hi")["error"] == "too_short"
    assert voice.process_audio(wav_bytes(tone(1.0, amp=0.0)), "hi")["error"] == "silence"


def test_gibberish_falls_back_to_tiles(fake_engine):
    fake_engine("zzz qqq")
    out = voice.process_audio(wav_bytes(tone()), "pa")
    assert out["mode"] == "tiles"


def test_noise_cleanup_reduces_steady_noise():
    rng = np.random.default_rng(1)
    n = 16000 * 2
    steady = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) / np.maximum(np.arange(n // 2 + 1), 20), n)
    steady = (steady / steady.std() * 0.1).astype(np.float32)
    cleaned = noise.clean(steady)
    assert len(cleaned) == len(steady)
    assert np.isfinite(cleaned).all()
    assert cleaned.std() < steady.std()


def test_noise_cleanup_keeps_speech_like_bursts():
    # steady noise is removed, but a burst that is clearly louder (like speech) survives
    rng = np.random.default_rng(0)
    sig = np.zeros(32000, dtype=np.float32)
    sig[10000:22000] = tone(0.75, amp=0.5)
    noisy = sig + 0.01 * rng.standard_normal(len(sig)).astype(np.float32)
    cleaned = noise.clean(noisy)
    assert cleaned[10000:22000].std() > 0.5 * noisy[10000:22000].std()
    assert cleaned[:8000].std() < noisy[:8000].std()


def test_demo_profiles_seed():
    f = Flight()
    assert seed(f) >= 10
    assert f.passengers["24C"].lang == "pa" and f.passengers["24C"].senior
