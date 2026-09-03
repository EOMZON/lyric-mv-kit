# lyric-mv-kit

> Pure-Python kinetic lyric-MV renderer. Eight visual styles. One CLI.
> *Not* Remotion, *not* a browser engine — just Pillow, numpy and ffmpeg.

A kinetic lyric video is the boring name for "the kind of video where the song's
words stay on screen in a designed typography style while the music drives the
motion." This is the toolkit that ships them.

---

## Why pure Python?

This kit ships a Python frame renderer rather than a React/Remotion pipeline.
Short version:

- **deterministic** — same `plan.json` + same audio features → byte-exact pixels
- **no browser footprint** — only Pillow, numpy, ffmpeg; no Chromium download
- **already shipped** — this is the engine that made the reference video; a
  Remotion port is a possible next step (see
  [`docs/PORTING-TO-REMOTION.md`](docs/PORTING-TO-REMOTION.md)), but not the
  default

If you came here expecting `npx remotion studio`, that exists elsewhere. If you
came here expecting "make a lyric MV without writing JavaScript," welcome.

---

## Eight styles

All eight stills were rendered from the same `plan.json` and
`audio_features.npz`; only the visual treatment differs.

| Key | Look | Signature motion |
|------|------|------------------|
| `A_editorial_air` | light paper white | per-char reveal, editorial |
| `B_album_sleeve` | warm grey card | moving film grain |
| `C_cinematic_letterbox` | black, letterboxed | spectrum burst on the bar |
| `D_kinetic_poster` | dark → orange | beat scale + RGB offset |
| `E_neon_bloom` | dark violet | neon bloom breathing |
| `F_aurora_ribbon` | cool | flowing aurora ribbons |
| `G_terminal_glitch` | black/green | periodic glitch, RGB split |
| `H_prism_kaleidoscope` | black | rotating kaleidoscope |

Stills and the full contact sheet live under [`showcase/`](showcase/).

```text
$ python -m lyric_mv styles
A_editorial_air            编辑留白 · 浅纸底
B_album_sleeve             唱片内页 · 暖灰卡
C_cinematic_letterbox      电影黑边 · 字幕位
D_kinetic_poster           动力海报 · 冲击
E_neon_bloom               霓虹绽放 · 赛博
F_aurora_ribbon            极光飘带 · 梦幻
G_terminal_glitch          终端故障 · 科技
H_prism_kaleidoscope       棱镜万花筒 · 最炫
```

---

## Quickstart

```bash
# 1. install (Pillow + numpy; PyYAML if you want config.yaml)
pip install -U pillow numpy pyyaml

# 2. optional: pull open-source fonts (≈ 25 MB; SIL OFL)
python scripts/fetch_fonts.py

# 3. verify the environment is ready
python -m lyric_mv check

# 4. analyse a song + render a full MP4
python -m lyric_mv build-plan   --audio song.wav --lyrics lyrics.txt \\
                               --song presets/song.example.json --outdir work
python -m lyric_mv render       --plan work/plan.json \\
                               --features work/audio_features.npz \\
                               --style F_aurora_ribbon --out out/song.mp4

# 5. generate a cover art PNG (4:3 / 1146x860)
python -m lyric_mv cover --title "歌名" --subtitle "艺人 · 极光歌词MV" \\
                         --out out/cover.png
```

That's the entire happy path. The full CLI surface:

```text
$ python -m lyric_mv --help
usage: lyric-mv [-h] {check,styles,build-plan,render,preview,demo,cover} ...

positional arguments:
  {check,styles,build-plan,render,preview,demo,cover}
    check                verify ffmpeg + fonts
    styles               list available styles
    build-plan           audio + lyrics -> plan.json
    render               plan.json -> full-song mp4
    preview              render stills at given timestamps
    demo                 short audio-bearing clip per style
    cover                4:3 cover art
```

---

## How it works

```
   ┌────────────────┐    ┌──────────────────┐    ┌────────────────┐
   │ audio_features │    │    plan.json     │    │  song.json     │
   │   .npz         │    │ (sections + cues │    │ (title/artist/ │
   │ (rms/bass/     │    │  + meta)         │    │  sections/     │
   │  treble/bands) │    │                  │    │  cue_times)    │
   └───────▲────────┘    └─────────▲────────┘    └────────▲───────┘
           │                       │                       │
           │      lyric_mv/audio.py + plan.py              │
           │                       │                       │
           └────────────►  Renderer.frame(i)  ◄─────────────┘
                                 │
                                 │  rawvideo pipe
                                 ▼
                          ffmpeg (libx264 + aac)
                                 │
                                 ▼
                              song.mp4
```

Every piece of the diagram is a single-file Python module in `lyric_mv/`:

| File | Lines | What it does |
|------|-------|--------------|
| `audio.py` | 130 | ffmpeg-decode → log-spaced 96-band spectrum → BPM |
| `plan.py` | 130 | clean lyrics → build `plan.json`; auto or hand-aligned timings |
| `align.py` | 100 | optional Whisper + stable-ts; produces `cue_times` |
| `separate.py` | 40 | optional Demucs vocal-stem extraction |
| `renderer.py` | 670 | the base `Renderer` class (background / spectrum / particles / lyric / HUD) |
| `styles_ad.py` | 400 | A–D style subclasses |
| `styles_eh.py` | 500 | E–H style subclasses + demo-clip renderer |
| `cover.py` | 220 | the lyric-MV cover generator |
| `cli.py` | 200 | unified CLI entry point |

---

## The plan.json contract

`plan.json` is the single source of truth — see
[`schemas/plan.schema.md`](schemas/plan.schema.md) for the full schema.
Nothing about the song lives anywhere else, which is what makes the styles
swappable and (eventually) a Remotion port possible.

---

## Reference song and showcase

The kit was originally authored to produce the aurora-ribbon lyric MV for the
song 《我拒绝被定义》 by ROYAZON / 音右. The reference video is not
redistributed in this repo; the stills in [`showcase/`](showcase/) are redrawn
from the same design tokens as the shipped video.

- Bili: link to the public video
- NetEase: <https://music.163.com/#/song?id=3422948585>
- Brand site: <https://music.zondev.top>

---

## License

MIT — see [`LICENSE`](LICENSE). Font attribution in
[`NOTICE`](NOTICE). All bundled fonts are SIL Open Font License 1.1 (via
`scripts/fetch_fonts.py`); no proprietary system fonts are bundled or shipped.

---

## See also

- [`docs/FONTS.md`](docs/FONTS.md) — how the three font families are resolved
- [`docs/PORTING-TO-REMOTION.md`](docs/PORTING-TO-REMOTION.md) — why this is
  Python and what a Remotion port would look like
- [`docs/FAQ.md`](docs/FAQ.md) — common questions

```text
$ python -m lyric_mv check
ffmpeg      : /usr/bin/ffmpeg
font heavy  : /usr/share/fonts/truetype/noto/NotoSerifSC-Bold.ttf
font sans   : /usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf
font latin  : /usr/share/fonts/truetype/noto/NotoSansSC-Bold.ttf
brand       : ROYAZON

OK
```