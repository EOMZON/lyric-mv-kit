#!/usr/bin/env python
"""Audit a music catalog for *verified* distribution channels.

Selection harness behind lyric-mv-kit#9. Read-only: never mutates the catalog.

What it answers
---------------
* how many distribution channels each record really has (``url.strip()`` non-empty
  **and** ``platform`` is a distribution channel — see :mod:`lyric_mv.dataset`);
* which records are still placeholders (channel declared, link missing);
* which records would survive the selection gate, optionally intersected with
  audio masters you already have locally — the fastest way to pick a song you
  can actually render today.

Usage
-----
    # channel-count distribution + placeholders + top candidates
    python scripts/audit_catalog.py ../music-board/catalog.json

    # strict: at least 3 channels and must include 网易云
    python scripts/audit_catalog.py catalog.json --min-channels 3 --require netease

    # restrict to songs whose master audio exists locally (skips nothing: matches on filename stem)
    python scripts/audit_catalog.py catalog.json --local-master ../music-pipeline/album

    # machine-readable output for issue comments / CI
    python scripts/audit_catalog.py catalog.json --json audit.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Any, Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyric_mv.dataset import (  # noqa: E402
    duplicate_titles,
    has_placeholder_links,
    link_audit,
    real_platforms,
    select_real_distributed,
)

AUDIO_SUFFIXES = (".flac", ".wav", ".mp3", ".m4a", ".aiff", ".aif", ".ogg")


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("items", "records", "songs", "tracks"):
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
        # single-record catalogs are unlikely; fall back to values that look like records
        return [v for v in data.values() if isinstance(v, dict) and "links" in v]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    raise SystemExit(f"unsupported catalog shape in {path}")


def local_master_titles(root: Path) -> dict[str, set[str]]:
    """Map ``filename stem -> set of album folders`` for local audio masters."""
    found: dict[str, set[str]] = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.lower().endswith(AUDIO_SUFFIXES):
                album = PureWindowsPath(os.path.relpath(dirpath, root)).as_posix()
                found.setdefault(Path(name).stem, set()).add(album)
    return found


def _best_platforms(records: Sequence[dict[str, Any]]) -> set[str]:
    """The strongest **single** record — never a union across duplicates."""
    if not records:
        return set()
    return max((real_platforms(r) for r in records), key=len)


def index_by_title(records: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("type") not in (None, "song"):
            continue
        title = str(record.get("title", "")).strip().lower()
        if title:
            index.setdefault(title, []).append(record)
    return index


def _merge(records: Sequence[dict[str, Any]]) -> tuple[set[str], str, int]:
    """Union channels across title duplicates.

    Marked low confidence on purpose: the catalog owner has not adjudicated
    these collisions, so this is a *lead generator*, not a gate.
    """
    union = {r for record in records for r in real_platforms(record)}
    artists = sorted({str(r.get("artist") or "?") for r in records})
    return union, "low (title collision, not merged upstream)", len(records)


def build_report(
    records: Sequence[dict[str, Any]],
    *,
    min_channels: int,
    require: tuple[str, ...],
    masters: dict[str, set[str]] | None,
    merge_duplicates: bool = False,
) -> dict[str, Any]:
    songs = [r for r in records if r.get("type") == "song"]
    distribution = Counter(len(real_platforms(r)) for r in songs)
    placeholders = sum(1 for r in records if has_placeholder_links(r))

    candidates = select_real_distributed(
        records, min_n=min_channels, require=require
    )

    if masters is not None:
        index = index_by_title(records)
        duplicates = duplicate_titles(records)
        enriched: list[dict[str, Any]] = []
        for title, albums in masters.items():
            key = title.strip().casefold()
            matched = index.get(key, [])
            if not matched:
                continue
            platforms = _best_platforms(matched)
            artists = sorted({str(r.get("artist") or "?") for r in matched})
            row = {
                "title": title,
                "master_albums": sorted(albums),
                "channels": sorted(platforms),
                "channel_count": len(platforms),
                "duplicate_records": len(matched),
                "identity_confidence": (
                    "single record" if len(matched) == 1
                    else "LOW: title collision across %s" % artists
                ),
            }
            if len(platforms) < min_channels or (set(require) - platforms):
                if not (merge_duplicates and duplicates.get(key)):
                    continue
                platforms, row["identity_confidence"], row["duplicate_records"] = _merge(matched)
                row["channels"] = sorted(platforms)
                row["channel_count"] = len(platforms)
                row["merged"] = True
                if len(platforms) < min_channels or (set(require) - platforms):
                    continue
            enriched.append(row)
        enriched.sort(key=lambda row: (-row["channel_count"], row["title"]))
        candidates_section: Any = enriched
    else:
        candidates_section = candidates

    return {
        "records": len(records),
        "songs": len(songs),
        "channel_distribution": dict(sorted(distribution.items(), reverse=True)),
        "records_with_placeholder_links": placeholders,
        "gate": {"min_channels": min_channels, "require": list(require)},
        "candidates_count": len(candidates_section),
        "candidates": candidates_section,
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("catalog", type=Path, help="path to catalog.json")
    ap.add_argument("--min-channels", type=int, default=3,
                    help="gate threshold (default: 3)")
    ap.add_argument("--require", action="append", default=[],
                    help="channel that must be present; repeatable")
    ap.add_argument("--local-master", type=Path, default=None,
                    help="root dir of local audio masters to intersect with")
    ap.add_argument("--merge-duplicates", action="store_true",
                    help="union channels across same-title records (LOW identity "
                         "confidence; for lead generation, never for the gate)")
    ap.add_argument("--limit", type=int, default=25, help="rows to print")
    ap.add_argument("--json", type=Path, default=None, help="also write JSON report")
    args = ap.parse_args(argv)

    if not args.catalog.exists():
        raise SystemExit(f"catalog not found: {args.catalog}")

    records = load_records(args.catalog)
    masters = local_master_titles(args.local_master) if args.local_master else None
    report = build_report(
        records,
        min_channels=args.min_channels,
        require=tuple(args.require),
        masters=masters,
        merge_duplicates=args.merge_duplicates,
    )

    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    print(f"records: {report['records']}  songs: {report['songs']}")
    print("channel distribution (real distribution channels only):")
    for count, n in sorted(report["channel_distribution"].items(),
                           key=lambda kv: -int(kv[0])):
        print(f"  {count} channels : {n}")
    print(f"records with placeholder links: {report['records_with_placeholder_links']}")
    gate = report["gate"]
    print(f"\ngate: >= {gate['min_channels']} channels"
          + (f", require {gate['require']}" if gate["require"] else ""))
    print(f"candidates: {report['candidates_count']}")

    rows = report["candidates"][: args.limit]
    if masters is not None:
        print("\nlocal masters that pass the gate:")
        for row in rows:
            flag = ("MERGED" if row.get("merged")
                    else ("DUP" if row.get("duplicate_records", 1) > 1 else ""))
            dup = f" dup={row['duplicate_records']}" + (f" {flag}" if flag else "")
            print(f"  {row['channel_count']}ch | {row['title'][:26]:26} | "
                  f"{row['master_albums'][0][:30]:30} | {row['channels']}{dup}")
            if str(row.get("identity_confidence", "")).startswith("LOW"):
                print(f"         ^ identity: {row['identity_confidence']}")
    else:
        print("\ntop candidates:")
        for row in rows:
            print(f"  {len(row['real_platforms'])}ch | {str(row['title'])[:30]:30} | "
                  f"{str(row['artist'])[:12]:12} | {row['real_platforms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
