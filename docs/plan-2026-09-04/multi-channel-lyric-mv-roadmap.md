# ROYAZON 多渠道歌词 MV 路线图（2026-09-04）

## 已验证的基线

- B站：《我拒绝被定义》，`BV1zRtX6WE5q`。
- YouTube：《I Refuse To Be Defined — Aurora Kinetic Lyric MV ｜ ROYAZON》，`rxPFQV7zfMg`，已公开并通过匿名访问验证。
- YouTube 成功路径是复用用户已登录的真实 Chrome，经 Codex/ChatGPT Chrome 扩展操作 YouTube Studio；关键前置是扩展开启 **Allow access to file URLs**。不需要复制 Cookie、关闭 Chrome 或新建浏览器 profile。
- 本次测试曲只有网易云链接，证明了视频生产和发布能力，但不是后续商业推广的最优选曲范式。

## 长期 Skill 架构

`video-publication-pipeline` 是跨渠道总控；它持有统一 manifest、渠道矩阵、状态与恢复点。

- `bili-publication-pipeline`：保留为兼容入口与 B站工作流，不硬改名。
- `bili-video-publish` / `bili-comment-publish`：B站平台动作。
- `youtube-publication-pipeline`：YouTube 上传、公开状态、匿名验证和恢复。
- `video-content-manifest`：共享事实、标题、简介、章节、标签及渠道变体。
- `netease-album-upload` / `music-board-netease-album-sync`：网易云发布与回填。
- `distrokid-album-upload` / `music-board-distrokid-album-sync`：全球分发与回填。
- 未来抖音、小红书分别新增平台 Skill；在真实跑通前不把假定流程写进总控。

## 选曲模型：先解决“到哪里听”，再决定“怎么画”

歌曲进入量产队列前，按以下门槛排序：

1. 网易云与全球 DSP 均已发布，且本地 catalog 有可验证的稳定链接。
2. 歌曲身份唯一，能区分同名歌、不同专辑和版本。
3. 母带、歌词、版权来源、封面素材完整。
4. 有适合的视觉模板，且能补足近期内容的风格多样性。
5. 最后再按传播潜力、时长和系列编排排序。

平台状态必须区分：`not_distributed`、`pending_release`、`pending_sync`、`unverified`、`verified`。DistroKid 页面显示 “Submitted to” 只证明已提交，不能当作歌曲在 Spotify、Apple Music、YouTube Music 等平台已经公开，更不能自动生成猜测链接。

当前本地 catalog 按规范化歌名交叉统计，有约 **154 首**同时出现于网易云与 DistroKid/全球分发数据，可作为候选池；真正进入发布队列前仍需逐首校验 canonical track URL。已有较完整多平台链接的首批候选包括 `Cha-Cha Groove`、`Cha-Cha Heat`、`Neon Snow`、`Tropical Beat`；中文候选可从《比昨天勇敢一点》《别问后来先开麦》《成长》《除夕旧去新来》《纯真告白》等继续核验。

《我拒绝被定义》在 catalog 中有两个网易云同名记录，必须用稳定 ID 锁定本次版本：`netease-song-3422948585`（专辑《在场的人》），不可只按歌名更新。

## 每支视频的链接闭环

发布前生成同一事实源、不同渠道文案：

- YouTube：全球 DSP 智能链接或已验证单曲链接、官网、B站对应视频、开源仓库（适用时）。
- B站：网易云、官网、YouTube 对应视频、开源仓库（适用时）。
- 官网/catalog：网易云、Spotify、Apple Music、YouTube Music、B站视频、YouTube 视频等已验证入口。

上传适配器只返回平台 ID、URL、状态和证据；catalog 由同步适配器单独写入，避免多个任务同时改大文件。

## 模板现状与分类

当前不是“没有模板”，而是“探索模板与生产引擎没有合流”：

- Python/Pillow 探索栈已有 A–N 共 14 种视觉风格和 11 种动效包，静态样图较完整。
- Remotion 生产栈能稳定生成成片，但当前主要是一个黑底居中歌词模板加 5 组配色。
- 因此，已渲染不等于已形成 14 套可量产模板；参考图、实现、动态样片、用户批准是四种不同状态。

建议把模板登记为以下 8 个可理解的产品族，并为每个模板记录稳定 ID、引擎、横竖屏比例、可读性约束、动效密度、样片和批准状态：

1. 编辑留白 / 杂志排版（A、B、L）。
2. 电影字幕 / 黑边叙事（C）。
3. 动态海报 / 强节拍（D、I）。
4. 霓虹 / 故障科技（E、G）。
5. 极光 / 氛围飘带（F，已由《我拒绝被定义》验证）。
6. 棱镜 / 万花筒（H）。
7. 国风书写 / 水彩宣纸（J）。
8. 日落手写、星野、奶油波点等情绪插画系（K、M、N）。

视觉风格、歌词动效、运镜继续三层解耦。先为每一族做 20–30 秒动态样片并评审；批准后才渲整首。不要先一次性把 14 套全部迁移，否则会重复昨天“两套引擎都做了、成片仍只有一种”的问题。

## 推荐推进顺序

### P0：曲目覆盖矩阵

产出一张稳定的歌曲清单：唯一 work ID、网易云状态、DistroKid release、各 DSP canonical URL、歌词/母带状态、可选模板。先从约 154 首交集候选中核验 10–20 首。

### P1：模板合流试点

从风格跨度最大的 4 族各选 1 个做 Remotion 动态样片：编辑浅色、泼墨强节拍、日落手写、星野极简。保留已验证的极光作为第 5 个基准。评审后再决定其余风格是迁移到 Remotion，还是保留在 Pillow 做专用渲染。

### P2：批量生产器

把“选歌 → 锁定版本 → 选择模板 → 生成 plan → 短样片 → 审批 → 整片 → QA → 两渠道发布 → 链接回填”固化成 manifest 驱动的批处理；同一歌曲的音频文件名必须唯一，避免并行渲染覆盖。

### P3：展示与开源

官网展示“视觉参考、动态样片、已批准模板、实际成片”四种状态；开源仓库只承诺已经实现并可复现的模板，不把静态参考图写成已支持功能。

## 建议拆分为 3 个独立任务

1. **全平台歌曲覆盖矩阵**：只负责身份去重、平台状态与 canonical URL；不渲视频。
2. **歌词模板合流与动态评审**：只负责 4+1 个试点模板、动态样片和统一引擎决策；不上传平台。
3. **多渠道批量发布器**：消费已批准曲目与模板，执行 QA、B站/YouTube 发布、链接回填和证据归档。

三项可以分别推进，但依赖顺序是：覆盖矩阵与模板试点可并行，批量发布器在两者各有首批批准结果后开始。

## 当前不要做的事

- 不干预正在运行的 50 首网易云上传任务。
- 不把 DistroKid 的 Submitted 状态当作已上线。
- 不按歌名模糊更新同名歌曲。
- 不批量渲染未通过动态样片评审的 14 套风格。
- 不同时让多个任务直接写 `music-board/catalog.json`。
