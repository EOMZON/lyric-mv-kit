# Handoff P2 — 官网新增 /lyric-studio 风格展示子页面

**维度**：在 `music.zondev.top` 新增一个独立子页面 `/lyric-studio`，专门展示歌词排版
MV 的 8 种视觉风格（A–H），让访客直观看到「同一首歌、8 种排版」，并引导他们去
GitHub 仓库 `lyric-mv-kit` 做自己的风格。

---

## 现状事实（精确，新对话无需重探）

- 仓库：`D:/ZON/codex/music-board`，纯静态 SPA，Vercel，push main 即上线。
- 路由：hash 模式，分发逻辑在 `app.js` 约 1040–1095 行（`parseRoute` + `buildHash`）。
  现有 route：`home / collections / tracks / notes / stats / platform / topic / collection / track`。
  **新增 route 只需**：在 `parseRoute` 加 `if (parts[0] === "lyric-studio") return { route: "lyric-studio" };`，
  在 `buildHash` 加对应分支，并在主渲染分发处 `if (route === "lyric-studio") renderLyricStudio();`。
- 展示素材（已在 GitHub 仓库 `lyric-mv-kit`）：
  - `showcase/styles/A_editorial_air.png … H_prism_kaleidoscope.png`（8 张 1920×1080 静帧）
  - `showcase/cover.png`（4:3 封面）
  - `showcase/README.md`（风格说明）
  - 8 套风格键名与中文标签见 `lyric-mv-kit/lyric_mv/styles.py`：
    `A_editorial_air 编辑留白`、`B_album_sleeve 唱片内页`、`C_cinematic_letterbox 电影黑边`、
    `D_kinetic_poster 动力海报`、`E_neon_bloom 霓虹绽放`、`F_aurora_ribbon 极光飘带`、
    `G_terminal_glitch 终端故障`、`H_prism_kaleidoscope 棱镜万花筒`。
- 参考风格数据集（建议内联到新页面，避免跨域拉取）：可直接在 `app.js` 写死一个
  `LYRIC_STYLES = [{key, zh, en, img}]` 数组，图片用**相对路径**或**来自 lyric-mv-kit 的
  GitHub Pages / raw 链接**（见 P4 资源闭环：仓库可开启 Pages 或把 showcase 当静态资源）。
- 页面风格：站点用 CSS 变量调色板（`--surface / --line / --ink / --surface-soft` 等），
  新增区块应继承，不要硬编码颜色。

---

## 方案

1. **新增路由** `lyric-studio`，在 `parseRoute` / `buildHash` / 主分发三处加分支。
2. **新增 `renderLyricStudio()` 函数**：
   - 顶部：一句话定位（「同一首歌，8 种排版」）+ 跳转 GitHub 仓库的 CTA 按钮。
   - 网格：8 张卡片，每张 = 风格静帧 + 中文标签 + 一句话动效说明 + 「查看源码风格键」提示。
   - 底部：GitHub 仓库链接 + 「用 lyric-mv-kit 做你自己的风格」引导。
3. **导航入口**：在首页/顶栏加一个「歌词排版工作室」链接到 `#/lyric-studio`
   （具体位置读 `app.js` 的导航渲染函数，grep `nav` / `header` / `menu`）。
4. **图片资源策略**（与 P4 联动）：
   - 短期：把 8 张静帧复制到 `music-board` 仓库的 `assets/lyric-studio/`（随站部署）；
     或引用 `raw.githubusercontent.com/EOMZON/lyric-mv-kit/main/showcase/styles/*.png`。
   - 长期：见 P4——仓库开启 GitHub Pages，子页面走 Pages 域名，彻底解耦。

---

## 实施步骤

1. 读 `app.js` 路由分发三处（1040–1095 行 + 主渲染 switch），确认插入点。
2. 读导航渲染位置（grep `nav`/`header`），决定入口放哪。
3. 写 `renderLyricStudio()`：内联 `LYRIC_STYLES` 数组（key/zh/en + 图片路径），
   用站点既有卡片/网格 CSS class（grep 现有 `.card`/`.grid` 复用），不要新写一套样式体系。
4. 加路由三处分支 + 导航入口。
5. 本地 `python -m http.server` 自测：`#/lyric-studio` 渲染 8 卡、CTA 跳转、移动端响应式。
6. `git commit && git push origin main`；Vercel 上线后访问验证。

---

## 验收标准

- [ ] `#/lyric-studio` 可访问，展示 8 种风格静帧 + 标签 + 动效说明。
- [ ] 每张卡/页面有跳转 `https://github.com/EOMZON/lyric-mv-kit` 的入口。
- [ ] 顶栏/首页有进入该子页的导航。
- [ ] 移动端 + 桌面端响应式正常，风格继承站点调色板。
- [ ] 未引入新依赖；图片资源策略与 P4 一致（优先仓库内 `assets/` 或 raw.githubusercontent）。

---

## 可直接粘贴到新对话的 Prompt

```
给静态音乐站点 music.zondev.top（仓库 D:/ZON/codex/music-board，纯 SPA，Vercel，
push main 即上线）新增一个子页面 /lyric-studio，展示歌词排版 MV 的 8 种视觉风格。

要求：
1. 路由是 hash 模式，分发逻辑在 app.js 约 1040–1095 行（parseRoute + buildHash）。
   新增 route "lyric-studio"：在 parseRoute 加分支、buildHash 加分支、主渲染分发加
   if (route === "lyric-studio") renderLyricStudio();
2. 在 app.js 新增 renderLyricStudio()：内联一个 LYRIC_STYLES 数组（8 项，key/中文标签/
   英文标签/图片路径）。8 套风格键名见 https://github.com/EOMZON/lyric-mv-kit 的
   lyric_mv/styles.py：A_editorial_air 编辑留白、B_album_sleeve 唱片内页、
   C_cinematic_letterbox 电影黑边、D_kinetic_poster 动力海报、E_neon_bloom 霓虹绽放、
   F_aurora_ribbon 极光飘带、G_terminal_glitch 终端故障、H_prism_kaleidoscope 棱镜万花筒。
   静帧图：先引用 https://raw.githubusercontent.com/EOMZON/lyric-mv-kit/main/showcase/styles/<KEY>.png
   （如后续仓库开 Pages 再换域名）。
3. 页面结构：顶部一句定位「同一首歌，8 种排版」+ 跳 GitHub 仓库 CTA；中部 8 卡网格
   （静帧+中文标签+一句话动效）；底部再放 GitHub 仓库链接与「做你自己的风格」引导。
4. 在顶栏/首页加一个「歌词排版工作室」入口链接到 #/lyric-studio（grep app.js 的
   nav/header 渲染位置）。
5. 风格必须继承站点 CSS 变量调色板（--surface/--line/--ink/--surface-soft），复用现有
   .card/.grid class，不新建样式体系、不引入依赖。
6. 本地 python -m http.server 自测移动端+桌面端，再 git commit && git push origin main，
   并验证 #/lyric-studio 上线。

完成后回报新增的函数名、路由分支位置、以及上线验证结果。
```
