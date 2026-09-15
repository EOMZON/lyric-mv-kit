"""Reusable motion-template and song-level motion-score primitives.

This module deliberately knows nothing about typography, palettes or a concrete
Renderer subclass. It turns three data sources into a small camera/parallax
state for a timestamp:

1. plan.json        -> song duration, cues and sections
2. motion template -> reusable defaults for a lyric-video archetype
3. motion score    -> optional song-specific segment overrides

The separation lets a visual style and a motion template evolve independently.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MotionState:
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    background_parallax: float = 0.30
    foreground_parallax: float = 1.0


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _ease(name: str, u: float) -> float:
    u = _clamp(u)
    if name == "linear":
        return u
    if name == "ease_in":
        return u * u
    if name == "ease_out":
        return 1.0 - (1.0 - u) * (1.0 - u)
    if name == "sine":
        return 0.5 - 0.5 * math.cos(math.pi * u)
    return u * u * (3.0 - 2.0 * u)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_template(template: dict[str, Any]) -> None:
    required = ("id", "version", "camera", "parallax")
    missing = [key for key in required if key not in template]
    if missing:
        raise ValueError(f"motion template missing keys: {', '.join(missing)}")
    cam = template["camera"]
    for key in ("pan_x_px", "pan_y_px", "zoom", "period_seconds"):
        if key not in cam:
            raise ValueError(f"motion template camera missing {key!r}")
    para = template["parallax"]
    for key in ("background", "foreground"):
        if key not in para:
            raise ValueError(f"motion template parallax missing {key!r}")


def validate_score(score: dict[str, Any], duration: float | None = None) -> None:
    if int(score.get("version", 0)) != 1:
        raise ValueError("motion score version must be 1")
    segments = score.get("segments", [])
    last_start = -1.0
    for idx, seg in enumerate(segments):
        start = float(seg["start"])
        end = float(seg["end"])
        if start < 0 or end <= start:
            raise ValueError(f"invalid motion segment #{idx}: {start}..{end}")
        if start < last_start:
            raise ValueError("motion segments must be ordered by start time")
        if duration is not None and start > duration + 1e-6:
            raise ValueError(f"motion segment #{idx} starts after song duration")
        last_start = start


def load_template(path: str | Path) -> dict[str, Any]:
    value = load_json(path)
    validate_template(value)
    return value


def load_score(path: str | Path, duration: float | None = None) -> dict[str, Any]:
    value = load_json(path)
    validate_score(value, duration=duration)
    return value


class MotionController:
    """Sample reusable template motion plus optional explicit song choreography."""

    def __init__(self, plan: dict[str, Any], template: dict[str, Any],
                 score: dict[str, Any] | None = None):
        validate_template(template)
        if score is not None:
            validate_score(score, duration=float(plan["duration"]))
        self.plan = plan
        self.template = template
        self.score = score or {"version": 1, "segments": []}
        self.duration = max(0.001, float(plan["duration"]))
        self.cues = list(plan.get("cues") or [])

    def _cue_phase(self, t: float) -> tuple[int, float]:
        for idx, cue in enumerate(self.cues):
            start = float(cue["start"])
            end = float(cue["end"])
            if start <= t < end:
                return idx, _clamp((t - start) / max(0.001, end - start))
        return -1, 0.0

    def _template_state(self, t: float, bass: float, treble: float) -> MotionState:
        cam = self.template["camera"]
        para = self.template["parallax"]
        period = max(0.25, float(cam.get("period_seconds", 12.0)))
        phase = 2.0 * math.pi * t / period
        progress = _clamp(t / self.duration)
        cue_idx, cue_u = self._cue_phase(t)
        cue_sign = -1.0 if cue_idx >= 0 and cue_idx % 2 else 1.0

        pan_x = float(cam.get("pan_x_px", 0.0))
        pan_y = float(cam.get("pan_y_px", 0.0))
        progress_x = float(cam.get("progress_x_px", 0.0))
        progress_y = float(cam.get("progress_y_px", 0.0))
        cue_sway = float(cam.get("cue_sway_px", 0.0))
        zoom = float(cam.get("zoom", 0.0))

        x = pan_x * math.sin(phase) + progress_x * (progress - 0.5)
        y = pan_y * math.sin(phase * 0.83 + 0.7) + progress_y * (progress - 0.5)
        if cue_idx >= 0:
            x += cue_sign * cue_sway * math.sin(math.pi * cue_u)

        audio = self.template.get("audio_reactivity") or {}
        bass_zoom = float(audio.get("bass_zoom", 0.0)) * _clamp(float(bass))
        bass_push_y = float(audio.get("bass_push_y_px", 0.0)) * _clamp(float(bass))
        treble_sway_x = float(audio.get("treble_sway_x_px", 0.0)) * _clamp(float(treble))
        y -= bass_push_y
        x += treble_sway_x * math.sin(phase * 2.0)
        scale = 1.0 + zoom * (0.5 - 0.5 * math.cos(phase * 0.5)) + bass_zoom

        return MotionState(
            x=x,
            y=y,
            scale=max(0.90, scale),
            rotation=0.0,
            background_parallax=float(para.get("background", 0.30)),
            foreground_parallax=float(para.get("foreground", 1.0)),
        )

    def _segment_override(self, t: float) -> dict[str, float] | None:
        for seg in self.score.get("segments", []):
            start = float(seg["start"])
            end = float(seg["end"])
            if not (start <= t <= end):
                continue
            u = _ease(str(seg.get("easing", "ease_in_out")),
                      (t - start) / max(0.001, end - start))
            frm = seg.get("from") or {}
            to = seg.get("to") or frm
            return {
                key: _lerp(float(frm.get(key, to.get(key, 0.0))),
                           float(to.get(key, frm.get(key, 0.0))), u)
                for key in ("x", "y", "scale", "rotation")
                if key in frm or key in to
            }
        return None

    def state_at(self, t: float, bass: float = 0.0, treble: float = 0.0) -> MotionState:
        base = self._template_state(t, bass=bass, treble=treble)
        ov = self._segment_override(t)
        if not ov:
            return base
        return MotionState(
            x=float(ov.get("x", base.x)),
            y=float(ov.get("y", base.y)),
            scale=max(0.90, float(ov.get("scale", base.scale))),
            rotation=float(ov.get("rotation", base.rotation)),
            background_parallax=base.background_parallax,
            foreground_parallax=base.foreground_parallax,
        )


def merge_score(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Layer generated and manual score data and validate the result."""
    value = _deep_merge(base, override)
    validate_score(value)
    return value
