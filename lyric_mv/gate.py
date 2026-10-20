"""Fail-closed pre-render alignment-sync gate.

Why this exists
---------------
2026-10-12 a shipped bilingual MV drifted out of sync from ~1:00. Root cause:
the per-line forced alignment silently fell back to beat-grid ``auto`` times on
fast hooks / quiet tail (19 of 80 cues) and nothing blocked the render, so the
drift shipped. Ink-coverage audits and a couple of spot-check frames cannot see
the *time* dimension, so they passed.

This gate runs BEFORE any expensive render and fails closed on:

  1. FALLBACK  — every cue must carry real word-level alignment.
                 ``fallback_count > max_fallback`` -> FAIL.
  2. TIMING    — ``start < end``, monotonic non-overlapping (min gap),
                 within ``[0, duration]``.
  3. DIVERGENCE — WARNING only: cues whose aligned start is far from the
                 beat-grid seed are *reported* (that is where auto timing
                 would have been visibly wrong), but do not fail the gate —
                 we render the aligned time, and a big correction is often
                 exactly the fix (e.g. the 3s-early cue the GT rebuild moved).

Exit codes: 0 = PASS, 1 = FAIL (blocks render). Reads a plan + its raw
alignment provenance; never mutates them.

CLI::

    python -m lyric_mv gate --plan work/plan.bilingual.json \\
                           --align work/alignment.gt.json \\
                           [--max-fallback 0] [--max-diverge 1.0]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def run(plan_path: Path | str, align_path: Path | str,
        max_fallback: int = 0, max_diverge: float = 1.0) -> int:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(align_path).read_text(encoding="utf-8"))
    dur = float(plan["duration"])
    cues = plan["cues"]

    problems: list[str] = []
    fb = [r for r in raw if r.get("fallback")]
    fb_idx = [r["index"] for r in fb]

    # 1. fallback gate
    if len(fb) > max_fallback:
        detail = ", ".join(f"{i}:{raw[i]['text'][:16]}" for i in fb_idx)
        problems.append(
            f"FALLBACK {len(fb)} > max {max_fallback} — beat-grid auto timing "
            f"(the drift source). Offenders: {detail}")

    # 2. timing gate
    prev_end = -1.0
    for i, c in enumerate(cues):
        s, e = float(c["start"]), float(c["end"])
        if e <= s:
            problems.append(f"TIMING cue {i} '{c['text'][:16]}' end<=start ({s},{e})")
        if s < prev_end - 1e-6:
            problems.append(
                f"TIMING cue {i} '{c['text'][:16]}' overlaps previous (s={s} < {prev_end})")
        if s < -0.001 or e > dur + 0.1:
            problems.append(
                f"TIMING cue {i} '{c['text'][:16]}' out of song range ({s},{e}) dur={dur}")
        prev_end = max(prev_end, e)

    # 3. divergence — WARNING only (see module docstring)
    worst = []
    for r in raw:
        a = r.get("aligned")
        seed = r.get("seed") or r.get("auto")
        if a and seed:
            worst.append((abs(a[0] - seed[0]), r["index"], r["text"]))
    worst.sort(reverse=True)
    warnings = []
    big = [w for w in worst if w[0] > max_diverge]
    if big:
        detail = "; ".join(f"cue{i} Δ{d:.2f}s '{t[:14]}'" for d, i, t in big[:6])
        warnings.append(f"DIVERGENCE {len(big)} cue(s) |aligned-seed|>{max_diverge}s: {detail}")

    print(f"[sync-gate] plan={plan_path}")
    if worst:
        print(f"[sync-gate] cues={len(cues)} fallback={len(fb)} "
              f"max|Δstart|={worst[0][0]:.2f}s (cue{worst[0][1]})")
    for w in warnings:
        print("[sync-gate] WARN: " + w)
    if problems:
        print("[sync-gate] FAIL:")
        for p in problems:
            print("   - " + p)
        return 1
    print("[sync-gate] PASS — safe to render")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="fail-closed pre-render alignment-sync gate")
    ap.add_argument("--plan", required=True, help="plan json (rendered cues)")
    ap.add_argument("--align", required=True, help="raw alignment provenance json")
    ap.add_argument("--max-fallback", type=int, default=0,
                    help="max cues allowed to fall back to beat-grid auto timing")
    ap.add_argument("--max-diverge", type=float, default=1.0,
                    help="report cues whose |aligned_start - seed_start| exceeds this")
    args = ap.parse_args()
    return run(args.plan, args.align, args.max_fallback, args.max_diverge)


if __name__ == "__main__":
    raise SystemExit(main())
