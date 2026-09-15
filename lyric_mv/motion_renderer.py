"""Renderer adapter that adds macro motion without rewriting visual styles."""
from __future__ import annotations

from PIL import Image

from .motion import MotionController


def _transform_layer(image: Image.Image, x: float, y: float, scale: float,
                     rotation: float = 0.0, fill=(0, 0, 0, 0)) -> Image.Image:
    rgba = image.convert("RGBA")
    if abs(rotation) > 1e-3:
        rgba = rgba.rotate(rotation, resample=Image.Resampling.BICUBIC,
                           expand=True, fillcolor=fill)
    if abs(scale - 1.0) > 1e-4:
        rgba = rgba.resize((max(1, round(rgba.width * scale)),
                            max(1, round(rgba.height * scale))),
                           Image.Resampling.BICUBIC)
    out = Image.new("RGBA", image.size, fill)
    px = round((out.width - rgba.width) / 2 + x)
    py = round((out.height - rgba.height) / 2 + y)
    out.alpha_composite(rgba, (px, py))
    return out


class MotionRenderer:
    """Wrap an existing visual-style renderer with camera/parallax choreography.

    HUD is intentionally composited after macro motion so title/progress metadata
    remains stable. Existing style methods remain the single owner of visual
    appearance and lyric micro-animation.
    """

    def __init__(self, base_renderer, controller: MotionController):
        self.base = base_renderer
        self.controller = controller
        self.n = base_renderer.n
        self.fps = base_renderer.fps
        self.dur = base_renderer.dur

    def frame(self, i: int):
        b = self.base
        t = i / b.fps
        acc = b.accent_at(t)
        bass = float(b.bass[i])
        treb = float(b.treb[i])
        state = self.controller.state_at(t, bass=bass, treble=treb)

        background = b.background(i, acc, bass, treb).convert("RGBA")
        foreground = Image.new("RGBA", background.size, (0, 0, 0, 0))
        b.draw_spectrum(foreground, i, bass)
        b.draw_particles(foreground, i, bass, treb)
        b.draw_lyric(foreground, t, i, acc)

        bg_scale = max(1.018, 1.0 + (state.scale - 1.0) * 0.45)
        bg = _transform_layer(
            background,
            state.x * state.background_parallax,
            state.y * state.background_parallax,
            bg_scale,
            state.rotation * 0.20,
            fill=(8, 10, 12, 255),
        )
        fg = _transform_layer(
            foreground,
            state.x * state.foreground_parallax,
            state.y * state.foreground_parallax,
            state.scale,
            state.rotation,
            fill=(0, 0, 0, 0),
        )
        img = Image.alpha_composite(bg, fg).convert("RGB")
        if t > 1.0:
            b.draw_hud(img, t)
        return img
