# 风穿过指尖的梦 — v3 smooth

22-second review candidate for the “paper-wind” motion direction.

- `render_v3_smooth.py` is independent of v2 and reads alignment only.
- `wind-dream-v3-smooth.mp4` is the audible 1280×720 / 24fps / 22.000s output.
- `contact-7.28-8frames.jpg` shows eight consecutive frames across the reviewed 7.28–7.82s window.
- `v3-smooth-result.json` records source paths, media probe, SHA-256 and lint output.

The render keeps LongCang gold glyphs geometrically static. A #FFF9E7 raised-cosine focus travels through the source character timing; all line hand-offs use a 0.24s two-layer crossfade. Spectrum, notes and particles are disabled; the backdrop drift is limited to ±4px / ±3px.

Run:

```powershell
python .\render_v3_smooth.py
```

Not tested: manual listening review and a full-song render.
