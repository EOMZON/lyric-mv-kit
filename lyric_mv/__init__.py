"""lyric-mv-kit — build kinetic lyric MVs from an audio file and a lyric text.

Pure-Python frame renderer (Pillow + numpy) piped straight into ffmpeg.
No browser, no headless Chrome, no React/Remotion runtime.

Quick start
-----------
    python -m lyric_mv build-plan  --audio song.wav --lyrics lyrics.txt \\
                                   --song presets/song.example.json --outdir work/
    python -m lyric_mv render      --plan work/plan.json --features work/audio_features.npz \\
                                   --style F_aurora_ribbon --out out/full.mp4
    python -m lyric_mv preview     --plan work/plan.json --features work/audio_features.npz \\
                                   --out-dir work/stills
    python -m lyric_mv cover       --title "歌名" --out work/cover.png

The heavy, optional dependencies (Whisper / stable-ts / Demucs) are only
imported by :mod:`lyric_mv.align` and :mod:`lyric_mv.separate`, so a plain
``pip install lyric-mv-kit`` gives you the full renderer without them.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
