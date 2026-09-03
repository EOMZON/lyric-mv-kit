# Porting to Remotion (and other engines)

This document explains why the current engine is **not** Remotion, and what
what it would take to swap it out. It's here so contributors don't re-litigate
the same decision in every PR.

## TL;DR

| | Python renderer (this repo) | Remotion port |
|--|-----------------------------|---------------|
| Authoring | Python classes / static methods | React components |
| Live preview | `python -m lyric_mv preview` writes PNGs | `npx remotion studio` hot-reloads in Chrome |
| Render | Pillow → rawvideo pipe → ffmpeg | React DOM at 30fps → MediaRecorder / headless Chrome |
| Headless requirements | ffmpeg | Node + Chromium |
| Determinism | byte-exact (same input → same pixels) | depends on font/CSS environment |
| Audio analysis | same code (numpy FFT) | re-implement or call back to Python |

The Python engine is **good enough** for what the kit ships today. Pick Remotion
when one of these becomes important to you:

- Designers want to iterate the typography in a browser, not in Python
- You need React components (e.g. drag a drop-shadowed lyric onto the canvas)
- You want a single repo to host both MVs and other React-rendered content

## What stays the same

The data layer is engine-agnostic. Everything in the `data` folder stays put:

- `plan.json`  — the timing model
- `audio_features.npz` — the spectrum envelope, bass / mid / treble / bands
- `song.json` (caller-provided) — sections + cue_times
- the cover tokens (`INK`, `GLOW`, `RIBBONS`, `SPECTRUM_STOPS`) — copy-paste
  the values; they are pixel-level equivalent to CSS colour tokens

So a Remotion port is *just* replacing the renderer. The whole analysis stack
(`audio.py`, `plan.py`, `align.py`) keeps working.

## What the Remotion port needs to re-implement

The 8 styles are subclasses of a single `Renderer` whose frame lifecycle is
fixed:

```
frame(i):
  background(i)      # gradient + aurora + edge lights
  draw_spectrum(i)    # 96 log bands around a ring
  draw_particles(i)   # 60 orbiting glints
  draw_lyric(t, i)    # per-character typography with timing
  draw_hud(t)         # brand, corner, timecode, progress bar
  draw_title(t)       # opening title card (0–6s)
```

In Remotion terms, each method becomes one or more components, with
`useCurrentFrame()` providing `i` and `useVideoConfig().fps` providing `fps`.
The audio features stay numpy; load them with `np.load()` on the server /
during pre-processing, then expose them as JSON.

A worked scaffolding:

```tsx
// src/AuroraRibbon.tsx — minimal port of StyleAuroraRibbon
import { useCurrentFrame, useVideoConfig, AbsoluteFill, Audio } from "remotion";

export const AuroraRibbon: React.FC<{plan: Plan, feats: Feats}> = ({plan, feats}) => {
  const i = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = i / fps;
  // ... same maths as lyric_mv/styles_eh.py::StyleAuroraRibbon
  return <AbsoluteFill>{/* spectrum + particles + lyric + HUD */}</AbsoluteFill>;
};
```

## Why we kept the current stack

1. The first version shipped with python in 36 hours. A Remotion port would
   have taken longer than the engineering runway allowed.
2. Rendering is already deterministic and fast enough (≈ 25 min for a 140 s
   song on 8 cores, no browser footprint).
4. The skill directory tree (`bili-publication-pipeline`) is full of Python;
   keeping the same language means the cover generator and the renderer share
   one tokenizer / one colour palette / one font resolver.
5. Future contributors can read it without learning the React + Remotion
   composition model.

If you ship a Remotion port that reuses `plan.json` + `audio_features.npz`
unchanged, drop us a PR — we'd like to add it as `lyric_mv_engines/remotion/`
without forking the data layer.