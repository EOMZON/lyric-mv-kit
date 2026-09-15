# Handoff — Motion Template System v5 / Wind Dream v5

## Start here

- Branch: `codex/motion-template-system-v5`
- Base main SHA: `7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec`
- Issue: https://github.com/EOMZON/lyric-mv-kit/issues/1
- Architecture / design analysis: https://github.com/EOMZON/lyric-mv-kit/blob/codex/motion-template-system-v5/docs/analysis/2026-09-15-motion-template-system-v5.md
- Motion schema: https://github.com/EOMZON/lyric-mv-kit/blob/codex/motion-template-system-v5/schemas/motion-score.schema.md
- Motion template pack: https://github.com/EOMZON/lyric-mv-kit/tree/codex/motion-template-system-v5/presets/motion
- Wind Dream v5 candidate: https://github.com/EOMZON/lyric-mv-kit/tree/codex/motion-template-system-v5/runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score
- Governance: https://github.com/EOMZON/codex-skills-private/blob/9a8e385ccc98f068b0990133f9a2e80681ffa9ec/github-ops/references/test-main-governance.md

## Goal

Do **not** continue v4 by increasing random effect counts or character lift.

Validate the new architecture:

```text
Visual Style × Motion Template × optional Song Motion Score
```

For 《风穿过指尖的梦》, keep the v4 visual language and test the concrete v5 macro choreography in `motion-score.json`.

## Cloud work already completed

1. Re-read Issue #1, v2/v3/v4 scripts and v4 audit.
2. Confirmed v4's root problem is composition-scale motion, not frame continuity.
3. Created a clean task branch from `main`, rather than merging the contaminated old review branch.
4. Saved the full architecture and template analysis.
5. Added renderer-neutral `motion-score` schema.
6. Added `lyric_mv/motion.py`:
   - template validation;
   - score validation;
   - cue-aware template motion;
   - audio-reactive defaults;
   - song segment overrides.
7. Added `lyric_mv/motion_renderer.py`:
   - separates background and foreground depth planes;
   - applies different parallax rates;
   - draws HUD after macro motion.
8. Added five reusable templates:
   - `steady-karaoke`
   - `cinematic-float`
   - `type-camera`
   - `ambient-story`
   - `beat-push`
9. Added generic `scripts/render_motion.py` bridge for existing visual styles.
10. Added Wind Dream v5 concrete score and a run-specific v5 renderer that preserves v4 typography/micro-motion.

## Cloud validation completed

The new Python modules/scripts were independently syntax-compiled before GitHub submission.

The five template JSON files and Wind Dream score were loaded through the new validator in an isolated test; boundary samples at 0 / 1.04 / 4.34 / 7.40 / 10.08 / 13.20 / 16.98 / 19.90 / 22.00s returned the intended continuous states.

This is **not** a substitute for repository-local or visual playback validation.

## Why final MP4 is still local-only

The remote branch does not contain every local/ignored run input required by the existing v4 pipeline, specifically the forced alignment and source lyric run data. The cloud runtime also does not have the user's Windows ffmpeg/font paths or the source audio context.

Therefore the current truth is:

```text
architecture: implemented
candidate code: implemented
score: implemented
static checks: passed
22s real render: not tested here
manual visual/listening review: not tested
full song: intentionally not rendered
main: unchanged
```

## Local execution checklist

### 0. Protect other AI work

Do not reset/clean the existing workspace. First inspect:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
git worktree list
```

If the current worktree is dirty or another AI is writing to it, create a separate worktree:

```bash
git fetch origin
git worktree add ../lyric-mv-kit-motion-v5 origin/codex/motion-template-system-v5
cd ../lyric-mv-kit-motion-v5
```

Otherwise safely switch/fetch according to the current repository state; do not discard local changes.

### 1. Static validation

```bash
python -m py_compile lyric_mv/motion.py lyric_mv/motion_renderer.py scripts/render_motion.py scripts/check_motion_configs.py
python scripts/check_motion_configs.py \
  --score runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/motion-score.json \
  --duration 22
```

Expected: five template PASS lines plus one score PASS.

### 2. Confirm local run inputs exist

Check these paths before rendering:

```text
runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_alignment/forced_alignment.json
runs/wind-dream/lyric-paper-staff-v1/v20260910-01/00_source/lyrics-wind-dream.txt
samples/review/real-song-demos/00_source/wind-dream/netease.mp3
samples/review/references/style-faithful/003-wind-dream-bg.png
assets/fonts/reusable/LongCang-Regular.ttf
```

If the alignment/lyrics are ignored and only exist in another local worktree, copy/materialize them into this isolated review worktree without committing them unless repository policy explicitly allows it. Do not rewrite their timing.

### 3. Preview-only first

Windows example:

```bat
python runs\wind-dream\lyric-paper-staff-v1\v20260910-01\03_render\v5-motion-score\render_v5_motion_score.py --preview
```

Review the eight boundary stills around score changes. Confirm:

- no exposed background edges;
- lyric stays inside safe frame;
- title/HUD remains stable;
- scale/translation direction is continuous;
- long lyric at ~17–20s stays readable.

### 4. Render only the 22s candidate

```bat
python runs\wind-dream\lyric-paper-staff-v1\v20260910-01\03_render\v5-motion-score\render_v5_motion_score.py
```

Expected:

```text
wind-dream-v5-motion-score.mp4
v5-motion-result.json
```

### 5. Manual review windows

Review at minimum:

- `4.34–7.40s`: first obvious composition shift;
- `7.40–10.08s`: upward melodic lift;
- `13.20–16.98s`: peak push into reunion;
- `16.98–19.90s`: long-line tracking/release;
- full 22s at normal playback speed.

Acceptance question is not “are there effects?” It is:

> At normal playback, does the whole image clearly feel like one continuous visual journey driven by the song, while lyrics remain effortless to follow?

### 6. Compare against v4

Keep v4 as the control. Do not delete it.

The v5 candidate should improve perceived macro motion without regressing:

- missing/blank character audit;
- sentence crossfade;
- edge clipping;
- line completeness;
- audio/lyric sync.

### 7. Do not render full song yet

Only after user explicitly accepts the 22s motion direction should the 69.3s score be expanded and rendered.

## Recommended fixed-template product strategy

New songs should start with this selection order:

1. `steady-karaoke` — safe universal default.
2. `cinematic-float` — strong existing artwork/footage.
3. `type-camera` — lyrics themselves are the visual hero.
4. `ambient-story` — lyrical/dreamy illustrated worlds.
5. `beat-push` — energetic rhythm-first songs.

Do not create a new renderer just because a new song arrives. Try a template first. Add a Song Motion Score only for truly song-specific build/peak/release events.

## Full prompt for the local AI

Use this document itself as the main prompt. The short instruction can simply be:

> Read this HANDOFF, the architecture analysis, Issue #1 and the governance doc. Work only on `codex/motion-template-system-v5` or an isolated worktree. Validate the new motion modules, render the Wind Dream v5 22s candidate, compare it against v4, save MP4/stills/audit evidence in the existing v5 run directory, and do not render the full song or merge main until the 22s candidate passes manual review. Preserve all existing local work and do not reset/clean/force-push.
