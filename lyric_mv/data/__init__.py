"""lyric_mv.data — Data / Domain layer (componentization phase 1).

This package is the single source of truth for *facts* the renderer and cover
generator consume: lyric timing, section model, and style presets. It contains
NO drawing code. The UI layer (renderer.py / cover.py) is meant to import
``StyleSpec`` / ``SongPlan`` from here instead of hard-coding palettes and
sizes, so a future template change is a data edit, not a code edit.

See docs/plan-2026-09-23/architecture-componentization.md for the full
Data / Domain → Projection / UI → Runtime → Evidence separation.
"""

from .schema import LyricLine, SongPlan, Timing
from .presets import StyleSpec, get_preset, DEFAULT_PRESETS

__all__ = [
    "LyricLine",
    "SongPlan",
    "Timing",
    "StyleSpec",
    "get_preset",
    "DEFAULT_PRESETS",
]
