"""Build ``plan.json`` + ``audio_features.npz`` — the single source of truth.

``plan.json`` is the contract between the analysis stage and the renderer.
Everything the renderer knows about the song lives in it, which is what makes
the 8 styles interchangeable and the whole thing portable to another engine
(see ``docs/PORTING-TO-REMOTION.md``).

Inputs
------
audio        any format ffmpeg can decode
lyrics       a plain .txt, one lyric line per row (credit rows are dropped)
song         a JSON "song config" holding title/meta/section map/cue times

The song config is what used to be hardcoded inside the build script. Two
levels of effort are supported:

* **hand-aligned** — you supply ``cue_times`` (one ``[start, end]`` pair per
  lyric line). This is what shipped in the reference MV; it is the difference
  between "the words line up" and "the words are close".
* **auto** — omit ``cue_times`` and lines are distributed across each section
  proportionally to character count. Good enough for a first draft; drift of
  several seconds is normal on long held notes.

See ``schemas/plan.schema.md`` and ``presets/song.example.json``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from . import audio as audio_mod

CREDIT_RE = re.compile(r"^\s*(作词|作曲|编曲|混音|制作|录音|词|曲|编|混)\s*[:：]")


def clean_lyrics(raw: str) -> list[str]:
    """Drop blank lines, credit rows and ``[section]`` markers."""
    lines = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or CREDIT_RE.match(ln):
            continue
        # Timing carries the held note; the display lyric stays clean. Using a
        # katakana long-vowel mark made "定—义" look like the wrong character.
        ln = ln.replace("—", "").replace("–", "").replace("-", "")
        ln = re.sub(r"\[[^\]]*\]", "", ln).strip()
        if ln:
            lines.append(ln)
    return lines


def load_song(path: Path | str) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("title", "sections"):
        if key not in cfg:
            raise SystemExit(f"song config 缺少必填字段 {key!r}: {path}")
    return cfg


def _section_for_line(sections: list[dict], n_lines: int) -> dict[int, str]:
    """Map each lyric line index to a section kind."""
    explicit = {}
    for sec in sections:
        rng = sec.get("lines")
        if rng:
            for i in range(int(rng[0]), int(rng[1])):
                explicit[i] = sec["kind"]
    if explicit:
        return explicit

    # Fallback: spread lines across sections that can hold lyrics, weighted by
    # how long each section is. Sections flagged ''lyricless'' are skipped.
    holders = [s for s in sections if not s.get("lyricless")]
    if not holders:
        holders = sections
    spans = [max(0.01, float(s["end"]) - float(s["start"])) for s in holders]
    total = sum(spans)
    out, idx = {}, 0
    for sec, span in zip(holders, spans):
        share = max(1, round(n_lines * span / total))
        for _ in range(share):
            if idx >= n_lines:
                break
            out[idx] = sec["kind"]
            idx += 1
    for i in range(idx, n_lines):
        out[i] = holders[-1]["kind"]
    return out


def _distribute(lines: list[str], start: float, end: float) -> list[tuple[float, float]]:
    """Spread lines across [start, end) weighted by character count."""
    weights = [max(1, len(x)) for x in lines]
    total_w = sum(weights)
    span = max(0.05, end - start)
    gap = min(0.25, span / (len(lines) * 6))
    usable = max(0.05, span - gap * (len(lines) - 1))
    out, cur = [], start
    for w in weights:
        d = usable * w / total_w
        out.append((round(cur, 3), round(cur + d, 3)))
        cur += d + gap
    return out


def build_cues(lines: list[str], song: dict) -> list[dict]:
    sections = song["sections"]
    cue_times = song.get("cue_times")

    if cue_times:
        if len(cue_times) != len(lines):
            raise SystemExit(
                f"cue_times 有 {len(cue_times)} 条，歌词有 {len(lines)} 行；"
                "数量必须一致（或删掉 cue_times 走自动分配）。"
            )
        mapping = _section_for_line(sections, len(lines))
        return [
            {"text": line, "section": mapping.get(i, sections[-1]["kind"]),
             "start": float(st), "end": float(en)}
            for i, (line, (st, en)) in enumerate(zip(lines, cue_times))
        ]

    mapping = _section_for_line(sections, len(lines))
    buckets: dict[str, list[int]] = {}
    for i in range(len(lines)):
        buckets.setdefault(mapping[i], []).append(i)

    cues: list[dict | None] = [None] * len(lines)
    for sec in sections:
        idxs = buckets.get(sec["kind"], [])
        if not idxs:
            continue
        s0, s1 = float(sec["start"]), float(sec["end"])
        for i, (st, en) in zip(idxs, _distribute([lines[i] for i in idxs], s0, s1)):
            cues[i] = {"text": lines[i], "section": sec["kind"],
                       "start": st, "end": en}
    return [c for c in cues if c is not None]


def build_plan(audio: Path | str, lyrics: Path | str, song: dict,
               outdir: Path | str, fps: int = 30,
               width: int = 1920, height: int = 1080) -> tuple[dict, Path]:
    """Analyse the audio and write ``plan.json`` + ``audio_features.npz``."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    audio = Path(audio).resolve()

    print(f"[1/4] decoding {audio.name}", flush=True)
    x = audio_mod.decode(audio)
    dur = len(x) / audio_mod.SR
    print(f"      {dur:.2f}s  {len(x)} samples @ {audio_mod.SR}Hz", flush=True)

    print("[2/4] per-frame spectrum", flush=True)
    feats = audio_mod.envelope(x, fps)
    nframes = feats["nframes"]
    print(f"      {nframes} frames @ {fps}fps", flush=True)

    print("[3/4] tempo + lyric timeline", flush=True)
    hop_s = 1.0 / fps
    total = len(feats["raw_rms"]) * hop_s
    bpm = audio_mod.detect_bpm(feats["raw_rms"], hop_s)
    if bpm < 80:
        bpm *= 2
    beat = 60.0 / bpm
    print(f"      bpm={bpm:.1f}  beat={beat:.3f}s  total={total:.2f}s", flush=True)

    lines = clean_lyrics(Path(lyrics).read_text(encoding="utf-8"))
    cues = build_cues(lines, song)
    print(f"      {len(cues)} lyric cues "
          f"({'hand-aligned' if song.get('cue_times') else 'auto'})", flush=True)

    print("[4/4] writing plan", flush=True)
    npz = audio_mod.save_features(feats, outdir / "audio_features.npz")

    meta = {"bpm": round(float(bpm))}
    meta.update(song.get("meta") or {})

    plan = {
        "audio": str(audio),
        "duration": round(dur, 3),
        "fps": fps,
        "nframes": int(nframes),
        "width": width,
        "height": height,
        "title": song.get("title", ""),
        "artist": song.get("artist", ""),
        "album": song.get("album", ""),
        "sections": {
            "total": round(total, 3),
            "bpm": round(float(bpm), 2),
            "beat": round(float(beat), 4),
            "map": [
                {"kind": s["kind"], "start": float(s["start"]),
                 "end": float(s["end"]) if s.get("end") is not None else round(total, 3)}
                for s in song["sections"]
            ],
        },
        "cues": cues,
        "meta": meta,
    }
    plan_path = outdir / "plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"      -> {plan_path}", flush=True)
    return plan, npz
