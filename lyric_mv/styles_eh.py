"""Style demo renderer — short, audio-bearing clips for each visual style.

Reuses the live Renderer in 02_render.py (HUD already shows the song title at
top-right, artist hidden).  Styles A–D come from 07_style_variants.py;
E–H (the "showy" ones) are defined here.

Each style is rendered as two segments (verse1 tail + chorus1) and concat'd
into one mp4 so you can see both a quiet and a loud moment, with real audio.

Run one style per process so the global layer cache stays small and so several
styles can be rendered in parallel.

    python 08_style_demos.py --style E_neon_bloom
"""
import argparse
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

from . import renderer as render
from . import styles_ad as sv

DEFAULT_OUT = Path("03_preview/_demos")

W, H = render.W, render.H
text_layer = render.text_layer
font = render.font
paste = render.paste
FONT_SANS = render.FONT_SANS
FONT_LATIN = render.FONT_LATIN

# (start, end) seconds — verse1 tail, then chorus1 (shows the section change)
# Demo clip windows (start_s, end_s) — defaults sample a verse then a chorus
# of the shipped reference song. Override with --segs "0,10 45,58".
SEGS = [(21.5, 32.0), (44.4, 58.5)]


# ------------------------------------------------------------------ helpers
def lerp_stops(stops, n):
    out = []
    for i in range(n):
        t = i / max(1, n - 1) * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        f = t - k
        a, b = stops[k], stops[k + 1]
        out.append(tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)))
    return out


def hsv_rgb(h, s, v):
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255), int(g * 255), int(b * 255))


def neon_glow(img, overlay, radius=18):
    """Screen-blend a blurred copy of `overlay`, then composite it crisp."""
    b = overlay.filter(ImageFilter.GaussianBlur(radius))
    bg = Image.new("RGB", (W, H), (0, 0, 0))
    bg.paste(b, (0, 0), b)
    img.paste(ImageChops.screen(img, bg), (0, 0))
    img.paste(overlay, (0, 0), overlay)


class Style(render.Renderer):
    """Common base: shared HUD + helpers, per-style accent override."""

    NAME = "base"
    INK = (214, 226, 246)
    GLOW = (70, 130, 210)
    LABEL = "ROYA STUDIO"
    ACCENT_OVERRIDE = None

    def __init__(self, plan, feats, cover=None):
        if self.ACCENT_OVERRIDE:
            old = dict(render.ACCENT)
            render.ACCENT.update(self.ACCENT_OVERRIDE)
            try:
                super().__init__(plan, feats, cover)
            finally:
                render.ACCENT.clear()
                render.ACCENT.update(old)
        else:
            super().__init__(plan, feats, cover)

    def cue_at(self, t):
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                return c
        return None

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        wm = text_layer("ROYAZON", FONT_LATIN, 24, self.INK, self.GLOW, 8, 0.9)
        img.paste(wm, (80, 62), wm)
        cl = self.corner_layer
        img.paste(cl, (W - 80 - cl.width, 56), cl)
        x0, x1, y = 80, W - 80, H - 74
        d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 34), width=2)
        p = min(1.0, t / self.dur)
        if p > 0.001:
            d.line([(x0, y), (x0 + (x1 - x0) * p, y)],
                   fill=tuple(self.INK) + (195,), width=2)
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        tl = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                        FONT_SANS, 22, self.INK, self.GLOW, 6, 0.7)
        img.paste(tl, (80, H - 46), tl)
        cap = text_layer(self.LABEL, FONT_LATIN, 18, self.INK, self.GLOW, 4, 0.5)
        img.paste(cap, (W - 80 - cap.width, H - 44), cap)


# ================================================== E. Neon Bloom (绚丽 · 霓虹)
class StyleNeonBloom(Style):
    NAME = "E_neon_bloom"
    INK = (255, 250, 255)
    GLOW = (255, 70, 180)
    LABEL = "NEON EDITION"
    ACCENT_OVERRIDE = {
        "verse1": (255, 70, 170), "break": (180, 90, 255),
        "chorus1": (70, 230, 255), "verse2": (255, 70, 170),
        "chorus2": (70, 230, 255), "outro": (150, 90, 255),
    }

    def __init__(self, plan, feats, cover=None):
        super().__init__(plan, feats, cover)
        self.bar_col = lerp_stops(
            [(255, 40, 140), (196, 60, 255), (70, 220, 255),
             (110, 255, 215), (196, 60, 255), (255, 40, 140)], self.nbar)

    def background(self, i, acc, bass, treb):
        t = i / self.fps
        f = np.zeros((self.LH, self.LW, 3), dtype=np.float32)
        blobs = [
            (0.24 + 0.11 * math.sin(t * 0.37), 0.30 + 0.13 * math.cos(t * 0.29),
             (255, 40, 150), 0.36),
            (0.78 + 0.10 * math.cos(t * 0.33), 0.70 + 0.11 * math.sin(t * 0.41),
             (40, 220, 255), 0.34),
            (0.50 + 0.15 * math.sin(t * 0.21), 0.48 + 0.15 * math.cos(t * 0.23),
             (150, 80, 255), 0.28),
        ]
        for bx, by, col, amp in blobs:
            dx = (self.ax - bx) * 1.9
            dy = (self.ay - by)
            g = np.exp(-(dx * dx + dy * dy) / (2 * 0.16 * 0.16))
            g = g * (amp * (0.55 + 0.80 * bass))
            f += g[:, :, None] * np.array(col, dtype=np.float32)[None, None, :]
        up = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB")
        up = up.resize((W, H), Image.BICUBIC)
        glow = up.filter(ImageFilter.GaussianBlur(34))
        arr = (np.asarray(up).astype(np.float32) * 0.80
               + np.asarray(glow).astype(np.float32) * 0.66)
        arr *= self.vign[:, :, None]
        arr += 5.0 + self.flash[i] * 7.0
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass):
        vals = self.band_mix @ self.bands[i]
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov, "RGBA")
        cx, cy = W / 2, H / 2 - 20
        R0 = 322.0 + bass * 26.0
        for k in range(self.nbar):
            v = float(vals[k])
            ca, sa = math.cos(self.angles[k]), math.sin(self.angles[k])
            r1 = R0 + 10.0
            r2 = r1 + 16.0 + v * 158.0
            col = self.bar_col[k]
            d.line([(cx + ca * r1, cy + sa * r1), (cx + ca * r2, cy + sa * r2)],
                   fill=col + (185,), width=6)
            ri1 = R0 - 12.0
            ri2 = ri1 - (8.0 + v * 74.0)
            d.line([(cx + ca * ri1, cy + sa * ri1), (cx + ca * ri2, cy + sa * ri2)],
                   fill=col + (85,), width=3)
        neon_glow(img, ov, 18)

    def draw_particles(self, img, i, bass, treb):
        d = ImageDraw.Draw(img, "RGBA")
        t = i / self.fps
        cx, cy = W / 2, H / 2 - 20
        for k in range(self.np_):
            a = self.p_a[k] + t * 0.20 * self.p_s[k] * (1 + treb * 2.6)
            r = self.p_r[k] * 660.0 * (1.0 + bass * 0.32) + 90.0
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r * 0.74
            sz = max(1, int(self.p_z[k] * 1.8))
            al = int(70 + 170 * self.p_s[k] * (0.35 + treb))
            col = (255, 190, 240) if k % 2 else (190, 245, 255)
            d.ellipse([(x - sz, y - sz), (x + sz, y + sz)],
                      fill=col + (min(255, al),))


# ================================================= F. Aurora Ribbon (绚丽 · 极光)
class StyleAuroraRibbon(Style):
    NAME = "F_aurora_ribbon"
    INK = (230, 244, 255)
    GLOW = (60, 200, 210)
    LABEL = "AURORA"
    ACCENT_OVERRIDE = {
        "verse1": (60, 225, 200), "break": (150, 120, 255),
        "chorus1": (255, 130, 170), "verse2": (60, 225, 200),
        "chorus2": (255, 130, 170), "outro": (120, 150, 255),
    }
    RW, RH = 220, 124

    def __init__(self, plan, feats, cover=None):
        super().__init__(plan, feats, cover)
        self.bar_col = lerp_stops(
            [(40, 235, 205), (120, 140, 255), (255, 120, 175), (40, 235, 205)],
            self.nbar)
        yv = np.linspace(0.0, 1.0, H, dtype=np.float32)
        self.vfade = (0.25 + 0.85 * (1.0 - np.abs(yv - 0.52) * 1.55)).clip(0, 1)
        self.vfade = self.vfade.astype(np.float32)[:, None, None]

    def background(self, i, acc, bass, treb):
        t = i / self.fps
        xs = np.linspace(0.0, 1.0, self.RW, dtype=np.float32)[None, :]
        ys = np.linspace(0.0, 1.0, self.RH, dtype=np.float32)[:, None]
        f = np.zeros((self.RH, self.RW, 3), dtype=np.float32)
        ribbons = [
            (0.9, 1.7, 0.42, (50, 235, 205)),
            (2.4, 2.3, 0.36, (150, 95, 255)),
            (4.1, 3.1, 0.30, (255, 110, 165)),
        ]
        for ph, fr, amp, col in ribbons:
            cyc = (0.5 + 0.16 * np.sin(xs * fr * math.pi * 2 + t * 0.32 + ph)
                   + 0.06 * np.sin(xs * fr * 3.7 - t * 0.19 + ph))
            dd = ys - cyc
            w = 0.085 + 0.05 * bass
            g = np.exp(-(dd * dd) / (2 * w * w)) * (amp * (0.42 + 0.62 * bass))
            f += g[..., None] * np.array(col, dtype=np.float32)[None, None, :]
        up = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB")
        up = up.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14))
        arr = np.asarray(up).astype(np.float32) * 1.05
        arr *= self.vfade
        arr *= (0.35 + 0.95 * self.vign)[:, :, None]
        arr += 3.0 + self.flash[i] * 3.0
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass):
        vals = self.band_mix @ self.bands[i]
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov, "RGBA")
        x0, x1 = 140, W - 140
        bw = (x1 - x0) / self.nbar
        base_y = H - 96
        for k in range(self.nbar):
            v = float(vals[k])
            hgt = 10.0 + v * 235.0
            bx = x0 + k * bw
            col = self.bar_col[k]
            d.rectangle([(bx + 1.5, base_y - hgt), (bx + bw - 2.5, base_y)],
                        fill=col + (150,))
            d.rectangle([(bx + 1.5, base_y + 5),
                         (bx + bw - 2.5, base_y + 5 + hgt * 0.28)],
                        fill=col + (48,))
        neon_glow(img, ov, 16)

    def draw_particles(self, img, i, bass, treb):
        d = ImageDraw.Draw(img, "RGBA")
        t = i / self.fps
        rng = np.random.default_rng(31)
        for k in range(46):
            a = rng.uniform(0, 2 * math.pi)
            sp = rng.uniform(0.2, 1.0)
            x = (rng.uniform(0, W) + t * 26 * sp) % W
            y = rng.uniform(120, H - 220)
            sz = max(1, int(rng.uniform(1.0, 2.6)))
            al = int(40 + 130 * sp * (0.4 + treb))
            d.ellipse([(x - sz, y - sz), (x + sz, y + sz)],
                      fill=(200, 245, 255, min(255, al)))


# ============================================ G. Terminal Glitch (酷 · 终端故障)
class StyleTerminal(Style):
    NAME = "G_terminal_glitch"
    INK = (155, 255, 205)
    GLOW = (20, 120, 80)
    LABEL = "SYS//ROYA"
    ACCENT_OVERRIDE = {k: (80, 255, 170) for k in
                       ("verse1", "break", "chorus1", "verse2", "chorus2", "outro")}

    def __init__(self, plan, feats, cover=None):
        super().__init__(plan, feats, cover)
        scan = (np.sin(np.arange(H, dtype=np.float32) * (math.pi / 2.2)) * 0.5 + 0.5) * 9.0
        tex = np.zeros((H, W, 3), dtype=np.float32)
        tex += scan[:, None, None]
        tex[:, ::90, :] += 9.0
        tex[::90, :, :] += 9.0
        self.bgtex = tex

    def background(self, i, acc, bass, treb):
        arr = np.full((H, W, 3), 6.0, dtype=np.float32) + self.bgtex
        arr *= self.vign[:, :, None]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass):
        d = ImageDraw.Draw(img, "RGBA")
        n0 = max(0, i - 360)
        seg = self.rms[n0:i + 1]
        pts = []
        L = len(seg)
        for k in range(L):
            x = 120 + (W - 240) * (k / 359.0)
            y = H - 150 - float(seg[k]) * 130.0
            pts.append((x, y))
        if len(pts) > 1:
            d.line(pts, fill=(80, 255, 170, 155), width=2)
            d.line([(120, H - 150), (W - 120, H - 150)], fill=(80, 255, 170, 45), width=1)

    def draw_particles(self, img, i, bass, treb):
        pass

    def draw_lyric(self, img, t, i, acc):
        cue = self.cue_at(t)
        if cue is None:
            return
        u = (t - cue["start"]) / max(0.001, cue["end"] - cue["start"])
        txt = cue["text"]
        chorus = cue["section"].startswith("chorus")
        size = 132 if chorus else 116
        dim = text_layer(txt, FONT_SANS, size, (28, 92, 66), (10, 40, 28), 4, 0.5)
        hot = text_layer(txt, FONT_SANS, size, (162, 255, 206), (40, 200, 140), 10, 0.9)
        cy = H / 2 - 20
        reveal = max(0.0, min(1.0, u / 0.88))
        clip = hot.crop((0, 0, max(1, int(hot.width * reveal)), hot.height))
        paste(img, dim, W / 2, cy, 0.72, 1.0)
        if chorus:
            rL = render.tint(hot, (255, 70, 95))
            cL = render.tint(hot, (70, 220, 255))
            paste(img, rL, W / 2 + 5, cy, 0.32, 1.0)
            paste(img, cL, W / 2 - 5, cy, 0.32, 1.0)
            paste(img, hot, W / 2, cy, 0.92, 1.0)
        else:
            paste(img, clip, W / 2 - (hot.width - clip.width) / 2, cy, 1.0, 1.0)
        d = ImageDraw.Draw(img, "RGBA")
        pad = int(size * 0.95)
        xr = W / 2 + dim.width / 2 - pad + 12
        if int(t * 3) % 2 == 0:
            d.rectangle([(xr, cy - size * 0.46), (xr + size * 0.11, cy + size * 0.46)],
                        fill=(162, 255, 206, 200))

    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        ink = (155, 255, 205, 225)
        m, L = 54, 44
        for px, py, sx, sy in ((m, m, 1, 1), (W - m, m, -1, 1),
                               (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            d.line([(px, py), (px + L * sx, py)], fill=ink, width=3)
            d.line([(px, py), (px, py + L * sy)], fill=ink, width=3)
        wm = text_layer("ROYAZON", FONT_LATIN, 24, (162, 255, 206), (20, 120, 80), 6, 0.8)
        img.paste(wm, (84, 66), wm)
        cl = self.corner_layer
        img.paste(cl, (W - 84 - cl.width, 60), cl)
        rng = np.random.default_rng(int(t * 10))
        hf = font(FONT_LATIN, 17)
        alpha = "0123456789ABCDEF"
        for k in range(20):
            s = "".join(alpha[int(x)] for x in rng.integers(0, 16, size=8))
            d.text((84, 150 + k * 26), f"0x{int(t * 30) + k:04X}  {s}",
                   font=hf, fill=(80, 210, 165, 115))
        # right-hand level meter
        bx, by = W - 116, 150
        for k in range(20):
            on = k > 20 - int(float(self.rms[int(t * self.fps)]) * 26)
            d.rectangle([(bx, by + k * 26), (bx + 30, by + k * 26 + 16)],
                        fill=(80, 255, 170, 190 if on else 34))
        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        tl = text_layer(f"{mm:02d}:{ss:02d}  /  {tm:02d}:{ts:02d}",
                        FONT_SANS, 22, (162, 255, 206), (20, 120, 80), 6, 0.8)
        img.paste(tl, (84, H - 108), tl)
        cap = text_layer("REC ●  SYS//ROYA", FONT_LATIN, 18,
                         (162, 255, 206), (20, 120, 80), 4, 0.6)
        img.paste(cap, (W - 84 - cap.width, H - 106), cap)

    def frame(self, i):
        img = super().frame(i)
        t = i / self.fps
        # 周期性故障（每 ~1.8s 一次）+ beat 闪时加强
        periodic = (t % 1.8) < 0.16
        if self.flash[i] > 0.5 or periodic:
            rng = np.random.default_rng(i)
            d = ImageDraw.Draw(img, "RGBA")
            n = 5 if periodic else 4
            for _ in range(n):
                y = int(rng.integers(120, H - 200))
                h = int(rng.integers(14, 64))
                dx = int(rng.integers(-40, 41))
                # RGB 错位：左右各裁一条位移
                slab = img.crop((0, y, W, y + h))
                img.paste(slab, (dx, y))
                col = (255, 70, 95) if rng.integers(0, 2) else (70, 220, 255)
                d.rectangle([(0, y), (W, y + h)], fill=col + (22,))
            # 全局色散位移一条
            shift = img.crop((0, 0, W, 40))
            img.paste(shift, (rng.integers(-10, 11), 0))
        return img


# ====================================== H. Prism Kaleidoscope (绚丽 · 棱镜万花筒)
class StylePrism(Style):
    NAME = "H_prism_kaleidoscope"
    INK = (245, 244, 255)
    GLOW = (150, 120, 255)
    LABEL = "PRISM"
    NSEG = 8
    ACCENT_OVERRIDE = {
        "verse1": (140, 130, 255), "break": (110, 170, 255),
        "chorus1": (255, 190, 110), "verse2": (140, 130, 255),
        "chorus2": (255, 190, 110), "outro": (120, 160, 255),
    }

    def __init__(self, plan, feats, cover=None):
        super().__init__(plan, feats, cover)
        self.bar_col = [hsv_rgb((k / self.nbar) * 0.85, 0.82, 1.0)
                        for k in range(self.nbar)]
        yy = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None]
        xx = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]
        r = np.sqrt((xx * 0.92) ** 2 + (yy * 2.30) ** 2)
        a = (np.clip(1.0 - r / 0.80, 0, 1) ** 1.5 * 205.0)
        self.shade = Image.fromarray(a.astype(np.uint8), "L")

    def background(self, i, acc, bass, treb):
        f = np.zeros((self.LH, self.LW, 3), dtype=np.float32)
        dx = (self.ax - 0.5) * 2.1
        dy = (self.ay - 0.5) * 2.1
        g = np.exp(-(dx * dx + dy * dy) / (2 * 0.28 * 0.28)) * (0.22 + 0.55 * bass)
        f += g[:, :, None] * np.array((120, 80, 255), dtype=np.float32)[None, None, :]
        up = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB")
        up = up.resize((W, H), Image.BICUBIC)
        arr = np.full((H, W, 3), 5.0, dtype=np.float32)
        arr += np.asarray(up).astype(np.float32) * 0.85
        arr *= self.vign[:, :, None]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    def draw_spectrum(self, img, i, bass):
        vals = self.band_mix @ self.bands[i]
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov, "RGBA")
        cx, cy = W / 2, H / 2 - 10
        rot = (i / self.fps) * 0.11
        R0 = 148.0 + bass * 34.0
        half = self.nbar // 2
        step = 2 * math.pi / self.NSEG
        for s in range(self.NSEG):
            b = rot + s * step
            for k in range(half):
                v = float(vals[k])
                a = (k / half) * step
                r1 = R0 + 18.0
                r2 = r1 + 26.0 + v * 268.0
                col = self.bar_col[k]
                for ang in (b + a, b - a):
                    ca, sa = math.cos(ang), math.sin(ang)
                    d.line([(cx + ca * r1, cy + sa * r1),
                            (cx + ca * r2, cy + sa * r2)],
                           fill=col + (150,), width=4)
        neon_glow(img, ov, 21)

    def draw_particles(self, img, i, bass, treb):
        pass

    def draw_lyric(self, img, t, i, acc):
        img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), self.shade)
        super().draw_lyric(img, t, i, acc)


# ==================================================================== driver
STYLES = {
    "A_editorial_air": sv.StyleEditorialAir,
    "B_album_sleeve": sv.StyleAlbumSleeve,
    "C_cinematic_letterbox": sv.StyleCinematic,
    "D_kinetic_poster": sv.StyleKineticPoster,
    "E_neon_bloom": StyleNeonBloom,
    "F_aurora_ribbon": StyleAuroraRibbon,
    "G_terminal_glitch": StyleTerminal,
    "H_prism_kaleidoscope": StylePrism,
}


def render_seg(r, t0, t1, outfile, audio, fps):
    i0 = int(round(t0 * fps))
    n = int(round(t1 * fps)) - i0
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(fps), "-i", "pipe:0",
        "-ss", f"{t0:.3f}", "-i", str(audio),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{n / fps:.3f}", "-movflags", "+faststart",
        str(outfile),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    t_start = time.time()
    try:
        for k in range(n):
            proc.stdin.write(r.frame(i0 + k).tobytes())
            if k % 100 == 0:
                el = time.time() - t_start
                rate = (k + 1) / max(0.001, el)
                print(f"\r    {k}/{n}  {rate:5.1f} fps  eta {(n - k) / max(0.001, rate):5.0f}s",
                      end="", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg failed: {err[-1500:]}")
    print(f"\r    {n}/{n}  done in {time.time() - t_start:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True, choices=sorted(STYLES))
    ap.add_argument("--plan", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--segs", default="",
                    help='windows in seconds, e.g. "0,10 45,58" (default: SEGS)')
    args = ap.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    feats = np.load(args.features)
    audio = Path(plan["audio"])
    if not audio.is_absolute():
        audio = plan_path.parent / audio
    fps = plan["fps"]

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    cls = STYLES[args.style]
    print(f"== {args.style} ==")
    r = cls(plan, feats)

    parts = []
    segs = SEGS
    if args.segs:
        segs = [tuple(float(x) for x in part.split(","))
                for part in args.segs.replace(";", " ").split() if part.strip()]

    for si, (t0, t1) in enumerate(segs):
        p = outdir / f"{args.style}_seg{si}.mp4"
        print(f"  seg{si}  {t0:.1f}-{t1:.1f}s")
        render_seg(r, t0, t1, p, audio, fps)
        parts.append(p)

    final = outdir / f"{args.style}.mp4"
    lst = outdir / f"{args.style}.concat.txt"
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")
    cp = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                         "-i", str(lst), "-c", "copy", str(final)],
                        capture_output=True)
    if cp.returncode != 0:
        print("  concat copy failed, re-encoding:",
              cp.stderr.decode(errors="replace")[-600:])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-b:a", "192k", str(final)], check=True)
    for p in parts:
        p.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    mb = final.stat().st_size / 1048576
    print(f"  -> {final}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
