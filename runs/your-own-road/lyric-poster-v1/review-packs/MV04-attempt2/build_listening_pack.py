"""Create a pending-only audition pack for MV04 timeline review.

This script does not modify the v20260908-01 candidate.  It extracts short
source-audio contexts for a human reviewer and writes hashes/readback data.
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[3]
LEGACY = RUNS / "your-own-road-poster-full"
CANDIDATE = RUNS / "your-own-road" / "lyric-poster-v1" / "v20260908-01"
FFMPEG = Path("D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe")
SOURCE_DURATION = 76.821
CONTEXT = 1.25
TARGETS = [
    (5, 6, "赢"), (5, 8, "忧"), (6, 5, "里"), (7, 1, "着"), (7, 7, "控"),
    (8, 11, "式"), (10, 2, "向"), (13, 1, "了"), (18, 3, "谁"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact(value: float) -> str:
    return f"{value:.3f}".replace(".", "p")


def main() -> None:
    clips = HERE / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    source = json.loads((LEGACY / "source.json").read_text(encoding="utf-8"))
    automatic = json.loads((LEGACY / "aligned.json").read_text(encoding="utf-8"))
    candidate = json.loads((CANDIDATE / "01_timeline" / "timing-candidate.json").read_text(encoding="utf-8"))
    audio = Path(source["source"]["audio"])
    proposed = {(entry["cueIndex"], entry["charIndex"]): entry for entry in candidate["edits"]}
    items = []
    for ordinal, (cue_index, char_index, char) in enumerate(TARGETS, start=1):
        old = automatic["segments"][cue_index]["words"][char_index]
        proposal = proposed[(cue_index, char_index)]
        assert old["word"].strip() == char == proposal["char"]
        clip_start = max(0.0, min(old["start"], proposal["start"]) - CONTEXT)
        clip_end = min(SOURCE_DURATION, max(old["end"], proposal["end"]) + CONTEXT)
        filename = (
            f"{ordinal:02d}_cue{cue_index + 1:02d}_{char}_"
            f"old-{compact(old['start'])}-{compact(old['end'])}_"
            f"proposed-{compact(proposal['start'])}-{compact(proposal['end'])}_"
            f"context-{compact(clip_start)}-{compact(clip_end)}.m4a"
        )
        clip = clips / filename
        command = [
            str(FFMPEG), "-y", "-v", "error", "-ss", f"{clip_start:.3f}", "-i", str(audio),
            "-t", f"{clip_end - clip_start:.3f}", "-map", "0:a:0", "-vn", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(clip),
        ]
        subprocess.run(command, check=True)
        items.append({
            "ordinal": ordinal,
            "cueIndex": cue_index,
            "cueNumber": cue_index + 1,
            "cueText": automatic["segments"][cue_index]["text"],
            "charIndex": char_index,
            "char": char,
            "oldSpan": {"start": old["start"], "end": old["end"]},
            "proposedSpan": {"start": proposal["start"], "end": proposal["end"]},
            "clip": {"path": f"clips/{filename}", "start": clip_start, "end": clip_end, "sha256": sha256(clip)},
            "reviewer": None,
            "observedAt": None,
            "verdict": "pending",
            "notes": "Do not infer a pass from the proposed span or from the clip's existence.",
        })
    concat_list = HERE / "concat-list.txt"
    concat_list.write_text("\n".join("file '" + item["clip"]["path"].replace("'", "'\\\\''") + "'" for item in items) + "\n", encoding="utf-8")
    combined = HERE / "MV04-attempt2-ordered-audition.m4a"
    subprocess.run([
        str(FFMPEG), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-map", "0:a:0", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(combined),
    ], check=True)
    manifest = {
        "packId": "MV04-attempt2",
        "purpose": "one-time human audition for the nine former zero-duration characters",
        "sourceAudio": str(audio),
        "sourceAudioSha256": sha256(audio),
        "sourceDurationSeconds": SOURCE_DURATION,
        "candidateReference": "../../v20260908-01/01_timeline/timing-candidate.json",
        "automaticReference": "../../../your-own-road-poster-full/aligned.json",
        "manualListeningVerified": False,
        "reviewer": None,
        "observedAt": None,
        "verdict": "pending",
        "items": items,
        "orderedAudition": {"path": combined.name, "sha256": sha256(combined), "order": [item["ordinal"] for item in items]},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "generationCommand": "build_listening_pack.py (short-context AAC extraction only; no alignment, separation, or video render)",
    }
    (HERE / "review-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    index = [
        "# MV04-attempt2 · 人耳审听包",
        "",
        "状态：`pending`。请只根据音频听感记录保留／修改／拒绝；不要将候选时间或本文件存在当作通过。",
        "",
        "审听顺序（合集与下列片段一致）：",
        "",
    ]
    for item in items:
        index.append(
            f"{item['ordinal']}. cue {item['cueNumber']}「{item['cueText']}」—「{item['char']}」："
            f"旧 {item['oldSpan']['start']:.3f}–{item['oldSpan']['end']:.3f}s；"
            f"候选 {item['proposedSpan']['start']:.3f}–{item['proposedSpan']['end']:.3f}s；"
            f"[{item['clip']['path']}]({item['clip']['path']})"
        )
    index.extend([
        "",
        f"合集：[{combined.name}]({combined.name})。",
        "",
        "待填写字段位于 `review-manifest.json`：每项 `reviewer`、`observedAt`、`verdict`。本 Builder 不填这些字段。",
    ])
    (HERE / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
