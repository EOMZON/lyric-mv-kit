# 交接文档：wind-dream 歌词 MV（v20260910-01）—— 当前状态

> 最近一次更新：**2026-09-11 18:01**
> 分支：`codex/mv03-v4-intro` ｜ HEAD：`811c7a4`
> 副产物（推荐先读）：`HANDOFF-truncation.md`（截断专项）、`check_no_blank_chars.py`（回归闸门）、`.workbuddy/memory/MEMORY.md`（项目长期约定）

---

## 1. 背景与目标

`lyric-mv-kit` 是一个本地 Python 工具，把一段带时间对齐的歌词渲染成歌词 MV 视频。
每个 `runs/<song>/lyric-paper-staff-v1/v<date>/` 是**一个 run**，内部分 4 段：

| 子目录 | 作用 |
|---|---|
| `00_source/` | 原歌词文本 + 原始音频 |
| `03_alignment/` | whisper 强制对齐结果（`forced_alignment.json`） |
| `03_render/` | 渲染脚本、产物视频、cue 事件、审计报告 |
| `run-config.json` | run 元数据（template.id / 对齐方式 / 是否人工听校） |

**wind-dream 这一跑**的设定：歌曲《风穿过指尖的梦》（音右），水彩底 + LongCang 金字 + aurora 文字动态。日期 `2026-09-10`，版本 `v01`。原计划是把它做成 5 套模板里的一个参考渲染。

**用户预期**（三轮迭代下来收敛成的）：
- 歌词行**始终完整可见**，当前唱到的字 = 白色高亮 + 浮升 + 微放大。
- 暗色水彩底上金字清晰可读。
- 「歌曲有律动感」——不能是死板的静态图文。
- 全曲（69.3s）能稳定复现。

---

## 2. 这一轮做了什么

按时间顺序，五件事：

### 2.1 修了「文字被截断/缺字」（5 轮才到位）

前 4 轮都打错了方向（几何 → 对比度 → 淡出逻辑），最后用「每帧渲染两次做像素差分」的审计才定位到**两个独立、非几何的元凶**：

| 元凶 | 现象 | 修复 |
|---|---|---|
| 逐字 alpha 断崖 | 每个字在开口瞬间 `alpha: 1.0 → 0.0` + 下坠 32px 升回 | `alpha = fade_out`（只受整行淡出影响）；`highlight_weight()` 梯形权重驱动浮升/放大/着色 |
| `char_glyph()` 裁剪错位 | `d.text((-bb[0],-bb[1]),...)` 重画后墨迹在 (0,0)，却用 `canvas.crop(bb)` 裁 → `bb[1]!=0` 的字全空白（命中「一」） | 改用 `canvas.crop((0, 0, bb[2]-bb[0], bb[3]-bb[1]))` |

完整事故复盘见 `HANDOFF-truncation.md`、方法论见 skill **`renderer-blank-text-triage`**。

### 2.2 去掉黑色描边、调高亮色为纯白

描边当初是掩盖 alpha 断崖的权宜之计（`STROKE_WIDTH=2`，8 邻域偏移）。真因修掉后它就**纯是装饰负担**，用户要求去掉。

去掉后发现原本靠描边撑住的暖白高亮色 `(255,253,238)` 在蓝底上发虚，做了 5 色并列实测（`_probe/accent-options.jpg`），最终选**纯白 `(255,255,255)`**。备选 amber `(255,205,70)` 留档。

### 2.3 加了自动审计闸门 `check_no_blank_chars.py`

每帧渲染「有歌词 / 无歌词」两张做像素差分，对每个字用 `char_box()` 的**实际绘制矩形**统计被贡献像素占比，`< 2%` 判 FAIL 并返回退出码 1。

可以这样理解：**它不靠肉眼判断「这字是不是缺的」**——而是直接量字符矩形里到底有没有非零像素贡献。两个窗口实测均 PASS，阈值 2% 离健康覆盖率 21%+ 约 10 倍余量，**不容易放过坏渲染**。

### 2.4 加了 5 层环境律动（应用户「页面动态太少」反馈）

原版只有「字级浮升 + 极轻 BOB 呼吸」，背景和版面是死水。新增 5 层（全部在歌词框外/后，不抢主视觉）：

| 层 | 开关 | 说明 |
|---|---|---|
| 背景微漂移 | `BG_DRIFT` | 水彩底 ±11px 缓慢正弦游移 |
| 节拍呼吸光晕 | `GLOW` | 歌词框后暖色径向光晕，随 pulse/bass 缩放 + 增亮 |
| 底部频谱条 | `SPECTRUM` | 全宽 64 段 log-spaced 频谱，金色半透明，y=682~716 |
| 跳动音符 | `NOTES` | 按 librosa 节拍在留白区升腾的矢量八分音符（3 spawn zone，确定性 RNG） |
| 浮尘微粒 | `PARTICLES` | 26 粒随 treble 闪烁的尘埃，限制在留白区 |

**音频特征全部复用 `audio_features()` 缓存**（bands/bass/treble/pulse/beats）—— 不用重新分析音频。

### 2.5 提交推送 + skill 沉淀

- `lyric-mv-kit` 提交 2 次：
  - `dfd632c` —— 截断/缺字修复（脚本 + 审计闸门 + 审计报告 + 交接文档）
  - `811c7a4` —— 环境律动层（频谱/音符/光晕/漂移/微粒）
- `codex-skills-private` 提交 1 次：`1fed9f5` —— 新建 skill `renderer-blank-text-triage`，已同步三处副本
- 项目级约定 `.workbuddy/memory/MEMORY.md` 新建：渲染器硬性规则、报障排查顺序、审计闸门用法、环境易错点、风格约定

---

## 3. 当前产物（本地路径）

| 文件 | 说明 |
|---|---|
| `runs/wind-dream/.../03_render/wind-dream-combined-v2.mp4` | 22.0s 片段，1280×720@24，主交付 |
| `runs/wind-dream/.../03_render/wind-dream-combined-v2-full.mp4` | 69.33s 全曲 |
| `runs/wind-dream/.../03_render/blank-char-audit-excerpt.json` | 22s 审计报告，min 22.53%，PASS |
| `runs/wind-dream/.../03_render/blank-char-audit-full.json` | 全曲审计报告，min 21.87%，PASS |
| `runs/wind-dream/.../03_render/HANDOFF-truncation.md` | 截断专项交接（含真因、修复、审计、设计规则） |
| `runs/wind-dream/.../03_render/_probe/` | 诊断用证据：before/after 对比、高亮色 5 选 1、节拍证据图、旧版留档 |
| `.workbuddy/memory/MEMORY.md` | 项目长期约定（硬性规则 + 报障顺序 + 风格） |
| `.workbuddy/memory/2026-09-11.md` | 今日工作日志 |

> ⚠️ **`*.mp4` 和 `*.npz` 在 `runs/` 下被 `.gitignore` 故意忽略**——视频成品与音频特征缓存留在本地，不进 git。要在远程仓库直接看视频，得本地 push 之前用 `git add -f` 强制加。

---

## 4. 怎么复现

```bash
# 基础：仓库根 base python 没 numpy，必须用 miniforge3
PY="D:/ZON/runtime/miniforge3/python.exe"
FF="D:/ZON/runtime/media-tools/Library/bin/ffmpeg.exe"
DIR="D:/ZON/codex/lyric-mv-kit/runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render"

cd "$DIR"

# 1) 22s 片段（默认窗口）
"$PY" render_wind_dream_combined_v2.py

# 2) 全曲
WD_TAG=-full WD_START=0.4 WD_END=69.7 \
  "$PY" render_wind-dream_combined_v2.py   # 注意文件名（脚本里是 _v2）

# 3) 审计
"$PY" check_no_blank_chars.py

# 4) 单帧抓图（脚本默认 2/6.16/8.16/15/18/20s 出 jpg）
"$PY" render_wind_dream_combined_v2.py
ls v2-*.jpg
```

---

## 5. 还差什么 / 明确留给你定

1. **`run-config.json` 未同步**：`template.id` 仍是 `lyric-aurora-v1`（纯 aurora），未体现「V3 包装 + aurora 动态 + 环境律动」。
   ⚠️ MV00–MV10 是用 `lyric-aurora-v1` 产出的，**直接改 `template.id` 会让历史记录失真**。建议另开一个实验 run 或新增字段（`template.tier` / `motion_layers: [...]`），而不是就地改。
2. **对齐精度**：本机没装 `faster-whisper`，用 `openai-whisper(base)` 兜底，存在多字合并词（最明显：「不会」）。`run-config.json` 里 `manual_listening_verified: false`，即**未人工听校**。精度敏感场景下换 `turbo` 或 `faster-whisper` 重跑对齐。
3. **律动层可调参集中在脚本顶部**：
   - `GLOW` 强度/范围、`SPECTRUM` 颜色/`NB`（默认 64）、`NOTES` 寿命/zone 比例（默认 0.33/0.33/0.33）、`PARTICLES` 数量、整体 alpha 区间
   - 5 层有独立开关（`VIZ` 总开关 / `BG_DRIFT` / `GLOW` / `SPECTRUM` / `NOTES` / `PARTICLES`），可单层关
4. **观感终审**：律动层是**主观节奏**——多强算多、什么时候算抢戏——只能由你确认。`_probe/viz-full-sheet.jpg` 是全曲 15 帧缩略图，可一眼扫过；如果觉得频谱太抢，把 `SPECTRUM = False` 即可。
5. **导出规格未定**：当前 1280×720@24 H.264 AAC 192k faststart。如果要上 B 站 / 抖音 / 公众号，需要不同码率/封装。ffmpeg 命令集中在 `main()`，改一行即可。
6. **未清理的 _probe 留档**：调试中产出的旧视频、对比图、节拍证据图都在 `_probe/`，有约 30+MB。如果发版不要带，可以删；如果想留作回归证据就保留。
7. **同名旧脚本 `render_wind_dream_combined.py`** 还在同目录（不是 `_v2`），是早期版本没删，跟新版本没关系。**别误跑**。

---

## 6. 风格/设计约定（提炼）

- 字体 LongCang，金 `#fff071`，水彩背景，左对齐 box `[65, 450, 790, 225]`
- 当前唱到的字 = 纯白 + 浮升 14px + 放大 6%，**无描边**
- 字高亮走**梯形权重**（前 0.10s 升 / 演唱期保持 / 后 0.10s 落，两端都归 0），相邻字区间重叠 → 平滑滑动
- **alpha 永不**被字自身进度调制（这是修复截断的硬规则）
- 律动层都**避开歌词框**：频谱在底部 y>680，音符在右/上留白，微粒在留白区
- 颜色仅在 `(255, 240, 170)` 暖金 与 `(255, 255, 255)` 暖白之间过渡；不引入新色

---

## 7. 跟上下游的边界

**上游**：对齐由 `03_alignment/forced_alignment.json` 提供（whisper 出）。如果想做精度更好的对齐，应在那一层修，不要改渲染脚本。
**下游**：
- B 站上传 pipeline / 公众号编辑器 / 抖音分发**还没有接入这个 run 的产物**——目前是「渲染出本地视频」为止。
- 如果下游要从 git 拿视频，得加 `git add -f *.mp4`（不推荐，约 7MB 二进制进仓）；或用云盘 / CDN 单独发。

---

## 8. 交接给下一个人/AI 的几句话

1. **「字被截断/缺字」** → 先跑 `check_no_blank_chars.py` 看审计通过/失败，再决定修哪里。**别先猜几何**——见 skill `renderer-blank-text-triage`。
2. **「页面太死」** → 5 层环境律动都集中在 `VIZ`/`BG_DRIFT`/`GLOW`/`SPECTRUM`/`NOTES`/`PARTICLES` 开关上，单层关即可。`render_wind_dream_combined_v2.py` 顶部所有可调参数都集中在一起。
3. **重新渲染前**：先 `rm v2-features.npz`（如果改了 `audio_features()` 的逻辑），否则会拿旧缓存。要新分析音频的话直接删 npz 再跑即可。
4. **任何对脚本的改动**：先在 22s 片段上验证（快，~30 秒），再决定是否上全曲（~4 分钟）。

---

_生成时间：2026-09-11 18:01 ｜ 仓库 HEAD：`811c7a4` ｜ 产物：2 段视频 + 2 份审计报告 + 1 个 skill + 1 份 MEMORY.md_
