"""MV03 attempt 2: a review-only v4 intro derived from authoritative v3 inputs."""
from __future__ import annotations
import hashlib, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[3]
LEGACY = ROOT / "runs" / "incision-paper-full"
AUDIO = ROOT / "samples/review/real-song-demos/00_source/incision-code/netease.mp3"
LYRICS = LEGACY / "00_source/lyrics.lrc"
EVENTS = LEGACY / "01_timeline/render-character-events.json"
DISPLAY = LEGACY / "01_timeline/display-events-v3.json"
MUSIC = LEGACY / "01_timeline/music-events.json"
V3 = LEGACY / "03_render/incision-paper-full-v3-retained.mp4"
TEMPLATE = ROOT / "samples/review/real-song-demos/render_character_styles.py"
FONT = ROOT / "assets/fonts/reusable/LongCang-Regular.ttf"
FF = Path("D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe")
PROBE = Path("D:/ZON/runtime/media-tools/Library/bin/ffprobe.exe")
V4 = RUN / "03_render/incision-and-code-v4-intro-review.mp4"
CMP = RUN / "03_render/incision-and-code-v3-intro-comparator.mp4"
FPS, DURATION, W, H = 24, 15.5, 1280, 720

def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b"") : h.update(b)
    return h.hexdigest()

def write(p: Path, value) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def fade(a, b, amount): return tuple(round(x * (1 - amount) + y * amount) for x, y in zip(a, b))

def draw_note(d, x, y, size, color):
    d.ellipse((x-size, y-size*.7, x+size, y+size*.7), fill=color)
    d.line((x+size*.7, y, x+size*.7, y-size*4), fill=color, width=max(2, round(size/3)))
    d.line((x+size*.7, y-size*4, x+size*2.1, y-size*3.5), fill=color, width=max(2, round(size/3)))

def make_frame(frame_no: int, first, beats) -> Image.Image:
    t = frame_no / FPS
    page, ink, blue, muted = (238,235,225), (33,48,55), (55,116,141), (118,133,135)
    im = Image.new("RGB", (W,H), page); d = ImageDraw.Draw(im)
    title = ImageFont.truetype(str(FONT),46); ui = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",20)
    lyric = ImageFont.truetype(str(FONT),82); small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",18)
    d.text((66,44), "切口与暗号", font=title, fill=ink)
    d.text((69,98), "ROYAZON EOM  ·  v4 前奏短样（候选，未批准）", font=ui, fill=muted)
    line_progress = min(1, t/3); focus = max(0, min(1, (t-7)/(first["start"]-7)))
    left, right, sy = 126+60*focus, 1154-180*focus, 238
    for n in range(5):
        reveal=max(0,min(1,line_progress*5-n)); x2=left+(right-left)*reveal
        if x2>left: d.line((left,sy+n*31,x2,sy+n*31),fill=fade((202,205,195),blue,reveal),width=2)
    for idx,b in enumerate([b for b in beats if b <= t]):
        age=t-b
        if age<=4.2:
            x=left+((idx*83)%max(120,int(right-left-40))); y=sy+76-((idx*31)%110)
            draw_note(d,x,y,7+8*(1-age/4.2),fade(muted,blue,1-age/4.2))
    if focus:
        box=(int(115*focus),424,int(1165-115*focus),640)
        d.rounded_rectangle(box,radius=18,fill=(244,242,234),outline=fade((215,216,207),blue,focus),width=2)
        d.text((box[0]+34,box[1]+26), f"第一句 · 权威首字 {first['start']:.3f}s · 首帧 {math.ceil(first['start']*FPS)/FPS:.3f}s",font=small,fill=muted)
        x, y = box[0]+44, box[1]+78
        for item in first["chars"]:
            start_frame=math.ceil(item["start"]*FPS); end_frame=math.ceil(item["end"]*FPS)
            if frame_no < start_frame: color=(188,192,185)
            elif frame_no <= end_frame:
                color=blue; d.rounded_rectangle((x-8,y-10,x+74,y+100),radius=14,fill=(218,232,235))
            else: color=ink
            d.text((x,y),item["char"],font=lyric,fill=color); x+=76
    return im

def media_meta(path: Path):
    return json.loads(subprocess.check_output([str(PROBE),"-v","error","-show_entries","format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,duration,nb_frames","-of","json",str(path)],text=True,encoding="utf-8"))

def main():
    for sub in ("00_source","01_timeline","03_render","05_evidence"): (RUN/sub).mkdir(parents=True,exist_ok=True)
    required=(AUDIO,LYRICS,EVENTS,DISPLAY,MUSIC,V3,TEMPLATE,FONT)
    if not all(p.exists() for p in required): raise FileNotFoundError("required v3 source input missing")
    first=json.loads(EVENTS.read_text(encoding="utf-8"))[0]
    assert first["chars"][0]["char"] == "公" and first["start"] == first["chars"][0]["start"] == 10.04
    beats=[b for b in json.loads(MUSIC.read_text(encoding="utf-8"))["onset_seconds"] if b <= DURATION]
    rendered_first_frame=math.ceil(first["start"]*FPS); rendered_first_time=rendered_first_frame/FPS
    inputs={"immutableReadOnlyInputs":[{"kind":"v3 complete MP4","path":str(V3),"sha256":digest(V3)},{"kind":"source audio","path":str(AUDIO),"sha256":digest(AUDIO)},{"kind":"lyrics","path":str(LYRICS),"sha256":digest(LYRICS)},{"kind":"authoritative current render character timing","path":str(EVENTS),"sha256":digest(EVENTS)},{"kind":"v3 display timing","path":str(DISPLAY),"sha256":digest(DISPLAY)},{"kind":"music events","path":str(MUSIC),"sha256":digest(MUSIC)},{"kind":"template code","path":str(TEMPLATE),"sha256":digest(TEMPLATE)},{"kind":"font","path":str(FONT),"sha256":digest(FONT)}],"nativeDesign":"1280x720","output":"1920x1080 Lanczos upscaled","authoritativeFirstCharacter":{"char":"公","eventTime":10.04,"firstVisibleFrame":rendered_first_frame,"firstVisibleTime":rendered_first_time,"frameRate":FPS},"manualListening":"not performed; independent listener required"}
    write(RUN/"00_source/input-lock.json",inputs)
    write(RUN/"01_timeline/intro-design-v4.json",{"kind":"optional review-only v4 intro","duration":DURATION,"audioStart":0,"audioSpeed":1.0,"firstCharacter":inputs["authoritativeFirstCharacter"],"stages":[{"range":"0.000–3.000","change":"staff lines reveal"},{"range":"3.000–7.000","change":"decorative notes at existing detected onset events"},{"range":f"7.000–{rendered_first_time:.3f}","change":"staff converges to lyric reading area"},{"range":f"{rendered_first_time:.3f}–15.500","change":"characters are quantized to 24fps from authoritative current render timing"}],"notApproved":True,"notForUpload":True,"doesNotReplace":str(V3),"noteSemantics":"decorative rhythm cues, not pitch transcription"})
    cmd=[str(FF),"-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(AUDIO),"-t",str(DURATION),"-map","0:v:0","-map","1:a:0","-frames:v",str(round(DURATION*FPS)),"-vf","scale=1920:1080:flags=lanczos","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(V4)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE); assert p.stdin
    for n in range(round(DURATION*FPS)): p.stdin.write(make_frame(n,first,beats).tobytes())
    p.stdin.close()
    if p.wait(): raise RuntimeError("v4 render failed")
    # Re-encode (not stream-copy) to make video/audio both exactly the 0–15.500s review interval.
    subprocess.run([str(FF),"-y","-v","error","-i",str(V3),"-vf",f"trim=duration={DURATION},setpts=PTS-STARTPTS","-af",f"atrim=duration={DURATION},asetpts=PTS-STARTPTS","-frames:v",str(round(DURATION*FPS)),"-map","0:v:0","-map","0:a:0","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(CMP)],check=True)
    for name,src,time in (("v4-000",V4,0),("v4-650",V4,6.5),("v4-first-frame",V4,rendered_first_time),("v4-1120",V4,11.2),("v3-first-frame",CMP,rendered_first_time)):
        subprocess.run([str(FF),"-y","-v","error","-ss",str(time),"-i",str(src),"-frames:v","1",str(RUN/"05_evidence"/(name+".jpg"))],check=True)
    for media in (V4,CMP): subprocess.run([str(FF),"-v","error","-i",str(media),"-f","null","-"],check=True)
    result={"status":"candidate-not-approved-awaiting-independent-review","v4":{"path":str(V4),"sha256":digest(V4),"probe":media_meta(V4)},"v3Comparator":{"path":str(CMP),"sha256":digest(CMP),"probe":media_meta(CMP),"sourceInterval":"v3 0.000–15.500, re-encoded"},"firstCharacter":inputs["authoritativeFirstCharacter"]}
    write(RUN/"05_evidence/render-result.json",result)

if __name__ == "__main__": main()
