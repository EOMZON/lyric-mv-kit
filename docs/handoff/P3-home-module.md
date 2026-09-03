# Handoff P3 — 官网首页新增「歌词视频」模块 + 仓库引流

**维度**：在 `music.zondev.top` 首页新增一个醒目模块，展示歌词排版 MV（以《我拒绝被定义》
极光版为代表），并把访客引导到 GitHub 仓库 `lyric-mv-kit`「参考做自己的风格」。
这是**资源闭环的入口层**——首页是流量最大的页面，从这里把人导去仓库/子页面。

---

## 现状事实（精确，新对话无需重探）

- 仓库：`D:/ZON/codex/music-board`，纯静态 SPA，Vercel。
- **首页渲染**：主入口 `app.js` 约 8867 行 `if (route === "home")`；首页由一组
  `renderHomeXxx` 函数拼装（在 4925–5590 行区间），例如：
  - `renderHomeLeadCard` (4925)、`renderHomeHeroMiniCard` (4960)、
    `renderHomeLeadRail` (4973)、`renderHomeEditorialSection` (5028)、
    `renderHomeHeatList` (5045)、`renderHomeLatestCollections` (5091)、
    `renderHomePlatformLatestShelf` (5145)、`renderHomeTopicGroups` (5453)、
    `renderHomeThemes` (5504)、`renderHomePlatformBadges` (5574)、
    `renderHomeTimelineItem` (5590)。
  - `renderSection(title, sub, bodyHtml)`（3598 行）是通用区块容器，新增模块优先复用它。
- **依赖 P1/P2**：本模块要展示的视频播放器依赖 P1 的 embed 渲染（已在站点支持），
  要展示的 8 风格入口依赖 P2 的 `/lyric-studio` 子页面。建议**先完成 P1、P2**，
  再跑本 handoff；若并行，则本模块对 P1/P2 的产物用占位链接。
- 资源：
  - 代表视频：B站 `(待 P1 上传)` / YouTube `(待 YouTube 上传)`；封面可用
    `lyric-mv-kit/showcase/cover.png`。
  - 仓库：`https://github.com/EOMZON/lyric-mv-kit`。
  - 子页面：`#/lyric-studio`（P2 产出）。
- 风格：站点 CSS 变量调色板；新增区块继承，不硬编码颜色。

---

## 方案

1. **新增首页区块** `renderHomeLyricVideoSection()`，用 `renderSection` 包裹：
   - 标题：「歌词排版 MV」+ 副标「同一首歌，8 种排版」或「用开源工具做你自己的风格」。
   - 主体：左侧一个 16:9 代表视频播放器（B站/YouTube embed，复用 P1 的 embed 机制，
     或直接 iframe 一个公开视频）；右侧 2–3 张风格静帧缩略图，点击进 `/lyric-studio`。
   - CTA：按钮/链接「查看开源仓库 lyric-mv-kit →」指向 GitHub，以及「看全部风格 →」
     指向 `#/lyric-studio`。
2. **接入首页拼装**：在主 `route === "home"` 的渲染链里（约 8867 行附近），
   在合适位置（如 hero 之后、或「最新发行」之前）调用 `renderHomeLyricVideoSection()`。
3. **导航/可见性**：确保首页有该模块入口即可，无需额外路由（模块就在首页）。

---

## 实施步骤

1. 读 `app.js` 约 8867 行起的 home 渲染链，确认区块插入点与各 `renderHomeXxx` 的调用顺序。
2. 写 `renderHomeLyricVideoSection()`：内联代表视频 embed（占位 BV/id 先写死，
   真实值由 P1 回填） + 2–3 张静帧缩略（用 `raw.githubusercontent.com/EOMZON/lyric-mv-kit/
   main/showcase/styles/{F_aurora_ribbon,...}.png`） + 两个 CTA 链接。
3. 在 home 拼装处插入调用；确认不破坏既有区块顺序。
4. 本地 `python -m http.server` 自测：首页出现模块、播放器可播、CTA 跳转正确、响应式。
5. `git commit && git push origin main`；Vercel 上线后首页验证。

---

## 验收标准

- [ ] 首页出现「歌词排版 MV」模块，含代表视频播放器。
- [ ] 模块内可跳转 GitHub 仓库与 `/lyric-studio` 子页（P2）。
- [ ] 移动端 + 桌面端响应式正常，风格继承站点调色板。
- [ ] 未引入新依赖；与 P1/P2 产物衔接（视频/子页链接）。
- [ ] Vercel 上线后首页验证通过。

---

## 可直接粘贴到新对话的 Prompt

```
给 music.zondev.top（仓库 D:/ZON/codex/music-board，纯 SPA，Vercel，push main 即上线）
首页新增一个「歌词排版 MV」模块，把访客导去 GitHub 仓库 lyric-mv-kit 和 /lyric-studio 子页。

前置（若已完成）：P1 已在歌曲页渲染歌词 MV embed；P2 已新增 #/lyric-studio 子页。
（若未完成，视频/子页链接先用占位。）

要求：
1. 读 app.js 约 8867 行起的 if (route === "home") 渲染链，以及 4925–5590 行的
   renderHomeXxx 函数群；新增模块优先复用 renderSection(title, sub, bodyHtml)（3598 行）。
2. 新增 renderHomeLyricVideoSection()：
   - 标题「歌词排版 MV」+ 副标「同一首歌，8 种排版」；
   - 主体左侧一个 16:9 代表视频（B站用 player.bilibili.com/player.html?bvid= 或
     YouTube youtube.com/embed/<id>，先用占位 id），右侧 2–3 张风格静帧缩略
     （raw.githubusercontent.com/EOMZON/lyric-mv-kit/main/showcase/styles/<KEY>.png）；
   - 两个 CTA：「查看开源仓库 lyric-mv-kit →」跳 https://github.com/EOMZON/lyric-mv-kit，
     「看全部风格 →」跳 #/lyric-studio。
3. 在 home 渲染链合适位置（hero 之后）调用该模块；不破坏既有区块顺序。
4. 风格继承站点 CSS 变量调色板，复用现有 .card/.grid class，不引入依赖。
5. 本地 python -m http.server 自测移动端+桌面端，再 git commit && git push origin main，
   验证首页上线。

完成后回报新增函数名、插入位置、上线验证结果。
```
