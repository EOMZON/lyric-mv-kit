"""Build and validate a non-destructive MV04 timeline candidate from the preserved automatic alignment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[0]
LEGACY = RUN.parents[2] / "your-own-road-poster-full"
MAX_DURATION = 76.821


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    original = json.loads((LEGACY / "aligned.json").read_text(encoding="utf-8"))
    candidate = json.loads((HERE / "timing-candidate.json").read_text(encoding="utf-8"))
    source = json.loads((LEGACY / "source.json").read_text(encoding="utf-8"))
    edits = {(item["cueIndex"], item["charIndex"]): item for item in candidate["edits"]}
    cues, issues = [], []
    for cue_index, segment in enumerate(original["segments"]):
        chars = []
        for char_index, word in enumerate(segment["words"]):
            char = word["word"].strip()
            item = {"char": char, "start": word["start"], "end": word["end"]}
            edit = edits.get((cue_index, char_index))
            if edit:
                if edit["char"] != char:
                    issues.append({"type": "character_mismatch", "cueIndex": cue_index, "charIndex": char_index})
                item.update(start=edit["start"], end=edit["end"])
            chars.append(item)
        for char_index, item in enumerate(chars):
            if len(item["char"]) != 1 or item["start"] < 0 or item["end"] <= item["start"] or item["end"] > MAX_DURATION:
                issues.append({"type": "invalid_span", "cueIndex": cue_index, "charIndex": char_index, **item})
            if char_index and chars[char_index - 1]["end"] > item["start"] + 0.001:
                issues.append({"type": "overlap", "cueIndex": cue_index, "left": chars[char_index - 1], "right": item})
        cues.append({"text": segment["text"], "chars": chars, "start": chars[0]["start"], "end": chars[-1]["end"]})
    canonical = "".join(line["text"] for line in cues)
    expected = "".join(source["catalog"]["lyrics"].replace("(嘘)", "").split())
    if canonical != expected:
        issues.append({"type": "canonical_text_mismatch", "expectedCharacters": len(expected), "actualCharacters": len(canonical)})
    audio = Path(source["source"]["audio"])
    report = {
        "versionId": "v20260908-01",
        "sourceDuration": MAX_DURATION,
        "sourceAudioSha256": sha256(audio),
        "originalAutomaticAlignmentSha256": sha256(LEGACY / "aligned.json"),
        "displayCharacters": sum(len(cue["chars"]) for cue in cues),
        "canonicalText": "pass" if canonical == expected else "fail",
        "issueCount": len(issues),
        "manualListeningVerified": False,
        "status": "candidate_structurally_valid_pending_manual_listening" if not issues else "candidate_invalid",
        "issues": issues,
    }
    (HERE / "candidate-character-events.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")
    (RUN / "05_evidence" / "candidate-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if issues:
        raise SystemExit(json.dumps(report, ensure_ascii=False))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
