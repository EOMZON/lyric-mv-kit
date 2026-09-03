# Fonts

The renderer needs **three** font families at runtime:

| Role | Used for |
|------|----------|
| `heavy` | The dramatic CJK serif (歌名大字 + 歌词大字) |
| `sans`  | CJK sans for subtitles / timecode / corner HUD |
| `latin` | Brand wordmark and the style tag in the bottom-right |

None of these are bundled with the package. They're licensed separately and
have to live on the host or in `assets/fonts/`.

## Resolution order (highest priority first)

1. Environment variables
   - `LYRIC_MV_FONT_HEAVY`
   - `LYRIC_MV_FONT_SANS`
   - `LYRIC_MV_FONT_LATIN`
   - `LYRIC_MV_BRAND`  (the top-left text, e.g. `ROYAZON`)

2. `fonts:` block in `config.yaml` next to the project

3. **`assets/fonts/` inside the project**, populated by `scripts/fetch_fonts.py`

4. OS font directory scan, in this order:

   | Role    | Candidates (first hit wins) |
   |---------|-----------------------------|
   | `heavy` | `Source Han Serif SC Heavy (TrueType).ttf`, `SourceHanSerifSC-Heavy.otf`, `SourceHanSerifSC-Bold.otf`, `NotoSerifCJKsc-Bold.otf`, `Noto Serif SC Bold.otf`, `NotoSerifSC-Bold.otf`, `Songti.ttc`, `SimSun.ttc` |
   | `sans`  | `SourceHanSansCN-Normal.ttf`, `SourceHanSansSC-Regular.otf`, `NotoSansCJKsc-Regular.otf`, `Noto Sans SC Regular.otf`, `NotoSansSC-Regular.otf`, `PingFang.ttc`, `msyh.ttc`, `msyh.ttf` |
   | `latin` | `Dengb.ttf`, `DejaVuSans-Bold.ttf`, `Helvetica.ttc`, `Arial Bold.ttf`, `Arialbd.ttf`, `LiberationSans-Bold.ttf` |

If step 4 finds nothing, `lyric_mv.config.resolve_fonts().require()` raises
`FontNotFound` with the same instructions as in this doc — `python -m
lyric_mv check` is the easiest way to see what's missing.

## Recommended open-source setup (no proprietary fonts)

```bash
python scripts/fetch_fonts.py            # ~40 MB download
python -m lyric_mv check                 # should now say "OK"
```

`fetch_fonts.py` downloads the three Noto CJK families from the Google Fonts
mirror, all SIL OFL 1.1:

- `NotoSerifSC-Bold.otf`           → `heavy`
- `NotoSansSC-Regular.otf`         → `sans`
- `NotoSansSC-Bold.otf`            → `latin` fallback (Latin glyphs)

The script is idempotent: re-running it skips what you already have.

## Why the renderer doesn't ship fonts

The font files themselves are 5–40 MB each, and at least one of the obvious
candidates (`Dengb`, `msyh.ttc`, `PingFang`) is a Microsoft / Apple
proprietary system font that cannot be redistributed. Shipping a font would
either bloat clone size or violate a license. Auto-detect + a one-line
download script is the smallest honest path.

## Picking a different look

The serif is what gives the cover its mood. Other families worth trying:

- **Noir poster** — swap the heavy serif for `Source Han Sans CN Heavy` (still
  SIL OFL; just set `LYRIC_MV_FONT_HEAVY` to its path).
- **Mono / terminal** — use `Source Code Pro Bold` + `Source Han Sans SC Regular`
  for a glitch-literate feel; combine with the `G_terminal_glitch` style.

The HUD itself does not change with the font choice; only the lyrics, title,
corner label and bottom timecode do.