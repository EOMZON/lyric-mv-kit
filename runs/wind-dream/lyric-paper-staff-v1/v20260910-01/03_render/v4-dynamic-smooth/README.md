# 风穿过指尖的梦 — v4 dynamic smooth

Second 22-second candidate: a visibly dynamic but continuously controlled “paper-wind” version.

- `render_v4_dynamic_smooth.py` is independent from v2/v3 and reads alignment only.
- `wind-dream-v4-dynamic-smooth.mp4` is the audible 1280×720 / 24fps / 22.000s output.
- `contact-4.42-8frames.jpg`, `contact-7.28-8frames.jpg`, and `contact-16.86-8frames.jpg` are eight-frame review sheets.
- `contact-environment-2s.jpg` samples two seconds at 4fps to inspect environmental movement.
- `v4-dynamic-smooth-result.json` records hashes, probes and lint evidence.

The lyric is the primary moving layer: a raised-cosine cursor expands into adjacent glyphs as a continuous wind field, with 5px maximum lift, 2% maximum scale and 1.2px whole-line breath. Gold remains the resting color; the moving field turns softly toward `#FFF9E7` with a restrained local shadow glow.

Secondary motion is intentionally quieter: background drift is ±4px / ±3px over 21s/19s, fifteen low-alpha particles drift continuously, a 20-segment low-alpha wave sits at the bottom, and a halo responds to RMS using a 0.25s attack and 0.35s release. No beat notes are used.

Layout lint includes actual nonzero glyph alpha bboxes and conservative shadow bounds against a 12px safety edge; dynamic shadow bounds remain inside it with zero overflow.

Run:

```powershell
python .\render_v4_dynamic_smooth.py
```

Not tested: manual listening review and full-song rendering.
