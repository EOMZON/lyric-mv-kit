"""Read-only verification for MV03 attempt 2."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]; FF=Path("D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe")
def sha(p):
 h=hashlib.sha256();
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def main():
 d=json.loads((RUN/"01_timeline/intro-design-v4.json").read_text(encoding="utf-8")); r=json.loads((RUN/"05_evidence/render-result.json").read_text(encoding="utf-8"))
 assert d["firstCharacter"]["eventTime"]==10.04 and d["firstCharacter"]["firstVisibleFrame"]==241 and d["firstCharacter"]["firstVisibleTime"]==241/24
 assert d["audioSpeed"]==1 and d["notApproved"] and d["notForUpload"]
 outcome={"scope":"candidate self-check only; independent manual listening is pending","verdict":"pass-for-review","checks":{}}
 for label,entry in (("v4",r["v4"]),("v3Comparator",r["v3Comparator"])):
  path=Path(entry["path"]); subprocess.run([str(FF),"-v","error","-i",str(path),"-f","null","-"],check=True)
  s={x["codec_type"]:x for x in entry["probe"]["streams"]}; assert s["video"]["codec_name"]=="h264" and s["video"]["nb_frames"]=="372"; assert s["audio"]["codec_name"]=="aac"; assert abs(float(s["video"]["duration"])-15.5)<.001 and abs(float(s["audio"]["duration"])-15.5)<.001
  outcome["checks"][label]={"decode":"pass","h264Frames":s["video"]["nb_frames"],"videoDuration":s["video"]["duration"],"audioDuration":s["audio"]["duration"],"sha256":sha(path)}
 outcome["visualEvidence"]={"staffAndOnsetDrivenNotes":"v4-650.jpg","authoritativeFirstCharacterFrame":"v4-first-frame.jpg","v3SameFrameComparator":"v3-first-frame.jpg","laterTextReadability":"v4-1120.jpg"}; outcome["notTested"]=["manual listening","user approval","upload","publication"]
 (RUN/"05_evidence/candidate-self-check.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__": main()
