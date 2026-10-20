# PIPELINE — any song → lyric MV

One command turns an audio file + a lyric text into a finished kinetic lyric
MV with word-level-accurate timing:

```bash
pip install -U "lyric-mv-kit[align]"      # or: pip install -U openai-whisper stable-ts demucs
python -m lyric_mv check                  # verify fonts + ffmpeg first

python -m lyric_mv pipeline run \
    --audio  song.wav \
    --lyrics lyrics.txt \
    --song   song.json \
    --template aurora-ribbon-en-primary \
    --work   work/ \
    --out    out/mv.mp4
```

`--song` is a small JSON (title/artist/sections; see
[`presets/song.example.json`](../presets/song.example.json)). `--lyrics` is a
plain text, one line per row; credit rows (`作词:` etc.) are dropped. For a
bilingual file, interleave the lines (one sung line, then its translation).

## Templates (language-primary variants)

| Template | Primary line | Auxiliary line |
| --- | --- | --- |
| `aurora-ribbon-en-primary` | English lyric (big kinetic type) | Chinese translation — small, dim |
| `aurora-ribbon-zh-primary` | Chinese lyric (big kinetic type) | English original — small, dim |

List with `python -m lyric_mv templates`. The auxiliary line always shares the
primary cue's fade envelope (appears and vanishes in unison) and is capped far
below the primary size, so the two languages never read as competing lines.

`--language` is the **sung** language of the audio (drives the pairing and the
whisper models); the template decides which language gets the big line. A
ZH-primary release of an English song is therefore `--language en --template
aurora-ribbon-zh-primary` — the pipeline re-times on the English vocal track
and then swaps the display roles, so the translation keeps the correct
(sung) timing.

## Stages

Every stage writes provenance JSON into `--work`; every stage is skippable via
`--stages` so re-runs are cheap (e.g. after fixing one stage).

| Stage | Does | Artifacts |
| --- | --- | --- |
| `separate` | Demucs `htdemucs` → vocal stem | `stems/htdemucs/<song>/vocals.wav` |
| `plan` | decode + spectrum + tempo + auto cue grid | `plan.auto.json`, `audio_features.npz` |
| `pair` | bilingual pairing (primary = `--language`) | `plan.paired.json` |
| `gt` | word-level ground truth on the stem | `words.tr.json`, `words.al.json` |
| `rebuild` | re-time every cue from the word timelines | `plan.gt.json`, `alignment.gt.json` |
| `finalize` | role-swap if template primary ≠ sung language | `plan.final.json` |
| `gate` | fail-closed sync gate — **blocks render** | (stdout) |
| `render` | full-song mp4 | `--out` |

Resume examples:

```bash
# reuse an existing stem + word timelines, only re-render
python -m lyric_mv pipeline run --stem work/stems/htdemucs/song/vocals.wav \
    --plan-in work/plan.auto.json --tr work/words.tr.json --al work/words.al.json \
    --template aurora-ribbon-en-primary --work work/ --stages rebuild,finalize,gate,render --out out/mv.mp4

# only build the plan for a new template direction
python -m lyric_mv pipeline run ... --template aurora-ribbon-zh-primary --stages pair
```

## Why word-level ground truth (the drift lesson)

Per-line forced alignment is **not trustworthy on fast, repetitive songs**: on
the Cha-Cha Groove production (2026-10-13) both a `base` model on the full mix
and a `small` model on the isolated vocal stem locked onto wrong positions in
the repetitive chorus, and energy-based arbitration then necessarily picked the
*late* candidate that still had vocal energy — repeated lines put energy at
many positions, so "energy present" ≠ "timing correct". The shipped video ran
3–23s behind the vocals from ~0:46 on.

The `gt` stage therefore builds **two independent word-level timelines** of the
vocal stem and adjudicates per line against the stem's RMS envelope:

- **TR** = stable-whisper `transcribe` (free decoding, word timestamps)
- **AL** = stable-whisper `align()` on the full known lyric text

Model mis-hearings of leading words are recovered by extending back over
contiguous non-ad-lib tokens; ad-lib runs (≥2 identical consecutive tokens,
e.g. "cha-cha") are never swallowed into a lyric line. Instrumental breaks
end up with no lyrics on screen because every cue is pinned to the words
actually sung.

## The gate (fail-closed, pre-render)

`gate` refuses to let a bad timeline reach the expensive render:

1. **FALLBACK** — any cue still on beat-grid `auto` timing → FAIL
   (`--max-fallback 0`).
2. **TIMING** — `start < end`, monotonic, non-overlapping, within
   `[0, duration]` → FAIL.
3. **DIVERGENCE** — `|aligned − seed| > --max-diverge` → WARNING only: a big
   correction is often exactly the fix, so it is reported for review, not
   blocked.

Run it standalone on any plan + provenance pair:

```bash
python -m lyric_mv gate --plan work/plan.final.json --align work/alignment.gt.json
```

## Verification (do this before publishing)

- **Word-level, not frame-level**: check each line's first-word time against
  the sung audio (spot frames at "safe" timestamps miss regional drift — that
  is how the ~1:00 drift shipped).
- Cover the problem regions: fast hooks, quiet bridge/outro, and every
  instrumental break (no lyric should show there).
- `preview` stills at the repaired cue times are a good second look:
  `python -m lyric_mv preview --plan work/plan.final.json --features
  work/audio_features.npz --style F_aurora_ribbon --times 51,64.5,72`.

## Pitfalls

- `--language` must be the **sung** language, not the display language.
- If `align()` reports a word-count mismatch, re-run `gt` with a larger
  `--model` (e.g. `medium`) or fix the lyric text — do not ship a partial
  alignment.
- Large models are slow on CPU; `small` was sufficient for a 160s dance track
  at 156 BPM once the stem was isolated.
- Keep `plan.json` (and its rebuilds) under version control with the run —
  they are the single source of truth for the renderer.
