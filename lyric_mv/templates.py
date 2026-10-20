"""Template registry — language-primary variants of the canonical anchor styles.

A *template* binds three things:

  * a visual style key (see :mod:`lyric_mv.styles`)
  * a **primary language** — which language carries the big kinetic line
  * the pairing direction for the bilingual transform (:mod:`lyric_mv.bilingual`)

The auxiliary line is always the *other* language, drawn small and dim as a
subordinate caption (kit commit ``d8791af``), so the two languages never read
as competing lines.

Canonical anchors (kit#13): ``aurora-ribbon`` (《我拒绝被定义》) and
``paper-staff`` (《切口与暗号》). Each anchor ships an EN-primary and a
ZH-primary variant. Adding a template is a data change — one entry here, no
renderer surgery: the renderer already draws ``cue["text"]`` as the primary
line and ``cue["translate"]`` as the auxiliary line, with per-glyph font
fallback covering CJK and Latin alike.
"""

from __future__ import annotations

TEMPLATES: dict[str, dict] = {
    "aurora-ribbon-en-primary": {
        "style": "F_aurora_ribbon",
        "primary": "en",
        "anchor": "aurora-ribbon (《我拒绝被定义》)",
        "summary": "英文歌词为主行（大号动力学字），中文译文为小号弱化辅助行。",
    },
    "aurora-ribbon-zh-primary": {
        "style": "F_aurora_ribbon",
        "primary": "zh",
        "anchor": "aurora-ribbon (《我拒绝被定义》)",
        "summary": "中文歌词为主行（大号动力学字），英文原文为小号弱化辅助行。",
    },
}


def names() -> list[str]:
    return list(TEMPLATES)


def get(name: str) -> dict:
    if name not in TEMPLATES:
        raise SystemExit(
            f"unknown template {name!r}; available: {', '.join(names())}")
    return TEMPLATES[name]


def style_of(name: str) -> str:
    return get(name)["style"]


def primary_of(name: str) -> str:
    return get(name)["primary"]
