"""Pair lyric lines with their translation into single bilingual cues.

The bilingual transform merges two cues that carry the same moment in two
languages into ONE cue: the primary language stays in ``text`` (the big
kinetic line), the other language moves to ``translate`` (the small dim
auxiliary line drawn in unison — kit commit ``d83d4ba``).

Direction is chosen by the template's primary language
(:mod:`lyric_mv.templates`):

  * ``primary="en"`` — each ZH line attaches to the preceding EN line
    (EN-primary templates; the Cha-Cha Groove production default)
  * ``primary="zh"`` — each EN line attaches to the preceding ZH line
    (ZH-primary templates; e.g. a Chinese release of an English song)

Input cue order matters: pairing looks *backwards* from each auxiliary line
to the most recent unpaired primary-language cue, which is the natural order
of an interleaved EN/ZH lyric file (one EN line followed by its ZH rendering).
"""

from __future__ import annotations

import re
from pathlib import Path

# CJK + kana + hangyl: anything in these ranges counts as "the Chinese side".
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]")


def is_cjk(text: str) -> bool:
    return bool(_CJK.search(text or ""))


def pair_cues(cues: list[dict], primary: str = "en",
              tail: float = 0.5, gap: float = 0.05) -> list[dict]:
    """Merge translation cues into their primary-language partner.

    ``tail`` extends a paired cue's end so the auxiliary line survives short
    pauses; the extension is capped before the next cue starts (``gap``).
    """
    primary_cjk = primary.lower().startswith("zh")
    out: list[dict] = []
    holder: dict | None = None
    for c in cues:
        text = (c.get("text") or "").strip()
        if is_cjk(text) == primary_cjk:
            holder = dict(c)
            holder["translate"] = ""
            out.append(holder)
        elif holder is not None and not holder.get("_paired"):
            holder["translate"] = text
            holder["_paired"] = True
        else:
            # same-language line with no free holder, or a stray translation:
            # keep it as its own cue (no pairing invented).
            out.append(dict(c))

    for k, c in enumerate(out):
        if c.get("translate") and k + 1 < len(out):
            nxt = out[k + 1]
            c["end"] = max(c["end"], min(c["end"] + tail, nxt["start"] - gap))
        c.pop("_paired", None)
    return out


def pair_plan(plan: dict, primary: str = "en", tail: float = 0.5,
              gap: float = 0.05, template: str | None = None) -> dict:
    """Return a copy of ``plan`` with bilingual cues + pairing provenance."""
    d = dict(plan)
    d["cues"] = pair_cues(plan.get("cues", []), primary, tail, gap)
    pairs = sum(1 for c in d["cues"] if c.get("translate"))
    d.setdefault("meta", {})
    d["meta"]["bilingual"] = {
        "primary": primary,
        "template": template,
        "paired_cues": pairs,
        "method": "translation rides the primary cue's fade envelope as a small dim auxiliary line",
    }
    return d


def load_plan(path: Path | str) -> dict:
    return __import__("json").loads(Path(path).read_text(encoding="utf-8"))
