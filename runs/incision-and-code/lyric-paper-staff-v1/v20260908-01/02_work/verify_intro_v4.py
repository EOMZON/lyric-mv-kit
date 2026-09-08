"""Repeatable structural checks for the MV03 candidate; no media is changed."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
FFMPEG = Path("D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe")
FFPROBE = Path("D:/ZON/runtime/media-tools/Library/bin/ffprobe.exe")
VIDEO = RUN / "03_render" / "incision-and-code-v4-intro-review.mp4"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    design = json.loads((RUN / "01_timeline" / "intro-design-v4.json").read_text(encoding="utf-8"))
    assert design["audio"]["speed"] == 1.0
    assert design["firstCharacter"] == {"char": "公", "start": 9.43, "source": "v3 character-events.json"}
    assert design["notApproved"] and design["notForUpload"]
    assert all((RUN / "05_evidence" / name).exists() for name in ("v4-000.jpg", "v4-650.jpg", "v4-943.jpg", "v4-1120.jpg", "v3-943.jpg"))
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(VIDEO), "-f", "null", "-"], check=True)
    meta = json.loads(subprocess.check_output([str(FFPROBE), "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(VIDEO)], text=True, encoding="utf-8"))
    streams = {s["codec_type"]: s for s in meta["streams"]}
    assert streams["video"]["codec_name"] == "h264"
    assert streams["video"]["width"] == 1920 and streams["video"]["height"] == 1080
    assert streams["video"]["r_frame_rate"] == "24/1"
    assert streams["audio"]["codec_name"] == "aac" and streams["audio"]["sample_rate"] == "44100"
    assert abs(float(meta["format"]["duration"]) - 15.5) < 0.02
    result = {
        "scope": "candidate-only self-check; independent Reviewer still required",
        "verdict": "pass-for-review",
        "videoHash": digest(VIDEO),
        "structuralChecks": {"mp4Decode": "pass", "h264_1920x1080_24fps": "pass", "aac_44100Hz": "pass", "duration_15p5s": "pass", "originalSpeed": "pass", "candidateNotApprovedOrUploadable": "pass"},
        "visualInspectionByBuilder": {"titleAndArtistReadable": "pass at v4-000.jpg", "staffAndEventDrivenNotesVisible": "pass at v4-650.jpg", "firstCharacterFocus": "pass at v4-943.jpg; 公 starts at 09.430s", "subsequentLyricReadability": "pass at v4-1120.jpg", "comparisonEvidence": "v3-943.jpg"},
        "notTested": ["full-song listening", "user approval", "platform upload", "publication"],
    }
    (RUN / "05_evidence" / "candidate-self-check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
