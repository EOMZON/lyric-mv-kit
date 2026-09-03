"""4 style variants preview generator.

Imports the live Renderer from 02_render.py (HUD already updated to show the
song title at top-right and drop the artist "音右" display), then subclasses
it for 4 fully different visual treatments and renders 3 key-time frames per
style into 03_preview/_styles/.

This is a preview-only tool. It does NOT overwrite the existing v4 master.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import renderer as render

W, H = render.W, render.H
text_layer = render.text_layer
font = render.font
paste = render.paste
FONT_SANS = render.FONT_SANS
FONT_LATIN = render.FONT_LATIN

DEFAULT_OUT = Path("03_preview/_styles")

# (time_seconds, label) — default sample points of the shipped demo song.
# Pass --times to sample your own track without editing this file.
TIMES = [
    (24.0, "verse1"),
    (49.0, "chorus1"),
    (78.0, "verse2"),
]


def _save(r, t, name, outdir):
    i = int(round(t * r.fps))
    img = r.frame(i)
    p = Path(outdir) / f"{name}_{t:05.1f}s.png"
    img.save(p, optimize=True)
    return p


# ============================================================ A. Editorial Air (浅纸底 · 印刷编辑)
class StyleEditorialAir(render.Renderer):
    NAME = "A_editorial_air"
    INK = (32, 28, 26)
    WARM = (150, 110, 80)

    def background(self, i, acc, bass, treb):
        arr = np.full((H, W, 3), 235.0, dtype=np.float32)
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
        arr = arr - 16.0 * yy                       # 上亮下微沉
        arr[..., 0] += 4.0                          # 纸的微暖
        arr[..., 2] -= 3.0
        arr = np.clip(arr, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8), "RGB")
        d = ImageDraw.Draw(img, "RGBA")
        # 编辑式栏线
        d.line([(150, 120), (150, H - 120)], fill=(150, 130, 110, 70), width=1)
        d.line([(W - 150, 120), (W - 150, H - 120)], fill=(150, 130, 110, 70), width=1)
        return img

    def draw_spectrum(self, img, i, bass): pass
    def draw_particles(self, img, i, bass, treb): pass

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        wm = text_layer("ROYAZON", FONT_LATIN, 24, (40, 36, 32), (150, 110, 80), 6, 0.9)
        img.paste(wm, (180, 92), wm)
        cl = self.corner_layer
        # 浅底上把右上角字改成深色
        dark_corner = text_layer(f"《{self.p['title']}》", FONT_SANS, 30,
                                 (60, 52, 46), (150, 110, 80), 6, 0.7)
        img.paste(dark_corner, (W - 180 - dark_corner.width, 88), dark_corner)
        d.line([(180, H - 120), (W - 180, H - 120)],
               fill=(120, 100, 82, 120), width=1)
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        ts_l = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                          FONT_SANS, 22, (70, 60, 52), (150, 110, 80), 4, 0.7)
        img.paste(ts_l, (180, H - 86), ts_l)
        cue = None
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                cue = c
                break
        if cue:
            cap = text_layer(f"{cue['section'].upper()}  ·  {self.p['album']}",
                             FONT_SANS, 18, (110, 92, 72), (150, 110, 80), 3, 0.6)
            img.paste(cap, (W - 180 - cap.width, H - 88), cap)
        # 左侧竖排 section 标注（编辑感）
        if cue:
            vert = text_layer(cue["section"].upper(), FONT_LATIN, 20,
                              (120, 100, 80), (150, 110, 80), 3, 0.6)
            img.paste(vert, (110, H // 2 - 40), vert)

    def draw_lyric(self, img, t, i, acc):
        cue = None
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                cue = c
                break
        if cue is None:
            return
        u = (t - cue["start"]) / max(0.001, cue["end"] - cue["start"])
        chorus = cue["section"].startswith("chorus")
        size = 132 if chorus else 112
        base = text_layer(cue["text"], FONT_SANS, size,
                          (30, 26, 24), (150, 110, 80), 8, 0.9)
        reveal = max(0.0, min(1.0, u / 0.85))
        clip = base.crop((0, 0, max(1, int(base.width * reveal)), base.height))
        paste(img, clip, W / 2 - (base.width - clip.width) / 2, H // 2 - 40, 1.0, 1.0)


# ============================================================ B. Album Sleeve
class StyleAlbumSleeve(render.Renderer):
    NAME = "B_album_sleeve"

    def background(self, i, acc, bass, treb):
        arr = np.full((H, W, 3), 16.0, dtype=np.float32)
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
        arr = arr * (1.0 - 0.4 * yy)
        arr[..., 0] += 4
        arr[..., 1] += 2
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass): pass
    def draw_particles(self, img, i, bass, treb): pass
    def draw_lyric(self, img, t, i, acc):
        # the current lyric line is rendered inside the sleeve card in draw_hud
        return

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        cx, cy = W // 2, H // 2 - 60
        cw, chh = 520, 520
        x0, y0 = cx - cw // 2, cy - chh // 2
        d.rectangle([(x0, y0), (x0 + cw, y0 + chh)], fill=(24, 24, 26, 255))
        d.rectangle([(x0, y0), (x0 + cw, y0 + chh)], outline=(200, 190, 170, 200), width=2)
        d.rectangle([(x0 + 16, y0 + 16), (x0 + cw - 16, y0 + chh - 16)],
                    outline=(120, 110, 95, 160), width=1)
        tl = text_layer(self.p["title"], FONT_SANS, 78, (235, 230, 220),
                        (180, 160, 130), 8, 0.9)
        paste(img, tl, cx, y0 + 130, 1.0, 1.0)
        sub = text_layer(f"ROYAZON  ·  《{self.p['album']}》",
                         FONT_SANS, 22, (190, 180, 160), (120, 100, 80), 4, 0.6)
        paste(img, sub, cx, y0 + 188, 1.0, 1.0)
        d.line([(x0 + 60, y0 + 240), (x0 + cw - 60, y0 + 240)],
               fill=(160, 145, 120, 180), width=1)
        cue = None
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                cue = c
                break
        if cue:
            ll = text_layer(cue["text"], FONT_SANS, 38, (225, 220, 205),
                            (160, 140, 110), 4, 0.6)
            paste(img, ll, cx, y0 + 340, 1.0, 1.0)
        cat = text_layer("CAT.NO.  ROYA · 2026", FONT_LATIN, 16,
                         (170, 160, 140), (90, 80, 60), 2, 0.4)
        paste(img, cat, cx, y0 + chh - 36, 1.0, 1.0)
        gh, gw = H // 2, W // 2
        g = np.random.default_rng(int(t * self.fps)).normal(0, 7, (gh, gw))
        from PIL import Image as _I
        grain = np.asarray(_I.fromarray(g.astype(np.float32), "F").resize(
            (W, H), _I.BILINEAR)).astype(np.int16)
        a = np.asarray(img).astype(np.int16)
        a = np.clip(a + grain[..., None], 0, 255).astype(np.uint8)
        img.paste(Image.fromarray(a, "RGB"))
        wm = text_layer("ROYAZON", FONT_LATIN, 22, (190, 175, 150), (90, 70, 40), 4, 0.6)
        img.paste(wm, (90, 70), wm)
        cl = self.corner_layer
        img.paste(cl, (W - 90 - cl.width, 66), cl)
        d.line([(140, H - 60), (W - 140, H - 60)], fill=(160, 145, 120, 110), width=1)
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        ts_l = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                          FONT_SANS, 22, (180, 165, 140), (90, 70, 40), 4, 0.6)
        img.paste(ts_l, (140, H - 38), ts_l)


# ============================================================ C. Cinematic Letterbox
class StyleCinematic(render.Renderer):
    NAME = "C_cinematic_letterbox"
    BAR = 78

    def background(self, i, acc, bass, treb):
        arr = np.full((H, W, 3), 4.0, dtype=np.float32)
        cy = H // 2
        yrange = 70
        vals = self.band_mix @ self.bands[i]
        for k in range(self.nbar):
            v = float(vals[k])
            ca = math.cos(self.angles[k])
            hx = int(W * 0.5 + ca * W * 0.42 * (1.0 + v * 0.5))
            top = cy + math.sin(self.angles[k]) * yrange
            bar = max(2, int(2 + v * 56))
            col = self.bar_col[k]
            y0 = int(max(0, top - bar // 2))
            y1 = int(min(H, top + bar // 2 + 1))
            x0 = int(max(0, hx - 2))
            x1 = int(min(W, hx + 2))
            if y1 <= y0 or x1 <= x0:
                continue
            arr[y0:y1, x0:x1, 0] = np.maximum(arr[y0:y1, x0:x1, 0], col[0])
            arr[y0:y1, x0:x1, 1] = np.maximum(arr[y0:y1, x0:x1, 1], col[1])
            arr[y0:y1, x0:x1, 2] = np.maximum(arr[y0:y1, x0:x1, 2], col[2])
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass): pass
    def draw_particles(self, img, i, bass, treb): pass

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([(0, 0), (W, self.BAR)], fill=(0, 0, 0, 255))
        d.rectangle([(0, H - self.BAR), (W, H)], fill=(0, 0, 0, 255))
        d.line([(0, self.BAR), (W, self.BAR)], fill=(120, 180, 220, 140), width=1)
        d.line([(0, H - self.BAR), (W, H - self.BAR)], fill=(120, 180, 220, 140), width=1)
        wm = text_layer("ROYAZON", FONT_LATIN, 22, (190, 200, 220), (60, 100, 160), 4, 0.7)
        img.paste(wm, (90, 28), wm)
        cl = self.corner_layer
        img.paste(cl, (W - 90 - cl.width, 24), cl)
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        ts_l = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                          FONT_SANS, 22, (190, 200, 220), (60, 100, 160), 4, 0.7)
        img.paste(ts_l, (90, H - 50), ts_l)
        cap = text_layer("ROYA STUDIO  ·  SIDE A", FONT_LATIN, 18,
                         (170, 180, 200), (40, 70, 120), 2, 0.4)
        img.paste(cap, (W - 90 - cap.width, H - 48), cap)

    def draw_lyric(self, img, t, i, acc):
        cue = None
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                cue = c
                break
        if cue is None:
            return
        rec = self.line_layers(cue)
        span = cue["end"] - cue["start"]
        u = (t - cue["start"]) / max(0.001, span)
        cy = H - self.BAR - 96
        bass = float(self.bass[i])
        acc_i = tuple(int(v) for v in acc)
        if rec["chorus"]:
            self._draw_chorus(img, rec, u, 1.0, cy, i, bass)
        else:
            self._draw_plain(img, rec, cue, u, 1.0, cy, bass, acc_i)


# ============================================================ D. Kinetic Poster
class StyleKineticPoster(render.Renderer):
    NAME = "D_kinetic_poster"
    BG_BY_SECTION = {
        "verse1": (16, 20, 26),
        "break": (14, 18, 22),
        "chorus1": (160, 78, 60),
        "verse2": (16, 20, 26),
        "chorus2": (170, 84, 64),
        "outro": (10, 14, 18),
    }

    def background(self, i, acc, bass, treb):
        t = i / self.fps
        cur = self.section_at(t)
        bg = self.BG_BY_SECTION.get(cur["kind"], (16, 20, 26))
        arr = np.full((H, W, 3), bg, dtype=np.float32)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
        r = ((xx - 0.5) * 1.4) ** 2 + ((yy - 0.5) * 1.0) ** 2
        bloom = np.clip(1.0 - r * 1.3, 0, 1)[:, :, None]
        arr += bloom * 8
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass): pass

    def draw_particles(self, img, i, bass, treb):
        rng = np.random.default_rng(i + 11)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(28):
            x = int(rng.uniform(80, W - 80))
            y = int(rng.uniform(120, H - 160))
            d.ellipse([(x - 1, y - 1), (x + 1, y + 1)],
                      fill=(245, 240, 230, int(40 + 80 * treb)))

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        bm = text_layer("ROYA//ZON", FONT_LATIN, 26, (245, 240, 230), (220, 100, 80), 4, 0.8)
        img.paste(bm, (80, 70), bm)
        cl = self.corner_layer
        img.paste(cl, (W - 80 - cl.width, 66), cl)
        d.line([(80, H - 88), (W - 80, H - 88)], fill=(245, 240, 230, 70), width=2)
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        ts_l = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                          FONT_SANS, 22, (245, 240, 230), (220, 100, 80), 4, 0.7)
        img.paste(ts_l, (80, H - 56), ts_l)
        cap = text_layer("SIDE A  ·  01", FONT_LATIN, 22, (245, 240, 230), (220, 100, 80), 4, 0.7)
        img.paste(cap, (W - 80 - cap.width, H - 56), cap)

    def draw_lyric(self, img, t, i, acc):
        cue = None
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                cue = c
                break
        if cue is None:
            return
        rec = self.line_layers(cue)
        u = (t - cue["start"]) / max(0.001, cue["end"] - cue["start"])
        bass = float(self.bass[i])
        scale = 1.0 + 0.05 * bass
        paste(img, rec["base"], W / 2, H / 2 - 30, 0.85, scale)
        if rec["chorus"]:
            scale_c = 1.10 + 0.10 * bass
            rL = render.tint(rec["whole"], (255, 80, 70))
            cL = render.tint(rec["whole"], (90, 200, 220))
            paste(img, rL, W / 2 + 4, H / 2 - 30, 0.55, scale_c)
            paste(img, cL, W / 2 - 4, H / 2 - 30, 0.55, scale_c)
            paste(img, rec["whole"], W / 2, H / 2 - 30, 1.0, scale_c)
        else:
            reveal = max(0.0, min(1.0, u / 0.9))
            L = rec["whole"]
            clip = L.crop((0, 0, max(1, int(L.width * reveal)), L.height))
            paste(img, clip, W / 2 - (L.width - clip.width) / 2, H / 2 - 30, 1.0, scale)


def main():
    ap = argparse.ArgumentParser(description="Render A-D style preview stills.")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--times", default="",
                    help="comma separated seconds, e.g. 24,49,78 (default: TIMES)")
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    feats = np.load(args.features)
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    times = ([float(x) for x in args.times.split(",") if x.strip()]
             if args.times else [t for t, _ in TIMES])

    styles = [StyleEditorialAir, StyleAlbumSleeve, StyleCinematic, StyleKineticPoster]
    for cls in styles:
        print(f"== {cls.__name__} ==")
        r = cls(plan, feats)
        for t in times:
            p = _save(r, t, cls.NAME, outdir)
            print(f"  -> {p.name}  ({p.stat().st_size // 1024} KB)")
    print("done.")


if __name__ == "__main__":
    main()
