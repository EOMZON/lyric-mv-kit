"""Audio analysis: per-frame spectrum envelope + rough tempo estimate.

Ported from the production pipeline that rendered the reference MV. Everything
is deterministic — the same input file always yields the same features, which
matters when you want reproducible renders across machines.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

SR = 22050
FFT_N = 1024
N_BANDS = 96


def decode(path: Path | str) -> np.ndarray:
    """Decode any audio to mono float32 PCM at :data:`SR` via ffmpeg."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-ac", "1", "-ar", str(SR), "-f", "f32le", "-",
    ]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"ffmpeg decode failed: {p.stderr.decode(errors='replace')}")
    return np.frombuffer(p.stdout, dtype=np.float32).astype(np.float32)


def _smooth_env(v: np.ndarray, attack: float = 0.45, decay: float = 0.88) -> np.ndarray:
    """Asymmetric smoothing: fast attack, slow decay -> punchy visuals."""
    out = np.empty_like(v)
    prev = 0.0
    for i, val in enumerate(v):
        a = attack if val > prev else decay
        prev = a * val + (1 - a) * prev
        out[i] = prev
    return out


def envelope(x: np.ndarray, fps: int, sr: int = SR) -> dict:
    """Per-frame RMS + 96-band log-spaced spectrum, all normalised to ~0..1."""
    hop = sr / fps
    nframes = int(len(x) / hop)
    idx = (np.arange(nframes) * hop).astype(np.int64)

    # --- build all analysis windows at once (stride trick) ---
    half = FFT_N // 2
    starts = np.clip(idx - half, 0, max(0, len(x) - FFT_N))
    win = np.lib.stride_tricks.sliding_window_view(x, FFT_N)
    safe = np.clip(starts, 0, len(win) - 1)
    frames = win[safe]  # (nframes, FFT_N)

    hann = np.hanning(FFT_N).astype(np.float32)
    spec = np.fft.rfft(frames * hann, axis=1)  # (nframes, FFT_N/2+1)
    mag = np.abs(spec).astype(np.float32)
    freqs = np.fft.rfftfreq(FFT_N, 1.0 / sr)

    # --- log-spaced band matrix ---
    edges = np.geomspace(30.0, min(12000.0, sr / 2 * 0.98), N_BANDS + 1)
    band = np.zeros((len(freqs), N_BANDS), dtype=np.float32)
    for b in range(N_BANDS):
        m = (freqs >= edges[b]) & (freqs < edges[b + 1])
        if not m.any():
            lo = int(np.argmin(np.abs(freqs - edges[b])))
            m = np.zeros(len(freqs), dtype=bool)
            m[lo] = True
        band[m, b] = 1.0 / max(1, m.sum())

    bands = mag @ band  # (nframes, N_BANDS)

    # perceptual-ish tilt: boost highs which are naturally quiet
    bands *= np.linspace(1.0, 3.2, N_BANDS, dtype=np.float32)

    # per-band normalisation so quiet bands stay visible
    p95 = np.percentile(bands, 95, axis=0) + 1e-9
    bands = np.clip(bands / p95, 0.0, 1.6)

    rms = np.sqrt((frames ** 2).mean(axis=1)).astype(np.float32)
    bass = bands[:, :12].mean(axis=1)
    mid = bands[:, 12:48].mean(axis=1)
    treble = bands[:, 48:].mean(axis=1)

    def norm(v):
        return _smooth_env(v / (np.percentile(v, 97) + 1e-9))

    return {
        "rms": norm(rms),
        "bass": norm(bass),
        "mid": norm(mid),
        "treble": norm(treble),
        "bands": np.apply_along_axis(_smooth_env, 0, bands),
        "raw_rms": rms,
        "fps": fps,
        "nframes": nframes,
    }


def detect_bpm(raw_rms: np.ndarray, hop_s: float, lo_bpm: int = 70, hi_bpm: int = 170) -> float:
    """Rough tempo estimate from the RMS novelty curve (autocorrelation)."""
    fps_a = 1.0 / hop_s
    e = np.diff(raw_rms, prepend=raw_rms[0]).clip(0)
    e = e / (e.std() + 1e-9)
    lo, hi = int(60.0 / hi_bpm * fps_a), int(60.0 / lo_bpm * fps_a)
    best, bl = -1e18, lo
    for l in range(lo, max(lo + 1, hi)):
        v = float(np.dot(e[:-l], e[l:]) / (len(e) - l))
        if v > best:
            best, bl = v, l
    return 60.0 * fps_a / bl


def save_features(feats: dict, out: Path | str) -> Path:
    """Write the subset the renderer reads into one compressed ``.npz``."""
    out = Path(out)
    np.savez_compressed(
        out,
        rms=feats["rms"],
        bass=feats["bass"],
        mid=feats["mid"],
        treble=feats["treble"],
        bands=feats["bands"].astype(np.float32),
    )
    return out
