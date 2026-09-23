"""Data / Domain schema for lyric MV.

Pure data structures — no PIL, no numpy, no rendering. These describe *what* a
song is (lines, timings, sections, translation) independent of *how* it is
drawn. Keeping this separate lets the renderer (UI) and the cover generator
(UI) share one canonical model and lets batch tooling validate plans before
any frame is rendered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Canonical section ids used across renderer accent map and roadmap coverage.
SECTIONS = ("verse1", "break", "chorus1", "verse2", "chorus2", "outro")


@dataclass(frozen=True)
class Timing:
    """A time span in seconds on the master timeline."""

    start: float
    end: float

    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class LyricLine:
    """One primary lyric line plus optional bilingual 'translate' line.

    Mirrors the renderer's bilingual feature (kit#12): ``translation`` is the
    secondary line shown in unison with the primary when present.
    """

    text: str
    timing: Timing
    section: str = "verse1"
    translation: Optional[str] = None

    def __post_init__(self) -> None:
        if self.section not in SECTIONS:
            # Do not hard-fail batch tooling; surface as a warning-worthy value.
            object.__setattr__(self, "section", "verse1")


@dataclass
class SongPlan:
    """The data model a single run consumes.

    Replaces ad-hoc JSON blobs in ``runs/<song>/01_plan/`` with a typed,
    validatable contract that the renderer and cover generator both read.
    """

    title: str
    lines: list[LyricLine] = field(default_factory=list)
    lang: str = "zh"
    isrc: Optional[str] = None

    def translations_present(self) -> bool:
        return any(line.translation for line in self.lines)
