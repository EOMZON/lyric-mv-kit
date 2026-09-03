# 多对话执行提示词总表（复制即用）

> 官网侧共需 **4 个新对话**（P1 → P2 → P3 → P4，顺序不可乱，P4 必须最后）。
> YouTube 真实上传**不需要新对话**——在当前对话完成登录后由 AI 直接执行。
> 每段提示词都自包含（路径、行号、约束、验收标准已写死），新建对话后整段粘贴即可。

## 执行顺序与依赖

| 顺序 | 对话 | 依赖 | 产物 |
|------|------|------|------|
| 0 | YouTube 上传（当前对话即可） | 你完成一次性登录 | YouTube 视频 URL + video id |
| 1 | P1 歌曲页嵌入 | 无（链接可后补） | 歌曲页播放器 + 多渠道链接条 |
| 2 | P2 风格子页 | 无 | `#/lyric-studio` 上线 |
| 3 | P3 首页模块 | P1/P2 产物（占位可先行） | 首页「歌词排版 MV」模块 |
| 4 | P4 闭环回填 | **必须最后**：YouTube URL + B站 BV | README/简介/五端链接全部回填 |

---

## 对话 1：P1 歌曲页嵌入歌词视频

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
   （B站/YouTube/网易云/GitHub/官网，带图标、可点外链）。
4. 本地 python -m http.server 自测移动端+桌面端，再 git commit && git push origin main。
5. 用 curl -H "Cache-Control: no-cache" https://music.zondev.top/catalog.json 验证上线。

注意：只增不改已有 section，风格跟随站点调色板 CSS 变量；不引入新依赖。
完成后回报改动的文件、新增函数名、以及上线 URL 验证结果。
```

## 对话 2：P2 /lyric-studio 风格子页面

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

## 对话 3：P3 首页歌词视频模块

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

## 对话 4：P4 资源闭环回填（必须最后执行）

```
做「歌词排版 MV」的多平台资源闭环回填。固定资产：
- GitHub 仓库 https://github.com/EOMZON/lyric-mv-kit（README 中英双版在
  D:/ZON/codex/lyric-mv-kit/README.md 与 README.zh-CN.md）
- 官网 https://music.zondev.top
- 网易云单曲 https://music.163.com/#/song?id=3422948585
- YouTube 频道 https://www.youtube.com/@ROYAZONEOM
- B站视频链接 <填真实 BV> / YouTube 视频链接 <填真实 id>（来自上传结果）

任务：
1. 编辑 README.md 与 README.zh-CN.md 的「在哪看」资源矩阵，把 B站/YouTube 的
   「待上传」替换为真实公开链接（中英同步）。
2. 在 D:/ZON/workbuddy/music-video-demo/bili_v5/description.txt（B站中文简介）增加
   GitHub 仓库行 + YouTube 行；在 description.en.txt（YouTube 英文简介，已含仓库+官网+
   网易云）补 B站行。保持中英对称。
3. 网易云单曲简介手动在创作者后台编辑（不要为此做浏览器自动化）：挂官网+GitHub+视频。
   若无法自动，请把建议文案输出给我手动粘贴。
4. 输出一份「闭环巡检清单」：GitHub/B站/YouTube/网易云/官网 五端各自应含的链接，
   标注哪些已亮、哪些待我手动处理。

不要改动代码；只动文案与 README。完成后回报每处改动的内容摘要。
```
