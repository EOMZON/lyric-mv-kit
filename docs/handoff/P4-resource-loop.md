# Handoff P4 — 资源闭环（仓库 ↔ 官网 ↔ B站 ↔ YouTube ↔ 网易云）

**维度**：把「歌词排版 MV」在各平台的入口互相挂接，形成可自循环的分发网络。
任何一个触点的访客，都能顺藤摸到其他所有触点，最终沉淀到 **GitHub 仓库**（开源复用）
或 **music.zondev.top**（官方聚合）。

---

## 闭环的每一段（缺一段即断）

| 从 → 到 | 挂载点 | 当前状态 |
|---------|--------|----------|
| GitHub → B站/YouTube | `README.md` / `README.zh-CN.md` 资源矩阵 | ✅ 已留位（链接待 P1 上传后回填） |
| GitHub → 官网 | README 资源矩阵 | ✅ 已挂 `music.zondev.top` |
| 官网 → GitHub | 歌曲页渠道条(P1) / /lyric-studio(P2) / 首页模块(P3) | ⬜ 随 P1–P3 落地 |
| 官网 → B站/YouTube | 歌曲页播放器(P1) | ⬜ 随 P1 |
| B站 → GitHub/官网 | 视频简介 `description.txt` | ⬜ 待回填（见下） |
| B站 → YouTube | 视频简介互链 | ⬜ 待回填 |
| YouTube → GitHub/官网 | 视频简介 `description.en.txt` | ✅ 已含 GitHub + 官网（见 `bili_v5/description.en.txt`） |
| YouTube → B站 | 视频简介互链 | ⬜ 待回填 |
| 网易云 → GitHub/官网/视频 | 单曲简介/评论 | ⬜ 待回填 |

---

## 现状事实（精确）

- **GitHub 仓库**：`D:/ZON/codex/lyric-mv-kit`，README 中英文双版已含资源矩阵占位
  （B站/YouTube 链接写「待上传」）。
- **YouTube 简介已就绪**：`D:/ZON/workbuddy/music-video-demo/bili_v5/description.en.txt`
  已含 GitHub 仓库 + 官网 + 网易云链接（英文受众）。
- **B站简介待补**：`D:/ZON/workbuddy/music-video-demo/bili_v5/description.txt`
  目前含网易云 + 官网，**缺 GitHub 仓库链接**，且未提 YouTube（因当时 YouTube 未做）。
- **网易云单曲**：`https://music.163.com/#/song?id=3422948585`；
  简介/评论编辑在网易云创作者后台（需手动或浏览器自动化，见下方注意）。
- **YouTube 上传 skill**（本轮已建）：`C:/Users/zonli/.workbuddy/skills/youtube-publication-pipeline/`
  manifest：`bili_v5/manifest.youtube.json`（已指向 16:9 封面 + 英文简介 + 真实成片）。
- 固定链接资产：
  - 仓库：`https://github.com/EOMZON/lyric-mv-kit`
  - 官网：`https://music.zondev.top`
  - B站（待上传）/ YouTube（待上传）

---

## 方案与步骤

### A. 回填 GitHub README 资源矩阵（P1 上传后立即做）
- 在 `README.md` 与 `README.zh-CN.md` 的「Reference song & 在哪看」表，把 B站/YouTube
  的「待上传」替换为真实公开链接。一次编辑，中英双版同步。

### B. 补 B站视频简介（上传 B站草稿时或之后改）
- 在 `bili_v5/description.txt` 增加一行 GitHub 仓库链接 + 一行 YouTube 链接
  （中文受众，与英文简介对称）。重新渲染/编辑 B站草稿简介时带入。

### C. YouTube 简介互链（已含仓库+官网，补 B站）
- `description.en.txt` 已含 GitHub + 官网 + 网易云；补一行 B站链接即可（若 B站先于
  YouTube 上传，则 YouTube 简介加 B站；若反之则 B站加 YouTube）。

### D. 网易云单曲简介/评论
- 手动在网易云音乐创作者后台编辑单曲简介，挂：官网 + GitHub 仓库 + （B站/YouTube 视频）。
- **注意**：网易云后台自动化风险高（账号风控），建议手动编辑或仅用评论区引导，
  不要为此新建浏览器自动化 skill。

### E. 官网侧（由 P1–P3 自动完成）
- P1 歌曲页渠道条、P2 /lyric-studio、P3 首页模块均已含 GitHub/官网/视频互链，
  本 handoff 只需在 P1–P3 落地后做一次**闭环巡检**（见验收）。

---

## 验收（闭环巡检清单）

- [ ] GitHub README（中/英）资源矩阵：B站、YouTube、网易云、官网 四链全亮，无「待上传」。
- [ ] B站视频简介：含 GitHub 仓库 + 官网 + YouTube（或反向互链）。
- [ ] YouTube 视频简介：含 GitHub 仓库 + 官网 + 网易云 + B站。
- [ ] 网易云单曲简介/评论：含官网 + GitHub + 视频链接。
- [ ] 官网：歌曲页可播视频 + 渠道条；/lyric-studio 可进；首页有歌词视频模块且链仓库。
- [ ] 任选一个触点进入，能不丢链路地走到 GitHub 仓库与官网（人工走查一遍）。

---

## 可直接粘贴到新对话的 Prompt

```
做「歌词排版 MV」的多平台资源闭环回填。固定资产：
- GitHub 仓库 https://github.com/EOMZON/lyric-mv-kit（README 中英双版在
  D:/ZON/codex/lyric-mv-kit/README.md 与 README.zh-CN.md）
- 官网 https://music.zondev.top
- 网易云单曲 https://music.163.com/#/song?id=3422948585
- B站视频链接 <填真实 BV> / YouTube 链接 <填真实 id>（来自 P1 上传结果）
- YouTube 频道 https://www.youtube.com/@ROYAZONEOM

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
