"""Speech synthesis, cabin-noise generation and mixing for the benchmark."""
from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np

SR = 16000
CACHE = Path(__file__).resolve().parent / ".cache"

# name -> (engine, voice, edge rate, edge pitch, speed factor for the resampling variant)
SPEAKERS = {
    "hi": {
        "hi-swara": ("edge", "hi-IN-SwaraNeural", "+0%", "+0Hz", 1.0),
        "hi-madhur": ("edge", "hi-IN-MadhurNeural", "+0%", "+0Hz", 1.0),
        "hi-madhur-fast": ("edge", "hi-IN-MadhurNeural", "+15%", "-8Hz", 1.0),
    },
    "pa": {
        "pa-gtts": ("gtts", "pa", "", "", 1.0),
        "pa-gtts-slow": ("gtts", "pa", "", "", 0.9),
        "pa-gtts-quick": ("gtts", "pa", "", "", 1.12),
    },
}


def decode(path: Path) -> np.ndarray:
    from faster_whisper.audio import decode_audio
    return decode_audio(str(path), sampling_rate=SR)


def synth(lang: str, speaker: str, text: str, key: str) -> np.ndarray:
    """Return 16 kHz mono float32 speech; cached on disk so reruns are fast."""
    CACHE.mkdir(exist_ok=True)
    engine, voice, rate, pitch, speed = SPEAKERS[lang][speaker]
    base = CACHE / f"{engine}-{voice}-{rate}-{pitch}-{key}.mp3".replace("%", "p").replace("+", "")
    if not base.exists() or base.stat().st_size < 500:
        if engine == "edge":
            import edge_tts
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(base)))
        else:
            from gtts import gTTS
            gTTS(text=text, lang=voice).save(str(base))
    pcm = decode(base)
    if speed != 1.0:  # crude speaker variant: changes tempo and pitch together
        n = int(len(pcm) / speed)
        pcm = np.interp(np.linspace(0, len(pcm) - 1, n), np.arange(len(pcm)), pcm).astype(np.float32)
    return pcm


def cabin_noise(n: int, rng: np.random.Generator, babble: list[np.ndarray] | None = None) -> np.ndarray:
    """Engine and air-flow rumble (steady, low heavy) plus faint voices from other seats."""
    white = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(white)
    f = np.fft.rfftfreq(n, 1 / SR)
    shape = 1.0 / np.maximum(f, 40.0) ** 0.9           # pink-ish, heavy below 500 Hz
    shape *= 1.0 / (1.0 + (f / 3500.0) ** 2)             # roll off the highs
    engine = np.fft.irfft(spec * shape, n)
    t = np.arange(n) / SR
    for hz, amp in ((110, 0.5), (220, 0.3), (330, 0.15)):  # fan and engine tones
        engine += amp * engine.std() * np.sin(2 * np.pi * hz * t + rng.uniform(0, 6.28))
    out = engine / (engine.std() + 1e-9)
    if babble:
        mix = np.zeros(n, dtype=np.float32)
        for clip in babble[:3]:
            start = int(rng.integers(0, max(1, len(clip))))
            seg = np.resize(np.roll(clip, -start), n)
            mix += seg / (seg.std() + 1e-9)
        out = 0.8 * out + 0.45 * mix / (mix.std() + 1e-9)
    return (out / (out.std() + 1e-9)).astype(np.float32)


def mix_snr(speech: np.ndarray, noise: np.ndarray, snr_db: float | None) -> np.ndarray:
    """Add noise so that speech power / noise power equals snr_db. None means clean."""
    if snr_db is None:
        return speech
    pad = SR // 2  # half a second of noise-only lead in and out, like a real push-to-talk clip
    sp = np.concatenate([np.zeros(pad, np.float32), speech, np.zeros(pad, np.float32)])
    n = noise[: len(sp)] if len(noise) >= len(sp) else np.resize(noise, len(sp))
    p_speech = float(np.mean(speech ** 2)) + 1e-12
    gain = np.sqrt(p_speech / (10 ** (snr_db / 10)) / (float(np.mean(n ** 2)) + 1e-12))
    out = sp + gain * n
    peak = float(np.max(np.abs(out)))
    return (out / peak * 0.9).astype(np.float32) if peak > 0.99 else out.astype(np.float32)
