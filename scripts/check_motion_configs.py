#!/usr/bin/env python3
"""Static validation for bundled motion templates and optional score files."""
from __future__ import annotations

import argparse
from pathlib import Path

from lyric_mv.motion import load_score, load_template


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset-dir", default="presets/motion")
    ap.add_argument("--score", action="append", default=[])
    ap.add_argument("--duration", type=float, default=None)
    args = ap.parse_args()

    root = Path(args.preset_dir)
    files = sorted(root.glob("*.json"))
    if not files:
        raise SystemExit(f"no motion templates found: {root}")
    ids = set()
    for path in files:
        value = load_template(path)
        tid = value["id"]
        if tid in ids:
            raise SystemExit(f"duplicate motion template id: {tid}")
        ids.add(tid)
        print(f"PASS template {tid:18s} {path}")

    for raw in args.score:
        value = load_score(raw, duration=args.duration)
        template = value.get("template")
        if template and template not in ids:
            raise SystemExit(f"score {raw} references unknown template {template!r}")
        print(f"PASS score    {value.get('id', Path(raw).stem)} {raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
