# 交接文档：歌词 MV 上传 YouTube + 回填 music-board（P1/P4 收尾）

> 给接手的 AI 看的自包含说明。照着做即可，不需要追问背景。
> 目标：把《我拒绝被定义》歌词 MV 传上 YouTube 频道 `@ROYAZONEOM`，
> 拿到真实 video id，回填 `music.zondev.top` 歌曲页（消除 YouTube 占位符），
> 完成跨平台资源闭环（P1 + P4）。B站 部分**已完成**，无需再做。

---

## 0. 当前真实状态（已核实，别重复排查）

- 目标曲目：`netease-song-3422948585`《我拒绝被定义》（artist：音右 / ROYAZON）
- `music-board/catalog.json` 该曲 `embeds` 现状：
  - `netease` ✓（外链播放器）
  - `bilibili` ✓ → `https://player.bilibili.com/player.html?bvid=BV1zRtX6WE5q...`（**B站已完成**）
  - `youtube` ✗ → `https://www.youtube.com/embed/PLACEHOLDER_ID`（**占位符，待替换**）
- `links` 现状：`netease` + `github` + `official(site)` 都已存在。
- **结论：只差一个真实的 YouTube video id。** 拿到 id 后跑一次回填脚本即可，前端零改动。

---

## 1. 关键根因（别再踩这些死路）

Chrome 127+ 对登录态 cookie 做了 **应用绑定加密 (App-Bound Encryption, ABE)**：
Playwright 以「自动化子进程」拉起 Chrome 时，加密的 auth cookie
（`LOGIN_INFO` / `__Secure-1PSID` / `SAPISID`）会被**静默丢弃**。

**已实测失败的死路（不要再试）：**
- ❌ 把 `--profile` 指向真实的 `C:\Users\zonli\AppData\Local\Google\Chrome\User Data`
  → context 里只剩匿名 cookie（`YSC`/`VISITOR_INFO1_LIVE`/`PREF`），Studio 跳 Google 登录页。
- ❌ `robocopy` 复制 profile 到专用目录再用 → 同样跳登录页（ABE 跨目录解密失败）。
- ❌ `--single-process` → 直接崩 YouTube Studio（Polymer SPA）。

**两条能走通的路（二选一）：**
- **A. CDP 挂活浏览器（推荐，零登录）**：用户先全关 Chrome → 用调试口重开真实 Chrome
  → 脚本 `connect_over_cdp` 挂载，复用已在内存解密的会话。用户已在真实浏览器登录，无需再输密码。
- **B. 弹窗手动登录一次（bili 技能同款）**：脚本用真实 `chrome.exe` 拉起专用 profile，
  窗口里用户登一次，脚本轮询 `#channel-title` 自动续跑。

---

## 2. 环境事实（固定路径）

| 项 | 路径 |
|---|---|
| Python（含 playwright） | `C:/Users/zonli/.workbuddy/binaries/python/envs/default/Scripts/python.exe` |
| Chrome 可执行文件 | `D:\ZON\google\chrome-win64\chrome.exe` |
| 真实 User Data | `C:\Users\zonli\AppData\Local\Google\Chrome\User Data` |
| 专用 profile（路径 B 用） | `D:/ZON/google/youtube-chrome-data` |
| 一键启动器（路径 A 用） | `D:\ZON\google\launch_chrome_debug.bat` |
| 上传脚本 | `C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/scripts/upload_video.py` |
| 上传清单 | `D:/ZON/workbuddy/music-video-demo/bili_v5/manifest.youtube.json` |
| 证据/状态目录 | `D:/ZON/workbuddy/music-video-demo/bili_v5`（截图在 `evidence/`，状态在 `youtube-run-state.json`） |
| 回填脚本 | `D:/ZON/codex/music-board/scripts/backfill_lyric_mv_links.py` |
| catalog | `D:/ZON/codex/music-board/catalog.json` |
| 目标曲 id | `netease-song-3422948585` |

链接资产：GitHub `https://github.com/EOMZON/lyric-mv-kit` · 官网 `https://music.zondev.top` ·
YouTube 频道 `https://www.youtube.com/@ROYAZONEOM` · B站 BV `BV1zRtX6WE5q`（已填）。

---

## 3. 执行步骤

### 步骤 0 — 前置：确保 Chrome 完全关闭
```bat
tasklist | findstr /I chrome
```
若还有进程，先全部退出（含托盘图标）。**路径 A 尤其必须**，否则调试口不会绑到新实例。

### 步骤 1 — 选登录方式并触发上传（首跑默认 private）

**路径 A（推荐，零登录）：**
1. 双击运行 `D:\ZON\google\launch_chrome_debug.bat`
   （作用：用 `--remote-debugging-port=9222` 重开真实 profile）。
2. 等 Chrome 打开，确认 YouTube 是登录态（右上角头像/频道）。
3. 运行上传（**不要加任何可见性参数，默认 private**）：
```bat
C:/Users/zonli/.workbuddy/binaries/python/envs/default/Scripts/python.exe ^
  C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/scripts/upload_video.py ^
  --manifest D:/ZON/workbuddy/music-video-demo/bili_v5/manifest.youtube.json ^
  --project-dir D:/ZON/workbuddy/music-video-demo/bili_v5 ^
  --cdp http://127.0.0.1:9222 --apply
```

**路径 B（弹窗登一次）：**
```bat
C:/Users/zonli/.workbuddy/binaries/python/envs/default/Scripts/python.exe ^
  C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/scripts/upload_video.py ^
  --manifest D:/ZON/workbuddy/music-video-demo/bili_v5/manifest.youtube.json ^
  --project-dir D:/ZON/workbuddy/music-video-demo/bili_v5 ^
  --profile D:/ZON/google/youtube-chrome-data --wait-for-login --apply
```
窗口弹出后，在浏览器里登录 YouTube，脚本轮询到 `#channel-title` 自动续跑（默认 300s 超时）。

### 步骤 2 — 拿到 video id
上传成功会打印：
```
[apply] done. video_id=XXXXXXXXXXX url=https://www.youtube.com/watch?v=XXXXXXXXXXX
```
并写入 `D:/ZON/workbuddy/music-video-demo/bili_v5/youtube-run-state.json`（`video_id` / `video_url` 字段）。
记下这个 11 位 id（下文记为 `<VID>`）。

> ⚠️ 首跑**必须停在 private**。公开化要等用户确认后单独再跑一次（见步骤 6）。

### 步骤 3 — 回填 music-board（P1，消除占位符）
```bat
cd /D D:/ZON/codex/music-board
C:/Users/zonli/.workbuddy/binaries/python/envs/default/Scripts/python.exe ^
  scripts/backfill_lyric_mv_links.py ^
  --track netease-song-3422948585 --youtube-id <VID> --with-github-site --apply
```
脚本幂等、dry-run 默认。它会：把 `embeds` 里 platform=`youtube` 的占位条目替换为
`https://www.youtube.com/embed/<VID>`，并补 `links` 的 youtube 观看链；
保留已有的 netease / bilibili / github / site。先不加 `--apply` 跑一次看 `[plan]` 确认无误。

### 步骤 4 — 提交并验证上线
```bat
cd /D D:/ZON/codex/music-board
git add catalog.json
git commit -m "feat(song): wire real YouTube lyric-MV id for 我拒绝被定义"
git push
```
push main = Vercel 自动部署。部署后验证：
```bat
curl -H "Cache-Control: no-cache" https://music.zondev.top/catalog.json
```
grep 该曲，确认 `embeds` 里 youtube 的 url 已变成真实 `https://www.youtube.com/embed/<VID>`，
且线上歌曲页渲染出 YouTube iframe + 观看链、无破损 iframe。

### 步骤 5 —（可选）公开化
用户在 YouTube Studio 确认 private 视频无误后，再跑一次上传把它转公开：
```bat
C:/Users/zonli/.workbuddy/binaries/python/envs/default/Scripts/python.exe ^
  C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/scripts/upload_video.py ^
  --manifest D:/ZON/workbuddy/music-video-demo/bili_v5/manifest.youtube.json ^
  --project-dir D:/ZON/workbuddy/music-video-demo/bili_v5 ^
  --cdp http://127.0.0.1:9222 --apply --visibility public --authorize-publish
```
（依赖 `youtube-run-state.json` 续传，不会重新上传字节；必须显式带 `--authorize-publish`。）

### 步骤 6 — P4 资源闭环
该曲的跨平台互链（B站 / YouTube / GitHub / 官网 / 网易云）由步骤 3 的回填脚本覆盖。
更宏观的「首页资源闭环 / 引流」见 `lyric-mv-kit/docs/handoff/PROMPTS.md` 的 P4 段；
P2（`/lyric-studio` 子页）按记忆已上线，P3（首页模块）如未做可参考同目录 PROMPTS.md。

---

## 4. 验收标准（Done）

- [ ] `youtube-run-state.json` 含有效 `video_id`（11 位）与 `video_url`。
- [ ] `catalog.json` 该曲 `embeds` 的 youtube url = `https://www.youtube.com/embed/<VID>`（无 PLACEHOLDER）。
- [ ] 线上 `music.zondev.top` 该曲页渲染出 YouTube iframe + 观看链，无破损。
- [ ] B站（BV1zRtX6WE5q）维持原样不丢失。
- [ ] （如用户要求公开）YouTube 视频转 public 且 Studio 可见。

---

## 5. 排错速查

- **上传脚本报未登录 / 跳登录页**：ABE 导致专用 profile 永不在登录态。
  路径 A 请确认 Chrome 是用 `launch_chrome_debug.bat` 重开的（访问 `http://127.0.0.1:9222/json` 能返回 JSON 即说明调试口生效）；
  路径 B 请在弹窗里手动登录一次。
- **`connect_over_cdp` 连不上 9222**：Chrome 没带调试口启动（多半是没先关旧 Chrome，新实例把命令行转交旧进程了）。
  关干净 Chrome 再跑一次启动器。
- **上传卡在进度 / 选择器找不到**：YouTube Studio 是 Polymer SPA，选择器偶尔漂移；
  脚本已对每个步骤截图留证到 `bili_v5/evidence/yt_*.png`，按截图定位。
- **回填脚本报 `nothing to do`**：确认传了 `--youtube-id <VID>`（或 `--bilibili-bv` / `--with-github-site` 之一）。
- **catalog 改了但线上没变**：Vercel 部署有延迟；用 `curl -H "Cache-Control: no-cache"` 强制绕过缓存再看，并确认 `git push` 已成功。
