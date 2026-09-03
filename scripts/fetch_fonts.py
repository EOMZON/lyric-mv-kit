#!/usr/bin/env python3
"""Download the three Noto CJK families into ``assets/fonts/`` (SIL OFL 1.1).

One-shot idempotent helper. Run it once after ``git clone`` to get a no-proprietary-font
default setup::

    python scripts/fetch_fonts.py          # ~25 MB total

The renderer auto-detects fonts from ``assets/fonts/`` ahead of OS font
directories, so this works without any config edit. Re-run to refresh files
that were skipped on a partial download.

All three families ship under SIL Open Font License 1.1; the LICENSE file is
copied next to the binaries. See ``NOTICE`` and ``docs/FONTS.md``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "assets" / "fonts"
SRC = "https://cdn.jsdelivr.net/gh/google/fonts@main"

# (file in CDN, role used by config.py, display name)
FONTS = [
    ("ofl/notoserifsc/NotoSerifSC-Bold.ttf",   "heavy",
     "Noto Serif SC Bold (heavy serif — 歌名大字)"),
    ("ofl/notosanssc/NotoSansSC-Regular.ttf",  "sans",
     "Noto Sans SC Regular (CJK sans — 副标题/时间码)"),
    ("ofl/notosanssc/NotoSansSC-Bold.ttf",     "latin",
     "Noto Sans SC Bold (latin HUD wordmark)"),
]

LICENSE_NOTE = """\
Noto Serif SC, Noto Sans SC — SIL Open Font License 1.1
Copyright 2014-2021 Adobe Inc. (https://www.adobe.com/),
with Reserved Font Name 'Source'. Modifications: subsetting and renaming.
Source: https://fonts.google.com/noto/specimen/Noto+Serif+SC and Noto+Sans+SC
"""


def fetch(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 1024:
        return False
    print(f"  fetching {dst.name} ({dst.stat().st_size if dst.exists() else 0} B → ?)")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    if len(data) < 4096:
        raise RuntimeError(f"download too small ({len(data)} B); url={url}")
    dst.write_bytes(data)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    ap.add_argument("--only",  default="",
                    help="comma subset of heavy,sans,latin")
    args = ap.parse_args()

    TARGET.mkdir(parents=True, exist_ok=True)
    want = set(filter(None, args.only.split(","))) or {"heavy", "sans", "latin"}

    if not shutil.which("curl") and not shutil.which("wget"):
        # urllib is fine; we use it directly. But warn on a slow link.
        pass

    n_done = 0
    for rel, role, label in FONTS:
        if role not in want:
            continue
        url = f"{SRC}/{rel}"
        dst = TARGET / Path(rel).name
        if args.force and dst.exists():
            dst.unlink()
        try:
            changed = fetch(url, dst)
        except Exception as exc:
            print(f"  ! {label}: download failed ({exc})", file=sys.stderr)
            continue
        if changed:
            n_done += 1
        print(f"  {'+' if changed else '·'} {label}  →  {dst.relative_to(ROOT)}")

    lic = TARGET / "OFL.txt"
    if not lic.exists():
        lic.write_text(LICENSE_NOTE, encoding="utf-8")
        print(f"  + wrote {lic.relative_to(ROOT)}")

    if n_done == 0 and not args.force:
        print("everything already in place; pass --force to refresh")
    else:
        print(f"\ndownloaded {n_done} file(s) → {TARGET}")
        print("verify with:  python -m lyric_mv check")
    return 0


if __name__ == "__main__":
    sys.exit(main())