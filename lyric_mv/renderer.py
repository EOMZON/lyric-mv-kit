"""Render the lyric/visualizer video.

Frames are generated with PIL + numpy, driven by the real audio spectrum, and
piped straight into ffmpeg as raw RGB.

Layers per frame (bottom -> top)
  1. deep gradient + two audio-reactive aurora blobs (low-res field, upscaled)
  2. radial spectrum ring (96 log bands, real FFT of the master)
  3. orbiting particles pushed outward by treble
  4. beat flash
  5. kinetic typography (per-character stagger + RGB glitch on the hook)
  6. HUD: watermark, album, progress bar, time
"""

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080

from . import config as _cfg

# Fonts are resolved at import time from env vars / config.yaml / OS scan.
# See lyric_mv/config.py and docs/FONTS.md for the full resolution order.
_FONTS = _cfg.resolve_fonts()
FONT_HEAVY = _FONTS.heavy
FONT_SANS = _FONTS.sans
FONT_LATIN = _FONTS.latin

# The dramatic serif is missing a few punctuation glyphs (em-dash, horizontal
# bar, fullwidth hyphen). Fall back through latin then CJK sans.
FONT_FALLBACKS = [
    FONT_HEAVY,
    FONT_LATIN,
    FONT_SANS,
]

#: Wordmark burned into the top-left HUD. Override via ``LYRIC_MV_BRAND`` or
#: ``brand:`` in config.yaml.
BRAND = _cfg.brand()

# section -> accent colour used for the aurora + type glow
# Restrained editorial palette: ink blue + silver text + one mineral accent.
ACCENT = {
    "verse1":  (88, 150, 170),
    "break":   (112, 130, 140),
    "chorus1": (188, 142, 102),
    "verse2":  (82, 146, 166),
    "chorus2": (194, 148, 106),
    "outro":   (112, 142, 158),
}

_font_cache = {}
_glyph_font_cache = {}
_glyph_extent_cache = {}


def font(path, size):
    if not path:
        # Raise the actionable error here rather than a TypeError inside Pillow.
        _cfg.resolve_fonts().require()
        raise _cfg.FontNotFound("font path is empty")
    idx = 1 if path.endswith(".ttc") else 0
    key = (path, size, idx)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size, index=idx)
    return _font_cache[key]


def glyph_font(ch):
    """First font in FONT_FALLBACKS that renders `ch` as a real glyph."""
    if ch in _glyph_font_cache:
        return _glyph_font_cache[ch]
    for fp in FONT_FALLBACKS:
        f = font(fp, 150)
        im = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(im).text((10, 10), ch, font=f, fill=255)
        bb = im.getbbox()
        if not bb:
            continue
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        # The .notdef box fills almost the entire cell -> reject.
        if w * h < 150 * 150 * 0.7:
            _glyph_font_cache[ch] = fp
            return fp
    _glyph_font_cache[ch] = FONT_HEAVY
    return FONT_HEAVY


def char_layer(ch, size, fill, glow_rgb, glow_radius=30, glow_boost=1.35):
    """Layer for one character, picking the best supporting font."""
    return text_layer(ch, None, size, fill, glow_rgb, glow_radius, glow_boost)


def glyph_extent(ch, size, path=None):
    """(width, height, l_offset, t_offset) of the actual glyph cell."""
    key = (ch, size, path)
    if key in _glyph_extent_cache:
        return _glyph_extent_cache[key]
    fp = path if path is not None else glyph_font(ch)
    f = font(fp, size)
    bb = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), ch, font=f)
    ext = (bb[2] - bb[0], bb[3] - bb[1], bb[0], bb[1])
    _glyph_extent_cache[key] = ext
    return ext


# ---------------------------------------------------------------- type layers
_layer_cache = {}
_tint_cache = {}


def text_layer(text, path, size, fill, glow_rgb, glow_radius=30, glow_boost=1.35):
    """Build an RGBA layer for `text`. `path=None` = auto font fallback per char."""
    key = (text, path, size, fill, glow_rgb, glow_radius, round(glow_boost, 2))
    if key in _layer_cache:
        return _layer_cache[key]

    chars = list(text)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    measured = []  # (ch, font, l, t, r, b)
    for ch in chars:
        fp = path if path is not None else glyph_font(ch)
        f = font(fp, size)
        l, t, r, b = probe.textbbox((0, 0), ch, font=f)
        measured.append((ch, f, l, t, r, b))

    min_l = min(m[2] for m in measured)
    min_t = min(m[3] for m in measured)
    max_r = max(m[4] for m in measured)
    max_b = max(m[5] for m in measured)
    total_text_w = sum(m[4] - m[2] for m in measured)
    text_h = max_b - min_t

    pad = int(size * 0.95)
    LW, LH = total_text_w + pad * 2, text_h + pad * 2

    mask = Image.new("L", (LW, LH), 0)
    md = ImageDraw.Draw(mask)
    x = pad - min_l
    for ch, f, l, t, r, b in measured:
        md.text((x, pad - min_t), ch, font=f, fill=255)
        x += r - l

    sw, sh = max(1, LW // 6), max(1, LH // 6)
    small = mask.resize((sw, sh), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(glow_radius / 6.0))
    glow = small.resize((LW, LH), Image.BILINEAR).point(
        lambda v: min(255, int(v * glow_boost)))

    out = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    gc = Image.new("RGBA", (LW, LH), tuple(glow_rgb) + (0,))
    gc.putalpha(glow)
    out.alpha_composite(gc)
    tc = Image.new("RGBA", (LW, LH), tuple(fill) + (0,))
    tc.putalpha(mask)
    out.alpha_composite(tc)

    _layer_cache[key] = out
    return out


def tint(layer, rgb):
    key = (id(layer), rgb)
    if key in _tint_cache:
        return _tint_cache[key]
    out = Image.new("RGBA", layer.size, tuple(rgb) + (0,))
    out.putalpha(layer.getchannel("A"))
    _tint_cache[key] = out
    return out


_alpha_luts = {}


def alpha_lut(a):
    q = max(0, min(64, int(a * 64)))
    if q not in _alpha_luts:
        v = q / 64.0
        _alpha_luts[q] = [min(255, int(i * v)) for i in range(256)]
    return _alpha_luts[q]


def paste(base, layer, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.004:
        return
    L = layer
    if abs(scale - 1.0) > 0.002:
        L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))),
                     Image.BILINEAR)
    if alpha < 0.99:
        L = L.copy()
        L.putalpha(L.getchannel("A").point(alpha_lut(alpha)))
    x, y = int(cx - L.width / 2), int(cy - L.height / 2)
    if x < 0 or y < 0 or x + L.width > base.width or y + L.height > base.height:
        sx, sy = max(0, -x), max(0, -y)
        ex = min(L.width, base.width - x)
        ey = min(L.height, base.height - y)
        if ex <= sx or ey <= sy:
            return
        L = L.crop((sx, sy, ex, ey))
        x, y = x + sx, y + sy
    base.paste(L, (x, y), L)


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, plan, feats, cover=None):
        self.p = plan
        self.fps = plan["fps"]
        self.n = plan["nframes"]
        self.dur = plan["duration"]
        z = feats
        self.rms = z["rms"]
        self.bass = z["bass"]
        self.mid = z["mid"]
        self.treb = z["treb"] if "treb" in z.files else z["treble"]
        self.bands = z["bands"]
        self.nbands = self.bands.shape[1]

        sec = plan["sections"]
        self.bpm = sec.get("bpm", 129.0)
        self.beat = sec.get("beat", 60.0 / self.bpm)
        self.secmap = sec["map"]
        self.cues = plan["cues"]

        # ---- static background gradient --------------------------------
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
        xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
        # 0..1 normalised so the bg stays dark
        top = np.array([0.026, 0.034, 0.040], dtype=np.float32)
        bot = np.array([0.008, 0.010, 0.012], dtype=np.float32)
        diag = np.clip(yy * 0.72 + (1.0 - xx) * 0.28, 0, 1)
        self.base = bot[None, None, :] + (top - bot)[None, None, :] * diag[:, :, None]

        rv = ((xx - 0.5) * 1.78) ** 2 + ((yy - 0.5) * 1.0) ** 2
        self.vign = (1.0 - np.clip(np.sqrt(rv) / 0.92, 0, 1) ** 1.7 * 0.82).astype(np.float32)

        # ---- low-res aurora field --------------------------------------
        self.LH, self.LW = 135, 240
        self.ay = np.linspace(0.0, 1.0, self.LH, dtype=np.float32)[:, None]
        self.ax = np.linspace(0.0, 1.0, self.LW, dtype=np.float32)[None, :]

        # ---- spectrum geometry -----------------------------------------
        self.cx, self.cy = W / 2, H / 2 - 28
        self.R0 = 338.0
        self.nbar = 96
        self.angles = np.arange(self.nbar) * (2 * math.pi / self.nbar) - math.pi / 2
        self.bar_col = self._bar_colors(self.nbar)
        # map 96 analysis bands onto 112 drawn bars (mirror for symmetry)
        src = np.linspace(0, self.nbands - 1, self.nbar // 2)
        i0 = np.floor(src).astype(int)
        i1 = np.clip(i0 + 1, 0, self.nbands - 1)
        frac = (src - i0)[:, None]
        half = self.nbar // 2
        M = np.zeros((self.nbar, self.nbands), dtype=np.float32)
        for k in range(half):
            M[k, i0[k]] += (1 - frac[k, 0])
            M[k, i1[k]] += frac[k, 0]
        M[half:, :] = M[:half, :][::-1, :]
        self.band_mix = M

        # ---- particles --------------------------------------------------
        rng = np.random.default_rng(7)
        self.np_ = 60
        self.p_a = rng.uniform(0, 2 * math.pi, self.np_)
        self.p_r = rng.uniform(0.30, 1.02, self.np_)
        self.p_s = rng.uniform(0.25, 1.0, self.np_)
        self.p_z = rng.uniform(1.2, 4.4, self.np_)

        # ---- beat flash ---------------------------------------------------
        b = self.bass
        d = np.diff(b, prepend=b[0])
        onset = (d > 0.055) & (b > 0.70)
        flash = np.zeros(self.n, dtype=np.float32)
        cur = 0.0
        for i in range(self.n):
            if onset[i]:
                cur = 1.0
            cur *= 0.90
            flash[i] = cur
        self.flash = flash

        # ---- pre-rendered type -------------------------------------------
        self.type_cache = {}
        self._prepare_type()

        # ---- optional cover art ------------------------------------------
        self.cover = None
        if cover and Path(cover).exists():
            im = Image.open(cover).convert("RGB").resize((720, 720), Image.LANCZOS)
            self.cover = im

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _bar_colors(n):
        stops = [(70, 126, 148), (104, 160, 174), (156, 164, 156),
                 (176, 136, 98), (104, 160, 174), (70, 126, 148)]
        out = []
        for i in range(n):
            t = i / (n - 1) * (len(stops) - 1)
            k = min(int(t), len(stops) - 2)
            f = t - k
            a, b = stops[k], stops[k + 1]
            out.append(tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)))
        return out

    def _prepare_type(self):
        for c in self.cues:
            self.line_layers(c)
        # title card
        self.title_chars = []
        for ch in self.p["title"]:
            self.title_chars.append((ch, text_layer(ch, None, 168,
                                                    (245, 248, 255), (120, 190, 255), 34, 1.5)))
        self.sub_layer = text_layer(f"{BRAND}  ·  《{self.p['album']}》",
                                    FONT_SANS, 40, (200, 215, 240), (60, 130, 220), 16, 1.0)
        self.wm_layer = text_layer(BRAND, FONT_LATIN, 26, (235, 240, 255),
                                   (110, 150, 255), 12, 1.1)
        # top-right now shows the song title (per user direction 2026-09-02),
        # not the album; the artist name is intentionally hidden.
        self.corner_layer = text_layer(f"《{self.p['title']}》",
                                       FONT_SANS, 30, (205, 218, 240), (60, 120, 200), 12, 1.0)
        m = self.p["meta"]
        self.tech_layer = text_layer(f"{m['bpm']} BPM  ·  {m['key']}  ·  {m['style']}",
                                     FONT_SANS, 24, (170, 185, 215), (50, 90, 170), 10, 0.9)

    def line_layers(self, cue):
        key = (cue["text"], cue["section"])
        if key in self.type_cache:
            return self.type_cache[key]
        txt = cue["text"]
        acc = ACCENT.get(cue["section"], (120, 200, 255))
        chorus = cue["section"].startswith("chorus")
        size = 158 if chorus else 138
        glow = acc
        chars = []
        extents = []
        for ch in txt:
            L = text_layer(ch, None, size, (238, 241, 238), glow, 14, 0.60)
            chars.append(L)
            extents.append(glyph_extent(ch, size))
        whole = text_layer(txt, None, size, (238, 241, 238), glow, 14, 0.60)
        base = text_layer(txt, None, size, (88, 96, 98), (20, 24, 26), 5, 0.22)
        rec = {"chars": chars, "extents": extents, "whole": whole,
               "base": base, "chorus": chorus, "w": sum(c.width for c in chars)}
        self.type_cache[key] = rec
        return rec

    # -------------------------------------------------------------- sections
    def section_at(self, t):
        cur = self.secmap[0]
        for s in self.secmap:
            if t >= s["start"]:
                cur = s
            else:
                break
        return cur

    def accent_at(self, t):
        cur = self.section_at(t)
        nxt = None
        for i, s in enumerate(self.secmap):
            if s is cur and i + 1 < len(self.secmap):
                nxt = self.secmap[i + 1]
        a = np.array(ACCENT.get(cur["kind"], (120, 200, 255)), dtype=np.float32)
        if nxt is None:
            return a
        b = np.array(ACCENT.get(nxt["kind"], (120, 200, 255)), dtype=np.float32)
        fade_t = 1.1
        d = nxt["start"] - t
        if d > fade_t:
            return a
        k = float(np.clip(1.0 - d / fade_t, 0, 1))
        k = k * k * (3 - 2 * k)
        return a + (b - a) * k

    # ---------------------------------------------------------------- frame
    def background(self, i, acc, bass, treb):
        arr = self.base * 255.0 * (1.0 + 0.10 * bass)
        base = np.clip(arr, 0, 255).astype(np.float32)
        # Two small, low-saturation edge lights. Their centres remain outside
        # the canvas so they add colour without becoming large grey “walls”.
        t = i / self.fps
        field = np.zeros((self.LH, self.LW, 3), dtype=np.float32)
        lights = [
            (-0.10, 0.32 + 0.06 * math.sin(t * 0.11), 0.18,
             np.array((58, 126, 150), dtype=np.float32), 0.16 + 0.03 * bass),
            (1.10, 0.70 + 0.05 * math.cos(t * 0.09), 0.17,
             np.array((168, 126, 82), dtype=np.float32), 0.12 + 0.02 * treb),
        ]
        for bx, by, sig, col, amp in lights:
            dx = (self.ax - bx) * 1.78
            dy = self.ay - by
            g = np.exp(-(dx * dx + dy * dy) / (2 * sig * sig)) * amp
            field += g[:, :, None] * col[None, None, :]
        edge_light = Image.fromarray(np.clip(field, 0, 255).astype(np.uint8), mode="RGB")
        edge_light = edge_light.resize((W, H), Image.BICUBIC)
        base += np.asarray(edge_light).astype(np.float32) * 0.55
        base *= self.vign[:, :, None]
        base += self.flash[i] * 2.0
        return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode="RGB")

    def draw_spectrum(self, img, i, bass):
        d = ImageDraw.Draw(img, "RGBA")
        vals = self.band_mix @ self.bands[i]
        cx, cy, R0 = self.cx, self.cy, self.R0 + bass * 16.0
        outer_max, inner_max = 132.0, 64.0
        cos_a = np.cos(self.angles)
        sin_a = np.sin(self.angles)
        for k in range(self.nbar):
            v = float(vals[k])
            ca, sa = cos_a[k], sin_a[k]
            r1 = R0 + 14.0
            r2 = r1 + 16.0 + v * outer_max
            col = self.bar_col[k]
            d.line([(cx + ca * r1, cy + sa * r1), (cx + ca * r2, cy + sa * r2)],
                   fill=col + (142,), width=5)
            # mirrored inner spikes
            ri1 = R0 - 12.0
            ri2 = ri1 - (6.0 + v * inner_max)
            d.line([(cx + ca * ri1, cy + sa * ri1), (cx + ca * ri2, cy + sa * ri2)],
                   fill=col + (62,), width=3)
        ring_a = int(40 + 90 * bass)
        d.ellipse([(cx - R0, cy - R0), (cx + R0, cy + R0)],
                  outline=(190, 215, 255, ring_a), width=2)

    def draw_particles(self, img, i, bass, treb):
        d = ImageDraw.Draw(img, "RGBA")
        t = i / self.fps
        cx, cy = self.cx, self.cy
        for k in range(self.np_):
            a = self.p_a[k] + t * 0.16 * self.p_s[k] * (1 + treb * 2.4)
            r = (self.p_r[k] * 620.0) * (1.0 + bass * 0.30) + 70.0
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r * 0.72
            z = self.p_z[k]
            sz = max(1, int(z * 1.5))
            al = int(60 + 150 * self.p_s[k] * (0.35 + treb))
            d.ellipse([(x - sz, y - sz), (x + sz, y + sz)],
                      fill=(215, 235, 255, min(255, al)))

    # ------------------------------------------------------------- typography
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
        u = (t - cue["start"]) / max(0.001, span)   # 0..1
        acc_i = tuple(int(v) for v in acc)

        # envelope: in / hold / out
        ain, aout = 0.16, 0.14
        if u < ain:
            k = u / ain
            alpha = 1.0 - (1.0 - k) ** 2
        elif u > 1 - aout:
            k = (1.0 - u) / aout
            alpha = k ** 1.4
        else:
            alpha = 1.0

        cy = H / 2 - 20
        bass = float(self.bass[i])

        if rec["chorus"]:
            self._draw_chorus(img, rec, u, alpha, cy, i, bass)
        else:
            self._draw_plain(img, rec, cue, u, alpha, cy, bass, acc_i)

    def _draw_plain(self, img, rec, cue, u, alpha, cy, bass, acc):
        L = rec["whole"]
        paste(img, rec["base"], W / 2, cy, alpha * 0.92, 1.0)
        ain = 0.16
        if u < ain:
            k = u / ain
            e = 1.0 - (1.0 - k) ** 3
            scale = 0.84 + 0.16 * e
            dy = (1.0 - e) * 46
        else:
            scale = 1.0 + 0.020 * bass
            dy = 0.0
        if u > 0.86:
            scale *= 1.0 + (u - 0.86) / 0.14 * 0.07
            dy -= (u - 0.86) / 0.14 * 22

        long_line = (cue["end"] - cue["start"]) > 6.0
        if long_line:
            # echo trail: keeps a held final line alive instead of sitting still
            for e in (3, 2, 1):
                ea = alpha * (0.16 / e)
                paste(img, L, W / 2, cy + e * 26 + e * 6 * math.sin(u * 5 + e),
                      ea, scale * (1 + e * 0.035))
            breathe = 1.0 + 0.03 * math.sin(u * math.pi * 3.0)
            paste(img, L, W / 2, cy, alpha, scale * breathe)
        else:
            # The bright layer advances with the vocal phrase (karaoke fill).
            reveal = max(0.0, min(1.0, u / 0.90))
            clip = L.crop((0, 0, max(1, int(L.width * reveal)), L.height))
            paste(img, clip, W / 2 - (L.width - clip.width) / 2, cy, alpha, scale)

    def _draw_chorus(self, img, rec, u, alpha, cy, i, bass):
        chars = rec["chars"]
        extents = rec["extents"]
        n = len(chars)
        paste(img, rec["base"], W / 2, cy, alpha * 0.92, 1.0)

        # real glyph widths (not the padded layer widths)
        gw = [e[0] for e in extents]
        total_gw = sum(gw)
        step = total_gw / max(1, n)
        x = W / 2 - total_gw / 2
        acc_x = 0.0
        for k, L in enumerate(chars):
            cu = u - k * (0.055 / max(1, n * 0.28))
            if cu <= 0:
                acc_x += gw[k]
                continue
            kk = min(1.0, cu / 0.13)
            e = 1.0 - (1.0 - kk) ** 3
            # Highlight only characters already reached by the sung phrase.
            sung = max(0.0, min(1.0, u / 0.90))
            a = alpha * e if sung * n >= k else alpha * 0.10
            if a <= 0.01:
                acc_x += gw[k]
                continue
            sc = 0.72 + 0.28 * e
            sc *= 1.0 + 0.035 * bass
            dy = (1.0 - e) * 62 + math.sin(i * 0.09 + k) * 3.0
            if u > 0.88:
                sc *= 1.0 + (u - 0.88) / 0.12 * 0.09
            cxp = x + acc_x + gw[k] / 2
            paste(img, L, cxp, cy + dy, a, sc)
            acc_x += gw[k]

    # ------------------------------------------------------------------ HUD
    def draw_hud(self, img, t):
        d = ImageDraw.Draw(img, "RGBA")
        # top-left watermark
        img.paste(self.wm_layer, (78, 62), self.wm_layer)
        # top-right album
        cl = self.corner_layer
        img.paste(cl, (W - 78 - cl.width, 58), cl)

        # progress bar
        x0, x1, y = 120, W - 120, H - 74
        d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 42), width=3)
        p = min(1.0, t / self.dur)
        xe = x0 + (x1 - x0) * p
        if xe > x0:
            seg = 34
            for s in range(seg):
                a0 = x0 + (xe - x0) * s / seg
                a1 = x0 + (xe - x0) * (s + 1) / seg
                f = s / (seg - 1)
                v = int(132 + 62 * f)
                col = (v - 18, v - 2, v + 6, 205)
                d.line([(a0, y), (a1, y)], fill=col, width=3)
            d.ellipse([(xe - 6, y - 6), (xe + 6, y + 6)], fill=(255, 255, 255, 245))

        mm, ss = divmod(int(t), 60)
        tm, ts = divmod(int(self.dur), 60)
        lbl = text_layer(f"{mm}:{ss:02d} / {tm}:{ts:02d}", FONT_SANS, 24,
                         (200, 214, 238), (60, 120, 200), 10, 0.9)
        img.paste(lbl, (120, H - 46), lbl)
        tl = self.tech_layer
        img.paste(tl, (W - 120 - tl.width, H - 46), tl)

    def draw_title(self, img, t):
        # 0 -> 6.0s  : staggered title, then it dissolves into the first lyric
        if t > 6.2:
            return
        fade = 1.0 if t < 4.4 else max(0.0, 1.0 - (t - 4.4) / 1.8)
        if fade <= 0.01:
            return
        chars = self.title_chars
        n = len(chars)
        total = sum(c.width for c in chars for c in [c[1]])
        step = total / max(1, n)
        x = W / 2 - total / 2
        for k, (ch, L) in enumerate(chars):
            u = (t - 0.45 - k * 0.10) / 0.55
            if u <= 0:
                continue
            kk = min(1.0, u)
            e = 1.0 - (1.0 - kk) ** 3
            a = fade * e
            sc = 0.80 + 0.20 * e
            paste(img, L, x + step * (k + 0.5), H / 2 - 40 + (1 - e) * 40, a, sc)
        sl = self.sub_layer
        a2 = fade * max(0.0, min(1.0, (t - 1.5) / 0.8))
        paste(img, sl, W / 2, H / 2 + 92, a2, 1.0)
        d = ImageDraw.Draw(img, "RGBA")
        w = int(min(1.0, max(0.0, (t - 1.9) / 1.0)) * 420)
        if w > 0:
            d.line([(W / 2 - w, H / 2 + 150), (W / 2 + w, H / 2 + 150)],
                   fill=(150, 200, 255, int(150 * fade)), width=2)

    # ---------------------------------------------------------------- main
    def frame(self, i):
        t = i / self.fps
        acc = self.accent_at(t)
        bass = float(self.bass[i])
        treb = float(self.treb[i])

        img = self.background(i, acc, bass, treb)
        self.draw_spectrum(img, i, bass)
        self.draw_particles(img, i, bass, treb)
        # The song starts singing at 0.5s, so a full-screen title card would
        # cover the opening lyric. Metadata remains in the restrained HUD.
        self.draw_lyric(img, t, i, acc)
        if t > 1.0:
            self.draw_hud(img, t)
        return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cover", default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=0, help="0 = all frames")
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    feats = np.load(args.features)
    audio = Path(plan["audio"])
    if not audio.is_absolute():
        audio = Path(args.plan).resolve().parent / audio
    plan["audio"] = str(audio)
    r = Renderer(plan, feats, args.cover)

    n = r.n if args.count <= 0 else min(args.count, r.n - args.start)
    w, h = plan["width"], plan["height"]
    fps = plan["fps"]

    audio_input = ["-i", plan["audio"]]
    if args.start > 0:
        audio_input = ["-ss", f"{args.start / fps:.3f}", "-i", plan["audio"]]
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        *audio_input,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        args.out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    t0 = time.time()
    try:
        for k in range(n):
            i = args.start + k
            proc.stdin.write(r.frame(i).tobytes())
            if k % 150 == 0:
                el = time.time() - t0
                rate = (k + 1) / max(0.001, el)
                eta = (n - k - 1) / max(0.001, rate)
                print(f"\r  frame {k}/{n}  {rate:5.1f} fps  eta {eta:5.0f}s",
                      end="", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
    print()
    if rc != 0:
        print(err[-3000:])
        raise SystemExit(rc)
    print(f"  done in {time.time() - t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
