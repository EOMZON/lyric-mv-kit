# 交接文档：风穿过指尖的梦（wind-dream）V3 包装 + aurora 文字动态 ——「截断」问题【已解决】

> 状态：**2026-09-11 RESOLVED**。上一版交接把根因判断为「卡拉OK 揭示隐藏未唱字」，这个判断**不完整**。本轮通过逐帧像素审计定位到**两个独立缺陷**，均已修复并通过自动审计。
> 同日追加：按要求**去掉黑色描边**（描边当初只是掩盖 alpha 断崖的权宜之计），并把高亮色改为纯白。见 §3 第 7–8 条。
> 上一版结论中「几何无裁切」的实测是对的，但「整句常驻显示」的补丁引入了新缺陷，见下。

---

## 1. 背景（未变）

- 仓库：`D:\ZON\codex\lyric-mv-kit`，歌词 MV 生成工具包。
- 本曲：《风穿过指尖的梦》/ 演唱 音右（代号 `wind-dream`）。
- 目标：把 **V3 包装**（水彩背景 + LongCang 金色字）与 **aurora 的逐字动态**合二为一。
- 实验目录：`runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/`

### 关键文件（绝对路径）
| 用途 | 路径 |
|---|---|
| 主渲染脚本（本轮已修复） | `.../03_render/render_wind_dream_combined_v2.py` |
| **新增：自动审计闸门** | `.../03_render/check_no_blank_chars.py` |
| 审计报告（22s 片段） | `.../03_render/blank-char-audit-excerpt.json` |
| 审计报告（全曲） | `.../03_render/blank-char-audit-full.json` |
| 强制对齐 | `.../03_alignment/forced_alignment.json` |
| 歌词原文（19 行） | `.../00_source/lyrics-wind-dream.txt` |
| 音频源 | `samples/review/real-song-demos/00_source/wind-dream/netease.mp3`（69.77s） |
| V3 水彩背景 | `samples/review/references/style-faithful/003-wind-dream-bg.png` |
| 预设 | `samples/review/typography-presets.json`（key `wind-dream`） |
| aurora 参考实现 | `samples/review/real-song-demos/render_character_styles.py` |

---

## 2. 真正根因（两个，都已修复）

### 根因 A —— 逐字 alpha 断崖：字一开口就消失
旧代码对「已开口」的字用 `entry = ease(age / .22)` 作为 alpha，对「未开口」的字用 `alpha = 1.0`。于是在**每个字的开口瞬间**：

```
t = start-ε : alpha = 1.000   ← 未开口，常驻显示
t = start   : alpha = 0.000   ← 开口，alpha 归零
```

并且同时 `dy = 32*(1-entry)` →**瞬间下坠 32px 再升回来**。

实测（`你的笑像音符跳跃着` 的「像」，start=8.16）：

```
   t       age    alpha   dy
  8.110  -0.050  1.000     0.0
  8.160   0.000  0.000    32.0   <== 消失
  8.210   0.050  0.539    14.8
  8.330   0.150  0.968     1.0
```

**这就是用户看到的「截断 / 缺字」**：不是被画布裁掉，是字在开口瞬间真的变透明了。逐帧像素证据见 `_probe/proof-dip.jpg`（第 4 格，t=8.16，整行读作「你的笑」+ 空白）。

> 上一版交接只把 `if age < 0: continue` 改成常驻显示，却保留了 `entry` 这套 alpha，于是「藏起来」变成了「闪现式隐形」，症状没消失。

### 根因 B —— `char_glyph()` 裁剪坐标错位：「一」渲染成空图
```python
bb = d.textbbox((0, 0), ch, font=font)
d.text((-bb[0], -bb[1]), ch, font=font, fill=color + (255,))   # 重画，使墨迹落在 (0,0)
cropped = canvas.crop(bb)                                       # ← 错：仍按未平移的 bb 裁
```
重画后墨迹范围是 `(0, 0, bb[2]-bb[0], bb[3]-bb[1])`，却按 `bb` 去裁。只要 `bb[1] != 0`（墨迹不在画布原点），裁出来的就是**空白画布**。

- `一`（低位单横）→ glyph 96×40，**墨迹像素 = 0**，完全空白。
- `二` 同样空白；`三/十/七/人` 侥幸有墨迹。
- 全曲 170 字中命中 1 字：`每一步都是向你靠近的乐谱` 的「一」。

修正：`cropped = canvas.crop((0, 0, bb[2]-bb[0], bb[3]-bb[1]))`。

---

## 3. 修复内容（`render_wind_dream_combined_v2.py`）

1. **alpha 不再受字自身进度影响**。`alpha = fade_out`（只有整行级别的淡入淡出）。
2. **新增 `highlight_weight()`**：梯形权重 —— 开口前 0 → 前 0.10s 升到 1 → 演唱期间保持 1 → 结束前 0.10s 落回 0。相邻字权重区间重叠，高亮**平滑滑动**而非跳变；权重同时驱动浮升（`LIFT=14px`）与放大（`scale` 1.0→1.06）。
   - 因为入场与出场都回到静止姿态，**不存在任何 pop，也不存在任何隐形窗口**。
3. **修复 `char_glyph()` 裁剪坐标**（根因 B）。
4. **`layout_cue()` 加缓存**：`fit_size()`/`line_metrics()` 原本每帧重算，纯浪费；渲染耗时 528 帧从明显变快。
5. **新增 `char_box()`**：把「某个字在某时刻画在哪」抽成公共函数，`frame()` 与审计脚本共用同一套数学，避免审计与实际渲染漂移。
6. **窗口可配置**：`WD_START` / `WD_END` / `WD_TAG` 环境变量。

### 后续调整（同日，应要求）

7. **去掉黑色描边**：`STROKE_WIDTH` 由 2 改为 **0**（代码保留并注释：描边当初只是为掩盖 alpha 断崖导致的对比度问题，真因修掉后就成了多余装饰）。现在是 V3 原始观感 —— 水彩底 + 金 `#fff071`，只留柔和投影。设 `>0` 即可恢复（环按 8 邻域绘制）。
8. **高亮色改为纯白 `(255,255,255)`**：去掉描边后，原本靠描边撑住的暖白 `(255,253,238)` 暴露出发虚。做了 5 色并列实测（`_probe/accent-options.jpg`），纯白在蓝底上对比最高。若想留在金色系，amber `(255,205,70)` 是备选。


---

## 4. 新增审计闸门 `check_no_blank_chars.py`

思路：每帧渲染两次 —— 一次正常、一次不带歌词行 —— 做像素差分；凡是歌词层画上去的都会留下非零差值。然后对每个字，用 `char_box()` 给出**它实际被绘制的矩形**，统计该矩形内有多少像素被歌词层贡献过。

- 判据：`coverage < 2%` 即判定该字空白。
- 退出码 0 = PASS，1 = FAIL。可直接接进 CI / 发布前闸门。

### 实测结果（均为 PASS）

| 窗口 | 审计帧数 | 字号测量次数 | 最低覆盖率 | 中位覆盖率 | 结论 |
|---|---|---|---|---|---|
| 片段 29.5–51.5s（22s） | 528 | 4,567 | **21.9%** | 39.8% | PASS |
| 全曲 0.4–69.7s（69.3s） | 1,664 | 12,957 | **21.9%** | 38.5% | PASS |

没有任何一次测量接近 2% 阈值 —— 也就是说**不存在任何一帧、任何一个字是空的**。
（去描边前覆盖率约 27.9%；描边本身贡献了那部分像素，去掉后回落到 21.9%，仍高于阈值约 11 倍。）

---

## 4b. 方法论已固化：skill `renderer-blank-text-triage`

这类故障（“文字看起来被截断/缺字/闪一下”）的排查顺序已写成 skill，避免下次再走弯路：

1. **逐元素 alpha 时间序列**（找断崖）
2. **每个 glyph 的墨迹像素数**（找空图；要覆盖全部文本集 × 全部字号）
3. **最后**才是几何（bbox vs 画布 / BOX）

⚠️ **「geometric clipping: False」不等于已定位** —— 它只排除了 4 种可能中的 1 种。本轮前 4 次修复正是卡在这里：几何 → 对比度 → 淡出逻辑，全都没碰到真因。

skill 已写入三处：真值源 `D:\ZON\codex\codex-skills-private\`、加载目录 `C:\Users\zonli\.workbuddy\skills\`、镜像 `D:\ZON\workbuddy-home\skills\`。
项目级约定另见 `.workbuddy/memory/MEMORY.md`。


---

## 5. 产物

| 文件 | 说明 |
|---|---|
| `wind-dream-combined-v2.mp4` | 22.0s，1280×720@24，已修复（主交付） |
| `wind-dream-combined-v2-full.mp4` | 69.33s，全曲，已修复并通过审计 |
| `blank-char-audit-excerpt.json` / `blank-char-audit-full.json` | 审计报告 |
| `_probe/COMPARE-before-after.jpg` | 修复前/后对照（含「像」消失与「一」空白两例） |
| `_probe/accent-options.jpg` | 高亮色 5 选 1 实测（最终选纯白） |
| `_probe/proof-dip.jpg` | 修复前：t=8.16「像」消失的逐帧证据 |
| `_probe/proof-fixed.jpg` | 修复后：同一时间轴，整行始终完整 |
| `_probe/wind-dream-combined-v2-OLD-broken.mp4` | 修复前的旧渲染（留作对照） |

### 重新渲染
```bash
cd "D:/ZON/codex/lyric-mv-kit/runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render"
"D:/ZON/runtime/miniforge3/python.exe" render_wind_dream_combined_v2.py           # 22s 片段
WD_TAG=-full WD_START=0.4 WD_END=69.7 \
  "D:/ZON/runtime/miniforge3/python.exe" render_wind_dream_combined_v2.py        # 全曲
"D:/ZON/runtime/miniforge3/python.exe" check_no_blank_chars.py                    # 审计
```
注意：仓库根的 base python **无 numpy**，必须用 `D:/ZON/runtime/miniforge3/python.exe`。

---

## 6. 仍未处理（明确留给你决定）

1. **`run-config.json` 未同步**：`template.id` 仍是 `lyric-aurora-v1`（纯 aurora），未体现「V3 包装 + aurora 动态」。
   ⚠️ 该 run-config 是 v20260910-01 的**正式 run 记录**，MV00–MV10 是用 `lyric-aurora-v1` 产出的。直接改 `template.id` 会让历史记录失真 —— 建议**另开一个实验 run** 或新增字段，而不是就地改。
2. **对齐精度**：本机无 `faster-whisper`，用 `openai-whisper(base)` 兜底，存在多字合并词（如「不会」）。若精度关键，换 `turbo`/`faster-whisper` 重跑对齐。`run-config.json` 亦记录 `manual_listening_verified: false`，即**尚未人工听校**。
3. **观感终审**：本轮所有结论都建立在像素级审计 + 逐帧目视之上，几何、alpha、墨迹三项都已闭环。若仍有观感问题，最可能落在**主观参数**上 —— 它们全部集中在脚本顶部：

| 参数 | 当前值 | 作用 |
|---|---|---|
| `LIFT` | 14 | 当前字浮升高度（px）；设 0 = 只靠颜色/缩放提示 |
| `RAMP` | 0.10 | 高亮在相邻字之间的滑动秒数；调大更柔和 |
| `BOB` | 1.2 | 静止整行的微浮（px） |
| `ACCENT` | `(255,255,255)` | 当前唱到的字的颜色；备选 amber `(255,205,70)` |
| `STROKE_WIDTH` | 0 | 深色描边，已按要求关闭；设 1–2 可恢复 |

### 环境律动层（2026-09-11 追加）

用户反馈「页面动态律动太少了」，在歌词框外新增 5 层环境动效（全部有独立开关，可单独关闭）：

| 层 | 开关 | 说明 |
|---|---|---|
| 背景微漂移 | `BG_DRIFT` | 水彩底 ±11px 正弦游移 |
| 节拍呼吸光晕 | `GLOW` | 歌词框后暖色径向光晕，随 pulse/bass 脉动 |
| 底部频谱条 | `SPECTRUM` | 64 段 log-spaced 频谱，y=682~716，金色半透明 |
| 跳动音符 | `NOTES` | 节拍驱动的矢量八分音符在留白区升腾 |
| 浮尘微粒 | `PARTICLES` | 26 粒随 treble 闪烁的尘埃 |

音频特征复用现有 `audio_features()` 的 `bands`/`bass`/`treble`/`pulse`/`beats`，无需重新分析。审计兼容（viz 层在 bg-only 和 lyric 帧中一致渲染）。

---

_本轮备注：上一版交接的根因判断方向对了一半（确实与「逐字揭示」有关），但漏掉了 alpha 断崖导致的「开口瞬间隐形」和 `char_glyph` 裁剪错位导致的「一 = 空白」这两个真正的元凶。两者都不是几何裁切，所以按「调 BOX / 调对齐」的思路排查永远找不到。现已修复，并留下可复跑的审计闸门防止回归。_
