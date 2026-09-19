# PR #2 Source Delivery Manifest — 语义拆分清单

更新：2026-09-19
关联：Issue #3 (P0-2) · PR #2 `codex/motion-template-system-v5` (DRAFT, +2033)
状态：**manifest only** — 本文件不授权合入任何分支。PR #2 维持 Draft / HOLD。

## 目的

PR #2 同时携带「可复用产品候选」与「单曲制作证据」，违反 Issue #3 的仓库边界。
本清单把 PR #2 的 38 个文件逐一做**语义归类**，作为后续拆分（reusable 留 `lyric-mv-kit`，
song-specific 迁 `lyric-mv-workbench-private`）的唯一事实来源。拆分不得用「挑文件名看起来差不多」代替语义 reconciliation。

## 分类口径（来自 PRODUCT-SCOPE.zh-CN.md）

- `REUSABLE`：多模板共用的 renderer / contract / preset / 通用脚本 / 字体 / 面向开源用户的模板文档。
- `SONG_SPECIFIC`：单曲 production run、forced alignment、逐帧审计、contact sheet、single-song motion score、song bg。
- `HANDOFF`：AI prompt / 本机操作交接 → 不进入公开稳定产品文档（归 skills / publisher owner）。

## 清单（38 文件）

### REUSABLE — 留在 `lyric-mv-kit`

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `lyric_mv/motion.py` | renderer | 通用 motion 引擎，无 song 依赖 |
| 2 | `lyric_mv/motion_renderer.py` | renderer | 通用 motion 渲染层 |
| 3 | `presets/motion/README.md` | doc | 模板使用说明（开源用户需要） |
| 4 | `presets/motion/ambient-story.json` | preset | 可复用模板 |
| 5 | `presets/motion/beat-push.json` | preset | 可复用模板 |
| 6 | `presets/motion/cinematic-float.json` | preset | 可复用模板 |
| 7 | `presets/motion/steady-karaoke.json` | preset | 可复用模板 |
| 8 | `presets/motion/type-camera.json` | preset | 可复用模板 |
| 9 | `schemas/motion-score.schema.md` | contract | motion-score 数据契约 |
| 10 | `scripts/render_motion.py` | script | 通用渲染 CLI 入口 |
| 11 | `scripts/check_motion_configs.py` | script | 配置校验（公开用户需要） |
| 12 | `assets/fonts/reusable/LongCang-Regular.ttf` | font | 可复用字体（已放 reusable/ 子目录，命名合规） |
| 13 | `docs/analysis/2026-09-15-motion-template-system-v5.md` | doc | 模板架构分析；**发布前需裁剪** Wind Dream 调试叙述，只留面向开源用户的架构/用法部分 |

> 注：`docs/analysis/...` 当前含单曲调试叙述，属 PUBLIC_PRODUCT_DOC 候选但需 trim。若裁剪成本高，
> 可先归 `ARCHIVE_REFERENCE`，待模板 stable 后再写精简版。

### SONG_SPECIFIC — 迁 `lyric-mv-workbench-private`

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 14 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/00_source/lyrics-wind-dream.txt` | source | 单曲歌词 |
| 15 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_alignment/forced_alignment.json` | align | 单曲 forced alignment |
| 16 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/README.md` | doc | 单曲 v5 说明 |
| 17 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/V5-LOCAL-VALIDATION.md` | doc | 单曲验证 |
| 18 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/audit_v5_blank_and_safearea.py` | script | 单曲审计脚本 |
| 19 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/make_v4v5_compare_sheet.py` | script | 单曲对比 |
| 20 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/make_v5_contact_sheets.py` | script | 单曲 contact sheet |
| 21 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/motion-score.json` | data | 单曲 motion score |
| 22 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/render_v5_motion_score.py` | script | 单曲渲染入口 |
| 23 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v4-vs-v5-compare.jpg` | img | 单曲对比图 |
| 24 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-1.04.jpg` | img | 单曲帧 |
| 25 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-10.08.jpg` | img | 单曲帧 |
| 26 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-13.20.jpg` | img | 单曲帧 |
| 27 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-16.98.jpg` | img | 单曲帧 |
| 28 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-19.90.jpg` | img | 单曲帧 |
| 29 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-21.90.jpg` | img | 单曲帧 |
| 30 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-4.34.jpg` | img | 单曲帧 |
| 31 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-7.40.jpg` | img | 单曲帧 |
| 32 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-blank-char-audit.json` | data | 单曲审计 |
| 33 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-contact-boundaries.jpg` | img | 单曲 contact |
| 34 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-contact-journey.jpg` | img | 单曲 contact |
| 35 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-motion-audit.json` | data | 单曲审计 |
| 36 | `runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/v5-motion-score/v5-motion-result.json` | data | 单曲结果 |
| 37 | `samples/review/references/style-faithful/003-wind-dream-bg.png` | img | Wind Dream 专属背景参考 |

### HANDOFF — 归 skills / publisher owner（不进公开稳定产品文档）

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 38 | `docs/handoff/2026-09-15-motion-template-v5/HANDOFF.md` | handoff | AI prompt / 本机操作交接 |

## 拆分执行步骤（下一步，非本 manifest 范围）

1. 从最新 `test` 起一个 reusable-only 分支，只纳入上表 13 个 REUSABLE 文件（含 `docs/analysis` 裁剪版）。
2. 上述 23 个 SONG_SPECIFIC 文件整体迁到 `lyric-mv-workbench-private`（保留 git 历史/指针）。
3. `docs/handoff/.../HANDOFF.md` 迁到 publication skill owner。
4. 旧 PR #2 在复用集与 song-specific 均就位后关闭，替换为两个语义干净的 PR。
5. 验证：reusable 分支不引用任何 `runs/wind-dream/**` 路径；`lyric_mv/motion*` 无 song 硬编码。
