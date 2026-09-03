"""The 8 bundled visual styles, as one lazily-loaded registry.

Each style subclasses :class:`lyric_mv.renderer.Renderer` and overrides one or
more of ``background`` / ``draw_spectrum`` / ``draw_particles`` /
``draw_lyric`` / ``draw_hud``.

=========================  ==================  ============================
key                        mood                signature motion
=========================  ==================  ============================
A_editorial_air            light paper white   per-char reveal, editorial
B_album_sleeve             warm grey card      moving film grain
C_cinematic_letterbox      black, letterboxed  spectrum burst on the bar
D_kinetic_poster           dark -> orange      beat scale + RGB offset
E_neon_bloom               dark violet         neon bloom breathing
F_aurora_ribbon            cool                flowing aurora ribbons
G_terminal_glitch          black/green         periodic glitch, RGB split
H_prism_kaleidoscope       black               rotating kaleidoscope
=========================  ==================  ============================
"""

from __future__ import annotations

from typing import Callable

# Populated on first access so that importing this module stays cheap and does
# not fail when a style module has an optional dependency issue.
_REGISTRY: dict[str, Callable] | None = None

#: Short human labels used by the docs and the preview contact sheet.
LABELS: dict[str, str] = {
    "A_editorial_air": "编辑留白 · 浅纸底",
    "B_album_sleeve": "唱片内页 · 暖灰卡",
    "C_cinematic_letterbox": "电影黑边 · 字幕位",
    "D_kinetic_poster": "动力海报 · 冲击",
    "E_neon_bloom": "霓虹绽放 · 赛博",
    "F_aurora_ribbon": "极光飘带 · 梦幻",
    "G_terminal_glitch": "终端故障 · 科技",
    "H_prism_kaleidoscope": "棱镜万花筒 · 最炫",
}


def _build() -> dict[str, Callable]:
    # Imported here (not at module scope) to keep `import lyric_mv` light.
    from . import styles_ad, styles_eh

    return {
        "A_editorial_air": styles_ad.StyleEditorialAir,
        "B_album_sleeve": styles_ad.StyleAlbumSleeve,
        "C_cinematic_letterbox": styles_ad.StyleCinematic,
        "D_kinetic_poster": styles_ad.StyleKineticPoster,
        "E_neon_bloom": styles_eh.StyleNeonBloom,
        "F_aurora_ribbon": styles_eh.StyleAuroraRibbon,
        "G_terminal_glitch": styles_eh.StyleTerminal,
        "H_prism_kaleidoscope": styles_eh.StylePrism,
    }


def registry() -> dict[str, Callable]:
    """Return ``{style_key: Renderer subclass}``, loading modules on demand."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build()
    return _REGISTRY


def keys() -> list[str]:
    return sorted(registry())


def get(key: str):
    try:
        return registry()[key]
    except KeyError:
        raise SystemExit(
            f"未知风格 {key!r}。可选：{', '.join(keys())}"
        ) from None


# Backwards-compatible alias: the original project called this `STYLES`.
class _LazyStyles:
    def __getitem__(self, k):
        return registry()[k]

    def __iter__(self):
        return iter(registry())

    def __len__(self):
        return len(registry())

    def keys(self):
        return registry().keys()

    def items(self):
        return registry().items()

    def values(self):
        return registry().values()


STYLES = _LazyStyles()
