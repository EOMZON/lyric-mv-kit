"""V2: V3 packaging (watercolor bg + LongCang gold) + AURORA text dynamics, FIXED.

The line is ALWAYS fully readable. A character never leaves the screen: it sits at
the resting pose (INK gold) from the moment the line appears, and while it is being
sung it lifts ~14px and brightens to ACCENT, easing back down at BOTH ends of its
own interval. Highlight hand-off between neighbouring chars is a 0.10s cross-fade.

Aurora's raw `float` branch instead skips not-yet-sung chars (`if age<0: continue`),
which is what made a line read as half-missing. The previous "fix" kept the alpha=1
rest pose but also kept the old `entry=ease(age/.22)` alpha, so every character
snapped 1.0 -> 0.0 -> 1.0 at its own start time (plus a 32px downward jump): the
character visually blinked out exactly when it began to be sung.
"""
import argparse, json, math, os, subprocess, importlib.util
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
from fontTools.ttLib import TTFont

BASE = Path(__file__).resolve().parent
ALIGN = BASE.parent / '03_alignment' / 'forced_alignment.json'
V3_DIR = Path(r'd:\ZON\codex\lyric-mv-kit\samples\review\real-song-demos')
AUDIO = Path(r'd:\ZON\codex\lyric-mv-kit\samples\review\real-song-demos\00_source\wind-dream\netease.mp3')
BG = Path(r'd:\ZON\codex\lyric-mv-kit\samples\review\references\style-faithful\003-wind-dream-bg.png')
FONTROOT = Path(r'd:\ZON\codex\lyric-mv-kit\assets\fonts\reusable')
PRESETS = json.loads((V3_DIR.parent / 'typography-presets.json').read_text(encoding='utf-8'))
LINE_BREAKS = json.loads((V3_DIR / 'line-breaks.json').read_text(encoding='utf-8'))
TIMELINES = json.loads((V3_DIR / 'timelines.json').read_text(encoding='utf-8'))

W, H, FPS = 1280, 720, 24
# Lyric window. Defaults to the reviewed 22s excerpt; override for a full-song run:
#   WD_START=0.4 WD_END=69.7 WD_TAG=-full python render_wind_dream_combined_v2.py
START = float(os.environ.get('WD_START', 29.5))
END = float(os.environ.get('WD_END', 51.5))
TAG = os.environ.get('WD_TAG', '')
N = math.ceil((END - START) * FPS)
FFMPEG = r'D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe'
FFPROBE = r'D:\ZON\runtime\media-tools\Library\bin\ffprobe.exe'

P = PRESETS['wind-dream']
FONT = FONTROOT / P['font']
INK = ImageColor.getrgb(P['color'])            # gold #fff071 = resting color
ACCENT = (255, 255, 255)                        # pure white = the char being sung
BOX = P['box']

# --- motion tuning -----------------------------------------------------------
# The line is ALWAYS fully visible (never re-enters from invisible).  Only the
# character currently being sung floats up + brightens, and it eases back to the
# resting pose at BOTH ends of its interval, so there is no pop and no hole.
LIFT = 14          # px the highlighted char lifts off the baseline
RAMP = 0.10        # s: cross-fade half-width between neighbouring chars
BOB = 1.2          # px: subtle idle shimmer so the resting line still breathes
TARGET_SIZE = P['size']
TRACKING = P['tracking']
STRETCH = P['stretch']
SONG_TITLE = '风穿过指尖的梦'
ARTIST = '音右'

STROKE_COLOR = (20, 30, 60)          # dark navy — same as shadow, used as text outline
STROKE_WIDTH = 0                     # pixels; 1 subtle, 2 bold. DISABLED by request
                                     # (2026-09-11): the dark outline was added purely
                                     # to prop up contrast while the alpha-blink bug hid
                                     # characters. That bug is fixed, so the outline is
                                     # no longer needed and the V3 look is gold on water-
                                     # colour with only a soft drop shadow. Set >0 to
                                     # bring it back (the ring is drawn 8-way).

UTILITY = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)


def ease(x):
    return 1 - (1 - max(0, min(1, x))) ** 3


# Local phrasal-break overrides for wind-dream (kept out of the shared
# line-breaks.json so the review pipeline is untouched). These give meaningful
# line breaks instead of mechanical 5-char rows for the longer canonical lines.
EXTRA_BREAKS = {
    '跑道隐约拉长了影踪': '跑道隐约\n拉长了影踪',
    '分别后我把日历撕成纸飞机': '分别后我把日历\n撕成纸飞机',
    '窗台风吹得日子乱成跑道': '窗台风吹得日子\n乱成跑道',
    '远方却像地图上的迷宫': '远方却像\n地图上的迷宫',
    '你会不会也折一架机翼': '你会不会也\n折一架机翼',
    '跑道瞬间被云写成五线谱': '跑道瞬间被云\n写成五线谱',
    '你的笑像音符跳跃着': '你的笑像\n音符跳跃着',
    '我的心被旋律牵动着': '我的心被\n旋律牵动着',
    '只盼你会接住那份信仰': '只盼你会\n接住那份信仰',
    '我数着纸飞机的影子练马拉松配速': '我数着纸飞机的影子\n练马拉松配速',
}


def split_text(text):
    # 1) exact phrasal break (local override first, then shared)
    for table in (EXTRA_BREAKS, LINE_BREAKS):
        if text in table:
            return [l.strip() for l in table[text].splitlines() if l.strip()]
    # 2) prefix-aware: a known break key that is a *prefix* of this line
    #    (e.g. '我数着纸飞机的影子' + '练马拉松配速') -> break at phrase boundary
    #    instead of mechanical 5-char rows. Only triggers for longer canonical lines.
    for table in (EXTRA_BREAKS, LINE_BREAKS):
        for key in sorted(table, key=len, reverse=True):
            if text.startswith(key) and len(key) < len(text):
                return [key, text[len(key):]]
    cols = P['columns']
    phrases = text.split()
    if len(phrases) > 1 and all(len(x) <= cols for x in phrases):
        return phrases
    text = ''.join(phrases)
    count = max(1, math.ceil(len(text) / cols))
    width = math.ceil(len(text) / count)
    return [text[i:i + width] for i in range(0, len(text), width)]


def line_metrics(text, size):
    font = ImageFont.truetype(str(FONT), size)
    canvas = Image.new('RGBA', (max(W * 3, int(size * len(text) * 1.5)), size * 3))
    d = ImageDraw.Draw(canvas)
    x = size * .3
    placements = []
    for ch in text:
        bb = d.textbbox((x, size * .2), ch, font=font)
        placements.append({'char': ch, 'x': bb[0], 'w': bb[2] - bb[0], 'h': bb[3] - bb[1], 'origin_x': x})
        x += font.getlength(ch) + TRACKING
    total = placements[-1]['x'] + placements[-1]['w'] if placements else 0
    for p in placements:
        p['h'] = int(p['h'] * STRETCH)
    return total, placements


def fit_size(text):
    size = TARGET_SIZE
    while size >= 34:
        rows = split_text(text)
        ok = all(line_metrics(r, size)[0] <= BOX[2] for r in rows)
        total_h = sum(int(size * STRETCH) for _ in rows) + int(size * .10) * (len(rows) - 1)
        if ok and total_h <= BOX[3]:
            return size, rows
        size -= 3
    raise ValueError(f'Text does not fit: {text!r}')


def build_cues():
    """Use the 19 CANONICAL lyric lines (no mid-line splits) so a line never shows
    truncated. Long lines wrap visually via LINE_BREAKS but stay ONE timing unit.
    This matches the aurora renderer's line-units and avoids the V3 timeline's
    arbitrary half-line cue splits that read as '截断'."""
    align = json.loads(ALIGN.read_text(encoding='utf-8'))
    flat = []
    for s in align['segments']:
        for w in s['words']:
            txt = w['word'].strip()
            if not txt:
                continue
            n = len(txt)
            for k, ch in enumerate(txt):
                s0 = w['start'] + (w['end'] - w['start']) * k / n
                e0 = w['start'] + (w['end'] - w['start']) * (k + 1) / n
                flat.append({'char': ch, 'start': s0, 'end': e0})
    lyrics = [l.strip() for l in (BASE.parent / '00_source' / 'lyrics-wind-dream.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
    assert ''.join(c['char'] for c in flat) == ''.join(lyrics), 'alignment vs lyrics mismatch'
    cues = []
    idx = 0
    for line in lyrics:
        seg = flat[idx:idx + len(line)]
        idx += len(line)
        assert ''.join(c['char'] for c in seg) == line, f'line mismatch {line!r}'
        chars = [{'char': c['char'], 'start': c['start'] - START, 'end': c['end'] - START} for c in seg]
        cues.append({'text': line, 'chars': chars, 'start': seg[0]['start'] - START, 'end': seg[-1]['end'] - START})
    (BASE / 'v2-character-events.json').write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'cues: {len(cues)} full lines, {sum(len(c["chars"]) for c in cues)} chars, window {START}-{END}s', flush=True)
    return cues


def audio_features():
    cache = BASE / 'v2-features.npz'
    if cache.exists():
        return dict(np.load(cache))
    import librosa
    raw = subprocess.check_output([FFMPEG, '-v', 'error', '-ss', str(START), '-i', str(AUDIO),
                                   '-t', str(N / FPS), '-ar', '22050', '-ac', '1', '-f', 'f32le', '-'])
    y = np.frombuffer(raw, dtype=np.float32).copy()
    spec = importlib.util.spec_from_file_location('local_audio', r'd:\ZON\codex\lyric-mv-kit\lyric_mv\audio.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    features = mod.envelope(y, FPS)
    onset = librosa.onset.onset_strength(y=y, sr=22050, hop_length=256)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=22050, hop_length=256, units='time')
    times = librosa.onset.onset_detect(onset_envelope=onset, sr=22050, hop_length=256, units='time')
    pulse = np.zeros(N)
    for t in beats:
        for n in range(round(t * FPS), min(N, round(t * FPS) + 12)):
            pulse[n] = max(pulse[n], math.exp(-(n / FPS - t) / .12))
    features.update(pulse=pulse, beats=beats, onsets=times)
    np.savez_compressed(cache, **features)
    return features


@lru_cache(maxsize=256)
def char_glyph(ch, size, color):
    font = ImageFont.truetype(str(FONT), size)
    canvas = Image.new('RGBA', (max(1, int(size * 1.8)), int(size * 1.8)))
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), ch, font=font)
    d.text((-bb[0], -bb[1]), ch, font=font, fill=color + (255,))
    # The glyph is re-drawn shifted so its ink starts at (0,0), so the crop must
    # use the SHIFTED extent. Cropping `bb` (as before) silently kept a region of
    # empty canvas whenever bb[1] != 0 - which is exactly why "一" (a single low
    # horizontal stroke) rendered as a blank box, i.e. a "missing" character.
    cropped = canvas.crop((0, 0, bb[2] - bb[0], bb[3] - bb[1]))
    return cropped.resize((cropped.width, max(1, int(cropped.height * STRETCH))), Image.Resampling.LANCZOS)


# Ambient-motion master switches (added 2026-09-11: the original frame was
# visually static apart from the per-char float, so the song felt lifeless).
VIZ = True          # master on/off for all ambient layers below
BG_DRIFT = True     # slow parallax drift of the watercolour backdrop
GLOW = True         # warm breathing halo behind the lyric box, pulses on beats
SPECTRUM = True     # bottom full-width spectrum bar (the "song visualizer")
NOTES = True        # beat-synced eighth-notes floating up through the margins
PARTICLES = True    # faint dust/sparkle that twinkles with treble

BG_MARGIN = 36      # px of slack so the drift never exposes an edge


@lru_cache(maxsize=1)
def background():
    """Watercolour backdrop, slightly oversized so BG_DRIFT can shift it."""
    return Image.open(BG).convert('RGBA').resize((W + 2 * BG_MARGIN, H + 2 * BG_MARGIN),
                                                Image.Resampling.LANCZOS)


def drifted_bg(t):
    bg = background()
    if not BG_DRIFT:
        return bg.crop((BG_MARGIN, BG_MARGIN, BG_MARGIN + W, BG_MARGIN + H))
    dx = int(BG_MARGIN + 11 * math.sin(t * 0.18) + 4 * math.sin(t * 0.07))
    dy = int(BG_MARGIN + 8 * math.sin(t * 0.13 + 1.3) + 3 * math.sin(t * 0.05 + 0.7))
    dx = max(0, min(BG_MARGIN * 2, dx)); dy = max(0, min(BG_MARGIN * 2, dy))
    return bg.crop((dx, dy, dx + W, dy + H))


@lru_cache(maxsize=1)
def _glow_sprite():
    """Radial warm gradient, drawn once and reused (scaled per frame)."""
    S = 256
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    c = S / 2.0
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    a = (np.clip(1 - dist, 0, 1) ** 2 * 255).astype(np.uint8)
    spr = np.zeros((S, S, 4), np.uint8)
    spr[..., 0] = 255; spr[..., 1] = 240; spr[..., 2] = 175; spr[..., 3] = a
    return Image.fromarray(spr, 'RGBA')


def note(d, x, y, size, color):
    """Vector eighth note (no font dependency, scales cleanly at any size)."""
    d.ellipse((x - size * .3, y - size * .12, x + size * .3, y + size * .15), fill=color)
    d.line((x + size * .25, y, x + size * .25, y - size), fill=color, width=max(1, round(size * .1)))
    d.line((x + size * .25, y - size, x + size * .62, y - size * .66), fill=color, width=max(1, round(size * .11)))


def _note_schedule(features):
    """Deterministic per-beat spawn plan -> keeps notes out of the lyric box
    (x0=65,y0=450,w=790,h=225) by confining them to the right margin + top band."""
    rng = np.random.RandomState(20260911)
    sched = []
    for i, bt in enumerate(features['beats']):
        zone = i % 3
        if zone == 0:
            x, y0, rise = rng.uniform(905, 1235), rng.uniform(150, 470), -rng.uniform(120, 210)
        elif zone == 1:
            x, y0, rise = rng.uniform(905, 1235), rng.uniform(480, 690), -rng.uniform(120, 200)
        else:
            x, y0, rise = rng.uniform(120, 815), rng.uniform(70, 300), -rng.uniform(90, 160)
        sched.append((float(bt), float(x), float(y0), float(rise),
                      float(rng.uniform(9, 15)), float(rng.uniform(0, 6.28))))
    return sched


def draw_visualizer(canvas, t, n, features):
    """All ambient motion layers, composited behind the lyrics."""
    if not VIZ:
        return
    bands = features['bands'][min(n, len(features['bands']) - 1)]
    pulse = float(features['pulse'][min(n, len(features['pulse']) - 1)])
    bass = float(features['bass'][min(n, len(features['bass']) - 1)])
    treble = float(features['treble'][min(n, len(features['treble']) - 1)])
    rms = float(features['rms'][min(n, len(features['rms']) - 1)])

    # 1) breathing halo behind the lyric box
    if GLOW:
        g = _glow_sprite()
        energy = 0.10 + 0.30 * pulse + 0.12 * bass
        dia = int((210 + 70 * pulse + 30 * bass) * 2)
        g = g.resize((dia, dia), Image.Resampling.LANCZOS)
        g.putalpha(g.getchannel('A').point(lambda a: int(a * energy)))
        cx, cy = BOX[0] + BOX[2] // 2, BOX[1] + BOX[3] // 2
        canvas.alpha_composite(g, (cx - dia // 2, cy - dia // 2))

    # 2) bottom spectrum bar (capped below the lyric box's bottom edge)
    if SPECTRUM:
        d = ImageDraw.Draw(canvas)
        NB = 64
        x0, total, bw = 36, W - 72, (W - 72) // NB
        base_y = 716
        for j in range(NB):
            bi = int(j / NB * 95)
            v = float(bands[bi] + bands[min(bi + 1, 95)]) / 2
            h = 6 + min(34, v * 30)
            x = x0 + j * bw
            a = int(55 + 95 * min(1.0, v))
            d.rounded_rectangle([x, base_y - h, x + bw - 3, base_y], radius=min(3, bw // 2),
                                fill=(255, 240, 170, a))
        d.line((x0, base_y + 2, x0 + total, base_y + 2), fill=(255, 240, 170, 60), width=1)

    # 3) floating dust / sparkle that twinkles with treble (margins only)
    if PARTICLES:
        d = ImageDraw.Draw(canvas)
        for i in range(26):
            px = (0.10 + 0.80 * ((i * 73) % 97) / 97) * W
            py = (((i * 131) % 211) / 211) * H
            y = (py - (t * 7 + i * 13) % H) % H
            x = px + 6 * math.sin(t * 0.6 + i)
            if not (x > 880 or y < 420 or x < 55):
                continue  # keep the lyric area and title clear
            tw = 0.5 + 0.5 * math.sin(t * 1.7 + i * 2.1)
            a = int((22 + 55 * treble) * tw)
            if a <= 0:
                continue
            r = 1 + (i % 3)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 200, a))

    # 4) beat-synced eighth notes rising through the margins
    if NOTES:
        d = ImageDraw.Draw(canvas)
        LIFE = 2.2
        for bt, x, y0, rise, size, ph in _note_schedule(features):
            age = t - bt
            if age < 0 or age > LIFE:
                continue
            k = age / LIFE
            y = y0 + rise * k
            xo = x + 10 * math.sin(age * 2 + ph)
            fade = min(1, age / 0.3) * (1 - k)
            a = int(175 * fade)
            if a <= 0:
                continue
            note(d, xo, y, size + 5 * math.sin(min(1, age / .3) * math.pi / 2), (255, 240, 170, a))


def mix(a, b, w):
    """Linear blend between two RGB tuples; w=0 -> a, w=1 -> b."""
    w = max(0.0, min(1.0, w))
    return tuple(round(a[i] + (b[i] - a[i]) * w) for i in range(3))


def highlight_weight(t, ch, ramp=RAMP):
    """How strongly char `ch` reads as "the one being sung" at time t.

    Trapezoid: 0 before the char, ramps up over `ramp` seconds, plateaus while it
    is sung, ramps down over `ramp` seconds.  Because the up-ramp of char i+1 and
    the down-ramp of char i overlap, the highlight glides along the line instead
    of snapping - and we never touch alpha, so a character can never disappear.
    """
    s, e = ch['start'], ch['end']
    r = min(ramp, max(e - s, 1e-3) * 0.45)
    if t <= s - r or t >= e + r:
        return 0.0
    if t < s + r:
        return (t - (s - r)) / (2 * r)
    if t <= e - r:
        return 1.0
    return ((e + r) - t) / (2 * r)


_LAYOUT_CACHE = {}


def layout_cue(cue):
    """Memoised: fit_size()/line_metrics() are expensive and a given line always
    lays out identically, so rebuilding it on every frame is pure waste."""
    if cue['text'] in _LAYOUT_CACHE:
        return _LAYOUT_CACHE[cue['text']]
    size, rows = fit_size(cue['text'])
    line_h = int(size * STRETCH)
    gap = int(size * .10)
    total_h = line_h * len(rows) + gap * (len(rows) - 1)
    top = BOX[1] + (BOX[3] - total_h) // 2
    placements = []
    for row_i, row in enumerate(rows):
        _, metrics = line_metrics(row, size)
        row_x0 = BOX[0]
        y = top + row_i * (line_h + gap)
        for m in metrics:
            g = char_glyph(m['char'], size, INK)
            placements.append({'char': m['char'], 'x': int(row_x0 + m['x']),
                               'y': int(y + (line_h - g.height) // 2), 'glyph': g, 'index': len(placements)})
    _LAYOUT_CACHE[cue['text']] = placements
    return placements


def char_box(p, t, ch):
    """Where the glyph for char `ch` actually lands at time t, as (gx, gy, w, h).

    Shared by frame() and by check_no_blank_chars.py so the audit measures the
    exact pixels that get drawn rather than a separate approximation.
    """
    w = highlight_weight(t, ch)
    scale = 1.0 + 0.06 * w
    gw, gh = p['glyph'].size
    iw, ih = max(1, round(gw * scale)), max(1, round(gh * scale))
    dy = -LIFT * w + BOB * math.sin(t * 1.6 + p['index'])
    gx = int(round(p['x'] - (iw - gw) / 2))
    gy = int(round(p['y'] + dy - (ih - gh) / 2))
    return gx, gy, iw, ih, w, scale


def frame(n, cues, features):
    t = n / FPS
    canvas = drifted_bg(t)
    if VIZ:
        draw_visualizer(canvas, t, n, features)
    d = ImageDraw.Draw(canvas)
    d.text((48, 28), f'{SONG_TITLE} / {ARTIST}', font=UTILITY, fill=(255, 255, 255, 160))
    active = next((c for c in cues if c['start'] - .12 <= t < c['end'] + .45), None)
    if active:
        fade_out = min(1, max(0, (active['end'] + .45 - t) / .30))
        placements = layout_cue(active)
        for p in placements:
            ch = active['chars'][p['index']]
            w = highlight_weight(t, ch)
            color = mix(INK, ACCENT, w)
            # ALPHA IS NEVER MODULATED BY THE CHAR'S OWN PROGRESS. It only tracks
            # the line-level fade. A char therefore can never blink out.
            alpha = fade_out
            if alpha <= 0.01:
                continue
            gx, gy, iw, ih, _, scale = char_box(p, t, ch)
            im = Image.new('RGBA', p['glyph'].size, color + (255,))
            im.putalpha(p['glyph'].getchannel('A'))
            if scale != 1.0:
                im = im.resize((iw, ih), Image.Resampling.BICUBIC)
            im.putalpha(im.getchannel('A').point(lambda a: round(a * alpha)))
            # --- shadow (behind everything) ---
            shadow = Image.new('RGBA', im.size, (20, 30, 60, 0))
            shadow.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(4)))
            canvas.alpha_composite(shadow, (gx + 2, gy + 2))
            # --- stroke outline (dark border for readability on any bg) ---
            if STROKE_WIDTH > 0:
                stroke_im = Image.new('RGBA', im.size, STROKE_COLOR + (255,))
                # 8-way offsets close the ring; the 4 diagonal ones alone leave the
                # outline open at N/S/E/W, which is what let pale gold wash out.
                stroke_im.putalpha(im.getchannel('A').point(lambda a: round(a * alpha)))
                for dx in (-STROKE_WIDTH, 0, STROKE_WIDTH):
                    for dyy in (-STROKE_WIDTH, 0, STROKE_WIDTH):
                        if dx == 0 and dyy == 0:
                            continue
                        canvas.alpha_composite(stroke_im, (gx + dx, gy + dyy))
            # --- main glyph (on top) ---
            canvas.alpha_composite(im, (gx, gy))
    fade = min(ease(t / .25), ease((N / FPS - t) / .35))
    return Image.blend(Image.new('RGB', (W, H), (12, 14, 19)), canvas.convert('RGB'), fade)


def probe(path):
    return json.loads(subprocess.check_output([FFPROBE, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stills', action='store_true'); args = ap.parse_args()
    lyrics = [l.strip() for l in (BASE.parent / '00_source' / 'lyrics-wind-dream.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
    with TTFont(FONT) as fnt:
        missing = [c for c in set(SONG_TITLE + ''.join(lyrics)) if ord(c) not in fnt.getBestCmap()]
    assert not missing, f'missing glyphs: {missing}'
    cues = build_cues(); features = audio_features()
    # 8.16 / 6.16 / 18.0 are char-start instants - the exact moments the old build
    # blanked a character, so they are the frames worth eyeballing.
    for time in (2., 6.16, 8.16, 15., 18., 20.):
        frame(round(time * FPS), cues, features).save(BASE / f'v2-{time:.1f}.jpg', quality=92)
    if args.stills:
        print('stills only'); return
    dest = BASE / f'wind-dream-combined-v2{TAG}.mp4'
    cmd = [FFMPEG, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', str(START), '-i', str(AUDIO), '-t', str(N / FPS), '-map', '0:v', '-map', '1:a:0',
           '-af', f'afade=t=in:d=0.2,afade=t=out:st={N / FPS - .4}:d=0.4',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(dest)]
    with (BASE / 'v2-render.log').open('wb') as log:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)
        try:
            for n in range(N):
                proc.stdin.write(frame(n, cues, features).tobytes())
        finally:
            proc.stdin.close(); code = proc.wait()
    assert code == 0, 'ffmpeg failed'
    subprocess.run([FFMPEG, '-v', 'error', '-i', str(dest), '-f', 'null', '-'], check=True)
    meta = probe(dest)
    assert abs(float(meta['format']['duration']) - N / FPS) < .15
    assert any(x['codec_type'] == 'audio' for x in meta['streams'])
    (BASE / 'v2-render-result.json').write_text(json.dumps(
        {'style': 'V3-packaging + aurora-dynamics (fixed)', 'song': SONG_TITLE, 'video': str(dest),
         'duration': N / FPS, 'window': [START, END], 'decode': 'pass', 'glyphs': 'pass'}, indent=2), encoding='utf-8')
    print(f'v2 done -> {dest} ({N / FPS:.2f}s)', flush=True)


if __name__ == '__main__':
    main()
