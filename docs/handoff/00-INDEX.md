# Handoff Index — 歌词排版 MV 资源闭环

> 这是一组**自包含的拆分方案文档**。每个文件都可以整体复制、粘贴进一个**全新的对话**，
> 让 AI 在不依赖本对话上下文的情况下独立推进。这正是「多对话实现」的落地方式。

---

## 关于「开新对话的能力」

**我没有主动开启新对话的权限**——对话由你在客户端创建，我只能在一个对话内工作。
但每个 handoff 文件末尾都带一段 **「可直接粘贴到新对话的 Prompt」**，它把目标、现状事实
（精确路径 + 关键发现）、约束、验收标准都写死了。你新建对话后粘贴过去，等价于我在那个
对话里从头接手，且上下文零丢失。

建议节奏：**一次只开一个对话跑一份 handoff**，跑完把结果回填到本文档的「状态」列。

---

## 资源闭环总图

```
        ┌──────────────────────────────────────────────────────────┐
        │                                                            │
   ┌────▼─────┐        ┌──────────────────┐        ┌───────────────▼────┐
   │ GitHub   │◄───────┤  music.zondev.top │───────►│     B站 (中文)      │
   │ lyric-mv │   官网 │  官网(Vercel SPA) │   官网  │   《我拒绝被定义》  │
   │ -kit     │◄───────┤  catalog.json    │───────►│   极光歌词 MV       │
   └────▲─────┘   引流 │  + 歌词视频模块  │   视频  └───────────────▲────┘
        │        │    │  + /lyric-studio  │        │                 │
        │  仓库   │    └────────┬─────────┘        │  视频描述里挂     │
        │  地址   │             │ 歌曲页嵌入歌词视频 │  GitHub + 官网    │
        └────────┘             ▼                  │                 │
   ┌────▼─────┐        ┌──────────────────┐        │                 │
   │ YouTube  │◄───────┤  网易云音乐单曲   │────────┘                 │
   │ (英文)   │   回链  │  song 3422948585 │                          │
   └──────────┘        └──────────────────┘                          │
        ▲                                                              │
        └──────────── 视频简介挂 YouTube + 官网 + 仓库 ────────────────┘
```

闭环的每一段都是「平台 A 的页面/简介里出现平台 B 的链接」。缺任何一段，闭环就断。

---

## 文档清单与状态

| 文件 | 维度 | 状态 | 依赖 |
|------|------|------|------|
| **(本轮已交付)** YouTube 上传 | 自动化发布渠道 | ✅ skill + 脚本 + dry-run + 16:9 封面 | 真实上传待你授权触发 |
| `P1-song-page-embed.md` | 官网歌曲页嵌入歌词视频 + 多渠道 | ⬜ 待新对话 | catalog schema、track 渲染函数 |
| `P2-lyric-studio.md` | 官网新增 /lyric-studio 风格子页面 | ⬜ 待新对话 | showcase/ 静帧 + 风格元数据 |
| `P3-home-module.md` | 官网首页新增歌词视频模块 + 仓库引流 | ⬜ 待新对话 | P1/P2 的产物 |
| `P4-resource-loop.md` | 仓库 ↔ 官网 ↔ 各平台链接闭环 | ⬜ 待新对话 | P1–P3 + YouTube 上传结果 |

---

## 通用前置事实（每个新对话都应先读这些）

- **官网仓库**：`D:/ZON/codex/music-board`（origin `git@github.com:EOMZON/music-board.git`）
  - 纯静态 SPA，Vercel 部署，`git push origin main` 即上线。
  - 数据驱动：`catalog.json`（顶层 `{profile, items[]}`，items 共 1298 条）。
  - 路由：hash 模式，分发逻辑在 `app.js` 约 1066 行 `parts[0] === "c"` 等分支；
    `buildHash()` 在同文件下方。route 含 `home / collections / tracks / notes / stats /
    platform / topic / collection / track`。
  - 参考歌曲页 URL：`https://music.zondev.top/#/c/netease-album-393291196?track=netease-song-3422948585`
- **歌词 MV 仓库**：`D:/ZON/codex/lyric-mv-kit`（origin `git@github.com:EOMZON/lyric-mv-kit.git`）
  - 展示素材：`showcase/cover.png` + `showcase/styles/{A..H}.png` + `showcase/README.md`
  - 8 套风格元数据见 `lyric_mv/styles.py` 的键名（A_editorial_air … H_prism_kaleidoscope）。
- **YouTube 上传 skill**：`C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/`
  - 真实上传：`python scripts/upload_video.py --manifest <m> --apply`
    （首次需 `auth_login.py` 登录，停在 private，再 `--visibility public --authorize-publish`）。
- **参考歌曲固定标识**：
  - 网易云单曲：`https://music.163.com/#/song?id=3422948585`
  - 网易云专辑 collection id：`netease-album-393291196`，track id：`netease-song-3422948585`
- **字体/渲染环境**：`D:/ZON/runtime/miniforge3/envs/rvc/python.exe`（Pillow/numpy）；
  ffmpeg/ffprobe：`D:/ZON/runtime/media-tools/Library/bin/`。
- **品牌站**：`https://music.zondev.top`。

> 任何一份 handoff 的新对话 Prompt 都已内联上述关键事实，无需你再口述。
