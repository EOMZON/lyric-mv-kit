# 《风穿过指尖的梦》歌词 MV：动态感仍不足，请做设计与技术联合分析

## 一句话问题

目前版本已经解决掉帧、逐字跳变、句间硬切和文字裁切，但用户连续反馈：**画面仍然不够动态**。需要重新判断“动态”的设计模型，而不是继续在现有参数上做小幅增减。

## 最初目标

歌曲：《风穿过指尖的梦》／音右。

目标是制作一支水彩纸感的歌词 MV：

- 暗色水彩背景，LongCang 金色歌词，当前唱字以白色强调。
- 歌词始终完整、清晰、可跟唱，不能缺字、截断或突然消失。
- 画面必须有与歌曲相呼应的持续律动，不能像静态海报。
- 文字是第一视觉层，但“强调文字”不能等于机械逐字弹跳。
- 先用 22 秒片段快速验证，再决定是否渲染 69.3 秒全曲。

## 用户反复强调的内容

按反馈顺序：

1. “文字动态效果还是不太好，目前看起来一卡一卡的。”
2. 在为了消除卡顿而大幅收静之后：“可是动态怎么没有，我需要动态啊，不能在保障动态的情况下处理吗？”
3. 恢复连续文字波动、背景漂移、粒子、波形和光晕之后：“还是不够动态。”

这说明真正的验收标准不是单纯的“平滑”或“有几个动效层”，而是：

> **第一眼就能感到画面在随音乐生长和推进，同时运动连续、有方向、有层级，不像组件各自动，也不能只剩轻微到难以察觉的呼吸。**

## 已实现与已验证

### 基础修复

- 修复逐字 alpha 断崖导致的字符消失。
- 修复 `char_glyph()` 裁剪错位导致的空白字形。
- 新增逐帧像素差分审计 `check_no_blank_chars.py`。
- 移除黑色描边，保留金字与白色唱字强调。

相关提交：

- `dfd632c` — 修复歌词截断／缺字并加入审计。
- `811c7a4` — 加入背景漂移、光晕、频谱、音符和粒子。

### v2：动态多，但卡顿

入口：

- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/wind-dream-combined-v2.mp4`
- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/render_wind_dream_combined_v2.py`

特征：逐字上浮 14px、放大 6%、0.10 秒线性梯形高亮；背景漂移、64 段频谱、节拍光晕、音符和 26 个粒子同时运行。

已定位的卡顿根因：

- 24fps 下 0.10 秒只有约 2.4 帧；部分字时长甚至只有 0.04 秒，单帧可跳约 9.6px。
- 句切换曾由单个 `active = next(...)` 排他绘制，旧句接近透明后，下一帧新句直接满亮。
- beat pulse 没有 attack，单帧从 0 到峰值，同时驱动大光晕、频谱和音符。
- 多套不同节奏彼此竞争，没有统一的运动方向。

### v3：流畅，但过静

提交：

- `5da6cf3` — 新增 “paper-wind” 连续唱字光。
- `5b14c90` — 修复双行歌词底缘裁切。

入口：

- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v3-smooth/wind-dream-v3-smooth.mp4`
- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v3-smooth/render_v3_smooth.py`

改动：取消逐字位移和缩放，只让 `#FFF9E7` 高亮连续掠过；句间做 0.24 秒双层交叉淡化；关闭频谱、音符、粒子。

结果：技术上平滑，但用户认为“动态怎么没有”。这是一次有效的诊断 A/B，不是合格终稿。

### v4：恢复动态，但体感仍不够

提交：

- `fe25134` — 新增 dynamic-smooth 候选。

入口：

- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v4-dynamic-smooth/wind-dream-v4-dynamic-smooth.mp4`
- `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v4-dynamic-smooth/render_v4_dynamic_smooth.py`

已加入：

- 连续空间“风场”推动当前字和相邻字：最大上浮 5px、最大缩放 2%。
- 整行 1.2px 呼吸。
- 背景 ±4px／±3px，周期 21s／19s。
- 15 个低透明度漂浮粒子。
- 20 段低透明度底部波形。
- RMS 光晕，attack 0.25s、release 0.35s。
- 不恢复跳动音符。

自动与独立审核均通过：

- 1280×720、24fps、528 帧、22.000s、H.264 + AAC，完整解码通过。
- 七次句切换均有 4–5 帧重叠。
- `max Δweight = 0.14169`。
- 实际 `max Δy = 1.218px/frame`。
- `max Δscale = 0.002834/frame`。
- 环境 envelope `max Δ = 0.14926`，P95 `0.05174`。
- 动态字形与阴影均在安全区内，overflow = 0。

结果：没有明显卡顿、没有裁切，环境层也存在，但用户依旧认为“不够动态”。

## 当前关键判断

问题已经不是性能或帧率问题。三个视频都是固定 24fps，v3/v4 逐帧连续性指标正常。

更可能的设计问题包括：

- 运动幅度虽然存在，但缺少大尺度、可读的构图变化。
- 所有环境运动都被刻意压成第二层，导致正常播放时近似不可感知。
- 文字波峰主要是局部字形变化，没有形成一句歌词或整幅画面的推进感。
- 音乐驱动只调制局部参数，没有形成段落级的蓄力、释放和高潮。
- “粒子 + 波形 + 光晕”仍像几个附加组件，而不是同一个视觉事件。
- 22 秒片段可能需要明确的 motion choreography，而不是全程同一强度的循环。

## 请云端 AI 重点分析

请先看三个 22 秒视频，再读对应脚本和 JSON 证据。不要只根据参数大小判断。

希望得到：

1. 为什么 v4 已经包含多层运动，用户主观上仍会认为“不够动态”？请从构图、节奏、运动尺度、音乐结构和注意力层级分析。
2. 给出 **3 个结构性不同** 的动态方向，不要只是把 `5px` 改成 `10px`：
   - 至少一个以歌词排版／镜头为主；
   - 至少一个以水彩／纸飞机／风为主；
   - 至少一个以音乐段落编舞为主。
3. 每个方向说明：核心视觉事件、时间节奏、运动范围、哪些元素删除、风险与验证方法。
4. 推荐其中一个作为下一版，并给出 22 秒片段的逐段 motion storyboard（按秒或歌词句分段）。
5. 给出可落到现有 Python/Pillow/ffmpeg 渲染器的实现方案；如现有技术栈限制了效果，也请明确建议是否转向 After Effects、Remotion、WebGL 或其他方案，以及迁移成本。
6. 保留现有硬门：歌词完整可读、无单帧突变、句间连续、动态边界不裁切。

## 审阅素材与关键时间窗

本分支强制纳入了三个 22 秒 MP4 和精简 contact sheets，便于远端直接比较。视频原本被 `.gitignore` 排除，此次仅为问题分析加入审阅片段，不包含 69.3 秒全曲。

重点看：

- `4.42–4.88s`：第一处典型句切换。
- `7.28–7.82s`：文字运动与环境层最容易叠加的窗口。
- `16.86–17.44s`：短句转长句，最能观察构图推进与换行。

精简证据：

- `v3-smooth/contact-review-3windows.jpg`
- `v4-dynamic-smooth/contact-environment-2s.jpg`
- `v4-dynamic-smooth/contact-4.42-8frames.jpg`
- `v4-dynamic-smooth/contact-7.28-8frames.jpg`
- `v4-dynamic-smooth/contact-16.86-8frames.jpg`

## 范围与未完成项

- v3/v4 尚未做人工听感与逐字音画同步终审。
- v3/v4 尚未渲染 69.3 秒全曲；应在动态方向确认后再做。
- `run-config.json` 仍保留历史模板标识，避免就地改写旧 run 的事实记录。
- 本地工作区另有既存未提交内容；本次分支只提交与这次云端分析直接相关的脚本、结果、视频、精简证据和本文档。

## 分支与提交

请基于分支 `codex/wind-dream-motion-escalation` 分析。

最新相关提交链：

```text
dfd632c  fix(wind-dream): resolve lyrics truncation
811c7a4  feat(wind-dream): add ambient motion layers
5da6cf3  feat(wind-dream): add smooth paper-wind candidate
5b14c90  fix(wind-dream): keep smooth lyrics within safe frame
fe25134  feat(wind-dream): add dynamic smooth lyric candidate
```

