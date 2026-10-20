"""Word-level ground-truth cue timing — the fix for lyric drift.

Lesson from production (Cha-Cha Groove, 2026-10-13)
----------------------------------------------------
PER-LINE forced alignment is not trustworthy on fast, repetitive material:
a ``base`` model on the full mix AND a ``small`` model on the isolated vocal
stem both lock onto wrong positions in a repetitive chorus, and any
energy-based arbitration then necessarily picks the *late* candidate that
still has vocal energy — repeated lines put energy at many positions, so
"energy present" != "timing correct". The v4 video still ran 3–23s behind
the vocals from ~0:46 on.

Ground truth = two INDEPENDENT word-level timelines of the Demucs vocal stem:

  TR = stable-whisper ``transcribe`` (free decoding, word timestamps)
  AL = stable-whisper ``align`` on the full known lyric text

Adjudicated per line against the stem RMS envelope (TR primary; AL only where
TR's start sits in pure silence). Model mis-hearings of leading words
("Spot turn" -> "Walk to learn") are recovered by extending back over
contiguous non-ad-lib tokens; split tokens ("Chacha" -> "Cha -cha") re-grab
their first half. Ad-lib runs (>=2 identical consecutive tokens, e.g.
"cha-cha") are never swallowed into a lyric line.

This module ports that validated production algorithm (40/40 lines rebuilt,
max correction −23.0s) into a song-agnostic form: Latin word tokens and CJK
character tokens are both supported (``tokens_of``).
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

import numpy as np

from . import audio as audio_mod

# ---------------------------------------------------------------- constants
LEAD, HOLD, MIN_DUR, GAP = 0.08, 0.35, 0.50, 0.12
NEG = -0.8                      # gap penalty in the NW alignment
SIM_NEED_SHORT, SIM_NEED_LONG = 0.75, 0.50   # token match thresholds
SILENCE_ENERGY, LIVE_ENERGY = 0.10, 0.20     # RMS-envelope adjudication bands
BACK_MAX_SECS = 1.5             # backward recovery window

_TOK = re.compile(r"[A-Za-z0-9']+|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def tokens_of(text: str) -> list[str]:
    """Lyric tokens: Latin words (apostrophes kept) or single CJK characters."""
    return _TOK.findall((text or "").replace("’", "'").replace(",", " "))


def norm(w: str) -> str:
    return "".join(ch for ch in w.lower() if ch.isalnum() or ch == "'")


# ---------------------------------------------------------------- energy
class Envelope:
    """50ms RMS envelope of a (vocal) stem, smoothed over 5 frames."""

    def __init__(self, stem: Path | str):
        x = audio_mod.decode(stem)
        if x.ndim > 1:
            x = x.mean(axis=1)
        sr = audio_mod.SR
        hop = max(1, int(0.05 * sr))
        n = len(x) // hop
        rms = np.sqrt(np.array([np.mean(x[i * hop:(i + 1) * hop] ** 2) for i in range(n)]))
        self.env = np.convolve(rms, np.ones(5) / 5, mode="same")
        self.mx = float(self.env.max()) or 1.0
        self.n = n

    def at(self, sec: float, w: float = 0.25) -> float:
        """Mean normalised energy over [sec-0.05, sec+w)."""
        i0 = max(0, int((sec - 0.05) / 0.05))
        i1 = min(self.n, int((sec + w) / 0.05))
        if i1 <= i0:
            return 0.0
        return float(self.env[i0:i1].mean() / self.mx)


# ---------------------------------------------------------------- word timelines
def transcribe_words(stem: Path | str, language: str = "en",
                     model_size: str = "small",
                     out: Path | str | None = None) -> list[dict]:
    """TR: free decoding with word timestamps (stable-whisper)."""
    import stable_whisper

    model = stable_whisper.load_model(model_size)
    res = model.transcribe(str(stem), language=language, word_timestamps=True)
    words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip()}
             for seg in res.segments for w in seg.words]
    if out:
        Path(out).write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    return words


def _space_cjk(text: str) -> str:
    """Insert spaces around every CJK character.

    stable-whisper's ``align`` tokenises CJK into word-level units, which then
    merge common bigrams (慢慢/所有/下一…). ``rebuild`` chunks the AL timeline by
    per-character token counts, so the two must agree. Spacing every CJK char
    forces one token per character, matching :func:`tokens_of` exactly. Latin
    words are untouched, so this is a no-op for ``en`` songs.
    """
    out = []
    for ch in text:
        if re.match(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", ch):
            out.append(" " + ch + " ")
        else:
            out.append(ch)
    return "".join(out).replace("  ", " ").strip()


def align_words(stem: Path | str, lyrics_text: str, language: str = "en",
                model_size: str = "small",
                out: Path | str | None = None) -> list[dict]:
    """AL: force-align the full known lyric text onto the stem."""
    import stable_whisper

    text = _space_cjk(lyrics_text) if language.startswith("zh") else lyrics_text
    model = stable_whisper.load_model(model_size)
    res = model.align(str(stem), text, language=language)
    words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip()}
             for seg in res.segments for w in seg.words]
    if out:
        Path(out).write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    return words


def load_words(path: Path | str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- matching
def _nw_match(A: list[str], B: list[str]) -> dict[int, int]:
    """Needleman-Wunsch (fuzzy tokens) mapping lyric token index -> TR index."""
    n, m = len(A), len(B)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + NEG
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + NEG
    for i in range(1, n + 1):
        ai = A[i - 1]
        for j in range(1, m + 1):
            sim = difflib.SequenceMatcher(None, ai, B[j - 1]).ratio()
            dp[i][j] = max(dp[i - 1][j - 1] + (2 * sim - 1),
                           dp[i - 1][j] + NEG, dp[i][j - 1] + NEG)
    i, j, out = n, m, {}
    while i > 0 and j > 0:
        sim = difflib.SequenceMatcher(None, A[i - 1], B[j - 1]).ratio()
        if dp[i][j] == dp[i - 1][j - 1] + (2 * sim - 1):
            need = SIM_NEED_SHORT if len(A[i - 1]) <= 3 else SIM_NEED_LONG
            if sim >= need:
                out[i - 1] = j - 1
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + NEG:
            i -= 1
        else:
            j -= 1
    return out


def _is_adlib(B: list[str], j: int) -> bool:
    """True if TR token j belongs to a run of >=2 identical tokens (ad-libs)."""
    if len(B[j]) < 2:
        return False
    return (j + 1 < len(B) and B[j] == B[j + 1]) or (j - 1 >= 0 and B[j] == B[j - 1])


def rebuild(plan: dict, tr_words: list[dict], al_words: list[dict],
            env: Envelope) -> tuple[dict, list[dict]]:
    """Re-time every cue of ``plan`` from word-level ground truth.

    Returns ``(new_plan, provenance)``. ``new_plan`` is a copy with rebuilt
    ``start``/``end``; ``provenance`` carries per-cue source + divergence for
    the gate (:mod:`lyric_mv.gate`) and for cloud-AI review.
    """
    cues = plan["cues"]
    dur = float(plan["duration"])

    # ---- AL chunked 1:1 into lines (lyric token count per cue) ----
    al_spans, k = [], 0
    for c in cues:
        n = len(tokens_of(c["text"]))
        seg = al_words[k:k + n]
        k += n
        if not seg:
            raise SystemExit(
                "AL word timeline shorter than the lyric — alignment dropped "
                "words. Re-run the gt stage with a larger --model.")
        al_spans.append((seg[0]["start"], seg[-1]["end"]))
    if k != len(al_words):
        raise SystemExit(
            f"AL word count {len(al_words)} != lyric tokens {k} — the aligner "
            "split/merged words. Re-run the gt stage with a larger --model, "
            "or fix the lyric text.")

    # ---- NW: lyric tokens -> TR tokens ----
    lyric = []
    for i, c in enumerate(cues):
        for w in tokens_of(c["text"]):
            lyric.append((i, norm(w)))
    A = [w for _, w in lyric]
    B = [norm(w["word"]) for w in tr_words]
    map_a = _nw_match(A, B)

    # ---- per-line TR spans ----
    spans: dict[int, list] = {}
    for kk, (ci, _) in enumerate(lyric):
        if kk not in map_a:
            spans.setdefault(ci, [None, None])
            continue
        g = map_a[kk]
        s, e = spans.get(ci, [None, None])
        s = tr_words[g]["start"] if s is None else min(s, tr_words[g]["start"])
        e = tr_words[g]["end"] if e is None else max(e, tr_words[g]["end"])
        spans[ci] = [s, e]
    for ci in range(len(cues)):
        spans.setdefault(ci, [None, None])

    # split-token recovery: a lyric word heard as two identical tokens
    # ("Chacha" -> "Cha -cha") matched only its 2nd token -> pull back to 1st.
    claimed_by: dict[int, int] = {}
    for kk, g in map_a.items():
        claimed_by.setdefault(g, lyric[kk][0])
    for kk, g in list(map_a.items()):
        ci = lyric[kk][0]
        if g - 1 < 0 or B[g - 1] != B[g]:
            continue
        owner = claimed_by.get(g - 1)
        if owner is not None and owner != ci:
            continue
        if tr_words[g]["start"] - tr_words[g - 1]["start"] > 0.6:
            continue
        map_a[kk] = g - 1

    # backward recovery of UNMATCHED LEADING words (mis-heard line starts):
    # extend over contiguous non-ad-lib tokens never claimed by another line.
    first_gt: dict[int, int] = {}
    leading_unmatched: dict[int, int] = {}
    for kk, (ci, _) in enumerate(lyric):
        if kk in map_a:
            first_gt.setdefault(ci, map_a[kk])
        elif ci not in first_gt:
            leading_unmatched[ci] = leading_unmatched.get(ci, 0) + 1
    for ci, g0 in first_gt.items():
        need = leading_unmatched.get(ci, 0)
        if need == 0:
            continue
        s, e = spans[ci]
        g, grabbed = g0 - 1, 0
        while g >= 0 and grabbed < need + 2 and tr_words[g0]["start"] - tr_words[g]["start"] <= BACK_MAX_SECS:
            if _is_adlib(B, g):
                break
            owner = claimed_by.get(g)
            if owner is not None and owner != ci:
                break
            s = tr_words[g]["start"] if s is None else min(s, tr_words[g]["start"])
            grabbed += 1
            g -= 1
        spans[ci] = [s, e]

    # ---- adjudicate TR vs AL, build final cues ----
    new_cues, report = [], []
    prev_end = 0.0
    for i, c in enumerate(cues):
        nc = dict(c)
        tr_s, tr_e = spans[i]
        al_s, al_e = al_spans[i]
        src = "TR"
        if tr_s is None:
            s, e, src = al_s, al_e, "AL(no-TR)"
        else:
            s = tr_s
            if env.at(s) < SILENCE_ENERGY and env.at(al_s) > LIVE_ENERGY and abs(al_s - s) < 2.0:
                s, src = al_s, "AL(silence-fix)"
            e = tr_e if tr_e is not None else al_e
        start = max(0.0, s - LEAD)
        if start < prev_end + 0.02:
            start = prev_end + 0.02
        end = min(dur, e + HOLD)
        if end - start < MIN_DUR:
            end = min(dur, start + MIN_DUR)
        report.append({"index": i, "old_start": c["start"], "new_start": round(start, 3),
                       "true_start": s, "src": src, "energy": round(env.at(s), 3),
                       "text": c["text"]})
        nc["start"] = round(start, 3)
        nc["end"] = round(end, 3)
        new_cues.append(nc)
        prev_end = end

    for kk in range(len(new_cues) - 1):
        nxt = new_cues[kk + 1]["start"]
        if new_cues[kk]["end"] > nxt - GAP:
            new_cues[kk]["end"] = round(max(new_cues[kk]["start"] + MIN_DUR, nxt - GAP), 3)

    out = dict(plan)
    out["cues"] = new_cues
    out.setdefault("meta", {})
    out["meta"]["timings_source"] = (
        "word-level ground truth on the Demucs vocal stem: stable-whisper small "
        "transcribe (TR) + align() on the full lyric (AL), adjudicated per line "
        "against the stem RMS envelope")

    provenance = []
    for i, c in enumerate(new_cues):
        provenance.append({
            "index": i, "text": c["text"], "section": c.get("section", ""),
            "aligned": [c["start"], c["end"]],
            "seed": [cues[i]["start"], cues[i]["end"]],
            "fallback": False,
            "gt_source": report[i]["src"],
            "gt_word_span": spans[i],
        })
    return out, provenance
