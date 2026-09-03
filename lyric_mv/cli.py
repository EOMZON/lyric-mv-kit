"""Unified command-line entry point.

    python -m lyric_mv check                      # verify fonts + ffmpeg
    python -m lyric_mv styles                     # list the 8 styles
    python -m lyric_mv build-plan   ...           # audio + lyrics -> plan.json
    python -m lyric_mv render       ...           # plan.json -> full-song mp4
    python -m lyric_mv preview      ...           # stills at given timestamps
    python -m lyric_mv demo         ...           # short audio-bearing clip
    python -m lyric_mv cover        ...           # 4:3 cover art
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


def _load_plan(plan_path: str) -> dict:
    p = Path(plan_path).resolve()
    plan = json.loads(p.read_text(encoding="utf-8"))
    audio = Path(plan["audio"])
    if not audio.is_absolute():
        audio = p.parent / audio
    plan["audio"] = str(audio)
    return plan


# ------------------------------------------------------------------- commands
def cmd_check(args):
    from . import config as cfg

    ok = True

    ff = shutil.which("ffmpeg")
    print(f"ffmpeg      : {ff or 'MISSING — install ffmpeg and put it on PATH'}")
    ok &= bool(ff)

    fonts = cfg.resolve_fonts()
    print(f"font heavy  : {fonts.heavy or 'MISSING'}")
    print(f"font sans   : {fonts.sans or 'MISSING'}")
    print(f"font latin  : {fonts.latin or 'MISSING'}")
    try:
        fonts.require()
    except cfg.FontNotFound as exc:
        print("\n" + str(exc))
        ok = False

    print(f"brand       : {cfg.brand()}")
    print("\nOK" if ok else "\nNOT READY — see the messages above")
    return 0 if ok else 1


def cmd_styles(args):
    from . import styles

    for k in styles.keys():
        print(f"  {k:24s} {styles.LABELS.get(k, '')}")
    return 0


def cmd_build_plan(args):
    from . import plan as plan_mod

    song = plan_mod.load_song(args.song)
    plan, npz = plan_mod.build_plan(
        audio=args.audio, lyrics=args.lyrics, song=song,
        outdir=args.outdir, fps=args.fps,
        width=args.width, height=args.height,
    )
    print(f"plan      : {Path(args.outdir) / 'plan.json'}")
    print(f"features  : {npz}")
    return 0


def _make_renderer(style: str, plan: dict, feats, cover: str | None):
    from . import styles

    cls = styles.get(style)
    return cls(plan, feats, cover)


def cmd_render(args):
    plan = _load_plan(args.plan)
    feats = np.load(args.features)
    r = _make_renderer(args.style, plan, feats, args.cover)

    fps, n = plan["fps"], plan["nframes"]
    W, H = plan["width"], plan["height"]
    start = args.start
    count = r.n - start if args.count <= 0 else min(args.count, r.n - start)

    audio_input = ["-i", plan["audio"]]
    if start > 0:
        audio_input = ["-ss", f"{start / fps:.3f}", "-i", plan["audio"]]

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
        "-i", "pipe:0",
        *audio_input,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", args.audio_bitrate, "-shortest",
        args.out,
    ]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    t0 = time.time()
    try:
        for k in range(count):
            proc.stdin.write(r.frame(start + k).tobytes())
            if k % 250 == 0:
                el = time.time() - t0
                rate = (k + 1) / max(0.001, el)
                print(f"\r  frame {k}/{count}  {rate:5.1f} fps  "
                      f"eta {(count - k - 1) / max(0.001, rate):5.0f}s",
                      end="", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
    print()
    if rc != 0:
        print(err[-3000:])
        return rc
    mb = Path(args.out).stat().st_size / 1048576
    print(f"  done in {time.time() - t0:.0f}s -> {args.out}  ({mb:.1f} MB)")
    return 0


def cmd_preview(args):
    from . import styles

    plan = _load_plan(args.plan)
    feats = np.load(args.features)
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.style == "all":
        chosen = styles.keys()
    else:
        chosen = [args.style]

    times = [float(x) for x in args.times.split(",") if x.strip()]
    for key in chosen:
        r = _make_renderer(key, plan, feats, args.cover)
        for t in times:
            i = min(r.n - 1, int(round(t * r.fps)))
            p = outdir / f"{key}_{t:06.2f}s.png"
            r.frame(i).save(p, optimize=True)
            print(f"  -> {p}")
    print("done.")
    return 0


def cmd_demo(args):
    """Short audio-bearing clip per style (ported from the production demos)."""
    from . import styles_eh

    plan = _load_plan(args.plan)
    feats = np.load(args.features)
    r = _make_renderer(args.style, plan, feats, args.cover)

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    segs = [tuple(float(x) for x in part.split(","))
            for part in args.segs.replace(";", " ").split() if part.strip()]
    fps = plan["fps"]

    parts = []
    for si, (t0, t1) in enumerate(segs):
        p = outdir / f"{args.style}_seg{si}.mp4"
        styles_eh.render_seg(r, t0, t1, p, Path(plan["audio"]), fps)
        parts.append(p)

    final = outdir / f"{args.style}.mp4"
    lst = outdir / f"{args.style}.concat.txt"
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")
    cp = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                         "-i", str(lst), "-c", "copy", str(final)], capture_output=True)
    if cp.returncode != 0:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-b:a", "192k", str(final)], check=True)
    for p in parts:
        p.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    print(f"  -> {final}  ({final.stat().st_size / 1048576:.1f} MB)")
    return 0


def cmd_cover(args):
    from .cover import render_cover, STANDARD_SIZE, WIDE_SIZE

    W, H = WIDE_SIZE if args.ratio == "16:10" else STANDARD_SIZE
    out, size = render_cover(args.title, args.subtitle, args.out, W, H,
                             energy=args.energy, seed=args.seed, t=args.phase,
                             show_hud=not args.no_hud)
    print(f"OK  {out}  ({W}x{H})  title_size={size}px")
    return 0


# --------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    from . import styles

    ap = argparse.ArgumentParser(
        prog="lyric-mv",
        description="Kinetic lyric MV renderer (Pillow + numpy + ffmpeg).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="verify ffmpeg + fonts").set_defaults(func=cmd_check)
    sub.add_parser("styles", help="list available styles").set_defaults(func=cmd_styles)

    p = sub.add_parser("build-plan", help="audio + lyrics -> plan.json")
    p.add_argument("--audio", required=True)
    p.add_argument("--lyrics", required=True)
    p.add_argument("--song", required=True, help="song config JSON")
    p.add_argument("--outdir", default="work")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.set_defaults(func=cmd_build_plan)

    p = sub.add_parser("render", help="plan.json -> full-song mp4")
    p.add_argument("--plan", required=True)
    p.add_argument("--features", required=True)
    p.add_argument("--style", default="F_aurora_ribbon", choices=styles.keys())
    p.add_argument("--out", required=True)
    p.add_argument("--cover", default=None)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--count", type=int, default=0, help="0 = all frames")
    p.add_argument("--crf", type=int, default=19)
    p.add_argument("--preset", default="medium")
    p.add_argument("--audio-bitrate", default="192k")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("preview", help="render stills at given timestamps")
    p.add_argument("--plan", required=True)
    p.add_argument("--features", required=True)
    p.add_argument("--style", default="all", help="a style key, or 'all'")
    p.add_argument("--out-dir", default="work/stills")
    p.add_argument("--times", default="12,45,90")
    p.add_argument("--cover", default=None)
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("demo", help="short audio-bearing clip per style")
    p.add_argument("--plan", required=True)
    p.add_argument("--features", required=True)
    p.add_argument("--style", required=True, choices=styles.keys())
    p.add_argument("--out-dir", default="work/demos")
    p.add_argument("--segs", default="21.5,32.0 44.4,58.5")
    p.add_argument("--cover", default=None)
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("cover", help="4:3 cover art")
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", default="")
    p.add_argument("--out", default="work/cover.png")
    p.add_argument("--ratio", default="4:3", choices=["4:3", "16:10"])
    p.add_argument("--energy", type=float, default=0.72)
    p.add_argument("--seed", type=int, default=31)
    p.add_argument("--phase", type=float, default=0.0)
    p.add_argument("--no-hud", action="store_true")
    p.set_defaults(func=cmd_cover)

    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
