# FAQ

### Why pure Python instead of Remotion?

Three reasons:

1. **Determinism.** `frame(i)` is a pure function of `(plan, feats, i)` and
   the same input always renders to the same bytes. No browser, no
   font-loading race, no React hydration timing surprises.
2. **No headless footprint.** All you need is Pillow, numpy and ffmpeg. No
   Chromium download, no `playwright` profile to babysit, no
   `npx playwright install`.
3. **It already shipped.** The pipeline that produced the reference MV ran end
   to end with this stack. A Remotion port would have added a language to the
   skill repo for no quality gain.

See [`docs/PORTING-TO-REMOTION.md`](PORTING-TO-REMOTION.md) for the trade-off
spelled out and how to layer a Remotion port on top of the data layer.

### What ffmpeg version do I need?

Anything with `libx264` and `aac` is fine — 4.x or newer. macOS users: `brew
install ffmpeg`. Linux: any distro package labelled `ffmpeg` (not
`ffmpeg-minimal`) works. Windows: `winget install ffmpeg` or grab a build
from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).

`ffmpeg` only needs to be on `PATH` (or set via the `FFMPEG_BIN` env var if
you patch the launch script).

### Why no audio features for my song show up?

If the rendered video looks blank, run `python -m lyric_mv check` first. The
usual culprits are:

- Wrong ffmpeg / libx264 → 0-byte output
- Font not found → `FontNotFound` with a remediation hint
- `plan.json` lists a `cue_times` that doesn't match the number of lyric
  lines → `ValueError` from `lyric_mv.plan.build_cues`

For empty spectrum bands (rare): the band matrix is log-spaced from 30 Hz up
to `sr/2`. If your song is unusually bass-heavy and your `treble` band comes
out flat, raise `--fps` from 30 → 60 and re-render.

### Can I ship the cover template with my own brand?

Yes. Two options:

1. Set `LYRIC_MV_BRAND` (or `brand:` in `config.yaml`) — affects every part
   of the pipeline (video HUD and cover).
2. Pass `--no-hud` to `cover` for a fully bare cover, then post-process.

The cover generator's design language (aurora ribbons, the ink/glow colours,
the spectrum gradient, the HUD placement) is hard-coded to match the
`F_aurora_ribbon` video style. That is intentional: the cover is a *redraw*
of the same scene, so they look like they belong together. If your video
uses a different style, render its still with `python -m lyric_mv preview
--style <key>` instead — that's a frame grabbed from the actual render.

### Is this script safe to run on my laptop?

`python -m lyric_mv render` will happily burn a CPU core for ~25 min per song.
There's no GPU, no network, no upload — it's local-only. `ffmpeg` is the only
binary it shells out to; nothing else touches your filesystem outside the
output directory you pass.

### Does it run on macOS / Linux?

Yes. Font auto-detection covers macOS (`/System/Library/Fonts`,
`PingFang.ttc`) and Linux (`/usr/share/fonts`, Noto CJK). Windows works the
same way. The only platform-specific bit is `.ttc` font collection files
which use an `index=1` argument — handled by `lyric_mv.config.font()`.

### Why isn't the song's audio included in the repo?

Audio masters don't belong in version control:

- They bloat clone size (a 4-minute WAV is 40+ MB)
- They are typically not licensed for redistribution even if you wrote them
- They don't change the rendered output — you provide your own

The reference MV's audio and masters live in a separate private archive. See
`showcase/` for redrawn stills that demonstrate what the pipeline produces.

### My lyric text has section tags like `[verse]`. What happens?

They are stripped by `clean_lyrics` before timing is computed. They are not
displayed. If you want section markers on screen, add them as their own cue
lines with a short duration.

### How do I add a 9th visual style?

Subclass `lyric_mv.renderer.Renderer` and override one or more of:

* `background(i, acc, bass, treb)`
* `draw_spectrum(img, i, bass)`
* `draw_particles(img, i, bass, treb)`
* `draw_lyric(img, t, i, acc)`
* `draw_hud(img, t)`

Then register it in `lyric_mv/styles.py`. The 8 styles in
`lyric_mv/styles_ad.py` and `lyric_mv/styles_eh.py` are reference examples
with very different visual treatments — pick the one closest to your target
and start from there.