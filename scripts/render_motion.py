#!/usr/bin/env python3
"""Render or preview any existing lyric-mv visual style with macro motion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from lyric_mv import styles
from lyric_mv.motion import MotionController, load_score, load_template
from lyric_mv.motion_renderer import MotionRenderer


def _load_plan(path: str) -> dict:
    p = Path(path).resolve()
    plan = json.loads(p.read_text(encoding="utf-8"))
    audio = Path(plan["audio"])
    if not audio.is_absolute():
        audio = p.parent / audio
    plan["audio"] = str(audio)
    return plan


def build_renderer(args):
    plan = _load_plan(args.plan)
    feats = np.load(args.features)
    template = load_template(args.motion_template)
    score = load_score(args.motion_score, duration=float(plan["duration"])) if args.motion_score else None
    base = styles.get(args.style)(plan, feats, args.cover)
    return plan, MotionRenderer(base, MotionController(plan, template, score))


def render_preview(args, renderer):
    outdir = Path(args.preview_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    times = [float(x.strip()) for x in args.preview_times.split(",") if x.strip()]
    for t in times:
        frame = min(renderer.n - 1, max(0, round(t * renderer.fps)))
        dest = outdir / f"motion-{t:06.2f}s.png"
        renderer.frame(frame).save(dest, optimize=True)
        print(f"preview -> {dest}")


def render_video(args, plan, renderer):
    fps = int(plan["fps"])
    width, height = int(plan["width"]), int(plan["height"])
    start = max(0, args.start)
    count = renderer.n - start if args.count <= 0 else min(args.count, renderer.n - start)
    audio_input = ["-i", plan["audio"]]
    if start:
        audio_input = ["-ss", f"{start / fps:.3f}", "-i", plan["audio"]]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
        "-r", str(fps), "-i", "pipe:0",
        *audio_input,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", args.audio_bitrate, "-shortest", str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    started = time.time()
    try:
        for k in range(count):
            proc.stdin.write(renderer.frame(start + k).tobytes())
            if k % 250 == 0:
                rate = (k + 1) / max(0.001, time.time() - started)
                print(f"frame {k}/{count} {rate:.1f} fps", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        code = proc.wait()
    if code:
        raise SystemExit(err[-3000:])
    print(f"video -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply a reusable Motion Template to an existing lyric-mv visual style.")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--style", default="A_editorial_air", choices=styles.keys())
    ap.add_argument("--motion-template", required=True)
    ap.add_argument("--motion-score")
    ap.add_argument("--cover")
    ap.add_argument("--preview-times", default="")
    ap.add_argument("--preview-dir", default="work/motion-preview")
    ap.add_argument("--out", default="work/motion.mp4")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--audio-bitrate", default="192k")
    args = ap.parse_args()
    plan, renderer = build_renderer(args)
    if args.preview_times:
        render_preview(args, renderer)
        return 0
    render_video(args, plan, renderer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
