"""Optional: isolate the vocal stem with Demucs.

Needs ``pip install -U demucs`` (and torch). Only used by
:func:`lyric_mv.align.force_align` — the renderer itself never touches it, so
you can skip this entirely if you already have an acapella or are happy with
auto-distributed timings.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def separate(audio: Path | str, outdir: Path | str, model: str = "htdemucs",
             device: str | None = None) -> Path:
    """Run Demucs and return the directory holding the separated stems."""
    audio = Path(audio).resolve()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = ["python", "-m", "demucs", "-n", model, "-o", str(outdir), str(audio)]
    if device:
        cmd += ["-d", device]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise SystemExit("demucs failed:\n" + p.stderr.decode(errors="replace")[-3000:])
    return outdir / model / audio.stem


def vocals(audio: Path | str, outdir: Path | str, model: str = "htdemucs",
           device: str | None = None) -> Path:
    """Return the path to ``vocals.wav``, separating first if needed."""
    stem_dir = separate(audio, outdir, model=model, device=device)
    v = stem_dir / "vocals.wav"
    if not v.is_file():
        raise SystemExit(f"expected vocal stem not found: {v}")
    return v
