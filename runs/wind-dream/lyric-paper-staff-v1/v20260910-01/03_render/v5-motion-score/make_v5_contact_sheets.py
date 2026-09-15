"""Build v5 review contact sheets: a 12-frame journey sheet + an 8-boundary sheet."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MP4 = HERE / "wind-dream-v5-motion-score.mp4"
FFMPEG = r"D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\msyh.ttc"


def extract(times, outdir):
    outdir.mkdir(exist_ok=True)
    paths = []
    for t in times:
        p = outdir / f"f{t:06.2f}.png"
        subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(MP4),
                        "-frames:v", "1", str(p)], check=True)
        paths.append((t, p))
    return paths


def sheet(items, cols, cell_w, label_h, dest):
    cell_h = round(cell_w * 720 / 1280)
    rows = (len(items) + cols - 1) // cols
    W = cols * (cell_w + 8) + 8
    H = rows * (cell_h + label_h + 8) + 8
    canvas = Image.new("RGB", (W, H), (18, 20, 24))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 24)
    for k, (label, path) in enumerate(items):
        r, c = divmod(k, cols)
        img = Image.open(path).convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = 8 + c * (cell_w + 8)
        y = 8 + r * (cell_h + label_h + 8)
        canvas.paste(img, (x, y))
        d.text((x + 6, y + cell_h + 4), label, font=f, fill=(240, 240, 240))
    canvas.save(dest, quality=90)
    print(dest)


def main():
    journey = [1.04, 3.0, 4.34, 6.0, 7.40, 9.0, 10.08, 12.0, 13.20, 16.98, 19.90, 21.50]
    items = [(f"t={t:.2f}s", p) for t, p in extract(journey, HERE / "_contact_frames")]
    sheet(items, 4, 440, 34, HERE / "v5-contact-journey.jpg")
    bounds = [1.04, 4.34, 7.40, 10.08, 13.20, 16.98, 19.90, 21.90]
    items2 = [(f"t={t:.2f}s", HERE / f"v5-{t:.2f}.jpg") for t in bounds]
    sheet(items2, 4, 440, 34, HERE / "v5-contact-boundaries.jpg")


if __name__ == "__main__":
    main()
