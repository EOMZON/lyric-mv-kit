# 组件化架构：数据 / UI 分离（renderer componentization）

> 归属：lyric-mv-kit（公开模板产品仓） · 关联 issue：kit 新开 `renderer 组件化与数据/UI 分离`（P2-2 模板合流前置）
> 治理真源：codex-skills-private `issue-governance.md` §7（Data / UI / Runtime / Evidence 分离）
> 状态：Phase 1（数据层落地，UI 未接线，行为中性，不触碰 kit#12 修复）

---

## 1. 为什么做（背景）

当前 `lyric_mv/renderer.py` 与 `lyric_mv/cover.py` 把**样式事实**直接写死在代码里：

- `renderer.py`：`ACCENT = {...}`（段落→RGB）、`W, H = 1920, 1080`、`BRAND`
- `cover.py`：`RIBBONS`、`SPECTRUM_STOPS`、`INK/GLOW`、`STANDARD_SIZE/WIDE_SIZE/YT_SIZE`、HUD 尺寸

这导致：换一首歌的配色 / 加一个模板 / 调一个尺寸 = 改代码；批量器（P2-3）无法用数据驱动选模板；AI 接手时要在代码里翻硬编码常量。

目标：**把「事实（Data / Domain）」与「绘制（UI）」拆开**，让模板成为可编辑数据，renderer/cover 成为消费数据的纯绘制层。

---

## 2. 分层（对齐 issue-governance §7）

| 层 | 本仓落点 | 内容 |
|---|---|---|
| **Data / Domain** | `lyric_mv/data/schema.py` | `Timing` / `LyricLine` / `SongPlan`（歌词时序、段落、双语翻译）——纯数据，无 PIL/numpy |
| **Projection / ViewModel** | `lyric_mv/data/presets.py` + `presets.yaml` | `StyleSpec`：accent / ribbons / spectrum / sizes / HUD，从数据加载，含 YAML 覆盖 |
| **UI** | `lyric_mv/renderer.py` / `cover.py` | 只负责绘制；**Phase 2 改为 `from lyric_mv.data import get_preset` 消费 `StyleSpec`** |
| **Runtime** | `cli.py` / `plan.py` | 批量器（P2-3）按 `SongPlan` + `StyleSpec` 驱动渲染 |
| **Evidence** | `tests/` + 批量 run 的 sha256 | 每模板渲染产物可复现、可 diff、可回放 |

---

## 3. 目标包结构（Phase 完成后）

```
lyric_mv/
  data/                  # ← 新增：事实层
    __init__.py
    schema.py            # LyricLine / SongPlan / Timing（Data/Domain）
    presets.py           # StyleSpec + get_preset()（Projection/ViewModel）
    presets.yaml         # 可编辑样式数据（人类可读）
  renderer.py            # UI：Phase 2 改为消费 StyleSpec
  cover.py               # UI：Phase 2 改为消费 StyleSpec
  cli.py / plan.py       # Runtime：批量器入口
```

`presets.yaml` 是单一可编辑真源；`presets.py::DEFAULT_PRESETS` 为内置回退（无第三方依赖即可 import）。

---

## 4. Phase 划分（每阶段独立验收，不一次重写）

- **Phase 1（本 commit）**：落地 `data/` 层（schema + presets + yaml），值 1:1 保留现有硬编码常量。**不修改 renderer/cover**，行为完全中性。
- **Phase 2（后续 PR）**：renderer/cover 改为 `from lyric_mv.data import get_preset`；常量引用替换为 `spec.accent_for(section)` 等。含 kit#12 行宽自适应逻辑保留。需回归测试 + 视觉 diff 比对。
- **Phase 3（P2-2 模板合流）**：新增 `paper_staff` 等模板仅在 `presets.yaml` 加数据；批量器（P2-3）按 `SongPlan` 选模板 → 出片。

---

## 5. 验收标准（Evidence）

1. `python -m lyric_mv.data` 打印 preset 摘要，无 import 错误、无第三方依赖。
2. Phase 2 后：`renderer.py` / `cover.py` 不再出现硬编码 `ACCENT` / `RIBBONS` 字面量（grep 应为空）。
3. Phase 2 后：同一 `SongPlan` 用 `aurora_ribbon` 与 `paper_staff` 渲染，输出像素可区分且可复现（sha256 稳定）。
4. 每段逻辑变更需 `test-main-governance` 的 test→main 合入 + consumer（批量器）readback。

---

## 6. 当前下一动作

等待 Owner 授权：开 PR `feat/renderer-componentization-2026-09-23` → `test` → `main`，Phase 1 仅合数据层（不影响 kit#12 修复分支）。Phase 2 接线单独 PR，避免与 `feat/bilingual-translate-line` 冲突。
