"""Cover generator — same design language as the video, redrawn not scraped.

The cover is **redrawn from the same tokens** the ``F_aurora_ribbon`` style uses
(aurora ribbons, spectrum gradient, HUD placement), which is why it stays
consistent across songs. It is deliberately *not* a video frame grab: grabbing
frames means hunting for one where the reveal animation happens to be complete,
and any cue text that is mid-transition will show a discoloured trailing glyph.

Design law for this template: **no hashtag stickers, no tag cards, no grid
frames, no decorative borders, no extra logo badges.** The only HUD elements
are the brand (top-left) and the song title (top-right).

Default output is 4:3 / 1146x860, which fills a B站 feed panel without cropping.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config as _cfg

_F = _cfg.resolve_fonts()
FONT_HEAVY = _F.heavy
FONT_SANS = _F.sans
FONT_LATIN = _F.latin

INK = (230, 244, 255)        # primary text (near-white, blue-leaning)
GLOW = (60, 200, 210)        # glow colour (teal)
LABEL = "AURORA"             # style tag, bottom-right
BRAND = _cfg.brand()         # wordmark, top-left

# Three aurora ribbons: (phase, frequency, amplitude, colour)
RIBBONS = [
    (0.9, 1.7, 0.42, (50, 235, 205)),    # teal
    (2.4, 2.3, 0.36, (150, 95, 255)),    # violet
    (4.1, 3.1, 0.30, (255, 110, 165)),   # pink
]
# Spectrum gradient (teal -> violet -> pink -> teal)
SPECTRUM_STOPS = [(40, 235, 205), (120, 140, 255), (255, 120, 175), (40, 235, 205)]

# HUD metrics authored against a 1920x1080 reference, scaled to the output.
REF_W = 1920
HUD_MARGIN = 80
HUD_BRAND_SIZE = 24
HUD_LABEL_SIZE = 18
HUD_SUB_SIZE = 30

STANDARD_SIZE = (1146, 860)   # 4:3  — the default
WIDE_SIZE = (1146, 717)       # 16:10 — only when you want a wide-screen feel


# ------------------------------------------------------------------ primitives
def font(path, size):
    if not path:
        _cfg.resolve_fonts().require()
        raise _cfg.FontNotFound("font path is empty")
    idx = 1 if str(path).endswith(".ttc") else 0
    return ImageFont.truetype(path, size, index=idx)


def lerp_stops(stops, n):
    out = []
    for i in range(n):
        t = i / max(1, n - 1) * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        f = t - k
        a, b = stops[k], stops[k + 1]
        out.append(tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)))
    return out


def text_layer(txt, fp, size, ink=INK, glow=GLOW, gr=18, ga=0.9):
    """Glowing text layer, matching the look of ``renderer.text_layer``."""
    f = font(fp, size)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    x0, y0, x1, y1 = probe.textbbox((0, 0), txt, font=f)
    w, h = x1 - x0, y1 - y0
    pad = gr * 3
    layer = Image.new("RGBA", (max(1, w + pad * 2), max(1, h + pad * 2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((pad - x0, pad - y0), txt, font=f, fill=tuple(glow) + (int(255 * ga),))
    layer = layer.filter(ImageFilter.GaussianBlur(gr))
    ImageDraw.Draw(layer).text((pad - x0, pad - y0), txt, font=f, fill=tuple(ink) + (255,))
    return layer


def make_vign(W, H):
    """Radial vignette, centre 1 -> edge ~0.35."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
    return (0.35 + 0.95 * (1.0 - np.clip(r, 0, 1) ** 1.7)).clip(0, 1).astype(np.float32)


def aurora_background(W, H, t=0.0, bass=0.72, blur=14):
    """Aurora ribbon background — a static frame of the F-style algorithm."""
    RW, RH = 220, 124
    xs = np.linspace(0.0, 1.0, RW, dtype=np.float32)[None, :]
    ys = np.linspace(0.0, 1.0, RH, dtype=np.float32)[:, None]
    f = np.zeros((RH, RW, 3), dtype=np.float32)
    for ph, fr, amp, col in RIBBONS:
        cyc = (0.5 + 0.16 * np.sin(xs * fr * math.pi * 2 + t * 0.32 + ph)
               + 0.06 * np.sin(xs * fr * 3.7 - t * 0.19 + ph))
        dd = ys - cyc
        w = 0.085 + 0.05 * bass
        g = np.exp(-(dd * dd) / (2 * w * w)) * (amp * (0.42 + 0.62 * bass))
        f += g[..., None] * np.array(col, dtype=np.float32)[None, None, :]
    up = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB")
    up = up.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(up).astype(np.float32) * 1.05
    yv = np.linspace(0.0, 1.0, H, dtype=np.float32)
    vfade = (0.25 + 0.85 * (1.0 - np.abs(yv - 0.52) * 1.55)).clip(0, 1)
    arr *= vfade.astype(np.float32)[:, None, None]
    arr *= make_vign(W, H)[:, :, None]
    arr += 3.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def draw_spectrum(img, W, H, energy=0.72, nbars=64, alpha=150):
    """Bottom spectrum bar, statically simulating chorus energy."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    x0, x1 = int(140 * W / REF_W), W - int(140 * W / REF_W)
    bw = (x1 - x0) / nbars
    base_y = H - int(96 * H / 1080)
    cols = lerp_stops(SPECTRUM_STOPS, nbars)
    rng = np.random.default_rng(31)
    for k in range(nbars):
        u = k / max(1, nbars - 1)
        env = (0.35 + 0.65 * math.sin(math.pi * u) ** 0.8) * energy
        v = float(np.clip(env + rng.uniform(-0.08, 0.08), 0.05, 1.0))
        hgt = (10.0 + v * 235.0) * H / 1080
        bx = x0 + k * bw
        col = cols[k]
        d.rectangle([(bx + 1.5, base_y - hgt), (bx + bw - 2.5, base_y)],
                    fill=col + (alpha,))
        d.rectangle([(bx + 1.5, base_y + 5), (bx + bw - 2.5, base_y + 5 + hgt * 0.28)],
                    fill=col + (48,))
    glow = ov.filter(ImageFilter.GaussianBlur(16 * W / REF_W))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))


def draw_particles(img, W, H, n=46, seed=31):
    """Micro-glints, statically sampled from the video's particle field."""
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    for _ in range(n):
        sp = rng.uniform(0.2, 1.0)
        x = rng.uniform(0, W)
        y = rng.uniform(120 * H / 1080, H - 220 * H / 1080)
        sz = max(1, int(rng.uniform(1.0, 2.6) * W / REF_W))
        al = int(40 + 130 * sp * 0.8)
        d.ellipse([(x - sz, y - sz), (x + sz, y + sz)],
                  fill=(200, 245, 255, min(255, al)))


def fit_font_size(txt, fp, target_w, max_size, min_size=40):
    """Binary-search a font size so long titles never overflow."""
    lo, hi = min_size, max_size
    best = min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = font(fp, mid)
        bbox = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), txt, font=f)
        if bbox[2] - bbox[0] <= target_w:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# ---------------------------------------------------------------- main render
def render_cover(title, subtitle="", out="cover.png", W=STANDARD_SIZE[0],
                 H=STANDARD_SIZE[1], energy=0.72, seed=31, t=0.0, show_hud=True):
    scale = W / REF_W

    img = aurora_background(W, H, t=t, bass=energy, blur=max(6, int(14 * scale)))
    draw_particles(img, W, H, seed=seed)
    draw_spectrum(img, W, H, energy=energy)

    # ---- hero: the song title, centred, auto-fitted ----
    target_w = int(W * 0.74)
    size = fit_font_size(title, FONT_HEAVY, target_w, max_size=int(190 * scale) + 60)
    tl = text_layer(title, FONT_HEAVY, size, INK, GLOW,
                    gr=max(8, int(26 * scale)), ga=0.95)
    tx = (W - tl.width) // 2
    ty = int(H * 0.40) - tl.height // 2     # slightly above centre, room for spectrum
    img.paste(tl, (tx, ty), tl)

    if subtitle:
        ss = max(16, int(HUD_SUB_SIZE * scale))
        sl = text_layer(subtitle, FONT_SANS, ss, (200, 216, 240), GLOW,
                        gr=max(4, int(10 * scale)), ga=0.55)
        img.paste(sl, ((W - sl.width) // 2, ty + tl.height - int(6 * scale)), sl)

    if show_hud:
        m = int(HUD_MARGIN * scale)
        wm = text_layer(BRAND, FONT_LATIN, max(12, int(HUD_BRAND_SIZE * scale)),
                        INK, GLOW, gr=max(4, int(8 * scale)), ga=0.9)
        img.paste(wm, (m, int(62 * scale)), wm)

        cs = max(12, int(HUD_BRAND_SIZE * scale))
        cl = text_layer(f"《{title}》", FONT_SANS, cs, (200, 216, 240), GLOW,
                        gr=max(4, int(8 * scale)), ga=0.7)
        img.paste(cl, (W - m - cl.width, int(56 * scale)), cl)

        d = ImageDraw.Draw(img, "RGBA")
        y = H - int(74 * H / 1080)
        d.line([(m, y), (W - m, y)], fill=(255, 255, 255, 34), width=max(1, int(2 * scale)))

        cap = text_layer(LABEL, FONT_LATIN, max(10, int(HUD_LABEL_SIZE * scale)),
                         INK, GLOW, gr=max(3, int(4 * scale)), ga=0.5)
        img.paste(cap, (W - m - cap.width, H - int(44 * H / 1080)), cap)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out, size


def main():
    ap = argparse.ArgumentParser(description="Lyric-MV cover generator")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--out", default="cover.png")
    ap.add_argument("--ratio", default="4:3", choices=["4:3", "16:10"],
                    help="4:3 -> 1146x860 (default) | 16:10 -> 1146x717")
    ap.add_argument("--energy", type=float, default=0.72,
                    help="aurora/spectrum energy 0..1 (chorus 0.72, ballad 0.45)")
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--phase", type=float, default=0.0)
    ap.add_argument("--no-hud", action="store_true")
    a = ap.parse_args()

    W, H = WIDE_SIZE if a.ratio == "16:10" else STANDARD_SIZE
    out, size = render_cover(a.title, a.subtitle, a.out, W, H,
                             energy=a.energy, seed=a.seed, t=a.phase,
                             show_hud=not a.no_hud)
    print(f"OK  {out}  ({W}x{H})  title_size={size}px  ratio={a.ratio}")


if __name__ == "__main__":
    main()
