"""Audit gate: prove that NO character ever renders blank in the lyric window.

Regression test for the "文字被截断" reports. Two independent failure modes were
found and are both covered here:

  1. alpha blink  - a char's alpha was scaled by its own progress, so it snapped
                    1.0 -> 0.0 -> 1.0 at its start time (looked like a missing char).
  2. empty glyph  - char_glyph() cropped the unshifted bbox, so glyphs whose ink
                    does not start at the canvas origin (e.g. "一") were blank.

Method: render each frame twice - once normally, once with no lyric line - and
diff. Anything the lyric layer contributed shows up as a non-zero delta. For every
character we then measure how much of its actual drawn box (from char_box(), i.e.
the same maths frame() uses) contains contributed pixels.

Run:  D:/ZON/runtime/miniforge3/python.exe check_no_blank_chars.py
Exit code 0 = pass, 1 = a character rendered blank.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_wind_dream_combined_v2 as r  # noqa: E402

MIN_COVERAGE = 0.02   # 2% of a char's box must carry ink; a real glyph is 5-40%
DELTA = 30            # per-channel delta that counts as "the lyric layer drew here"


def main():
    cues = r.build_cues()
    feats = r.audio_features()
    rows = []
    blank = []
    for n in range(r.N):
        t = n / r.FPS
        act = next((c for c in cues if c['start'] - .12 <= t < c['end'] + .45), None)
        if act is None:
            continue
        fade_out = min(1, max(0, (act['end'] + .45 - t) / .30))
        # skip the global intro/outro blend: both renders are identical there,
        # so a zero diff would be a false positive rather than a real blank.
        if fade_out < .999 or not (.25 <= t <= r.N / r.FPS - .35):
            continue
        img = np.asarray(r.frame(n, cues, feats).convert('RGB'), dtype=np.int16)
        bg = np.asarray(r.frame(n, [], feats).convert('RGB'), dtype=np.int16)
        delta = np.abs(img - bg).max(axis=2)
        for p in r.layout_cue(act):
            ch = act['chars'][p['index']]
            gx, gy, iw, ih, _, _ = r.char_box(p, t, ch)
            x0, y0 = max(0, gx), max(0, gy)
            x1, y1 = min(r.W, gx + iw), min(r.H, gy + ih)
            if x1 <= x0 or y1 <= y0:
                continue
            sub = delta[y0:y1, x0:x1]
            cov = float((sub > DELTA).mean())
            rows.append(cov)
            if cov < MIN_COVERAGE:
                blank.append({'t': round(t, 3), 'line': act['text'],
                              'index': p['index'], 'char': ch['char'], 'coverage': round(cov, 4)})

    total = len(rows)
    report = {
        'window': [r.START, r.END],
        'frames_audited': r.N,
        'chars_measured': total,
        'min_coverage': round(min(rows), 4) if rows else None,
        'median_coverage': round(float(np.median(rows)), 4) if rows else None,
        'blank_characters': blank,
        'verdict': 'PASS' if not blank else 'FAIL',
    }
    out = Path(__file__).resolve().parent / f'blank-char-audit{r.TAG or "-excerpt"}.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'blank_characters'}, indent=2))
    if blank:
        print(f'\n{len(blank)} blank char samples (first 10):')
        for b in blank[:10]:
            print('  ', b)
    print(f'\nreport -> {out}')
    return 0 if not blank else 1


if __name__ == '__main__':
    raise SystemExit(main())
