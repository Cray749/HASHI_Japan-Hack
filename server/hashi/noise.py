"""Light spectral-gating noise cleanup (numpy only, no model download).

Cabin noise is mostly steady engine and air-flow rumble. For each frequency band we
estimate that steady level from the quietest frames, then turn down time-frequency cells
that are not clearly louder than it. This is the fallback named in the plan; a trained
suppressor such as RNNoise can replace `clean` behind the same signature.
"""
from __future__ import annotations

import numpy as np

N_FFT = 512
HOP = 128


def _stft(x: np.ndarray) -> np.ndarray:
    win = np.hanning(N_FFT).astype(np.float32)
    pad = N_FFT // 2
    x = np.pad(x, (pad, pad))
    n = 1 + (len(x) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.fft.rfft(x[idx] * win, axis=1)


def _istft(spec: np.ndarray, length: int) -> np.ndarray:
    win = np.hanning(N_FFT).astype(np.float32)
    frames = np.fft.irfft(spec, n=N_FFT, axis=1) * win
    out = np.zeros(HOP * (len(frames) - 1) + N_FFT, dtype=np.float32)
    norm = np.zeros_like(out)
    for i, fr in enumerate(frames):
        out[i * HOP:i * HOP + N_FFT] += fr
        norm[i * HOP:i * HOP + N_FFT] += win * win
    out /= np.maximum(norm, 1e-6)
    pad = N_FFT // 2
    return out[pad:pad + length]


def _smooth(m: np.ndarray) -> np.ndarray:
    k = np.ones((3, 3), dtype=np.float32) / 9
    padded = np.pad(m, 1, mode="edge")
    out = np.zeros_like(m)
    for dy in range(3):
        for dx in range(3):
            out += k[dy, dx] * padded[dy:dy + m.shape[0], dx:dx + m.shape[1]]
    return out


def clean(pcm: np.ndarray, sr: int = 16000, strength: float = 1.6) -> np.ndarray:
    """Return a denoised copy of float32 mono audio in [-1, 1]."""
    if len(pcm) < N_FFT * 2:
        return pcm
    pcm = pcm.astype(np.float32)
    spec = _stft(pcm)
    mag = np.abs(spec)
    noise = np.percentile(mag, 25, axis=0) * strength
    mask = np.clip((mag - noise[None, :]) / np.maximum(mag, 1e-8), 0.0, 1.0)
    mask = np.clip(_smooth(mask), 0.08, 1.0)  # a floor avoids "underwater" artefacts
    hz = np.fft.rfftfreq(N_FFT, 1 / sr)
    mask[:, hz < 80] = 0.0                      # drop rumble below 80 Hz
    out = _istft(spec * mask, len(pcm))
    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * min(1.0, float(np.max(np.abs(pcm))) / peak)).astype(np.float32)
