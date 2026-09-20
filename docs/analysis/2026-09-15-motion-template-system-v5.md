# Lyric MV Motion Template System v5

日期：2026-09-15

状态：任务分支候选，尚未合入 `main`。

关联：

- Issue #1：`https://github.com/EOMZON/lyric-mv-kit/issues/1`
- 旧专项分支：`codex/wind-dream-motion-escalation`
- 旧审阅包提交：`bbaad16`
- 本轮干净任务分支：`codex/motion-template-system-v5`
- Git 治理依据：`https://github.com/EOMZON/codex-skills-private/blob/9a8e385ccc98f068b0990133f9a2e80681ffa9ec/github-ops/references/test-main-governance.md`

## 1. 本轮决策

Issue #1 的核心不再定义为“把 v4 的参数调大”，而是：

> 为 `lyric-mv-kit` 建立可复用的 **Motion Template + Song Motion Score** 能力，并用《风穿过指尖的梦》作为第一支结构化验证样本。

现有仓库已经有 8 套 Visual Style，它们主要负责画面材质、色彩、字体气质和局部动效；本轮不再让 visual style 同时承担歌曲宏观编舞职责。

新的组合模型：

```text
plan.json
  ├─ song timing / cues / sections
  ├─ audio_features.npz
  │
  ├─ Visual Style
  │    └─ 颜色、字体、背景材质、局部歌词表现、visualizer
  │
  ├─ Motion Template
  │    └─ 可复用镜头/视差/节拍运动语法
  │
  └─ Song Motion Score（可选）
       └─ 仅覆盖歌曲真正需要特殊编舞的段落

                ↓
             Renderer
```

目标不是每首歌都写一份复杂 score。正确策略是：

- 70–80% 的歌直接使用固定 Motion Template；
- 20–30% 有明显叙事/副歌峰值的歌，再补少量 Song Motion Score；
- Visual Style 与 Motion Template 正交，可以独立替换。

## 2. 为什么 v4 “技术上在动，主观上仍然静”

### 2.1 v2 → v3 → v4 已经完成了一次很有效的诊断

- v2：14px 字符上浮、6% 缩放、频谱、音符、粒子、光晕，动态很多，但卡顿且各层节奏互相竞争。
- v3：取消空间运动，只保留连续高亮和交叉淡化，平滑，但用户直接反馈“动态怎么没有”。
- v4：恢复 5px 字符风场、2% scale、背景漂移、粒子、波形、RMS 光晕，连续性审计 PASS，但用户仍然反馈“不够动态”。

所以问题不是“有没有动效”，而是：

> 局部元素在运动，但整个画面的构图、运动方向和音乐段落没有发生可读的推进。

### 2.2 v4 的构图中心基本不变

歌词始终固定在同一个主要区域；标题、光晕、底部波形等也没有形成大的视觉中心迁移。

因此观看者先建立的是“固定海报”，然后才发现海报里有轻微运动。

### 2.3 背景漂移是防静帧级别，不是镜头级别

v4 背景位移只有个位数像素，周期约 20 秒，并且最终使用整数 crop 坐标。这对避免绝对静帧有效，但不足以产生可被第一眼识别的镜头推进感。

### 2.4 环境层被刻意压成第二层

粒子、wave、halo 都采用低透明度并避开歌词区域。这保证可读性，但也意味着除了歌词以外，其他运动很容易被视觉系统忽略。

### 2.5 音乐目前只在调参数，没有“导演画面”

v4 的 RMS/attack/release 很适合作为连续性控制，但它主要调制光晕、wave 等局部变量，没有决定：

- 什么时候镜头开始蓄力；
- 什么时候推进构图；
- 哪一句成为运动峰值；
- 哪一句需要释放；
- 运动应该向哪个统一方向发展。

因此下一步需要 motion choreography，而不是更多常驻 effect。

## 3. 产品化判断：歌词 MV 应该有固定模板，而不是每首完全创新

成熟歌词/音乐视频工具普遍采用“模板 + 动画文本 + 品牌/素材替换”的模型。模板是正确抽象，不是妥协。

本仓库下一阶段不应该扩展成“几十个互相重叠的 visual style”，而应该把模板拆成两个维度：

1. **Visual Style**：画面气质。
2. **Motion Template**：歌词和镜头怎样运动。

### 3.1 第一批固定 Motion Template

#### T1 — `steady-karaoke`

用途：绝大多数标准歌词视频、需要完整跟唱、低风险交付。

核心：

- 画面基本稳定；
- 局部 karaoke fill / 当前歌词强调；
- 极轻微呼吸和背景漂移；
- 不要求 Song Motion Score。

推荐视觉：`C_cinematic_letterbox` 或克制的 editorial style。

这是“可靠默认模板”。

#### T2 — `cinematic-float`

用途：已有高质量封面、摄影、AI 插画、风景或 narrative footage。

核心：

- 文字不抢背景；
- 10–25 秒的缓慢 push / pan；
- foreground 和 background 有轻微视差；
- 句间连续，不做逐字弹跳。

这是“高级、稳妥、最不容易过时”的模板。

#### T3 — `type-camera`

用途：歌词是第一视觉层，希望明显动态、但又不能变成逐字弹跳。

核心：

- 把歌词区域当成一个场景；
- 通过 camera pan / zoom / cue sway 构成连续推进；
- 微观高亮仍由 visual style 负责；
- 宏观 motion 由 Motion Template / Song Score 负责。

这是《风穿过指尖的梦》v5 推荐模板。

#### T4 — `ambient-story`

用途：抒情、梦幻、风、雨、纸张、天空、海面、自然环境等主题。

核心：

- 背景低倍率视差；
- 歌词层高倍率视差；
- 全曲只有一条统一运动方向；
- 风/尘/光等环境元素服从同一个方向，而不是随机组件各自动。

适合《风穿过指尖的梦》的视觉主题，但不建议单独成为控制系统；最好作为 `type-camera` 的视觉语义层。

#### T5 — `beat-push`

用途：说唱、电子、摇滚、强副歌、节奏清晰的歌曲。

核心：

- beat/bass 驱动 scale / push；
- cue 边界可以做冲击；
- 整体节奏快；
- 必须设置严格的单帧变化硬门。

不适合《风穿过指尖的梦》作为主模板。

### 3.2 暂时不作为 P0 的模板

以下方向未来有价值，但不应阻塞 v5：

- 多行歌词 stack / 上下滚动式歌词；
- 双语歌词；
- 逐词 bounding-box karaoke；
- 复杂路径 typography；
- WebGL 流体水彩；
- 3D camera / true depth plane。

这些属于第二阶段 renderer 能力，不应和当前问题一次性耦合。

## 4. 架构：数据 / 视觉 / 运动解耦

### 4.1 `plan.json`

保持现有定位不变：

- 音频位置；
- duration / fps / frame count；
- section；
- lyric cues；
- song metadata。

不要把歌曲编舞硬编码回 `plan.py`。

### 4.2 `Motion Template`

固定模板是可复用配置，第一版只定义：

- camera pan；
- progress drift；
- cue sway；
- zoom；
- foreground/background parallax；
- 少量 audio reactivity。

模板不应该包含某一首歌曲的绝对时间点。

### 4.3 `Song Motion Score`

歌曲 score 是可选覆盖层。

第一版 schema：

```json
{
  "version": 1,
  "id": "song-name-v5-motion-score",
  "template": "type-camera",
  "segments": [
    {
      "start": 4.34,
      "end": 7.40,
      "easing": "ease_in_out",
      "from": {"x": 24, "y": -6, "scale": 1.045},
      "to": {"x": 78, "y": -14, "scale": 1.052}
    }
  ]
}
```

只在确实有故事性/高潮的地方覆盖模板。

### 4.4 `MotionRenderer`

采用 adapter，而不是重写 8 套 visual style。

单帧结构：

```text
base visual style
  ├─ background layer
  ├─ foreground layer
  │    ├─ spectrum
  │    ├─ particles
  │    └─ lyric
  └─ HUD

MotionRenderer
  ├─ background：低倍率 camera/parallax
  ├─ foreground：高倍率 camera/parallax
  ├─ composite
  └─ HUD：最后绘制，保持稳定
```

这个结构直接解决 v4 的问题：运动第一次成为构图级事件，同时 HUD/可读性不会跟着晃。

## 5. 《风穿过指尖的梦》v5 推荐方案

推荐组合：

```text
Visual direction: 水彩纸感 / LongCang 金字 / 当前唱字白色
Motion Template: type-camera
Song Motion Score: wind-dream-v5
Motion metaphor: 一股连续向右上推进的风
```

不要恢复：

- 常驻跳动音符；
- 64 段频谱墙；
- 随机大量粒子；
- 每个字独立 10px+ 跳跃；
- 每句重新开始一套动画。

### 5.1 22 秒 storyboard

#### 0.00–1.04s — `朝我飞来`

承接前文，镜头从轻微左下开始向右上进入；不重置。

#### 1.04–4.34s — `当两束纸飞机在天空重叠`

两股视觉方向汇合。宏观镜头开始 push，歌词从稳定区进入更靠近画面中心的位置。

#### 4.34–7.40s — `跑道瞬间被云写成五线谱`

第一次明显构图变化。横向推进幅度增大；如果继续保留风迹/五线谱元素，它们必须服从同一方向。

#### 7.40–10.08s — `你的笑像音符跳跃着`

不放独立 ♪ 图标。通过整体轨迹上扬、歌词 baseline 或前景移动表达“音符跳跃”。

#### 10.08–13.20s — `我的心被旋律牵动着`

上一段的轨迹继续，不重置。缓慢提高 zoom 和上移趋势。

#### 13.20–16.98s — `奔向重逢那刻`

22 秒最大能量峰值。foreground 与 background 同向推进但有不同视差倍率，形成明显“奔向”的运动感。

#### 16.98–19.90s — `我数着纸飞机的影子练马拉松配速`

长句不逐字跳。镜头从峰值释放并进行横向 tracking，重点是持续前进。

#### 19.90–22.00s — `每一步都是向你靠近的乐谱`

能量收束。停止加速但不完全停，保留运动惯性，为后续全曲继续留方向。

## 6. 为什么这版比单纯“Ambient Story”更好

如果只做水彩/纸飞机/风，容易再次陷入“很多环境元素在动但歌词和构图没有推进”。

所以推荐关系是：

```text
控制系统：type-camera / motion score
视觉语义：wind / paper plane / watercolor
```

而不是：

```text
随机粒子 + 纸飞机 + 音符 + wave + glow
```

视觉主题必须服从统一运动语法。

## 7. 技术路线

### 7.1 当前阶段继续 Python / Pillow / ffmpeg

v5 的核心问题是 motion choreography，不是 shader 上限。

Pillow 足以完成：

- pan / zoom；
- 2.5D parallax；
- 简单 rotation；
- image transform；
- 可控 trail；
- 2x supersampling（后续）；
- 确定性批量渲染。

因此不把 Remotion 迁移作为 v5 前置条件。

### 7.2 Remotion 的合理触发条件

当以下情况出现，再启动现有 `PORTING-TO-REMOTION.md` 路线：

- 需要浏览器实时预览和人工拖拽；
- Motion Template 数量增长，设计调参速度成为主要瓶颈；
- 需要把歌词模板做成网页产品；
- 需要 React 组件直接参与视频生成。

数据层应保持 engine-neutral，因此 `plan.json + motion template + motion score` 不应依赖 Pillow。

## 8. 安全硬门

任何模板都必须保留 Issue #1 已验证出的硬门：

1. 歌词完整可读；
2. 不允许字符瞬间消失；
3. 句间有连续过渡；
4. 不允许动态边界裁切；
5. 运动必须连续；
6. 宏观动态不能靠提高单字符跳跃幅度获得；
7. 22 秒人工主观通过后，才允许渲染 69.3 秒全曲。

新增 motion 层后还要补：

8. background/foreground transform 不得暴露画布边缘；
9. camera segment 边界必须位置/scale 连续；
10. HUD 不跟随 macro camera；
11. song score 可以缺省，固定 template 必须独立可用。

## 9. Git 治理

### 9.1 旧专项分支不直接整体合 main

`codex/wind-dream-motion-escalation` 相对 main 混入了早期 `mv03/incision` 提交，不适合作为新能力的最终合并基线。

本轮从 `main@7dbdfc3` 创建干净任务分支：

```text
codex/motion-template-system-v5
```

本轮只在该任务分支开发、验证、保存；没有把候选冒充为 `main` 已完成。

### 9.2 main 是唯一稳定基线

遵循 `test-main-governance.md`：

- main 不作日常试错；
- 候选先在 task/test 分支；
- 未完成本机渲染验收之前，不进入 main；
- 不 force-push；
- 不 reset/clean 其他 AI 的工作；
- 不因为文档/备份提交触发不必要的生产发布。

## 10. 本轮完成定义

### 云端可以直接完成

- 保存分析与架构；
- 增加 Motion Template 数据模型；
- 增加 Motion Controller；
- 增加 MotionRenderer adapter；
- 增加第一批固定模板；
- 增加《风穿过指尖的梦》v5 concrete score；
- 增加命令行渲染桥接脚本；
- 静态/语法级验证；
- 建立 PR 供后续本机验证。

### 需要本机完成

原因不是代码逻辑，而是当前云端环境没有该 run 的 `forced_alignment.json`、歌词源、Windows 字体/ffmpeg 运行环境和完整本机素材。

本机需要：

1. 同步任务分支；
2. 使用现有 wind-dream 本地 run 数据生成/复用 plan + features；
3. 渲染 v5 22 秒；
4. 输出 MP4 + 关键窗口 contact sheet；
5. 主观人工听感/视觉验收；
6. 通过后再决定是否进入 test/main；
7. 仍不渲染全曲，除非 22 秒得到用户确认。

## 11. 后续模板演进顺序

P0：先把 5 个 template 做成稳定的 `camera/parallax` presets。

P1：引入 line-stack / current-prev-next 等布局模板。

P1：把 visual style 和 motion template 组合成公开 preset pack，例如：

- `classic-karaoke`
- `cinematic-lyrics`
- `dreamy-watercolor`
- `kinetic-type`
- `beat-poster`

P2：如设计调参频繁，再使用 Remotion Studio 做实时 authoring；仍复用同一 motion score。

---

一句话给后续 AI：

> 不要继续在 v4 上堆粒子或把 5px 改成 10px；先保持歌词微观动效稳定，用 Motion Template + Song Motion Score 制造构图级、段落级、统一方向的运动。