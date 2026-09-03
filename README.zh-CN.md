<div align="right">

**中文** · [English](README.md)

</div>

# lyric-mv-kit（歌词排版 MV 工具箱）

> 纯 Python 的「动态歌词排版 MV」渲染引擎。八种视觉风格。一个命令行。
> 不是 Remotion，也不是浏览器引擎——只有 Pillow、numpy 和 ffmpeg。

「动态歌词排版 MV」说的就是那种：歌词的字以精心设计的排版风格停在画面上、
由音乐本身驱动运动的视频。这个工具箱就是用来量产这类视频的。

---

## 为什么是纯 Python？

本工具箱提供的是一个 Python 逐帧渲染器，而不是 React/Remotion 流水线。简而言之：

- **确定性强** —— 同样的 `plan.json` + 同样的音频特征 → 逐像素一致的结果
- **零浏览器依赖** —— 只需 Pillow、numpy、ffmpeg，不下载 Chromium
- **已经跑通上线** —— 这个引擎就是参考视频（极光歌词 MV）的底层；Remotion 移植是
  可选的下一步（见 [`docs/PORTING-TO-REMOTION.md`](docs/PORTING-TO-REMOTION.md)），但**不是默认**

如果你来这里是为了 `npx remotion studio`，那在别处；如果你来这里是为了
「不写 JavaScript 也能做歌词 MV」，欢迎。

---

## 八种风格

八张静帧都来自同一份 `plan.json` 和 `audio_features.npz`，只有视觉处理不同。

| Key | 观感 | 标志动效 |
|------|------|------------------|
| `A_editorial_air` | 浅纸白底 | 逐字揭示，编辑感 |
| `B_album_sleeve` | 暖灰卡片 | 流动胶片颗粒 |
| `C_cinematic_letterbox` | 黑底信箱 | 黑边频谱爆发 |
| `D_kinetic_poster` | 暗→橙 | 节拍缩放 + RGB 错位 |
| `E_neon_bloom` | 暗紫 | 霓虹呼吸绽放 |
| `F_aurora_ribbon` | 冷调 | 极光飘带流动 |
| `G_terminal_glitch` | 黑/绿 | 周期故障 + RGB 分离 |
| `H_prism_kaleidoscope` | 黑底 | 旋转万花筒 |

所有静帧与完整对照表见 [`showcase/`](showcase/)。

```text
$ python -m lyric_mv styles
A_editorial_air            编辑留白 · 浅纸底
B_album_sleeve             唱片内页 · 暖灰卡
C_cinematic_letterbox      电影黑边 · 字幕位
D_kinetic_poster           动力海报 · 冲击
E_neon_bloom               霓虹绽放 · 赛博
F_aurora_ribbon            极光飘带 · 梦幻
G_terminal_glitch          终端故障 · 科技
H_prism_kaleidoscope       棱镜万花筒 · 最炫
```

---

## 快速上手

```bash
# 1. 安装（Pillow + numpy；想要 config.yaml 时再加 PyYAML）
pip install -U pillow numpy pyyaml

# 2. 可选：拉取开源字体（约 25 MB；SIL OFL 许可）
python scripts/fetch_fonts.py

# 3. 自检环境是否就绪
python -m lyric_mv check

# 4. 分析一首歌 + 渲染完整 MP4
python -m lyric_mv build-plan   --audio song.wav --lyrics lyrics.txt \
                               --song presets/song.example.json --outdir work
python -m lyric_mv render       --plan work/plan.json \
                               --features work/audio_features.npz \
                               --style F_aurora_ribbon --out out/song.mp4

# 5. 生成封面 PNG（B站用 4:3 / 1146x860，YouTube 用 16:9 / 1280x720）
python -m lyric_mv cover --title "歌名" --subtitle "艺人 · 极光歌词MV" \
                         --out out/cover.png
```

这就是完整的快乐路径。完整命令行：

```text
$ python -m lyric_mv --help
usage: lyric-mv [-h] {check,styles,build-plan,render,preview,demo,cover} ...

positional arguments:
  {check,styles,build-plan,render,preview,demo,cover}
    check               验证 ffmpeg + 字体
    styles              列出可用风格
    build-plan          音频 + 歌词 -> plan.json
    render              plan.json -> 整歌 mp4
    preview             在指定时间点渲染静帧
    demo                每种风格一段带声音的短片
    cover               4:3 / 16:9 / 16:10 封面
```

---

## 工作原理

```
   ┌────────────────┐    ┌──────────────────┐    ┌────────────────┐
   │ audio_features │    │    plan.json     │    │  song.json     │
   │   .npz         │    │ (段落 + 字幕对点 │    │ (标题/艺人/   │
   │ (rms/bass/     │    │  + 元信息)        │    │  段落/         │
   │  treble/bands) │    │                  │    │  歌词时间点)   │
   └───────▲────────┘    └─────────▲────────┘    └────────▲───────┘
           │                       │                       │
           │      lyric_mv/audio.py + plan.py              │
           │                       │                       │
           └────────────►  Renderer.frame(i)  ◄─────────────┘
                                 │
                                 │  rawvideo 管道
                                 ▼
                          ffmpeg (libx264 + aac)
                                 │
                                 ▼
                              song.mp4
```

图里每一块都是 `lyric_mv/` 下的单文件 Python 模块：

| 文件 | 行数 | 作用 |
|------|-------|--------------|
| `audio.py` | 130 | ffmpeg 解码 → 对数 96 段频谱 → BPM |
| `plan.py` | 130 | 清洗歌词 → 生成 `plan.json`；自动或手动对齐时间点 |
| `align.py` | 100 | 可选 Whisper + stable-ts；产出 `cue_times` |
| `separate.py` | 40 | 可选 Demucs 人声分离 |
| `renderer.py` | 670 | 基类 `Renderer`（背景 / 频谱 / 粒子 / 歌词 / HUD） |
| `styles_ad.py` | 400 | A–D 风格子类 |
| `styles_eh.py` | 500 | E–H 风格子类 + demo 短片渲染 |
| `cover.py` | 220 | 歌词 MV 封面生成器（4:3 / 16:10 / 16:9） |
| `cli.py` | 200 | 统一命令行入口 |

---

## plan.json 契约

`plan.json` 是唯一事实来源——完整 schema 见
[`schemas/plan.schema.md`](schemas/plan.schema.md)。关于这首歌的任何信息都不存在
别处，这正让风格可以互换，也（将来）让 Remotion 移植成为可能。

---

## 参考歌曲 & 在哪看

本工具箱最初就是为了给 ROYAZON / 音右 的歌曲《我拒绝被定义》做极光歌词 MV 而写。
在各平台观看：

| 渠道 | 链接 | 说明 |
|------|------|------|
| 🇨🇳 **B站（中文）** | *待上传，链接随后补* | 中文观众主阵地 |
| 🌐 **YouTube（英文）** | *待上传，链接随后补*——见 [English README](README.md) | 英文观众；同一视频，英文标题/文案 |
| 🎧 **网易云音乐** | <https://music.163.com/#/song?id=3422948585> | 歌曲本体 |
| 🏠 **品牌官网** | <https://music.zondev.top> | 完整曲库 + 歌词视频展示 |

> 参考视频**不**在本仓库内分发。 [`showcase/`](showcase/) 里的静帧是用与上线视频
> 相同的设计令牌重绘的。视频上线后，把公开链接填进上表以及
> [English README](README.md)——这样 GitHub ↔ B站 ↔ YouTube ↔ music.zondev.top
> 的资源闭环就闭合了。

---

## 许可证

MIT——见 [`LICENSE`](LICENSE)。字体归属见 [`NOTICE`](NOTICE)。所有内置字体均为
SIL 开放字体许可 1.1（通过 `scripts/fetch_fonts.py` 获取）；不内置或分发任何专有
系统字体。

---

## 延伸阅读

- [`docs/FONTS.md`](docs/FONTS.md) —— 三套字体族如何解析
- [`docs/PORTING-TO-REMOTION.md`](docs/PORTING-TO-REMOTION.md) —— 为什么是 Python、Remotion 移植长什么样
- [`docs/FAQ.md`](docs/FAQ.md) —— 常见问题

```text
$ python -m lyric_mv check
ffmpeg      : /usr/bin/ffmpeg
font heavy  : /usr/share/fonts/truetype/noto/NotoSerifSC-Bold.ttf
font sans   : /usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf
font latin  : /usr/share/fonts/truetype/noto/NotoSansSC-Bold.ttf
brand       : ROYAZON

OK
```
