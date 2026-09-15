"""Wind Dream v5: v4 readable micro-motion + macro Motion Score choreography.

The v4 visual language is preserved: LongCang gold lyrics, continuous paper-wind
white focus, restrained halo/particles/wave and smooth crossfades. The structural
change is that background, environment and lyric layers now move at different
parallax rates under one song-level motion score.
"""
import argparse, hashlib, json, math, subprocess, sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
RUN = OUT.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lyric_mv.motion import MotionController, load_score, load_template
from lyric_mv.motion_renderer import _transform_layer

ALIGN = RUN / '03_alignment' / 'forced_alignment.json'
LYRICS = RUN / '00_source' / 'lyrics-wind-dream.txt'
AUDIO = ROOT / 'samples/review/real-song-demos/00_source/wind-dream/netease.mp3'
BG = ROOT / 'samples/review/references/style-faithful/003-wind-dream-bg.png'
FONT = ROOT / 'assets/fonts/reusable/LongCang-Regular.ttf'
TEMPLATE = ROOT / 'presets/motion/type-camera.json'
SCORE = OUT / 'motion-score.json'
FFMPEG = Path(r'D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe')
FFPROBE = Path(r'D:\ZON\runtime\media-tools\Library\bin\ffprobe.exe')
W,H,FPS,START,DURATION = 1280,720,24,29.5,22.0
N = int(DURATION * FPS)
INK = ImageColor.getrgb('#fff071'); ACCENT=(255,249,231); BOX=(65,365,790,225)
SIZE, TRACKING, STRETCH = 156,-4,1.12
CROSSFADE=.24; CURSOR_RAMP=.46
WAVE_LIFT=5.0; WAVE_SCALE=.020; NEIGHBOR=.55; LINE_BREATHE=1.2
PARTICLE_COUNT=15; HALO_MAX_ALPHA=34; WAVE_SEGMENTS=20
BREAKS = {'跑道隐约拉长了影踪':'跑道隐约\n拉长了影踪','分别后我把日历撕成纸飞机':'分别后我把日历\n撕成纸飞机','窗台风吹得日子乱成跑道':'窗台风吹得日子\n乱成跑道','远方却像地图上的迷宫':'远方却像\n地图上的迷宫','你会不会也折一架机翼':'你会不会也\n折一架机翼','跑道瞬间被云写成五线谱':'跑道瞬间被云\n写成五线谱','你的笑像音符跳跃着':'你的笑像\n音符跳跃着','我的心被旋律牵动着':'我的心被\n旋律牵动着','只盼你会接住那份信仰':'只盼你会\n接住那份信仰','我数着纸飞机的影子练马拉松配速':'我数着纸飞机的影子\n练马拉松配速'}


def smooth(x):
    x=max(0.,min(1.,x)); return x*x*(3-2*x)
def cosine(x):
    x=max(0.,min(1.,x)); return .5-.5*math.cos(math.pi*x)
def mix(a,b,w): return tuple(round(a[i]+(b[i]-a[i])*w) for i in range(3))


def chars_from_alignment():
    data=json.loads(ALIGN.read_text(encoding='utf-8')); flat=[]
    for seg in data['segments']:
        for word in seg['words']:
            text=word['word'].strip()
            for i,ch in enumerate(text):
                s=word['start']+(word['end']-word['start'])*i/len(text)
                e=word['start']+(word['end']-word['start'])*(i+1)/len(text)
                flat.append({'char':ch,'raw_start':s,'raw_end':e,'start':s-START,'end':e-START})
    lines=[x.strip() for x in LYRICS.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert ''.join(x['char'] for x in flat)==''.join(lines)
    cues=[]; at=0
    for text in lines:
        cc=flat[at:at+len(text)]; at+=len(text)
        cues.append({'text':text,'chars':cc,'start':cc[0]['start'],'end':cc[-1]['end']})
    return cues


@lru_cache(maxsize=1)
def bg(): return Image.open(BG).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
@lru_cache(maxsize=128)
def glyph(ch,size):
    f=ImageFont.truetype(str(FONT),size); q=Image.new('L',(size*2,size*2)); d=ImageDraw.Draw(q)
    b=d.textbbox((0,0),ch,font=f); d.text((-b[0],-b[1]),ch,font=f,fill=255)
    return q.crop((0,0,b[2]-b[0],b[3]-b[1])).resize((b[2]-b[0],max(1,round((b[3]-b[1])*STRETCH))),Image.Resampling.LANCZOS)
def lines(text):
    return [row[i:i+6] for row in BREAKS.get(text,text).splitlines() for i in range(0,len(row),6)]
@lru_cache(maxsize=32)
def layout(text):
    rows=lines(text); size=SIZE if len(rows)<=2 else 112; f=ImageFont.truetype(str(FONT),size); out=[]; lineh=round(size*STRETCH); total=lineh*len(rows)+round(size*.1)*(len(rows)-1); top=BOX[1]+(BOX[3]-total)//2; k=0
    for r,row in enumerate(rows):
        widths=[f.getlength(ch)+TRACKING for ch in row]; x=BOX[0]
        for ch,adv in zip(row,widths):
            g=glyph(ch,size); out.append((k,x,top+r*(lineh+round(size*.1))+(lineh-g.height)//2,g)); x+=adv; k+=1
    return out
def cue_alpha(t,i,cues):
    c=cues[i]; a=smooth((t-(c['start']-CROSSFADE))/CROSSFADE)
    if i+1<len(cues): a*=1-smooth((t-(cues[i+1]['start']-CROSSFADE))/CROSSFADE)
    return a
def char_weight(t,ch):
    s,e=ch['start'],ch['end']; r=CURSOR_RAMP
    if t<s-r or t>e+r:return 0.
    if t<s:return cosine((t-(s-r))/r)
    if t<=e:return 1.
    return cosine(1-(t-e)/r)
def wave_weights(t,cue):
    raw=[char_weight(t,ch) for ch in cue['chars']]
    return [max(raw[i], NEIGHBOR*(raw[i-1] if i else 0), NEIGHBOR*(raw[i+1] if i+1<len(raw) else 0)) for i in range(len(raw))]
@lru_cache(maxsize=1)
def halo_sprite():
    s=320; yy,xx=np.mgrid[0:s,0:s].astype(float); d=np.sqrt((xx-s/2)**2+(yy-s/2)**2)/(s/2)
    a=(np.clip(1-d,0,1)**2*255).astype(np.uint8); x=np.zeros((s,s,4),np.uint8); x[...,0]=255;x[...,1]=242;x[...,2]=188;x[...,3]=a
    return Image.fromarray(x,'RGBA')
def audio_features():
    raw=subprocess.check_output([str(FFMPEG),'-v','error','-ss',str(START),'-i',str(AUDIO),'-t',str(DURATION),'-ar','22050','-ac','1','-f','f32le','-'])
    y=np.frombuffer(raw,dtype=np.float32); edges=np.linspace(0,len(y),N+1,dtype=int); rms=np.array([np.sqrt(np.mean(y[edges[i]:edges[i+1]]**2)+1e-9) for i in range(N)])
    norm=np.clip(rms/(np.percentile(rms,95)+1e-9),0,1); out=np.zeros(N); attack=1-math.exp(-1/(FPS*.25)); release=1-math.exp(-1/(FPS*.35))
    for i,v in enumerate(norm): out[i]=out[i-1]+(attack if v>out[i-1] else release)*(v-out[i-1]) if i else v
    return out
def draw_environment(canvas,t,n,envelope):
    g=halo_sprite().copy(); alpha=int(8+HALO_MAX_ALPHA*float(envelope[n])); g.putalpha(g.getchannel('A').point(lambda a: a*alpha//255)); canvas.alpha_composite(g,(300,275))
    d=ImageDraw.Draw(canvas,'RGBA'); rng=np.random.RandomState(20260914)
    for i in range(PARTICLE_COUNT):
        x0=rng.uniform(35,W-35); y0=rng.uniform(70,H-45); x=x0+5*math.sin(t*.35+i); y=(y0-t*(3.5+i%3))%H
        if 45<x<900 and 300<y<690: continue
        a=int(11+10*(.5+.5*math.sin(t*.8+i))); d.ellipse((x-1,y-1,x+1,y+1),fill=(255,248,210,a))
    pts=[]
    for j in range(WAVE_SEGMENTS):
        phase=t*.7+j*.43; amp=3+5*float(envelope[n]); pts.append((42+j*(W-84)/(WAVE_SEGMENTS-1),704-amp*(.5+.5*math.sin(phase))))
    d.line(pts,fill=(255,240,174,42),width=2)
def draw_cue(canvas,t,cue,alpha):
    if alpha<=.001:return
    weights=wave_weights(t,cue); breathe=LINE_BREATHE*math.sin(2*math.pi*t/10)
    for idx,x,y,mask in layout(cue['text']):
        w=weights[idx]; col=mix(INK,ACCENT,w); scale=1+WAVE_SCALE*w; mw,mh=mask.size; nw,nh=round(mw*scale),round(mh*scale); gx=x-(nw-mw)/2; gy=y+breathe-WAVE_LIFT*w-(nh-mh)/2
        a=mask.resize((nw,nh),Image.Resampling.BICUBIC).point(lambda p:round(p*alpha)); shadow=Image.new('RGBA',(nw,nh),(24,35,62,0)); shadow.putalpha(a.filter(ImageFilter.GaussianBlur(3)))
        canvas.alpha_composite(shadow,(round(gx+2),round(gy+2))); ink=Image.new('RGBA',(nw,nh),col+(255,)); ink.putalpha(a); canvas.alpha_composite(ink,(round(gx),round(gy)))


def make_controller(cues):
    plan={'duration':DURATION,'cues':[{'text':c['text'],'start':c['start'],'end':c['end']} for c in cues]}
    return MotionController(plan, load_template(TEMPLATE), load_score(SCORE, duration=DURATION))


def frame(n,cues,envelope,controller):
    t=n/FPS; state=controller.state_at(t,bass=float(envelope[n]),treble=0.)
    background=bg().convert('RGBA')
    environment=Image.new('RGBA',(W,H),(0,0,0,0)); draw_environment(environment,t,n,envelope)
    lyrics=Image.new('RGBA',(W,H),(0,0,0,0))
    for i,c in enumerate(cues): draw_cue(lyrics,t,c,cue_alpha(t,i,cues))
    bg_layer=_transform_layer(background,state.x*state.background_parallax,state.y*state.background_parallax,max(1.10,1+(state.scale-1)*.45),state.rotation*.15,(12,14,19,255))
    env_layer=_transform_layer(environment,state.x*.62,state.y*.62,1+(state.scale-1)*.70,state.rotation*.35,(0,0,0,0))
    lyric_layer=_transform_layer(lyrics,state.x,state.y,state.scale,state.rotation,(0,0,0,0))
    composed=Image.alpha_composite(bg_layer,env_layer); composed=Image.alpha_composite(composed,lyric_layer)
    d=ImageDraw.Draw(composed); utility=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18); d.text((48,28),'风穿过指尖的梦 / 音右',font=utility,fill=(255,255,255,145))
    fade=min(smooth(t/.25),smooth((DURATION-t)/.35)); return Image.blend(Image.new('RGB',(W,H),(12,14,19)),composed.convert('RGB'),fade)


def audit(cues,envelope,controller):
    states=[controller.state_at(n/FPS,bass=float(envelope[n]),treble=0.) for n in range(N)]
    motion={'max_camera_dx_per_frame':max(abs(states[i].x-states[i-1].x) for i in range(1,N)),'max_camera_dy_per_frame':max(abs(states[i].y-states[i-1].y) for i in range(1,N)),'max_camera_scale_delta_per_frame':max(abs(states[i].scale-states[i-1].scale) for i in range(1,N)),'x_range':[min(s.x for s in states),max(s.x for s in states)],'y_range':[min(s.y for s in states),max(s.y for s in states)],'scale_range':[min(s.scale for s in states),max(s.scale for s in states)]}
    transitions=[]
    for i in range(len(cues)-1):
        a,b=cues[i+1]['start']-CROSSFADE,cues[i+1]['start']; overlap=[n for n in range(N) if a<=n/FPS<=b and cue_alpha(n/FPS,i,cues)>.05 and cue_alpha(n/FPS,i+1,cues)>.05]
        if b < 0 or a > DURATION: continue
        transitions.append({'from':cues[i]['text'],'to':cues[i+1]['text'],'overlap_frames':len(overlap),'pass':len(overlap)>=4})
    return {'motion':motion,'crossfade_seconds':CROSSFADE,'all_transitions_pass':all(x['pass'] for x in transitions),'transitions':transitions}
def probe(path): return json.loads(subprocess.check_output([str(FFPROBE),'-v','error','-show_entries','format=duration:stream=codec_type,codec_name,r_frame_rate,nb_frames,width,height','-of','json',str(path)]))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--preview',action='store_true'); args=ap.parse_args(); cues=chars_from_alignment(); envelope=audio_features(); controller=make_controller(cues); audit_data=audit(cues,envelope,controller)
    if args.preview:
        for t in (1.04,4.34,7.40,10.08,13.20,16.98,19.90,21.90): frame(round(t*FPS),cues,envelope,controller).save(OUT/f'v5-{t:.2f}.jpg',quality=92)
        (OUT/'v5-motion-audit.json').write_text(json.dumps(audit_data,ensure_ascii=False,indent=2),encoding='utf-8'); print('preview pass'); return
    dest=OUT/'wind-dream-v5-motion-score.mp4'; cmd=[str(FFMPEG),'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-ss',str(START),'-i',str(AUDIO),'-t',str(DURATION),'-map','0:v','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(N): p.stdin.write(frame(n,cues,envelope,controller).tobytes())
    p.stdin.close(); assert p.wait()==0
    subprocess.run([str(FFMPEG),'-v','error','-i',str(dest),'-f','null','-'],check=True); meta=probe(dest)
    (OUT/'v5-motion-result.json').write_text(json.dumps({'design_brief':{'job':'22-second macro-motion review','base':'v4 readable micro-motion','template':'type-camera','score':'motion-score.json'},'output':{'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'media':meta},'checks':{'decode':'pass','audit':audit_data},'untested':['manual visual/listening review','full-song render']},ensure_ascii=False,indent=2),encoding='utf-8')
    print(dest)
if __name__=='__main__': main()
