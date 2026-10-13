"""Song-agnostic lyric-MV production pipeline.

One command, any song::

    python -m lyric_mv pipeline run \\
        --audio song.wav --lyrics lyrics.txt --song song.json \\
        --template aurora-ribbon-en-primary \\
        --work work/ --out out/mv.mp4

Stages (every stage writes provenance JSON into ``--work``; each stage is
skippable via ``--stages`` so re-runs are cheap):

  separate   Demucs htdemucs -> vocals.wav          (skip with --stem)
  plan       build-plan: auto cue grid + features    (skip with --plan-in)
  pair       bilingual pairing, primary = --language (the sung language)
  gt         word-level ground truth on the stem: TR (transcribe) + AL (align)
  rebuild    re-time every cue from the word timelines (:mod:`lyric_mv.gt`)
  finalize   role-swap if the template's primary language differs from the
             sung language (translation becomes the big line, same timings)
  gate       fail-closed sync gate (:mod:`lyric_mv.gate`) — blocks render
  render     full-song mp4 (reuses the ``render`` command)

Why this shape (2026-10-13 production lesson): per-line forced alignment is
not trustworthy on fast/repetitive songs — both a base model on the full mix
and a small model on the vocal stem lock onto wrong positions, and energy
arbitration then picks whichever late candidate still has vocal energy. Word-
level ground truth + the gate are the fix; see :mod:`lyric_mv.gt`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import bilingual, gt as gt_mod, templates as templates_mod

STAGES = ["separate", "plan", "pair", "gt", "rebuild", "finalize", "gate", "render"]


def _log(stage: str, msg: str) -> None:
    print(f"[pipeline:{stage}] {msg}", flush=True)


def _dump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- stages
def stage_separate(a: argparse.Namespace, work: Path) -> Path:
    from . import separate

    if a.stem:
        _log("separate", f"reusing stem {a.stem}")
        return Path(a.stem)
    outdir = work / "stems"
    vocals = separate.vocals(a.audio, outdir)
    _log("separate", f"vocals -> {vocals}")
    return Path(vocals)


def stage_plan(a: argparse.Namespace, work: Path) -> tuple[Path, Path]:
    from . import plan as plan_mod

    if a.plan_in:
        src = Path(a.plan_in).resolve()
        dst = work / "plan.auto.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        feats = Path(a.features) if a.features else src.parent / "audio_features.npz"
        _log("plan", f"reusing {src} (+ {feats})")
        return dst, Path(feats)
    song = plan_mod.load_song(a.song)
    plan, npz = plan_mod.build_plan(a.audio, a.lyrics, song, outdir=work)
    return work / "plan.json", npz


def stage_pair(a: argparse.Namespace, work: Path, plan_path: Path) -> Path:
    plan = _load(plan_path)
    paired = bilingual.pair_plan(plan, primary=a.language, template=a.template)
    out = work / "plan.paired.json"
    _dump(paired, out)
    pairs = paired["meta"]["bilingual"]["paired_cues"]
    _log("pair", f"{len(paired['cues'])} cues, {pairs} bilingual pairs -> {out}")
    return out


def stage_gt(a: argparse.Namespace, work: Path, stem: Path,
             paired_path: Path) -> tuple[Path, Path]:
    tr_out, al_out = work / "words.tr.json", work / "words.al.json"
    if a.tr and a.al:
        _log("gt", f"reusing word timelines {a.tr} + {a.al}")
        return Path(a.tr), Path(a.al)
    paired = _load(paired_path)
    text = " ".join(c["text"] for c in paired["cues"])
    _log("gt", f"transcribe ({a.language}, {a.model}) on {stem.name} ...")
    gt_mod.transcribe_words(stem, language=a.language, model_size=a.model, out=tr_out)
    _log("gt", "align full lyric ...")
    gt_mod.align_words(stem, text, language=a.language, model_size=a.model, out=al_out)
    return tr_out, al_out


def stage_rebuild(a: argparse.Namespace, work: Path, stem: Path,
                  paired_path: Path, tr_path: Path, al_path: Path) -> tuple[Path, Path]:
    paired = _load(paired_path)
    tr_words = gt_mod.load_words(tr_path)
    al_words = gt_mod.load_words(al_path)
    env = gt_mod.Envelope(stem)
    plan, provenance = gt_mod.rebuild(paired, tr_words, al_words, env)
    plan_path = work / "plan.gt.json"
    prov_path = work / "alignment.gt.json"
    _dump(plan, plan_path)
    _dump(provenance, prov_path)
    deltas = [round(abs(r["aligned"][0] - r["seed"][0]), 2) for r in provenance]
    _log("rebuild", f"{len(plan['cues'])} cues re-timed, max |Δ|={max(deltas):.2f}s "
                     f"-> {plan_path.name} + {prov_path.name}")
    return plan_path, prov_path


def stage_finalize(a: argparse.Namespace, work: Path, plan_path: Path) -> Path:
    """Role-swap when the template's display primary differs from the sung
    language: the translation becomes the big line and keeps the sung line's
    (correct) timings."""
    tpl = templates_mod.get(a.template)
    plan = _load(plan_path)
    if tpl["primary"] == a.language:
        final = plan
    else:
        swapped = 0
        for c in plan["cues"]:
            if c.get("translate"):
                c["text"], c["translate"] = c["translate"], c["text"]
                swapped += 1
        final = plan
        _log("finalize", f"swapped {swapped} cues to {tpl['primary']}-primary display")
    final.setdefault("meta", {})
    final["meta"]["template"] = a.template
    final["meta"]["sung_language"] = a.language
    audio = Path(final["audio"])
    if not audio.is_absolute():
        audio = (plan_path.parent / audio).resolve()
    final["audio"] = str(audio)
    out = work / "plan.final.json"
    _dump(final, out)
    _log("finalize", f"template={a.template} -> {out}")
    return out


def stage_gate(a: argparse.Namespace, work: Path, plan_path: Path,
               prov_path: Path) -> None:
    from . import gate

    rc = gate.run(plan_path, prov_path, a.max_fallback, a.max_diverge)
    if rc != 0:
        raise SystemExit("[pipeline:gate] FAILED — render blocked (fix the alignment first)")


def stage_render(a: argparse.Namespace, work: Path, plan_path: Path,
                 feats_path: Path) -> Path:
    from . import cli

    tpl = templates_mod.get(a.template)
    ns = argparse.Namespace(
        plan=str(plan_path), features=str(feats_path), style=tpl["style"],
        out=str(a.out), cover=a.cover, start=0, count=0,
        crf=a.crf, preset=a.preset, audio_bitrate=a.audio_bitrate)
    rc = cli.cmd_render(ns)
    if rc != 0:
        raise SystemExit(f"[pipeline:render] ffmpeg/renderer failed (rc={rc})")
    return Path(a.out)


# --------------------------------------------------------------------- main
def cmd_pipeline_run(a: argparse.Namespace) -> int:
    if isinstance(a.stages, str):
        a.stages = [s.strip() for s in a.stages.split(",") if s.strip()]
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    selected = [s for s in STAGES if s in a.stages] if a.stages else STAGES
    unknown = [s for s in a.stages if s not in STAGES] if a.stages else []
    if unknown:
        raise SystemExit(f"unknown stages {unknown}; available: {STAGES}")

    def _need(path, what, how):
        if path is None or not Path(path).exists():
            raise SystemExit(f"{what} missing ({how})")

    plan_path = feats_path = stem = None
    paired_path = tr_path = al_path = prov_path = None

    if "separate" in selected:
        stem = stage_separate(a, work)
    elif a.stem:
        stem = Path(a.stem)

    if "plan" in selected:
        plan_path, feats_path = stage_plan(a, work)
    elif a.plan_in:
        plan_path, feats_path = stage_plan(a, work)  # copies + locates features

    if "pair" in selected:
        _need(plan_path, "input plan", "pass --plan-in or include the plan stage")
        paired_path = stage_pair(a, work, plan_path)
    else:
        paired_path = work / "plan.paired.json"
        _need(paired_path, "paired plan", "include the pair stage")

    if "gt" in selected:
        _need(stem, "vocal stem", "pass --stem or include the separate stage")
        tr_path, al_path = stage_gt(a, work, stem, paired_path)
    else:
        tr_path = Path(a.tr) if a.tr else work / "words.tr.json"
        al_path = Path(a.al) if a.al else work / "words.al.json"
        _need(tr_path, "TR word timeline", "include the gt stage or pass --tr")
        _need(al_path, "AL word timeline", "include the gt stage or pass --al")

    if "rebuild" in selected:
        _need(stem, "vocal stem", "pass --stem or include the separate stage")
        plan_path2, prov_path = stage_rebuild(a, work, stem, paired_path, tr_path, al_path)
    else:
        plan_path2, prov_path = work / "plan.gt.json", work / "alignment.gt.json"
        _need(plan_path2, "rebuilt plan", "include the rebuild stage")
        _need(prov_path, "alignment provenance", "include the rebuild stage")

    if "finalize" in selected:
        final_path = stage_finalize(a, work, plan_path2)
    else:
        final_path = work / "plan.final.json"
        _need(final_path, "finalized plan", "include the finalize stage")

    if "gate" in selected:
        stage_gate(a, work, final_path, prov_path)

    if "render" in selected:
        _need(feats_path, "audio features", "pass --features or include the plan stage")
        stage_render(a, work, final_path, feats_path)
        _log("done", f"{a.out}")
    return 0


def add_pipeline_parser(sub) -> None:
    p = sub.add_parser("pipeline", help="song-agnostic production pipeline")
    psub = p.add_subparsers(dest="pcmd", required=True)

    r = psub.add_parser("run", help="run the pipeline (see stage list in docs/PIPELINE.md)")
    r.add_argument("--audio", help="song audio (any ffmpeg-decodable format)")
    r.add_argument("--lyrics", help="lyric .txt, one line per row (credits dropped)")
    r.add_argument("--song", help="song config JSON (title/sections; see presets/)")
    r.add_argument("--template", default="aurora-ribbon-en-primary",
                   help="template name (see: python -m lyric_mv templates)")
    r.add_argument("--language", default="en",
                   help="SUNG language of the audio (en/zh/...); drives pairing + GT models")
    r.add_argument("--model", default="small", help="whisper model size for the GT stage")
    r.add_argument("--work", default="work", help="working dir for stage artifacts")
    r.add_argument("--out", default="out/mv.mp4", help="final mp4 path (render stage)")
    r.add_argument("--cover", default=None, help="optional cover image for the render")
    r.add_argument("--stem", default=None, help="reuse an existing vocals.wav (skips separate)")
    r.add_argument("--plan-in", default=None, help="reuse an existing plan.json (skips plan)")
    r.add_argument("--features", default=None, help="audio_features.npz when using --plan-in")
    r.add_argument("--tr", default=None, help="reuse an existing TR word-timeline JSON")
    r.add_argument("--al", default=None, help="reuse an existing AL word-timeline JSON")
    r.add_argument("--stages", default="",
                   help="comma subset of: " + ",".join(STAGES))
    r.add_argument("--max-fallback", type=int, default=0)
    r.add_argument("--max-diverge", type=float, default=1.0)
    r.add_argument("--crf", type=int, default=19)
    r.add_argument("--preset", default="medium")
    r.add_argument("--audio-bitrate", default="192k")
    r.set_defaults(func=cmd_pipeline_run)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lyric-mv-pipeline",
                                 description="song-agnostic lyric-MV pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add_pipeline_parser(sub)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
