# Wind Dream v5 — Local 22s Validation Report

Branch: `codex/motion-template-system-v5` (worktree `lyric-mv-kit-motion-v5`)
Source PR: https://github.com/EOMZON/lyric-mv-kit/pull/2
Window: source `29.5s → 51.5s`, 22.000s, 1280×720, 24fps
Local env: miniforge python 3.x (Pillow 12.3 / numpy 2.5), ffmpeg `D:\ZON\runtime\media-tools\Library\bin`

> No `reset/clean/force-push` was used. The dirty main worktree
> (`codex/wind-dream-motion-escalation`) was left untouched; all work happened in the
> isolated worktree. Full song was NOT rendered; `main` was NOT merged.

## 1. Static validation
- `py_compile` of `motion.py`, `motion_renderer.py`, `render_motion.py`, `check_motion_configs.py` → OK
- `check_motion_configs.py --duration 22` → **5 template PASS** (`steady-karaoke`, `cinematic-float`, `type-camera`, `ambient-story`, `beat-push`) + **1 score PASS** (`wind-dream-v5-motion-score`)

## 2. Local run inputs (materialized from main repo, untracked, not committed)
- `03_alignment/forced_alignment.json` (40 KB)
- `00_source/lyrics-wind-dream.txt` (528 B)
- `samples/.../wind-dream/netease.mp3`, `samples/.../003-wind-dream-bg.png`
- `assets/fonts/reusable/LongCang-Regular.ttf`
> Alignment↔lyrics char assertion passed (no timing rewrite).

## 3. 22s render
- `wind-dream-v5-motion-score.mp4` (4.12 MB) produced, decode pass.
- Media: h264 1280×720 24fps / 528 frames, aac audio, 22.000s.
- sha256 `685998d37c4fa15c5b59d299f3f6bb77435e63f18d48956fc8e6dd1ef3ebf1f3`.

## 4. Camera / continuity audit (`v5-motion-audit.json`)
- Per-frame camera deltas are tiny & smooth: dx ≤ 1.86px, dy ≤ 0.79px, scaleΔ ≤ 0.0005.
- Camera travel (logical px, ×parallax for bg): **x −18 → +175 (≈193px), y +8 → −70 (≈78px)**.
- Scale range 1.018 → 1.095 (peak in reunion section 13.2–16.98s).
- Crossfade: **7/7 transitions pass** (overlap 4–5 frames, identical to v4).

## 5. Blank-char + safe-area audit (`v5-blank-char-audit.json`)
Adapted the v4 `check_no_blank_chars.py` method to the v5 renderer (diff with/without
lyric layer, mapped each glyph through the v5 camera transform) — called `audit_v5_blank_and_safearea.py`.
- 5127 chars measured, **0 blank characters**.
- min coverage 0.147, median 0.333 — far above the 2% gate.
- Lyric ink bbox `49..1182 × 198..663` → **inside 12px safe margin** (no dynamic edge clipping).

## 6. v4 (control) vs v5 comparison

| Axis | v4 (control) | v5 (motion score) |
|---|---|---|
| Composition-level camera | none — poster with ±4/±3px bg drift | continuous right/upward journey, ≈193×78px travel |
| Max per-frame lyric delta | 0.74px y / 0.0028 scale | camera x≤1.86 / y≤0.79px, smooth |
| Background parallax | none | 0.30 low; lyric 1.0 full |
| Peak motion | none | reunion section 13.2–16.98s, release after |
| Blank-char audit | PASS (min 0.225) | PASS (min 0.147) |
| Crossfade | 7/7 pass | 7/7 pass |
| Safe area / edge clip | 0 overflow | inside 12px margin |
| Audio/lyric sync | aligned @29.5s | same alignment, same start |

**Conclusion:** v5 adds the macro choreography v4 structurally lacked (the accepted
diagnosis: "technically moving, subjectively still" because local elements moved but the
composition never advanced). It does so **without regressing** any v4 safety gate — no
blank chars, all crossfades hold, no edge clipping, sync preserved. Subjective quality
is for the human to confirm at normal playback; the objective gates all pass.

## 7. Deliverables in this directory
- `wind-dream-v5-motion-score.mp4` — the 22s candidate
- `v5-contact-journey.jpg` — 12-frame motion arc
- `v5-contact-boundaries.jpg` — 8 score-boundary stills
- `v4-vs-v5-compare.jpg` — matched-timestamp v4/v5 side-by-side
- `v5-motion-result.json`, `v5-motion-audit.json`, `v5-blank-char-audit.json`
- `v5-1.04.jpg … v5-21.90.jpg` — 8 boundary stills
- `audit_v5_blank_and_safearea.py`, `make_v5_contact_sheets.py`, `make_v4v5_compare_sheet.py`

## 8. Next step (blocked on human confirmation)
Do **not** expand to 69.3s or merge `main` until the user accepts the 22s motion direction.
