# plan.json schema

The renderer's **single source of truth**. ``build-plan`` writes this file; the
renderer and the cover generator read it. Nothing about the song lives anywhere
else.

## Top level

```jsonc
{
  "audio":     "absolute path to the master wav/mp3 (or relative to the plan file)",
  "duration":  139.87,        // seconds
  "fps":       30,
  "nframes":   4196,
  "width":     1920,
  "height":    1080,
  "title":     "歌名",
  "artist":    "艺人",        // kept in metadata but NOT shown in the HUD
  "album":     "专辑名",
  "sections":  { /* see below */ },
  "cues":      [ /* see below */ ],
  "meta":      { "bpm": 129, "key": "B 小调", "style": "Hook Pop × Minimal House" }
}
```

## sections

```jsonc
"sections": {
  "total": 139.867,            // seconds (audio length)
  "bpm":   128.57,
  "beat":  0.4667,             // 60 / bpm, in seconds
  "map": [
    { "kind": "verse1",  "start":  0.7, "end": 43.26 },
    { "kind": "chorus1", "start": 45.02, "end": 63.48 }
    // …
  ]
}
```

Section kinds recognised by the renderer's accent palette:

* ``verse1``, ``verse2`` — main vocal line (ink-blue accent)
* ``break`` — silence / instrument (slate)
* ``chorus1``, ``chorus2`` — hook (mineral accent; renders with per-char reveal)
* ``outro`` — fade tail

Add new kinds freely — they fall back to a neutral cool accent and behave like
``verse1`` for typography.

## cues

```jsonc
"cues": [
  { "text": "第一句",  "section": "verse1",  "start":  0.7, "end":  1.82 },
  { "text": "副歌来了", "section": "chorus1", "start": 45.02, "end": 47.65 }
]
```

* ``start`` / ``end`` are in seconds, inclusive-exclusive. They MUST be sorted
  and MUST NOT overlap — the renderer picks the first cue whose window
  contains ``t``, so overlaps silently swallow lines.
* ``text`` is what appears on screen; canonical lyric lines are kept verbatim
  (no dashes, no ``[section]`` markers — those are stripped by
  ``lyric_mv.plan.clean_lyrics``).

## How cues are produced

1. **Hand-aligned** (recommended) — write ``cue_times`` in the song config, one
   ``[start, end]`` pair per lyric line. Land times within ~100 ms of the
   actual vocal.
2. **Auto** — drop ``cue_times``. ``build-plan`` distributes each line across its
   section, weighted by character count. Drift of a few seconds is normal on
   long held notes; fine for a draft, not for a release.
3. **Forced alignment** — Demucs-vocals + stable-ts; the helper
   ``lyric_mv.align.segments_to_cue_times`` writes the exact ``cue_times``
   shape ready to paste into your song config. See ``lyric_mv/align.py``.