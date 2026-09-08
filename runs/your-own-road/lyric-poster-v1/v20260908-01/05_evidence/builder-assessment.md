# MV04-attempt1 · Builder assessment

This version is a non-destructive timeline candidate for `路是你自己走` / `isrc-QZTB42619429`. The prior automatic result remains read-only at `runs/your-own-road-poster-full`.

## Observed input

- Decoded release-source duration: `76.821` seconds (Opus, 48 kHz, stereo).
- The legacy catalog field says 150 seconds. It is retained as conflicting metadata only; no stretch, loop, or 150-second output is permitted.
- Canonical body: 22 lines, 197 displayed characters; `(嘘)` remains a performance direction and is omitted from display text.
- The automatic result contains nine zero-duration characters: 赢、忧、里、着、控、式、向、了、谁.

## Evidence commands

```powershell
D:\ZON\runtime\media-tools\Library\bin\ffprobe.exe -v error -show_entries format=duration:stream=index,codec_type,codec_name,sample_rate,channels -of json D:\ZON\codex\lyric-mv-kit\samples\review\real-song-demos\00_source\your-own-road\youtube.webm
D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe -hide_banner -v error -i <audio> -filter_complex <eight-local-waveform-trims> -frames:v 1 D:\ZON\runtime\temp-user\mv04-waveforms.png
```

The waveform trims cover the affected neighborhoods: 24.2–25.8, 28.8–29.9, 30.7–31.5, 31.8–32.6, 35.1–35.8, 38.4–39.1, 44.9–45.6, and 59.8–60.7 seconds. They are timing evidence only, not a human listening attestation.

## MVT status at this handoff

| Test | Status | Result |
|---|---|---|
| MVT-03 | pass | Source decodes and is exactly 76.821 seconds. |
| MVT-04 | partial | Canonical lyrics and identity were carried forward; released-version listening review remains required. |
| MVT-05 | partial | `lyric-poster-v1` policy specifies one persistent top-left title and retention behavior, but no new rendered frame yet exists. |
| MVT-07 | pass (structural candidate) | Re-running `validate_candidate.py` yields 197/197 canonical characters, zero invalid spans, zero overlaps, and all spans inside 76.821 seconds. Human review is still required before promotion. |
| MVT-08 | blocked | No human full-song listening verdict is claimed. |
| MVT-09–16 | not_run | There is no full MP4, package, or upload in this attempt. |

## Required recovery action

An independent listener must inspect the nine local clips against the release source, resolve cue 10 `谁` at 38.8 seconds and validate every provisional boundary. Only then may C create a new immutable timing revision and run one render job. This attempt intentionally does not render a misleading 150-second or supposedly-final MV.
