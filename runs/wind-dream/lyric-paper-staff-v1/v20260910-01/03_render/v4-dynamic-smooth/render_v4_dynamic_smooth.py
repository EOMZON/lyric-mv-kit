"""22-second paper-wind lyric candidate.  Render-only timing; source alignment untouched."""
import argparse, hashlib, json, math, subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
RUN = OUT.parent.parent
ALIGN = RUN / '03_alignment' / 'forced_alignment.json'
LYRICS = RUN / '00_source' / 'lyrics-wind-dream.txt'
AUDIO = ROOT / 'samples/review/real-song-demos/00_source/wind-dream/netease.mp3'
BG = ROOT / 'samples/review/references/style-faithful/003-wind-dream-bg.png'
FONT = ROOT / 'assets/fonts/reusable/LongCang-Regular.ttf'
FFMPEG = Path(r'D:\ZON\runtime\media-tools\Library\bin\ffmpeg.exe')
FFPROBE = Path(r'D:\ZON\runtime\media-tools\Library\bin\ffprobe.exe')
W,H,FPS,START,DURATION = 1280,720,24,29.5,22.0
N = int(DURATION * FPS)
INK = ImageColor.getrgb('#fff071'); ACCENT=(255,249,231); BOX=(65,365,790,225)
SIZE, TRACKING, STRETCH = 156,-4,1.12
CROSSFADE=.24; CURSOR_RAMP=.46  # raised-cosine step <= .143 at 24 fps
SAFE_MARGIN=12; SHADOW_OFFSET=(2,2); SHADOW_EXTENT=9  # GaussianBlur(3) conservative bounds
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
def bg(): return Image.open(BG).convert('RGB').resize((W+8,H+8),Image.Resampling.LANCZOS)
@lru_cache(maxsize=128)
def glyph(ch,size):
    f=ImageFont.truetype(str(FONT),size); q=Image.new('L',(size*2,size*2)); d=ImageDraw.Draw(q)
    b=d.textbbox((0,0),ch,font=f); d.text((-b[0],-b[1]),ch,font=f,fill=255)
    return q.crop((0,0,b[2]-b[0],b[3]-b[1])).resize((b[2]-b[0],max(1,round((b[3]-b[1])*STRETCH))),Image.Resampling.LANCZOS)
def lines(text):
    # Six LongCang glyphs remain legible at the established scale.  Reflow only
    # render copies of long rows; alignment/source text stay untouched.
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
    # A raised-cosine temporal kernel: static glyph geometry, continuously moving white focus.
    s,e=ch['start'],ch['end']; r=CURSOR_RAMP
    if t<s-r or t>e+r:return 0.
    if t<s:return cosine((t-(s-r))/r)
    if t<=e:return 1.
    return cosine(1-(t-e)/r)
def wave_weights(t,cue):
    """Temporal cosine cursor expanded to adjacent glyphs: one continuous wind field."""
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
    # Slow halo only reacts to attack/release-smoothed audio, below lyric contrast.
    g=halo_sprite().copy(); alpha=int(8+HALO_MAX_ALPHA*float(envelope[n])); g.putalpha(g.getchannel('A').point(lambda a: a*alpha//255)); canvas.alpha_composite(g,(300,275))
    d=ImageDraw.Draw(canvas,'RGBA'); rng=np.random.RandomState(20260914)
    for i in range(PARTICLE_COUNT):
        x0=rng.uniform(35,W-35); y0=rng.uniform(70,H-45); x=x0+5*math.sin(t*.35+i); y=(y0-t*(3.5+i%3))%H
        if 45<x<900 and 300<y<690: continue
        a=int(11+10*(.5+.5*math.sin(t*.8+i))); d.ellipse((x-1,y-1,x+1,y+1),fill=(255,248,210,a))
    # A restrained 20-segment smooth wave, visually secondary to the lyric field.
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
        canvas.alpha_composite(shadow,(round(gx+SHADOW_OFFSET[0]),round(gy+SHADOW_OFFSET[1]))); ink=Image.new('RGBA',(nw,nh),col+(255,)); ink.putalpha(a); canvas.alpha_composite(ink,(round(gx),round(gy)))
def frame(n,cues,envelope):
    t=n/FPS; dx=round(4*math.sin(2*math.pi*t/21)); dy=round(3*math.sin(2*math.pi*t/19+1.1)); base=bg().crop((4+dx,4+dy,4+dx+W,4+dy+H)).convert('RGBA'); draw_environment(base,t,n,envelope)
    d=ImageDraw.Draw(base); utility=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18); d.text((48,28),'风穿过指尖的梦 / 音右',font=utility,fill=(255,255,255,145))
    for i,c in enumerate(cues): draw_cue(base,t,c,cue_alpha(t,i,cues))
    fade=min(smooth(t/.25),smooth((DURATION-t)/.35)); return Image.blend(Image.new('RGB',(W,H),(12,14,19)),base.convert('RGB'),fade)
def layout_audit(cues):
    """Bounds of actual nonzero glyph pixels and their conservative blurred shadows."""
    safe=(SAFE_MARGIN,SAFE_MARGIN,W-SAFE_MARGIN,H-SAFE_MARGIN); glyphs=[]
    for cue in cues:
        for idx,x,y,mask in layout(cue['text']):
            bb=mask.getbbox()
            if not bb: continue
            ink=(x+bb[0],y+bb[1],x+bb[2],y+bb[3])
            shadow=(ink[0]+SHADOW_OFFSET[0]-SHADOW_EXTENT,ink[1]+SHADOW_OFFSET[1]-SHADOW_EXTENT,ink[2]+SHADOW_OFFSET[0]+SHADOW_EXTENT,ink[3]+SHADOW_OFFSET[1]+SHADOW_EXTENT)
            glyphs.append({'cue':cue['text'],'char':cue['chars'][idx]['char'],'ink':ink,'shadow':shadow})
    boxes=[g['ink'] for g in glyphs]+[g['shadow'] for g in glyphs]
    overall=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    offenders=[g for g in glyphs if g['shadow'][0]<safe[0] or g['shadow'][1]<safe[1] or g['shadow'][2]>safe[2] or g['shadow'][3]>safe[3]]
    # Dynamic field can add a 5px lift, 1.2px line breath and 2% centered scale.
    dynamic=(overall[0]-3,overall[1]-WAVE_LIFT-LINE_BREATHE-3,overall[2]+3,overall[3]+LINE_BREATHE+3)
    return {'safe_rect':{'left':safe[0],'top':safe[1],'right':safe[2],'bottom':safe[3]},'actual_ink_bounds':{'min_x':min(g['ink'][0] for g in glyphs),'min_y':min(g['ink'][1] for g in glyphs),'max_x':max(g['ink'][2] for g in glyphs),'max_y':max(g['ink'][3] for g in glyphs)},'shadow_inclusive_bounds':{'min_x':overall[0],'min_y':overall[1],'max_x':overall[2],'max_y':overall[3]},'dynamic_shadow_bounds':{'min_x':dynamic[0],'min_y':dynamic[1],'max_x':dynamic[2],'max_y':dynamic[3]},'glyph_count':len(glyphs),'overflow':len(offenders),'overflow_examples':offenders[:3]}
def audit(cues,envelope):
    weights=[]; alphas=[]
    for n in range(N):
        t=n/FPS; weights += [char_weight(t,ch) for c in cues for ch in c['chars']]; alphas.append([cue_alpha(t,i,cues) for i in range(len(cues))])
    maxdw=max(abs(weights[i]-weights[i-len(weights)//N]) for i in range(len(weights)//N,len(weights)))
    transitions=[]
    for i in range(len(cues)-1):
        a,b=cues[i+1]['start']-CROSSFADE,cues[i+1]['start']; overlap=[n for n in range(N) if a<=n/FPS<=b and cue_alpha(n/FPS,i,cues)>.05 and cue_alpha(n/FPS,i+1,cues)>.05]
        if b < 0 or a > DURATION: continue
        transitions.append({'from':cues[i]['text'],'to':cues[i+1]['text'],'start':a,'end':b,'overlap_frames':len(overlap),'pass':len(overlap)>=4})
    raw=[(x['char'],x['raw_end']-x['raw_start']) for c in cues for x in c['chars']]; norm=[(x['char'],max(4,round((x['end']-x['start'])*FPS))) for c in cues for x in c['chars']]
    allw=[]
    for n in range(N): allw += [w for c in cues for w in wave_weights(n/FPS,c)]
    step=len(allw)//N; maxwave=max(abs(allw[i]-allw[i-step]) for i in range(step,len(allw)))
    delta=np.abs(np.diff(envelope)); return {'crossfade_seconds':CROSSFADE,'all_transitions_pass':all(x['pass'] for x in transitions),'transitions':transitions,'max_highlight_delta_per_frame':maxwave,'max_lyric_delta_y':WAVE_LIFT*maxwave+LINE_BREATHE*2*math.sin(math.pi/FPS/10),'max_lyric_delta_scale':WAVE_SCALE*maxwave,'layout':layout_audit(cues),'environment_envelope':{'attack_seconds':.25,'release_seconds':.35,'max_delta':float(delta.max()),'p95_delta':float(np.percentile(delta,95))},'raw_extremes':{'shortest':sorted(raw,key=lambda x:x[1])[:8],'longest':sorted(raw,key=lambda x:x[1],reverse=True)[:8]},'render_only_grid_note':'No timing override applied: source timing preserved; hypothetical min-4-frame durations listed below.','minimum_4_frame_normalized_preview':norm[:20]}
def probe(path): return json.loads(subprocess.check_output([str(FFPROBE),'-v','error','-show_entries','format=duration:stream=codec_type,codec_name,r_frame_rate,nb_frames,width,height','-of','json',str(path)]))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--preview',action='store_true'); args=ap.parse_args(); cues=chars_from_alignment(); envelope=audio_features(); audit_data=audit(cues,envelope)
    if args.preview:
        for t in (4.42,4.62,4.88,7.28,7.5,7.82,16.86,17.14,17.44): frame(round(t*FPS),cues,envelope).save(OUT/f'preview-{t:.2f}.jpg',quality=90)
        print('preview pass'); return
    dest=OUT/'wind-dream-v4-dynamic-smooth.mp4'; cmd=[str(FFMPEG),'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-ss',str(START),'-i',str(AUDIO),'-t',str(DURATION),'-map','0:v','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(N): p.stdin.write(frame(n,cues,envelope).tobytes())
    p.stdin.close(); assert p.wait()==0
    subprocess.run([str(FFMPEG),'-v','error','-i',str(dest),'-f','null','-'],check=True); meta=probe(dest)
    (OUT/'v4-dynamic-smooth-result.json').write_text(json.dumps({'design_brief':{'job':'22-second dynamic lyric motion review','priority':'continuous wind-wave lyric field','secondary':'low-alpha particles, smooth halo, restrained wave'},'parameters':{'fps':FPS,'size':[W,H],'highlight':'raised cosine spatial wind field, #FFF9E7','wave_lift_px':WAVE_LIFT,'wave_scale':WAVE_SCALE,'line_breathe_px':LINE_BREATHE,'crossfade':CROSSFADE,'background_drift_px':[4,3],'particles':PARTICLE_COUNT,'halo_alpha_max':HALO_MAX_ALPHA,'wave_segments':WAVE_SEGMENTS},'inputs':{'alignment':str(ALIGN),'audio':str(AUDIO),'background':str(BG)},'output':{'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'media':meta},'checks':{'decode':'pass','audit':audit_data},'untested':['manual listening review','full-song render']},ensure_ascii=False,indent=2),encoding='utf-8')
    print(dest)
if __name__=='__main__': main()
