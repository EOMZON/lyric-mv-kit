"""v5 regression audit: blank-char + lyric safe-area for the Wind Dream v5 candidate.

Adapts the v4 `check_no_blank_chars.py` method to `render_v5_motion_score.py`:
renders each frame twice (with / without the lyric layer), diffs to isolate the
lyric ink, then maps every character's drawn rect through the v5 layer transform
(camera translation + scale) so coverage is measured in final output space.

Also accumulates the union bounding box of contributed lyric ink so the macro
camera can be checked against a safe area (safety gate: no dynamic edge clipping).

Run: D:/ZON/runtime/miniforge3/python.exe <this file>
Exit code 0 = pass, 1 = a character rendered blank.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SCORE_ROOT = HERE.parents[5]
if str(SCORE_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORE_ROOT))

spec = importlib.util.spec_from_file_location("rv5", HERE / "render_v5_motion_score.py")
rv5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rv5)

MIN_COVERAGE = 0.02   # 2% of a char's box must carry ink; a real glyph is ~20-45%
DELTA = 30            # per-channel delta that counts as "the lyric layer drew here"
SAFE_MARGIN = 12      # px from the canvas edge the lyric ink must not cross


def layer_origin(scale: float, x: float, y: float):
    """Replicate render_v5_motion_score._transform_layer geometry for the lyric layer."""
    nw = round(rv5.W * scale)
    nh = round(rv5.H * scale)
    px = round((rv5.W - nw) / 2 + x)
    py = round((rv5.H - nh) / 2 + y)
    return scale, px, py


def main() -> int:
    cues = rv5.chars_from_alignment()
    env = rv5.audio_features()
    ctrl = rv5.make_controller(cues)
    rows = []
    blank = []
    min_x = min_y = 10 ** 9
    max_x = max_y = -10 ** 9
    for n in range(rv5.N):
        t = n / rv5.FPS
        # skip the global intro/outro blend where both renders stay identical
        if not (0.25 <= t <= rv5.DURATION - 0.35):
            continue
        with_img = np.asarray(rv5.frame(n, cues, env, ctrl).convert("RGB"), dtype=np.int16)
        without = np.asarray(rv5.frame(n, [], env, ctrl).convert("RGB"), dtype=np.int16)
        ink = np.abs(with_img - without).max(axis=2) > DELTA
        if ink.any():
            ys, xs = np.where(ink)
            min_x = min(min_x, int(xs.min())); max_x = max(max_x, int(xs.max()))
            min_y = min(min_y, int(ys.min())); max_y = max(max_y, int(ys.max()))
        state = ctrl.state_at(t, bass=float(env[n]), treble=0.0)
        scale, px, py = layer_origin(state.scale, state.x, state.y)
        for i, cue in enumerate(cues):
            # Only audit chars while their cue is substantially visible. Measuring
            # during a 5-12% crossfade-in/out tail triggers false "blank" positives
            # (faint ink falls below the absolute pixel-delta gate) without indicating a
            # real missing glyph. A genuine blank also shows at mid-cue alpha (~1.0).
            if rv5.cue_alpha(t, i, cues) <= 0.5:
                continue
            weights = rv5.wave_weights(t, cue)
            breathe = rv5.LINE_BREATHE * np.sin(2 * np.pi * t / 10)
            for (idx, gx0, gy0, mask), ch in zip(rv5.layout(cue["text"]), cue["chars"]):
                w = weights[idx]
                gscale = 1 + rv5.WAVE_SCALE * w
                mw, mh = mask.size
                nw = round(mw * gscale); nh = round(mh * gscale)
                gx = gx0 - (nw - mw) / 2
                gy = gy0 + breathe - rv5.WAVE_LIFT * w - (nh - mh) / 2
                X0 = round(gx * scale + px); Y0 = round(gy * scale + py)
                X1 = round((gx + nw) * scale + px); Y1 = round((gy + nh) * scale + py)
                x0, y0 = max(0, X0), max(0, Y0)
                x1, y1 = min(rv5.W, X1), min(rv5.H, Y1)
                if x1 <= x0 or y1 <= y0:
                    continue
                cov = float(ink[y0:y1, x0:x1].mean())
                rows.append(cov)
                if cov < MIN_COVERAGE:
                    blank.append({"t": round(t, 3), "line": cue["text"],
                                  "char": ch["char"], "coverage": round(cov, 4)})

    inside = None
    if rows and min_x < 10 ** 9:
        inside = (min_x >= SAFE_MARGIN and min_y >= SAFE_MARGIN
                  and max_x <= rv5.W - SAFE_MARGIN and max_y <= rv5.H - SAFE_MARGIN)
    report = {
        "score": "v5-motion-score",
        "window": [rv5.START, rv5.START + rv5.DURATION],
        "frames": rv5.N,
        "chars_measured": len(rows),
        "min_coverage": round(min(rows), 4) if rows else None,
        "median_coverage": round(float(np.median(rows)), 4) if rows else None,
        "blank_characters": blank,
        "lyric_ink_bounds": {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y},
        "safe_margin_px": SAFE_MARGIN,
        "inside_safe_area": inside,
        "verdict": "PASS" if not blank else "FAIL",
    }
    out = HERE / "v5-blank-char-audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "blank_characters"},
                     ensure_ascii=False, indent=2))
    if blank:
        print(f"\n{len(blank)} blank samples (first 10):")
        for b in blank[:10]:
            print("  ", b)
    print(f"\nreport -> {out}")
    return 0 if not blank else 1


if __name__ == "__main__":
    raise SystemExit(main())
