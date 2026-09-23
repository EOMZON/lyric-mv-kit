# lyric-mv-kit / MV 主线全盘复盘与目标对账（2026-09-23）

> 范围：本仓是治理执行主体；跨仓信息只纳入会直接影响 lyric-mv-kit 原始目标的证据。

## 1. 最初目标
1. lyric-mv-kit 成为可复用、可公开、可恢复的 lyric-MV renderer/template owner。
2. 长英文主歌词行不再被画幅裁切。
3. 单曲 production run 与公开模板边界清晰，避免私有/实验内容进入 public kit。
4. 模板事实逐步从 renderer/cover 硬编码迁移到 Data/Domain/Projection。
5. 所有候选必须经历 source → test → exact reconciliation → main → consumer readback。
6. workbench 只安全消费 main 上的 reusable renderer，而不是某个 AI 的本地候选分支。

## 2. 当前真实状态
### Git baseline
- main = 7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec
- test = 7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec
- 当前稳定基线没有包含本轮 P0 修复。

### kit#12
- fix/lyric-space-tofu-kit6 = d60f056c5a43aa50693be7aa14ed783e0ecf4f01 仍存在。
- PR#11 merge object a4ceefc99182c0d48b4be983592ad38f492f741b 可恢复。
- d83d4ba / 0090b18 当前没有可解析的远端 ref/object。
- 不能把 issue 中的历史命令草案当作 SOURCE_SAVED。
- 结论：阻塞在 source recovery，而不是代码逻辑本身。

### kit#14
- chore/gitignore-open-source-boundary 不在当前远程 branch inventory。
- 2e5e3a8 无法从当前 GitHub remote 解析。
- 结论：阻塞在 source recovery。

### kit#15
- source: feat/renderer-componentization-2026-09-23
- SHA: b8eb5fb1067d664841205b56cb5302aaa34d2d9d
- base test: 7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec
- exact diff: 5 files / 377 additions
- 仅 data layer + architecture doc，未修改 renderer.py / cover.py。
- 结论：已达到 SOURCE_SAVED，可进入 test，但不能视为 main 已发布。

## 3. 进展与偏移
### 已实现
- reusable public kit owner 边界已经明确。
- 长英文行问题已准确定位，修复方案已形成。
- tofu/whitespace 问题已有独立历史证据，不应再次混入 width fix。
- Data / Domain / Projection 架构已经形成 Phase 1 方案，并有真实 source branch。
- product-hub 已建立跨仓总入口。
- main/test/candidate 可以明确区分。

### 尚未实现
- kit#12 未进入 test/main。
- kit#14 未进入 test/main。
- kit#15 尚未进入 test。
- consumer readback 尚未发生。
- historical single-song runs 迁移收口仍未完成（kit#7）。
- 两模板 canonical 文档口径仍等待 kit#13。
- branch lifecycle / stale refs 尚未 evidence-gated 收口（kit#16）。
- renderer Phase 2 尚未真正消费 Data layer。

### 是否偏离原目标
有流程性偏移，但没有产品方向性偏移。

主要偏移：候选存在于历史/local/worktree，却没有 durable remote source；PR#11 tofu 混入导致 P0-1 需要重建；多条 task/worktree 分支长期存在；组件化开始前基础修复尚未闭环。

## 4. 理想架构
~~~mermaid
flowchart TB
  GOAL["MV 原始目标：可复用模板 + 稳定 renderer + 可持续生产"] --> HUB["product-hub：跨仓协调 / pointer / timeline"]
  HUB --> KIT["lyric-mv-kit：PUBLIC CANONICAL OWNER"]
  HUB --> WB["lyric-mv-workbench-private：PRIVATE RUN / QA / evidence"]
  HUB --> MB["music-board：song identity / queue"]
  subgraph K["lyric-mv-kit"]
    SRC["short-lived task branch"] --> TEST["test：integration candidate"]
    TEST --> REC["exact SHA reconciliation"]
    REC --> MAIN["main：stable reusable release"]
    MAIN --> DATA["Data / Domain / Projection"]
    MAIN --> UI["renderer.py / cover.py"]
    DATA --> UI
    UI --> CON["consumer adapter"]
  end
  MB --> WB
  WB --> CON
  CON --> EV["render / QA / receipt"]
  EV --> HUB
  MAIN --> RET["branch retirement"]
  RET --> EXIT["worktree exit / remote ref cleanup"]
  GOV["Git / Issue / Test→Main governance"] -.gate.-> SRC
  GOV -.gate.-> TEST
  GOV -.gate.-> MAIN
  GOV -.gate.-> RET
~~~

## 5. 理想 vs 当前差距
| 维度 | 理想 | 当前 | 优先级 |
|---|---|---|---|
| Width safety | 主行宽度约束 + regression gate | 修复候选存在但未进 main | P0 |
| Open-source boundary | public kit 只含 reusable | 裁定明确，防护/历史迁移未完全收口 | P0/P1 |
| Source durability | 每个候选有 remote recoverable ref | #12/#14 source 缺失 | P0 |
| Integration | test 是唯一集成候选线 | 候选散落 branches | P0 |
| Consumer truth | consumer 明确记录 renderer source SHA | 尚未 readback | P0 |
| Data/UI separation | Data 真源 + UI 纯消费 | Phase1 source 已存在，尚未合并 | P1 |
| Template lifecycle | candidate → approved → released | 尚未完全产品化 | P1 |
| Canonical templates | 2 个锚点口径一致 | kit#13 等待拍板 | P1 |
| Branch lifecycle | merge 后 retire | 多 refs 未分类 | P0/P1 |

## 6. 优化判断
现在最大的系统风险不是 renderer 缺少更多能力，而是 candidate/test/main/consumer 四层状态容易混淆。因此下一阶段应把 durable source + exact SHA + readback 作为第一类能力。

kit#15 Phase1 的 1:1 data extraction 是正确方向。Phase2 才让 renderer/cover 消费 StyleSpec，并做视觉 diff；不要与 width fix、boundary、batch producer 混成一个 PR。

Public kit 不应保存单曲音频、production run、provider session、本机绝对路径或 song-specific demo runtime；这些属于 private workbench/evidence。

## 7. 直接相关的跨仓信息
- product-hub#6：MV 主线总协调。
- product-hub#11：branch/worktree lifecycle。
- product-hub#61：post-merge / worktree sync evidence。
- workbench#10：Cha-Cha Groove 实际 consumer/run。
- workbench 2026-09-23 goal analysis：P0-1/P0-2/P0-4 与 kit#15 的依赖关系。

不纳入：求职、健康、自媒体及与 lyric-MV kit 无直接 dependency 的其他任务。

## 8. 最终收口路径
~~~mermaid
flowchart LR
  A["恢复 kit#12 source"] --> B["PR → test"]
  B --> C["exact diff + tests"]
  C --> D["main"]
  D --> E["consumer readback"]
  F["恢复 kit#14 source"] --> G["PR → test"]
  G --> H["boundary verification"]
  H --> I["main"]
  I --> E
  J["kit#15 source"] --> K["PR → test"]
  K --> L["data smoke"]
  L --> M["main"]
  M --> E
  N["branch inventory"] --> O["dry-run evidence"]
  O --> P["retire stale refs"]
  P --> Q["post-delete readback"]
  E --> R["Issue lifecycle close"]
  Q --> R
~~~

## 9. 治理/接手补充

### 状态机

```
SOURCE_SAVED → TEST_VERIFIED → SEMANTICALLY_RECONCILED → MAIN_MERGED → MAIN_READBACK → CONSUMER_UPDATED → ISSUE_CLOSED
```

- `SOURCE_SAVED` 只表示 GitHub remote 上存在可恢复的真实 source。
- `TEST_VERIFIED` 不代表 main 已发布。
- `MAIN_MERGED` 不代表 workbench 已消费。
- `CONSUMER_UPDATED` 必须记录 consumer 当前读取的 renderer source SHA。
- 任一层缺证据，状态必须停在对应 lifecycle，不得向后跳跃。

### 相关历史 Issue / PR pointer

- kit#12：width-adaptive 主歌词行；历史修复 `0090b18` 当前缺 remote object，等待 source recovery。
- kit#14：open-source boundary；历史 `2e5e3a8` 当前缺 remote object，等待 source recovery。
- kit#15：Phase1 Data / Domain / Projection，source `b8eb5fb...`。
- kit#16：本仓 branch lifecycle / release evidence canonical。
- kit#7：public/private semantic reconciliation。
- kit#13：2 canonical anchor templates 文档口径，等待用户拍板。
- PR #17：本复盘文档，目标 main，当前尚未合入。
- product-hub#6：MV 主线跨仓协调。
- product-hub#11：branch/worktree lifecycle 跨仓协调。

### 不应再扩张的范围

本轮主线不新增 batch producer、publication、无直接 dependency 的 Product Hub 任务；先完成 P0 release chain 与 Phase1 componentization，再进入 Phase2。

## 9. 接手检查表
1. source ref 在远端吗？
2. test exact SHA 是什么？
3. main exact SHA 是什么？
4. consumer 当前读取哪个 renderer SHA？
5. issue 是否记录 lifecycle 与 evidence？

任一答案不清楚，都不能标记完成。
