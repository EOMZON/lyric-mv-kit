"""Configuration and cross-platform font resolution.

Everything that used to be hardcoded to one Windows machine lives here:

* font paths (Windows / macOS / Linux, with env-var overrides)
* the brand string burned into the HUD
* render defaults (resolution, fps, encoder settings)

Resolution order for each font, highest priority first:

1. ``LYRIC_MV_FONT_HEAVY`` / ``..._SANS`` / ``..._LATIN`` environment variables
2. an explicit ``fonts:`` block in the project ``config.yaml``
3. auto-detection in the OS font directories
4. ``assets/fonts/`` inside the project (populated by ``scripts/fetch_fonts.py``)

If nothing resolves, :func:`resolve_fonts` raises :class:`FontNotFound` with
remediation instructions instead of failing deep inside Pillow.
"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "Fonts",
    "FontNotFound",
    "resolve_fonts",
    "brand",
    "load_project_config",
    "DEFAULT_BRAND",
]

DEFAULT_BRAND = "ROYAZON"

# Candidates are tried in order. The first one that exists on disk wins.
# Keep SIL OFL / Apache-licensed families first so the default setup is
# redistributable; proprietary system fonts stay as last-resort fallbacks.
_HEAVY_CANDIDATES: Sequence[str] = (
    "Source Han Serif SC Heavy (TrueType).ttf",  # Windows, installed by user
    "SourceHanSerifSC-Heavy.otf",
    "SourceHanSerifSC-Bold.otf",
    "NotoSerifCJKsc-Bold.otf",
    "Noto Serif SC Bold.otf",
    "NotoSerifSC-Bold.otf",
    "Songti.ttc",          # macOS
    "SimSun.ttc",          # Windows
)

_SANS_CANDIDATES: Sequence[str] = (
    "SourceHanSansCN-Normal.ttf",
    "SourceHanSansSC-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "Noto Sans SC Regular.otf",
    "NotoSansSC-Regular.otf",
    "PingFang.ttc",        # macOS
    "msyh.ttc",            # Windows (Microsoft YaHei)
    "msyh.ttf",
)

_LATIN_CANDIDATES: Sequence[str] = (
    "Dengb.ttf",           # Windows (DengXian Bold)
    "DejaVuSans-Bold.ttf",
    "Helvetica.ttc",       # macOS
    "Arial Bold.ttf",      # macOS
    "Arialbd.ttf",         # Windows
    "LiberationSans-Bold.ttf",
)


def _font_dirs() -> list[Path]:
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        win = Path(os.environ.get("WINDIR", "C:/Windows"))
        return [win / "Fonts", home / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"]
    if system == "Darwin":
        return [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
            home / "Library" / "Fonts",
        ]
    return [
        home / ".fonts",
        home / ".local" / "share" / "fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
    ]


def _project_font_dir() -> Path | None:
    """``assets/fonts/`` next to the repo root, if the tree is a checkout."""
    root = Path(__file__).resolve().parent.parent
    candidate = root / "assets" / "fonts"
    return candidate if candidate.is_dir() else None


def _first_existing(names: Iterable[str], extra_dirs: Sequence[Path] = ()) -> Path | None:
    dirs = list(extra_dirs) + _font_dirs()
    project = _project_font_dir()
    if project:
        dirs.insert(0, project)
    for d in dirs:
        for n in names:
            p = d / n
            if p.is_file():
                return p
    return None


class FontNotFound(RuntimeError):
    """Raised when a required font family cannot be located."""


@dataclass
class Fonts:
    """Resolved font paths. Every field is a string path or ``None``."""

    heavy: str | None = None
    sans: str | None = None
    latin: str | None = None

    def require(self) -> "Fonts":
        missing = [k for k in ("heavy", "sans", "latin") if not getattr(self, k)]
        if missing:
            raise FontNotFound(
                "缺少字体: " + ", ".join(missing) + "\n"
                " lyric-mv-kit 需要一款 CJK 衬线（heavy）、一款 CJK 无衬线（sans）"
                "和一款拉丁字体（latin）。三种方式任选其一：\n"
                "  1) 下载开源字体到 assets/fonts/ :  python scripts/fetch_fonts.py\n"
                "  2) 直接用环境变量指定绝对路径：\n"
                "       LYRIC_MV_FONT_HEAVY=/path/to/serif.ttf\n"
                "       LYRIC_MV_FONT_SANS=/path/to/sans.ttf\n"
                "       LYRIC_MV_FONT_LATIN=/path/to/latin.ttf\n"
                "  3) 在项目 config.yaml 里写 fonts: {heavy: ..., sans: ..., latin: ...}\n"
                "Noto Serif SC / Noto Sans SC（SIL OFL）是推荐的默认选择。"
            )
        return self

    def as_dict(self) -> dict:
        return {"heavy": self.heavy, "sans": self.sans, "latin": self.latin}


def _from_env() -> dict[str, str | None]:
    return {
        "heavy": os.environ.get("LYRIC_MV_FONT_HEAVY") or None,
        "sans": os.environ.get("LYRIC_MV_FONT_SANS") or None,
        "latin": os.environ.get("LYRIC_MV_FONT_LATIN") or None,
    }


def _from_yaml(project_dir: Path | None) -> dict[str, str | None]:
    cfg = load_project_config(project_dir)
    block = cfg.get("fonts") or {}
    out: dict[str, str | None] = {}
    for k in ("heavy", "sans", "latin"):
        v = block.get(k)
        out[k] = str(v) if v else None
    return out


def resolve_fonts(project_dir: Path | None = None) -> Fonts:
    """Locate the three font families, honouring env vars then config then OS scan."""
    env = _from_env()
    try:
        yml = _from_yaml(project_dir)
    except Exception:
        yml = {"heavy": None, "sans": None, "latin": None}

    out = Fonts()
    for key, candidates in (
        ("heavy", _HEAVY_CANDIDATES),
        ("sans", _SANS_CANDIDATES),
        ("latin", _LATIN_CANDIDATES),
    ):
        chosen = env.get(key) or yml.get(key)
        if not chosen:
            hit = _first_existing(candidates)
            chosen = str(hit) if hit else None
        setattr(out, key, chosen)
    return out


def brand(project_dir: Path | None = None) -> str:
    """The wordmark burned into the top-left HUD."""
    return (
        os.environ.get("LYRIC_MV_BRAND")
        or (load_project_config(project_dir).get("brand") if project_dir else None)
        or DEFAULT_BRAND
    )


def load_project_config(project_dir: Path | None = None) -> dict:
    """Read ``config.yaml`` from *project_dir* if it exists. Never raises."""
    if project_dir is None:
        return {}
    p = Path(project_dir) / "config.yaml"
    if not p.is_file():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        # PyYAML is optional; without it we only support env vars and auto-detect.
        return {}
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class RenderDefaults:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    crf: int = 19
    preset: str = "medium"
    audio_bitrate: str = "192k"

    @classmethod
    def from_dict(cls, d: dict | None) -> "RenderDefaults":
        if not d:
            return cls()
        known = {k: v for k, v in d.items() if k in cls().__dict__}
        return cls(**known)


@dataclass
class Project:
    """A resolved, path-independent view of one MV project."""

    dir: Path
    brand: str = DEFAULT_BRAND
    fonts: Fonts = field(default_factory=Fonts)
    render: RenderDefaults = field(default_factory=RenderDefaults)

    @classmethod
    def load(cls, project_dir: str | Path) -> "Project":
        d = Path(project_dir).resolve()
        return cls(
            dir=d,
            brand=brand(d),
            fonts=resolve_fonts(d),
            render=RenderDefaults.from_dict(load_project_config(d).get("render")),
        )

    def path(self, *parts: str) -> Path:
        return self.dir.joinpath(*parts)
