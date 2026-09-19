# Motion Templates

These presets define **how the composition moves**. They do not define fonts, colors or artwork; those remain owned by the existing Visual Style registry.

## Bundled v1 templates

| id | default use | recommended existing visual style | motion character |
|---|---|---|---|
| `steady-karaoke` | universal readable lyrics | `C_cinematic_letterbox` | nearly fixed camera, safest default |
| `cinematic-float` | strong photography/artwork | `C_cinematic_letterbox` | slow push/pan, restrained parallax |
| `type-camera` | typography-first lyric MV | `A_editorial_air` | obvious macro camera movement without character jumping |
| `ambient-story` | dreamy/lyrical/illustrated songs | `F_aurora_ribbon` | continuous drift with background/foreground depth |
| `beat-push` | rap/electronic/strong chorus | `D_kinetic_poster` | bass-reactive push and cue sway |

## Composition model

```text
Visual Style × Motion Template × optional Song Motion Score
```

A new song should **start by choosing a template**, not by writing a custom renderer.

Only add a Song Motion Score when the song has specific section-level choreography that a reusable template should not generalize.

## Validation

```bash
python -m py_compile lyric_mv/motion.py lyric_mv/motion_renderer.py scripts/render_motion.py scripts/check_motion_configs.py
python scripts/check_motion_configs.py
```

Validate an explicit song score as well:

```bash
python scripts/check_motion_configs.py \
  --score path/to/your-motion-score.json \
  --duration 22
```

## Generic render bridge

`render_motion.py` can wrap any of the existing 8 visual styles without modifying their classes:

```bash
python scripts/render_motion.py \
  --plan work/plan.json \
  --features work/audio_features.npz \
  --style A_editorial_air \
  --motion-template presets/motion/type-camera.json \
  --preview-times 4,8,12
```

Add `--motion-score <path>` for song-specific choreography.
