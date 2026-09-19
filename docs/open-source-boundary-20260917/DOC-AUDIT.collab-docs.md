# Collaboration-Doc Audit — P0-3 内部协作文档分类

更新：2026-09-19
关联：Issue #3 (P0-3)
范围：`docs/handoff/**` · `docs/plan-2026-09-03/**` · `docs/plan-2026-09-04/**`
状态：分类清单（待 owner 确认后执行迁移；公开仓库不得保留 personal daily production / upload SOP / operational metrics owner 职责）

## 分类口径（来自 PRODUCT-SCOPE.zh-CN.md §3 + Issue #3 P0-3）

- `PUBLIC_PRODUCT_DOC`：只面向开源用户的 renderer / template / FAQ 文档。
- `MOVE_TO_MUSIC_BOARD`：song page / home module / resource loop / promotion roadmap / catalog patch。
- `MOVE_TO_WORKBENCH`：实验 / 单曲 run / QA。
- `MOVE_TO_SKILLS`：AI prompt / handoff / 本机操作交接 / 上传脚本交接。
- `ARCHIVE_REFERENCE`：历史参考，仅作归档指针。

## 清单（10 文件，0 个留公开仓库）

### `docs/handoff/` （7）

| 文件 | 分类 | 去向 | 理由 |
|------|------|------|------|
| `00-INDEX.md` | ARCHIVE_REFERENCE | 归档指针 | 内部 handoff 导航索引，非公开产品文档 |
| `P1-song-page-embed.md` | MOVE_TO_MUSIC_BOARD | music-board | 单曲页嵌入 = 音乐业务页面 |
| `P2-lyric-studio.md` | MOVE_TO_SKILLS | skills owner | 内部创作工具交接，非公开 renderer 文档 |
| `P3-home-module.md` | MOVE_TO_MUSIC_BOARD | music-board | `music.zondev.top` home 模块 |
| `P4-resource-loop.md` | MOVE_TO_MUSIC_BOARD | music-board | 资源循环 / 运营路线 |
| `PROMPTS.md` | MOVE_TO_SKILLS | skills owner | AI prompt 合集，明确不进公开稳定产品 |
| `YOUTUBE_UPLOAD_HANDOFF.md` | MOVE_TO_SKILLS | publisher owner | 上传流程交接 = 渠道适配/回执 |

### `docs/plan-2026-09-03/` （2）

| 文件 | 分类 | 去向 | 理由 |
|------|------|------|------|
| `resource-loop-checklist.md` | MOVE_TO_MUSIC_BOARD | music-board | 资源循环 checklist |
| `data-patches/youtube-rxPFQV7zfMg.md` | MOVE_TO_MUSIC_BOARD | music-board | 单曲 catalog 补丁（song-specific） |

### `docs/plan-2026-09-04/` （1）

| 文件 | 分类 | 去向 | 理由 |
|------|------|------|------|
| `multi-channel-lyric-mv-roadmap.md` | MOVE_TO_MUSIC_BOARD | music-board | 多渠道宣传路线 = 运营 roadmap |

## 结论

- 这 10 个文件**全部不应留在 `lyric-mv-kit` 公开稳定线**（0 个 PUBLIC_PRODUCT_DOC）。
- 7 个归 music-board（业务页面 / 资源循环 / 宣传路线 / catalog 补丁）。
- 3 个归 skills / publisher owner（AI prompt、创作工具交接、上传交接）。
- 1 个作归档指针（handoff 索引）。
- 执行迁移前需保留每个文件的 recovery ref（指向原 commit），不得直接删除公开仓库历史证据。
