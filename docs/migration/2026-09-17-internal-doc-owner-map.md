# `lyric-mv-kit` 内部历史文档 Owner Map

更新：2026-09-17  
状态：迁移审计候选；**本文件不授权删除原文件**。

产品边界：
https://github.com/EOMZON/lyric-mv-kit/blob/docs/open-source-boundary-20260917/docs/PRODUCT-SCOPE.zh-CN.md

总 Issue：
https://github.com/EOMZON/lyric-mv-kit/issues/3

Music Promotion System：
https://github.com/EOMZON/music-board/issues/25

Merge Reconciliation：
https://github.com/EOMZON/codex-skills-private/issues/29

## 1. 目的

公开仓库最终应让开源用户看到：

```text
模板效果
→ released template
→ 如何使用
→ renderer / schema / extension docs
```

而不是看到 Zon 自己的：

```text
本机路径
AI 对话 prompt
平台登录/上传交接
单曲 catalog patch
官网内部实施步骤
运营 checklist
```

历史文件先逐项确定 canonical owner / successor，再迁移；在目标端没有可恢复证据前不删除 source。

状态分类：

```text
KEEP_PUBLIC_PRODUCT_DOC
MOVE_TO_MUSIC_BOARD
MOVE_TO_WORKBENCH
MOVE_TO_PUBLICATION_OWNER
ARCHIVE_REFERENCE_THEN_REMOVE_FROM_PUBLIC_HEAD
SUPERSEDED_WITH_EVIDENCE
```

## 2. 明确保留的公开产品文档

| 文件 | 决策 | 理由 |
|---|---|---|
| `docs/FAQ.md` | `KEEP_PUBLIC_PRODUCT_DOC` | 面向开源使用者的通用 FAQ |
| `docs/FONTS.md` | `KEEP_PUBLIC_PRODUCT_DOC` | renderer 字体复现说明 |
| `docs/PORTING-TO-REMOTION.md` | `KEEP_PUBLIC_PRODUCT_DOC` | 通用技术扩展/移植说明 |
| `schemas/**` | `KEEP_PUBLIC_PRODUCT_DOC` | public renderer contract |
| `showcase/**` | `KEEP_PUBLIC_PRODUCT_DOC`（逐资产许可/真实性审计） | 模板/风格公开效果入口 |

`showcase` 保留的前提是内容代表真实可复现实现，不把静帧参考冒充已经 release 的动态模板。

## 3. `docs/handoff/**` 分类

### `docs/handoff/00-INDEX.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/00-INDEX.md

决策：

```text
ARCHIVE_REFERENCE_THEN_REMOVE_FROM_PUBLIC_HEAD
```

理由：这是“多对话 handoff index”，包含本机 Windows 路径、WorkBuddy skill 路径、Music Board 实现细节和 AI 协作说明，不是开源产品文档。

目标：有效 owner 信息分别迁往 Music Board / publication owner / private workbench；原 index 只作为历史 commit 可追溯。

### `docs/handoff/P1-song-page-embed.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/P1-song-page-embed.md

决策：

```text
MOVE_TO_MUSIC_BOARD
SUPERSEDED_WITH_EVIDENCE（大部分实现事实）
```

理由：内容实际是 `music.zondev.top` 歌曲页、catalog `embeds/links`、`app.js` 与 Vercel 发布步骤；canonical owner 是 Music Board。

当前 successor：

- Song promotion model：
  https://github.com/EOMZON/music-board/blob/test/song-promotion-model.js
- Promotion system：
  https://github.com/EOMZON/music-board/issues/25
- Existing data loop：
  https://github.com/EOMZON/music-board/issues/16

迁移时只保留仍有历史价值的决策/证据，不照抄旧“push main 即上线”等过时指令。

### `docs/handoff/P2-lyric-studio.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/P2-lyric-studio.md

决策：

```text
MOVE_TO_MUSIC_BOARD
SUPERSEDED_WITH_EVIDENCE
```

理由：它要求修改 Music Board router/app.js，且旧方案建议把 8 风格数组写死在 UI；当前仓库已经存在 data/model 分离的 Lyric Studio 六模板事实，新架构明确禁止再造第二套 template truth。

当前 successor：

- existing data：
  https://github.com/EOMZON/music-board/blob/test/lyric-studio-data.js
- existing model：
  https://github.com/EOMZON/music-board/blob/test/lyric-studio-model.js
- Promotion Domain：
  https://github.com/EOMZON/music-board/issues/26
- Template Gallery：
  https://github.com/EOMZON/music-board/issues/27

旧“直接在 app.js 写死 `LYRIC_STYLES`”不再作为实现建议。

### `docs/handoff/P3-home-module.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/P3-home-module.md

决策：

```text
MOVE_TO_MUSIC_BOARD
SUPERSEDED_WITH_EVIDENCE
```

理由：这是首页产品/视觉实现任务，不属于 renderer。当前 Music Board 已有独立 homepage/discovery/visual governance，Template Gallery 也不应成为首页主产品。

当前 successor：

- Visual owner：
  https://github.com/EOMZON/music-board/issues/17
- Editorial showcase：
  https://github.com/EOMZON/music-board/issues/22
- Template Gallery：
  https://github.com/EOMZON/music-board/issues/27

如未来首页需要模板入口，只做真实 reviewed data 驱动的轻量入口，不照搬旧“hero 后固定插一个 8 风格模块”。

### `docs/handoff/P4-resource-loop.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/P4-resource-loop.md

决策：

```text
MOVE_TO_MUSIC_BOARD
+
MOVE_TO_PUBLICATION_OWNER
```

理由：它混合两类真相：

- website/public catalog links → Music Board；
- B站/YouTube/网易云发布简介与渠道操作 → publication owner/skills。

当前 successor：

- Promotion parent：
  https://github.com/EOMZON/music-board/issues/25
- Distribution domain：
  https://github.com/EOMZON/music-board/issues/26
- Provider metrics/data facts：
  https://github.com/EOMZON/music-board/issues/16

`lyric-mv-kit` 最终只需要在 README 中保留少量真实 example/live gallery link，不拥有完整 channel operations checklist。

### `docs/handoff/YOUTUBE_UPLOAD_HANDOFF.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/handoff/YOUTUBE_UPLOAD_HANDOFF.md

决策：

```text
MOVE_TO_PUBLICATION_OWNER
ARCHIVE_REFERENCE_THEN_REMOVE_FROM_PUBLIC_HEAD
```

理由：包含：

- 本机 Chrome / Python / profile 路径；
- 登录态与 CDP 操作；
- YouTube Studio 上传步骤；
- platform visibility/publication action；
- local run state / evidence path。

这不仅不是开源 template 文档，还会让公开 repo 承担错误的 provider/runtime owner。

迁移目标必须优先复用现有 `youtube-publication-pipeline` / channel publication owner，不在公开 repo 再维护第二份 SOP。

### `docs/handoff/PROMPTS.md`

决策：

```text
ARCHIVE_REFERENCE_THEN_REMOVE_FROM_PUBLIC_HEAD
```

理由：paste-ready AI 协作 prompt 是内部执行材料。有效业务决策应进入 owner repo 的 Issue/architecture docs；有效发布动作进入 publication skill；有效 Workbench 迁移进入 private repo。

在逐条确认 successor 前保留 source，不直接删除。

## 4. `docs/plan-2026-09-03/**` 分类

### `resource-loop-checklist.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/plan-2026-09-03/resource-loop-checklist.md

决策：

```text
MOVE_TO_MUSIC_BOARD
+
MOVE_TO_PUBLICATION_OWNER
ARCHIVE_REFERENCE_THEN_REMOVE_FROM_PUBLIC_HEAD
```

这是《我拒绝被定义》的五端运营/发布状态快照，不是 template 产品文档。

历史状态仍有证据价值，但未来状态 owner 应是：

```text
Music Board DistributionReceipt / public catalog
+
publication provider receipt
```

### `data-patches/youtube-rxPFQV7zfMg.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/plan-2026-09-03/data-patches/youtube-rxPFQV7zfMg.md

决策：

```text
MOVE_TO_MUSIC_BOARD
SUPERSEDED_WITH_EVIDENCE
```

这是一个具体 track 的 Music Board YouTube backfill 请求。Track identity、embed/watch URL 和 catalog mutation owner 都属于 Music Board。

保留其历史证据的目标是解释为什么某条 URL 进入 public projection，而不是继续作为开源模板仓 active plan。

## 5. `docs/plan-2026-09-04/**` 分类

### `multi-channel-lyric-mv-roadmap.md`

原文：
https://github.com/EOMZON/lyric-mv-kit/blob/main/docs/plan-2026-09-04/multi-channel-lyric-mv-roadmap.md

决策：

```text
MOVE_TO_MUSIC_BOARD
+
MOVE_TO_WORKBENCH
+
MOVE_TO_PUBLICATION_OWNER
SUPERSEDED_WITH_EVIDENCE
```

这是一个跨域 roadmap，已经同时讨论：

- 全平台歌曲覆盖矩阵；
- 模板动态评审；
- 批量视频生产；
- 多渠道发布；
- catalog 回填。

这些职责已经被最新架构拆开：

- Music business / promotion：
  https://github.com/EOMZON/music-board/issues/25
- Promotion Domain：
  https://github.com/EOMZON/music-board/issues/26
- Open-source template boundary：
  https://github.com/EOMZON/lyric-mv-kit/issues/3
- Private Workbench bootstrap：
  https://github.com/EOMZON/music-board/blob/docs/music-promotion-system-20260917/docs/handoff/2026-09-17-lyric-mv-workbench-bootstrap.md

因此不应继续在公开 template repo 维护这份跨域 active roadmap。

## 6. 迁移原则

### 先 copy/port + target readback，再删 source

不能：

```text
决定 owner
→ 直接 rm source docs
```

必须：

```text
source manifest
→ target owner document/issue exists
→ semantic port / supersession pointer
→ target exact-ref readback
→ source pointer
→ test verify
→ 才考虑从 public HEAD 删除
```

### 不照搬过时指令

上述历史 handoff 多处包含：

```text
git push origin main
push main 即 Vercel 上线
直接写 app.js 数组
占位 ID
固定本机路径
```

迁移时只保留仍然成立的事实/决策，不把旧执行命令复制到新 owner。

### 公开历史仍由 Git 保留

从未来 public `main` 删除 active handoff 文件，不等于抹除历史；原 commit/tag/PR 仍可追溯。必要时在新 README / migration note 留 legacy pointer。

## 7. 并行建议

可以并行：

1. Music Board 接收/supersede P1/P2/P3/P4 业务语义；
2. publication owner 接收 YouTube/channel SOP；
3. private workbench 创建后接收 experiment/run 语义；
4. `lyric-mv-kit` 准备 template-first README 候选。

但**删除 public source docs**必须等 1–3 的目标 readback 完成，再由一个 integration owner 串行处理。

## 8. Definition of Done

- [ ] 每个 internal doc 有 target owner / successor；
- [ ] target repo 有可达 Issue/doc/skill；
- [ ] 过时指令未被复制为新规范；
- [ ] publication SOP 不再由 public template repo owner；
- [ ] Music Board tasks 不再由 public template repo owner；
- [ ] private runs/handoffs 有 private workbench owner；
- [ ] source removal 前完成 Merge Reconciliation；
- [ ] `test` exact SHA verification；
- [ ] 用户明确授权后才进入 public `main`。
