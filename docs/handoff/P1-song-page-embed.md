# Handoff P1 — 官网歌曲页嵌入歌词视频 + 多渠道链接

**维度**：在 `music.zondev.top` 的歌曲页（`#/c/netease-album-393291196?track=netease-song-3422948585`）
展示《我拒绝被定义》的歌词 MV，并把所有分发渠道（B站 / YouTube / 网易云 / GitHub 仓库 / 官网）
以可点的形式陈列出来。

---

## 现状事实（精确，新对话无需重探）

- 仓库：`D:/ZON/codex/music-board`，纯静态 SPA，Vercel，push main 即上线。
- 数据：`catalog.json`，顶层 `{profile, items[]}`。目标 track 的 item：
  ```json
  {
    "id": "netease-song-3422948585",
    "title": "我拒绝被定义",
    "artist": "音右",
    "collectionId": "netease-album-393291196",
    "embeds": [...],          // ← 视频嵌入字段已存在，复用它
    "links":  [...],          // ← 平台外链字段已存在，复用它
    "lyrics": "...", "tags": [...], "refs": [...]
  }
  ```
- 歌曲页渲染入口：`app.js` 路由 `route === "track"` / `route === "collection"`，
  **实际渲染在 `app.js` 约 8601–8867 行**（含 `route === "track"` 与 `route === "collection"`
  两套分支）。`renderPrimarySourcePanel(track, source)` 在 3106 行，`renderModal` 在 3177 行。
- **关键利好**：站点**已完整支持**视频嵌入与多渠道链接，无需写新渲染函数：
  - 视频嵌入：`pickEmbed(item)`（`app.js` 2699 行）从 `item.embeds` 取嵌入，
    collection 页已在 `app.js` ~864 行渲染为 `collectionEmbed`（`const collectionEmbed = pickEmbed(c);`）。
  - 平台链接条：`renderPlatformIcons(links, limit)`（`app.js` 947 行）从 `item.links` 渲染图标。
  - track/collection 构建：`trackFromItem` / `collectionFromItem`（~1858/1882 行）已把
    `item.embeds` / `item.links` 透传到前端模型。
  - 结论：**P1 主要是 catalog.json 数据回填 + 确认渲染**，前端改动极小甚至为零。
- **先读**：`pickEmbed`（2699 行）确认 `embeds` 元素的 schema（platform/bvid/id/url 形态），
  以及 `renderPlatformIcons`（947 行）确认 `links` 元素的 schema（platform/url 形态），
  严格按现有 schema 填，不要发明新字段。
- 参考视频链接（本轮对话产出，上传后回填）：
  - B站：`(待上传)`
  - YouTube：`(待上传)`
  - 网易云单曲：`https://music.163.com/#/song?id=3422948585`
  - GitHub 仓库：`https://github.com/EOMZON/lyric-mv-kit`
  - 官网：`https://music.zondev.top`

---

## 方案

**首选（最小改动）**：纯数据回填。站点已从 `item.embeds`（经 `pickEmbed`）渲染视频、
从 `item.links`（经 `renderPlatformIcons`）渲染渠道图标。只要按现有 schema 在
`catalog.json` 的参考歌曲 item 上填 `embeds`（B站 bvid + YouTube id）与 `links`
（B站/YouTube/网易云/GitHub/官网），歌曲页即自动出现播放器与渠道条，**前端零改动**。

**仅当现有渲染不满足时**（例如要并排 B站+YouTube 双播放器、或要在歌词上方固定一个
"歌词 MV"专区）才在前端加轻量区块：用 `renderSection(title, sub, bodyHtml)`（3598 行）
包裹，风格跟随站点 CSS 变量，只增不改。

1. **视频嵌入**：在 `track.embeds` 加 `{platform:"bilibili", bvid:"<BV>"}` 与
   `{platform:"youtube", id:"<videoId>"}`，交由已有 `pickEmbed` 渲染 16:9 播放器。
2. **多渠道链接条**：在 `track.links` 补 5 个 `{platform, url}`，交由已有
   `renderPlatformIcons` 渲染图标行。
3. **数据回填**：把真实视频 id 写进 `catalog.json` 目标 item；缺失字段补齐。
4. **不破坏现有渲染**：除非必要，不新增前端函数。

---

## 实施步骤

1. 读 `app.js` 约 8601–8867 行，弄清 track 页 DOM 结构与被调用的子渲染函数；
   同时 grep `embeds` 找到现有消费逻辑与 schema（这是避免重复造字段的关键）。
2. 写一个小脚本或直接编辑 `catalog.json`，给 `netease-song-3422948585` 的 `embeds`
   加 `{platform:"bilibili", bvid:"<BV>"}` 与 `{platform:"youtube", id:"<videoId>"}`；
   给 `links` 补 `{platform:"github", url:"https://github.com/EOMZON/lyric-mv-kit"}` 等。
3. 在 track 渲染函数里，紧邻 `renderPrimarySourcePanel` 调用之后，插入
   `renderLyricVideoBlock(track)`（新增函数，读取 `embeds` 生成播放器 + 链接条）。
4. 本地起静态服务器自测：`python -m http.server` 于 music-board 根目录，
   打开 `http://localhost:8000/#/c/netease-album-393291196?track=netease-song-3422948585`，
   确认播放器与链接条渲染正确、响应式、不遮挡歌词。
5. `git commit` + `git push origin main`；等 Vercel 部署完成，用
   `curl -H "Cache-Control: no-cache" https://music.zondev.top/catalog.json` 验证已上线。
6. 把真实 B站/YouTube 链接回填本 handoff 顶部「参考视频链接」。

---

## 验收标准

- [ ] 参考歌曲页出现 16:9 歌词 MV 播放器，可播放。
- [ ] 页内出现 B站 / YouTube / 网易云 / GitHub / 官网 五个可点渠道。
- [ ] 移动端与桌面端均正常（响应式）。
- [ ] `catalog.json` 改动最小，复用既有 `embeds`/`links` 字段。
- [ ] Vercel 上线后真实 URL 可访问，缓存已刷新。

---

## 可直接粘贴到新对话的 Prompt

```
我要给静态音乐站点 music.zondev.top（仓库 D:/ZON/codex/music-board，纯 SPA，Vercel，
push main 即上线）的歌曲页加「歌词 MV 播放器 + 多渠道链接条」。

目标歌曲：网易云单曲《我拒绝被定义》音右，track id = netease-song-3422948585，
collection id = netease-album-393291196，页面路由 #/c/netease-album-393291196?track=netease-song-3422948585。

要求：
1. 先读 app.js 约 8601–8867 行（route==="track"/"collection" 的实际渲染入口），
   以及 grep `embeds` 找出 catalog item 现有 embeds/links 字段的 schema 与消费逻辑——
   不要新建字段，复用 embeds（视频）和 links（外链）。
2. 在目标 item（catalog.json 中 id="netease-song-3422948585"）的 embeds 加上
   B站与 YouTube 嵌入（真实 id 待我提供，先用占位），links 补 GitHub 仓库
   https://github.com/EOMZON/lyric-mv-kit 与官网 https://music.zondev.top。
3. 在 track 渲染函数里插入一个新的 renderLyricVideoBlock(track)：读取 embeds 渲染
   16:9 响应式播放器（B站用 player.bilibili.com/player.html?bvid=，YouTube 用
   youtube.com/embed/<id>），并用 renderSection 包一个多渠道链接条
   （B站/YouTube/网易云/ GitHub/官网，带图标、可点外链）。
4. 本地 python -m http.server 自测移动端+桌面端，再 git commit && git push origin main。
5. 用 curl -H "Cache-Control: no-cache" https://music.zondev.top/catalog.json 验证上线。

注意：只增不改已有 section，风格跟随站点调色板 CSS 变量；不引入新依赖。
完成后回报改动的文件、新增函数名、以及上线 URL 验证结果。
```
