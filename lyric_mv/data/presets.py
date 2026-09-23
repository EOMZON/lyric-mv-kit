"""Style presets as DATA (componentization phase 1).

These are the exact palette / ribbon / spectrum / size values currently
hard-coded inside ``renderer.py`` (``ACCENT``) and ``cover.py``
(``RIBBONS`` / ``SPECTRUM_STOPS`` / ``*_SIZE``). They are extracted here as the
single canonical source so the UI layer can consume a ``StyleSpec`` instead of
embedding literals. Values are preserved 1:1 — this change is behaviour-neutral
until the renderer/cover are later wired to read from here (phase 2).

Loading prefers a YAML override (``presets.yaml``) but falls back to the
built-in ``DEFAULT_PRESETS`` so the package imports with no third-party deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

RGB = Tuple[int, int, int]

# --------------------------------------------------------------------------
# Canonical data — extracted verbatim from renderer.py / cover.py (pre-kit#12
# baseline kept intentionally; kit#12 width-adaptive logic is UI, not data).
# --------------------------------------------------------------------------
DEFAULT_PRESETS: Dict[str, dict] = {
    "aurora_ribbon": {
        # renderer.ACCENT — section -> accent colour
        "accent": {
            "verse1": (88, 150, 170),
            "break": (112, 130, 140),
            "chorus1": (188, 142, 102),
            "verse2": (82, 146, 166),
            "chorus2": (194, 148, 106),
            "outro": (112, 142, 158),
        },
        # cover.RIBBONS — (phase, frequency, amplitude, colour)
        "ribbons": [
            (0.9, 1.7, 0.42, (50, 235, 205)),
            (2.4, 2.3, 0.36, (150, 95, 255)),
            (4.1, 3.1, 0.30, (255, 110, 165)),
        ],
        # cover.SPECTRUM_STOPS — teal -> violet -> pink -> teal
        "spectrum_stops": [
            (40, 235, 205),
            (120, 140, 255),
            (255, 120, 175),
            (40, 235, 205),
        ],
        # cover.*_SIZE / renderer W,H
        "video_size": (1920, 1080),
        "cover_sizes": {
            "standard": (1146, 860),  # 4:3  B站 feed panel
            "wide": (1146, 717),      # 16:10
            "youtube": (1280, 720),   # 16:9
        },
        # cover HUD tokens
        "hud": {
            "margin": 80,
            "brand_size": 24,
            "label_size": 18,
            "sub_size": 30,
            "label": "AURORA",
        },
    },
    "paper_staff": {
        # second anchor template used by wind-dream (paper-staff)
        "accent": {
            "verse1": (70, 90, 120),
            "break": (110, 120, 130),
            "chorus1": (150, 110, 90),
            "verse2": (80, 100, 130),
            "chorus2": (160, 120, 95),
            "outro": (100, 120, 140),
        },
        "ribbons": [
            (1.0, 1.4, 0.30, (90, 200, 210)),
            (2.6, 2.0, 0.26, (140, 120, 230)),
            (4.3, 2.8, 0.22, (220, 130, 170)),
        ],
        "spectrum_stops": [
            (60, 210, 215),
            (130, 150, 240),
            (230, 140, 180),
            (60, 210, 215),
        ],
        "video_size": (1920, 1080),
        "cover_sizes": {
            "standard": (1146, 860),
            "wide": (1146, 717),
            "youtube": (1280, 720),
        },
        "hud": {
            "margin": 80,
            "brand_size": 24,
            "label_size": 18,
            "sub_size": 30,
            "label": "PAPER",
        },
    },
}


@dataclass(frozen=True)
class StyleSpec:
    """Projection / ViewModel: a resolved style the UI layer draws against."""

    name: str
    accent: Dict[str, RGB] = field(default_factory=dict)
    ribbons: List[Tuple[float, float, float, RGB]] = field(default_factory=list)
    spectrum_stops: List[RGB] = field(default_factory=list)
    video_size: Tuple[int, int] = (1920, 1080)
    cover_sizes: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    hud: Dict[str, object] = field(default_factory=dict)

    def accent_for(self, section: str) -> RGB:
        return self.accent.get(section, (112, 142, 158))


def _from_dict(name: str, d: dict) -> StyleSpec:
    return StyleSpec(
        name=name,
        accent={k: tuple(v) for k, v in d.get("accent", {}).items()},
        ribbons=[tuple(r) for r in d.get("ribbons", [])],
        spectrum_stops=[tuple(s) for s in d.get("spectrum_stops", [])],
        video_size=tuple(d.get("video_size", (1920, 1080))),
        cover_sizes={k: tuple(v) for k, v in d.get("cover_sizes", {}).items()},
        hud=dict(d.get("hud", {})),
    )


def get_preset(name: str = "aurora_ribbon") -> StyleSpec:
    """Return a resolved StyleSpec, preferring ``presets.yaml`` override."""
    data = DEFAULT_PRESETS
    yaml_path = Path(__file__).with_name("presets.yaml")
    if yaml_path.exists():
        try:
            import yaml  # local import: no hard dependency

            with yaml_path.open("r", encoding="utf-8") as fh:
                overrides = yaml.safe_load(fh) or {}
            data = {**DEFAULT_PRESETS, **overrides}
        except Exception:
            # Fall back to built-in canonical data on any parse error.
            pass
    if name not in data:
        name = next(iter(DEFAULT_PRESETS))
    return _from_dict(name, data[name])


if __name__ == "__main__":
    spec = get_preset("aurora_ribbon")
    print(f"preset={spec.name} video={spec.video_size} sections={list(spec.accent)}")
    print(f"ribbons={len(spec.ribbons)} spectrum_stops={len(spec.spectrum_stops)}")
