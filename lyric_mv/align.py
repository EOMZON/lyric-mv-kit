"""Optional: derive lyric timings from the audio instead of hand-aligning.

These functions need heavy optional dependencies that are **not** installed by
default::

    pip install -U openai-whisper stable-ts demucs

Typical flow for a brand-new song::

    from lyric_mv import separate, align

    vocals = separate.vocals("song.wav", "work/stems")     # Demucs
    result = align.force_align(vocals, "lyrics.txt")       # stable-ts
    times  = align.segments_to_cue_times(result)           # -> cue_times
    # paste `times` into your song config as "cue_times", then build-plan

Why bother: hand-typed timings drift. Forced alignment against an isolated
vocal stem lands each line within ~100 ms, which is what makes the per-character
karaoke reveal feel locked to the voice.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CREDIT_RE = re.compile(r"^\s*(作词|作曲|编曲|混音|制作|录音|词|曲|编|混)\s*[:：]")


def canonical_lines(lyrics: Path | str) -> list[str]:
    """Read a lyric .txt and return the display lines, credits dropped."""
    raw = Path(lyrics).read_text(encoding="utf-8")
    out = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or CREDIT_RE.match(ln):
            continue
        ln = re.sub(r"\[[^\]]*\]", "", ln).strip()
        if ln:
            out.append(ln)
    return out


def transcribe(vocals: Path | str, lyrics: Path | str, model_size: str = "small",
               out: Path | str | None = None) -> dict:
    """Whisper transcription with word timestamps, primed with the real lyrics.

    Passing the canonical lyrics as ``initial_prompt`` keeps the recogniser from
    inventing homophones, which is the usual cause of "the sung word and the
    on-screen word disagree".
    """
    import whisper  # optional dependency

    prompt = "，".join(canonical_lines(lyrics))
    model = whisper.load_model(model_size)
    result = model.transcribe(
        str(vocals),
        language="zh",
        task="transcribe",
        initial_prompt=prompt,
        word_timestamps=True,
        condition_on_previous_text=False,
        temperature=0,
        fp16=False,
    )
    if out:
        Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    return result


def force_align(vocals: Path | str, lyrics: Path | str, model_size: str = "small",
                language: str = "zh", out: Path | str | None = None):
    """Force-align canonical lyric lines onto the vocal stem.

    Sentence punctuation is inserted between lines so the aligner sees explicit
    lyric-line boundaries instead of one undifferentiated blob.
    """
    import stable_whisper  # optional dependency

    lines = canonical_lines(lyrics)
    text = "。\n".join(lines) + "。"
    model = stable_whisper.load_model(model_size)
    result = model.align(
        str(vocals), text, language=language,
        original_split=True, vad=True, nonspeech_skip=1.0,
        failure_threshold=0.35,
    )
    if result is None:
        raise RuntimeError("forced alignment failed — try a larger model or a cleaner stem")
    if out:
        result.save_as_json(str(out))
    return result


def segments_to_cue_times(result, min_gap: float = 0.02) -> list[list[float]]:
    """Convert an alignment result to the ``cue_times`` shape used by song configs.

    Accepts a stable-ts result object, a dict, or a path to a saved JSON.
    """
    if isinstance(result, (str, Path)):
        result = json.loads(Path(result).read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        result = result.to_dict()

    segs = result.get("segments") or []
    times: list[list[float]] = []
    prev_end = 0.0
    for s in segs:
        st = float(s["start"])
        en = float(s["end"])
        # Guard against overlapping or zero-length cues: the renderer picks the
        # first cue whose window contains t, so overlaps silently swallow lines.
        st = max(st, prev_end + min_gap) if times else st
        if en <= st:
            en = st + min_gap
        times.append([round(st, 3), round(en, 3)])
        prev_end = en
    return times
