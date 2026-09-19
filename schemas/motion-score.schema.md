# Motion Score schema v1

`motion-score.json` is the optional song-specific choreography layer between a reusable Motion Template and the renderer.

It must not contain visual-style concerns such as fonts, colors, artwork paths, lyric text or brand HUD.

## Shape

```json
{
  "version": 1,
  "id": "example-song-motion-score",
  "template": "type-camera",
  "window": {
    "source_start_seconds": 29.5,
    "duration_seconds": 22.0
  },
  "intent": "one continuous right/upward journey",
  "segments": [
    {
      "start": 4.34,
      "end": 7.40,
      "easing": "ease_in_out",
      "from": {"x": 24, "y": -6, "scale": 1.045},
      "to": {"x": 78, "y": -14, "scale": 1.052}
    }
  ]
}
```

## Required fields

- `version`: currently `1`.
- `segments`: ordered array. It may be empty when a reusable template is enough.
- segment `start`: seconds in the render window.
- segment `end`: seconds in the render window; must be greater than `start`.

## Optional fields

- `id`: stable human-readable identifier.
- `template`: expected reusable Motion Template id.
- `window`: source window metadata for review runs. It is descriptive; the renderer samples segment time relative to the active plan.
- `intent`: short art-direction note.
- segment `easing`: `linear`, `ease_in`, `ease_out`, `ease_in_out`, or `sine`. Unknown values fall back to smoothstep/ease-in-out.
- `from` / `to`: any subset of `x`, `y`, `scale`, `rotation`.

## Units

- `x`, `y`: output pixels, positive x = right, positive y = down.
- `scale`: dimensionless camera/foreground scale. Values around `1.0` are expected.
- `rotation`: degrees.
- `start`, `end`: seconds.

## Ownership boundary

### plan.json owns

- audio path;
- duration / fps / frame count;
- sections;
- lyric cues;
- song metadata.

### Motion Template owns

- reusable pan / zoom grammar;
- cue sway defaults;
- parallax ratios;
- small audio-reactive defaults.

### Motion Score owns

- song-specific macro-camera events;
- section-level build / peak / release;
- explicit directional choreography that should not be generalized to every song.

### Visual Style owns

- typography;
- palette;
- visualizer appearance;
- background material;
- particles / glows as visual elements;
- lyric micro-animation.

## Validation gates

1. Segments are ordered by `start`.
2. Every segment has `end > start >= 0`.
3. Segment start must not exceed the plan duration.
4. A score does not need to cover the whole song; uncovered time falls back to the reusable template.
5. Adjacent segments should normally share matching boundary values to avoid visible jumps.
6. A score must remain optional: a Motion Template has to render meaningfully without it.
7. Macro motion must not replace lyric readability checks, transition overlap checks or safe-area checks.

## Compatibility

The schema is renderer-neutral. A Pillow renderer, Remotion renderer or future WebGL renderer should be able to consume the same score after mapping `x/y/scale/rotation` to its own transform system.