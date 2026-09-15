"""Matched-timestamp side-by-side comparison sheet: v4 (control) vs v5 (motion score)."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
V5_MP4 = HERE / "wind-dream-v5-motion-score.mp4"
V4_MP4 = Path(r"D:\ZON\codex\lyric-mv-kit\runs\wind-dream\lyric-paper-staff-v1\v20260910-01\03_render\v4-dynamic-smooth\wind-dream-v4-dynamic-smooth.mp4")
FFMPEG = r"D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TIMES = [1.04, 4.34, 7.40, 10.08, 13.20, 16.98]


def grab(mp4, t, dest):
    subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
                    "-frames:v", "1", str(dest)], check=True)
    return Image.open(dest).convert("RGB")


def main():
    tmp = HERE / "_compare_frames"
    tmp.mkdir(exist_ok=True)
    cell_w = 520
    cell_h = round(cell_w * 720 / 1280)
    pad, lab = 8, 40
    cols = len(TIMES)
    W = pad + cols * (cell_w + pad)
    H = pad + 2 * (cell_h + lab + pad)
    canvas = Image.new("RGB", (W, H), (18, 20, 24))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 22)
    for r, (tag, mp4) in enumerate([("V4 (control, static frame)", V4_MP4),
                                    ("V5 (motion score, moving frame)", V5_MP4)]):
        for c, t in enumerate(TIMES):
            img = grab(mp4, t, tmp / f"r{r}-{t:.2f}.png").resize((cell_w, cell_h),
                                                                 Image.Resampling.LANCZOS)
            x = pad + c * (cell_w + pad)
            y = pad + r * (cell_h + lab + pad)
            canvas.paste(img, (x, y))
            d.text((x + 6, y + cell_h + 6), f"{tag}  t={t:.2f}s", font=f, fill=(240, 240, 240))
    out = HERE / "v4-vs-v5-compare.jpg"
    canvas.save(out, quality=90)
    print(out)


if __name__ == "__main__":
    main()
