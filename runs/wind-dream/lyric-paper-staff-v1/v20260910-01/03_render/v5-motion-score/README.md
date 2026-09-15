# Wind Dream v5 — Motion Score candidate

This candidate preserves the readable v4 paper-wind typography but adds a macro choreography layer.

## What changes from v4

- Background, ambient environment and lyrics are separate depth planes.
- All three planes follow one `motion-score.json` instead of independent loops.
- Background moves at low parallax, environment at medium parallax, lyrics at full camera motion.
- Song title / artist utility text is drawn after camera transforms and therefore stays stable.
- v4 character focus, crossfade and low-alpha environment are intentionally preserved for A/B comparability.

## What does not change

- 24fps / 1280×720 review contract.
- 29.5s source start and 22s review duration.
- LongCang gold resting lyric and warm-white current focus.
- Source alignment is not rewritten.
- Full-song rendering remains blocked until the 22s candidate is manually accepted.

## Local-only dependencies

The current Git branch intentionally does **not** manufacture or rewrite ignored/local run inputs. The script expects the same local files as v4:

- `v20260910-01/03_alignment/forced_alignment.json`
- `v20260910-01/00_source/lyrics-wind-dream.txt`
- `samples/review/real-song-demos/00_source/wind-dream/netease.mp3`
- `samples/review/references/style-faithful/003-wind-dream-bg.png`
- `assets/fonts/reusable/LongCang-Regular.ttf`
- Windows ffmpeg/ffprobe paths already used by v4

## Review commands

```bat
python runs\wind-dream\lyric-paper-staff-v1\v20260910-01\03_render\v5-motion-score\render_v5_motion_score.py --preview
```

This writes eight boundary stills and `v5-motion-audit.json`.

Then render only the 22s candidate:

```bat
python runs\wind-dream\lyric-paper-staff-v1\v20260910-01\03_render\v5-motion-score\render_v5_motion_score.py
```

Expected output:

```text
wind-dream-v5-motion-score.mp4
v5-motion-result.json
```

Do not render the 69.3s full song until the user accepts the motion direction.
