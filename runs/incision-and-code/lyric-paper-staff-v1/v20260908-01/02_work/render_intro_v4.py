"""Render a review-only v4 intro study for 切口与暗号.

This is deliberately a new run: it reads the v3 source/timings but never writes
to them.  The 15.5-second segment uses the original MP3 from 00:00 at original
speed, with the first sung character at the v3's measured 9.43 seconds.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[3]
LEGACY = ROOT / "runs" / "incision-paper-full"
AUDIO = ROOT / "samples" / "review" / "real-song-demos" / "00_source" / "incision-code" / "netease.mp3"
V3 = LEGACY / "03_render" / "incision-paper-full-v3-retained.mp4"
FFMPEG = Path("D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe")
FFPROBE = Path("D:/ZON/runtime/media-tools/Library/bin/ffprobe.exe")
FONT = ROOT / "assets" / "fonts" / "reusable" / "LongCang-Regular.ttf"
OUT = RUN / "03_render" / "incision-and-code-v4-intro-review.mp4"
COMPARATOR = RUN / "03_render" / "incision-and-code-v3-intro-comparator.mp4"
DURATION, FPS, WIDTH, HEIGHT = 15.5, 24, 1280, 720
FIRST = [
    ("公", 9.43, 10.23), ("告", 10.23, 10.57), ("栏", 10.57, 10.99),
    ("上", 10.99, 11.41), ("贴", 11.41, 12.19), ("到", 12.19, 12.35),
    ("最", 12.35, 12.53), ("后", 12.53, 12.71), ("一", 12.71, 12.93), ("张", 12.93, 13.25),
]
# Measured audio events from the existing v3 music-events.json, retained here
# as a bounded intro-only subset. They are decorative rhythm cues, not pitch.
BEATS = [0.081, 0.766, 1.126, 1.753, 2.055, 2.403, 3.437, 6.107, 6.444, 6.780, 7.094, 7.430, 9.230, 10.066, 10.437, 10.762, 11.111, 11.297, 11.424, 11.773, 12.063, 12.434, 12.759, 13.050, 13.421, 13.769, 14.083, 14.431, 14.756, 15.023]


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rgba(blend: float, a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(round(x * (1 - blend) + y * blend) for x, y in zip(a, b))


def note(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, color: tuple[int, int, int]) -> None:
    draw.ellipse((x - size, y - size * .72, x + size, y + size * .72), fill=color)
    draw.line((x + size * .72, y, x + size * .72, y - size * 4.4), fill=color, width=max(2, round(size / 3)))
    draw.line((x + size * .72, y - size * 4.4, x + size * 2.3, y - size * 3.8), fill=color, width=max(2, round(size / 3)))


def frame(t: float) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (238, 235, 225))
    draw = ImageDraw.Draw(canvas)
    ink, blue, muted = (33, 48, 55), (55, 116, 141), (118, 133, 135)
    title_font = ImageFont.truetype(str(FONT), 46)
    artist_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    lyric_font = ImageFont.truetype(str(FONT), 82)
    small_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    draw.text((66, 44), "切口与暗号", font=title_font, fill=ink)
    draw.text((69, 98), "ROYAZON EOM  ·  v4 前奏短样（候选，未批准）", font=artist_font, fill=muted)

    # 0–3: the staff is built line by line; 3–7: actual detected rhythm events
    # accumulate.  7–9.43: the visual narrows into the lyric reading area.
    line_progress = min(1.0, t / 3.0)
    left = 126 + 60 * max(0.0, min(1.0, (t - 7.0) / 2.43))
    right = 1154 - 180 * max(0.0, min(1.0, (t - 7.0) / 2.43))
    staff_y = 238
    for i in range(5):
        reveal = max(0.0, min(1.0, line_progress * 5 - i))
        x2 = left + (right - left) * reveal
        if x2 > left:
            draw.line((left, staff_y + i * 31, x2, staff_y + i * 31), fill=rgba(reveal, (202, 205, 195), blue), width=2)

    active = [b for b in BEATS if b <= t]
    for idx, beat in enumerate(active):
        age = t - beat
        if age > 4.2:
            continue
        x = left + ((idx * 83) % max(120, int(right - left - 40)))
        y = staff_y + 76 - ((idx * 31) % 110)
        pulse = max(0.0, 1.0 - age / 4.2)
        note(draw, x, y, 7 + 8 * pulse, rgba(pulse, muted, blue))

    focus = max(0.0, min(1.0, (t - 7.0) / 2.43))
    if focus:
        panel = (int(115 * focus), 424, int(1165 - 115 * focus), 640)
        draw.rounded_rectangle(panel, radius=18, fill=(244, 242, 234), outline=rgba(focus, (215, 216, 207), blue), width=2)
        draw.text((panel[0] + 34, panel[1] + 26), "第一句 · 实测首字 09.430s", font=small_font, fill=muted)
        x = panel[0] + 44
        baseline = panel[1] + 78
        for char, start, end in FIRST:
            if t < start:
                color = (188, 192, 185)
            elif start <= t <= end:
                color = blue
                draw.rounded_rectangle((x - 8, baseline - 10, x + 74, baseline + 100), radius=14, fill=(218, 232, 235))
            else:
                color = ink
            draw.text((x, baseline), char, font=lyric_font, fill=color)
            x += 76
    return canvas


def main() -> None:
    for folder in ("00_source", "01_timeline", "03_render", "05_evidence"):
        (RUN / folder).mkdir(parents=True, exist_ok=True)
    if not AUDIO.exists() or not V3.exists() or not FONT.exists():
        raise FileNotFoundError("Required read-only v3/audio/font input is unavailable")
    design = {
        "kind": "review-only optional v4 intro study",
        "audio": {"source": str(AUDIO), "start": 0, "duration": DURATION, "speed": 1.0, "audioHash": sha256(AUDIO)},
        "firstCharacter": {"char": "公", "start": 9.43, "source": "v3 character-events.json"},
        "stages": [
            {"range": "0.00–3.00", "change": "staff lines reveal"},
            {"range": "3.00–7.00", "change": "decorative notes accumulate only at measured audio events"},
            {"range": "7.00–9.43", "change": "staff converges into the reading panel"},
            {"range": "9.43–15.50", "change": "first line enters character-by-character using v3 measured timings"},
        ],
        "notApproved": True,
        "notForUpload": True,
        "doesNotReplace": str(V3),
        "noteSemantics": "decorative rhythmic notes, not pitch transcription",
    }
    save(RUN / "01_timeline" / "intro-design-v4.json", design)
    save(RUN / "00_source" / "source-lock.json", {"catalogSongId": "netease-song-3334952179", "audioHash": sha256(AUDIO), "actualDuration": 146.541995, "sourceType": "existing v3 source audio; read-only", "verifiedBy": "MV03-attempt1"})
    cmd = [str(FFMPEG), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-i", str(AUDIO), "-t", str(DURATION), "-map", "0:v:0", "-map", "1:a:0", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT)]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        assert process.stdin is not None
        for n in range(math.ceil(DURATION * FPS)):
            process.stdin.write(frame(n / FPS).tobytes())
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("ffmpeg render failed")
    subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(V3), "-t", str(DURATION), "-map", "0:v:0", "-map", "0:a:0", "-c", "copy", str(COMPARATOR)], check=True)
    for label, stamp in (("v4-000", 0.0), ("v4-650", 6.5), ("v4-943", 9.43), ("v4-1120", 11.2), ("v3-943", 9.43)):
        source = OUT if label.startswith("v4") else COMPARATOR
        subprocess.run([str(FFMPEG), "-y", "-v", "error", "-ss", str(stamp), "-i", str(source), "-frames:v", "1", str(RUN / "05_evidence" / f"{label}.jpg")], check=True)
    subprocess.run([str(FFMPEG), "-v", "error", "-i", str(OUT), "-f", "null", "-"], check=True)
    probe = subprocess.check_output([str(FFPROBE), "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(OUT)], text=True, encoding="utf-8")
    save(RUN / "05_evidence" / "ffprobe-v4.json", json.loads(probe))
    save(RUN / "05_evidence" / "render-result.json", {"video": str(OUT), "videoHash": sha256(OUT), "comparisonVideo": str(COMPARATOR), "comparisonVideoHash": sha256(COMPARATOR), "duration": DURATION, "status": "candidate-not-approved", "decode": "pass", "audio": "aac copied from original-source timeline at 1.0x", "firstCharacterFocusFrame": "v4-943.jpg"})


if __name__ == "__main__":
    main()
