# lyric-mv-kit 开源产品边界

更新：2026-09-17  
状态：候选文档，等待按 Test → Verification → Main 验收后进入稳定线。

Git 治理：
https://github.com/EOMZON/codex-skills-private/blob/9a8e385ccc98f068b0990133f9a2e80681ffa9ec/github-ops/references/test-main-governance.md

## 1. 为什么需要重新定义边界

`lyric-mv-kit` 最初的目标不是记录 Zon 自己每一支 MV 的调试过程，而是把真实音乐宣传过程中已经验证、认可、可复现的歌词 MV 模板沉淀为一个公开开源产品。

当前稳定 `main` 已经具备一个合理的公开产品骨架：

- 通用 Python / Pillow / ffmpeg renderer；
- `plan.json` 等稳定数据契约；
- `presets/`；
- `showcase/`；
- 双语 README；
- LICENSE / NOTICE / FAQ / 字体说明。

但历史协作中又把以下内容放进了同一仓库或工作分支：

- 单首歌曲的 `runs/`、forced alignment、逐帧审计、contact sheets；
- v2/v3/v4/v5 单曲视觉调试；
- AI handoff / prompt / 本机操作交接；
- YouTube / B站上传流程；
- `music.zondev.top` 页面改造计划；
- 多渠道运营、选曲、发布、catalog 回填规划。

这些对象的生命周期和受众不同，继续混在一起会让公开仓库从“可复用成品”退化为“个人工作现场”。

## 2. 新的产品定位

`lyric-mv-kit` 只负责：

> **Approved, reproducible lyric-MV templates and the reusable rendering primitives required to use them.**

中文理解：

> **只发布已经认可、可复现、值得别人使用的歌词 MV 模板，以及支撑这些模板的通用渲染能力。**

它不是：

- Zon 的单曲制作工作台；
- MV 调试历史库；
- 音乐运营 Dashboard；
- 社媒发布机器人；
- YouTube / B站 / 小红书 / 抖音操作手册；
- AI prompt / handoff 仓库；
- `music.zondev.top` 的业务代码 owner；
- 每日宣传队列 owner。

## 3. 仓库职责

### 保留在 `lyric-mv-kit`

```text
lyric_mv/
presets/
schemas/
showcase/
README.md
README.zh-CN.md
LICENSE
NOTICE
通用 FAQ / 字体 / renderer 文档
```

允许进入稳定线的内容必须满足至少一个条件：

1. 是多个模板共同依赖的 renderer / contract；
2. 是已经批准的 reusable template；
3. 是复现公开模板所必需的示例、schema、测试或文档；
4. 是公开用户真正需要的安装、使用、扩展说明。

### 迁往未来私有 `lyric-mv-workbench-private`

未来私有工作台负责：

```text
单曲 production run
模板候选 / 失败尝试
v1/v2/v3... 视觉比较
forced alignment / song motion score
contact sheets / audit artifacts
人工审批证据
批量 render / QA
每日生产队列消费端
```

典型现有内容：

- `runs/wind-dream/**`
- 《风穿过指尖的梦》Issue #1 对应制作证据
- song-specific render scripts
- song-specific motion score
- single-song contact sheets / visual audit

该私有仓库尚未创建，因此当前只建立迁移计划，不从 `main` 删除唯一证据。

### 归 `EOMZON/music-board`

`music-board` / `music.zondev.top` 是音乐业务与公开体验 owner，负责：

- canonical song / album identity；
- promotion queue；
- approved template reference；
- MV / platform publication links；
- `music.zondev.top/templates` Template Gallery；
- PromotionAsset / Distribution / Performance read model；
- 运营指标与效果复盘。

相关项目定义：
https://github.com/EOMZON/music-board/blob/main/PROJECT.md

### 归发布 / skills 层

平台上传、浏览器动作、回执与渠道适配不属于本仓：

- YouTube / B站 / 后续小红书抖音 publisher；
- publication manifest；
- platform-specific recovery；
- 浏览器登录态操作说明。

应由现有发布 skills / 对应私有发布 owner 承担。

## 4. 产品主线与模板支线

音乐系统真正主线：

```text
歌曲池
→ 宣传队列
→ 使用 Approved Template 批量生成 MV
→ QA
→ 多平台分发
→ publication receipt
→ music-board 运营数据
→ 复盘播放 / 点击 / 收益
```

模板探索只是支线：

```text
EXPERIMENT
→ CANDIDATE
→ 20–30 秒样片
→ owner review
→ APPROVED
→ 才能进入每日生产池
→ 有复用价值时再进入 lyric-mv-kit
```

核心约束：

> **每日内容生产不得被 EXPERIMENT / CANDIDATE 模板阻塞。**

## 5. Template Lifecycle

建议统一状态：

```text
EXPERIMENT
CANDIDATE
APPROVED
RELEASED
DEPRECATED
```

语义：

- `EXPERIMENT`：只在私有工作台试验；
- `CANDIDATE`：已有短样片，等待人工认可；
- `APPROVED`：可进入个人每日 MV 生产池；
- `RELEASED`：已经整理为公开、可复现模板并进入 `lyric-mv-kit` 稳定线；
- `DEPRECATED`：仍可追溯，但不建议新项目使用。

`lyric-mv-kit/main` 不接收 `EXPERIMENT` 或仅针对单曲的 `CANDIDATE`。

## 6. PR #2 必须拆分，不原样合入

当前 Draft PR：
https://github.com/EOMZON/lyric-mv-kit/pull/2

它同时包含两类对象。

### A. 可复用产品候选

可继续审阅：

```text
lyric_mv/motion.py
lyric_mv/motion_renderer.py
presets/motion/*.json
presets/motion/README.md
schemas/motion-score.schema.md
scripts/check_motion_configs.py
scripts/render_motion.py
```

这些内容表达：

```text
Visual Style
× Motion Template
× optional Motion Score contract
```

有机会成为公开产品能力，但必须从单曲证据中独立出来，重新在最新 integration target 验证。

### B. 私有单曲制作证据

不应原样进入公开稳定线：

```text
runs/wind-dream/**
song-specific lyrics / alignment
v4-vs-v5 compare
v5 contact sheets
single-song audit JSON
single-song render script
single-song handoff
```

未来应迁往 `lyric-mv-workbench-private`。

### PR 处理原则

- PR #2 继续保持 Draft / HOLD；
- 不直接 merge；
- 新 reusable candidate 从最新 `test` 重新形成 coherent set；
- Wind Dream 唯一证据先保留，直到私有 workbench 有远端 recovery ref；
- 迁移完成后再关闭或标记旧 PR 为 superseded。

## 7. 当前 `main` 中需要后续迁移审计的文档

重点：

```text
docs/handoff/**
docs/plan-2026-09-03/**
docs/plan-2026-09-04/**
```

不是所有文件都要删除；应逐项分类：

```text
PUBLIC_PRODUCT_DOC
MOVE_TO_MUSIC_BOARD
MOVE_TO_WORKBENCH
MOVE_TO_SKILLS
ARCHIVE_REFERENCE
```

特别是：

- `P1-song-page-embed.md` / `P3-home-module.md` → Music Board；
- `P4-resource-loop.md` / 多渠道宣传规划 → Music Board / publication owner；
- `YOUTUBE_UPLOAD_HANDOFF.md` → publication skills / private owner；
- AI prompts / handoff → 不进入公开稳定产品文档。

在确认目标 owner 和远端保存前，不删除唯一历史材料。

## 8. 对外体验目标

未来 README / `music.zondev.top/templates` 应先展示模板成品，而不是先展示内部操作过程。

理想入口：

```text
Template Preview
→ Demo / Example Song
→ Supported Ratio / Characteristics
→ Stable Status
→ Use on GitHub
```

GitHub README 的信息优先级：

```text
1. 模板效果
2. 已发布模板列表
3. Live Gallery
4. Quick Start
5. CLI / API / Advanced
```

而不是把 CLI 参数和个人生产流程放在产品叙事之前。

## 9. Git / Worktree 治理

2026-09-17 已补 `test` 长期集成分支；后续路径：

```text
main = stable public release
  ↓ sync
test = integration candidate
  ↓
short-lived task branch
```

所有迁移 / README 重构 / reusable PR2 extraction 必须走 task → test → exact-SHA verification → main。

同时遵守 Merge Reconciliation Gate：

https://github.com/EOMZON/codex-skills-private/issues/29

特别注意：

- worktree 数量减少不等于成果已同步；
- PR merge / cherry-pick exit 0 不等于语义完整；
- 在删除旧 worktree / branch 前，必须确认 source 唯一资产已有远端 recovery ref；
- target 前进后，旧验证不得继续冒充最终组合验证；
- 这次 PR #2 拆分要先建立 delivery manifest，再做 reusable / song-specific 分类。

## 10. 本轮不做

本候选文档本身不执行：

- 删除任何 `main` 文件；
- 合并 PR #2；
- 删除旧分支 / worktree；
- 创建或部署 `music.zondev.top` 页面；
- 渲染新视频；
- 平台发布；
- provider / production side effect。

先把职责边界、Issues、迁移 owner 和可并行工作面固定，再执行实际搬迁。
