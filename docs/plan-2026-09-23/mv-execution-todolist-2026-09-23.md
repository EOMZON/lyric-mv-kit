# lyric-mv-kit / MV 主线执行清单（2026-09-23）

> 只覆盖 lyric-MV 原始目标直接相关事项。跨仓只保留直接 dependency。

## P0 — 先恢复发布链
### P0-1 kit#12 — width-adaptive 主歌词行
- [!] d83d4ba + 0090b18 当前无远端 source ref。
- [ ] 从真实可验证 commit 恢复 source；禁止按 issue 文本重建。
- [ ] 独立 source ref → test。
- [ ] exact diff 验证只含 width fix。
- [ ] 最长英文 cue 做 ink width × max scale regression。
- [ ] test → main。
- [ ] main exact SHA readback。
- [ ] consumer readback。
- [ ] 回 kit#12 写完整 lifecycle。
- 禁止把 PR#11 tofu commits 或 a4ceefc merge object 当作 P0-1 发布内容。

### P0-2 kit#14 — open-source boundary
- [!] 2e5e3a8 / chore branch 当前无远端 source ref。
- [ ] 恢复真实 source。
- [ ] PR → test。
- [ ] 验证 runs/、samples/、tests/ 防误跟踪，并验证既有例外。
- [ ] test → main。
- [ ] main readback。
- [ ] kit#14 lifecycle 收口。

### P0-4 kit#16 — branch lifecycle / stale refs
- [~] 已建立 kit#16。
- [ ] branch / SHA / owner / role / issue / merged-base / disposition inventory。
- [ ] 实时 remote readback。
- [ ] 明确 ACTIVE / STALE。
- [ ] stale 删除前 dry-run evidence。
- [ ] 只删除无唯一价值且无 active dependency 的 refs。
- [ ] 删除后 remote readback。
- 不按“11 条”机械删除。

## P1 — 模板产品化收口
### P1-1 kit#15 Phase1
- [x] source branch remote-backed。
- [ ] PR → test。
- [ ] data smoke/import。
- [ ] exact diff verification。
- [ ] test → main。
- [ ] main + consumer readback。
- [ ] Phase1 close；Phase2 单独 PR。

### P1-2 kit#13
- [~] WAITING_FOR_USER。
- [ ] 用户确认 A/B/C。
- [ ] README / rollout 文档统一为 2 canonical anchor templates + 6 style profiles。
- [ ] test → main。

### P1-3 kit#7
- [ ] 按原 issue 做 semantic reconciliation。
- [ ] your-own-road / incision-paper production runs 迁出 public kit。
- [ ] reusable-only audit。
- [ ] 回 kit#7，不重复建 issue。

## P2 — 架构能力
### P2-1 Phase2 Data → UI
- [ ] 新 PR。
- [ ] renderer.py / cover.py 消费 get_preset / StyleSpec。
- [ ] 单一 preset truth。
- [ ] visual diff + hash regression。
- [ ] 保留 kit#12 width logic。

### P2-2 Template lifecycle
- [ ] EXPERIMENT / CANDIDATE / APPROVED / RELEASED。
- [ ] 只有 RELEASED 可被 workbench queue 消费。
- [ ] metadata 记录 source revision / schema version。

### P2-3 Runtime contract
- [ ] kit 提供稳定 CLI/contract。
- [ ] workbench 通过 adapter 调用。
- [ ] 不 fork renderer。
- [ ] receipt 记录 renderer source revision。

## 并行拆分
### 对话 A：本对话
lyric-mv-kit release + governance：P0-1 / P0-2 / P0-4 / P1-1 / P1-2 / P1-3。可能触碰同一 integration refs，因此建议串行。

### 对话 B：完全解耦
lyric-mv-workbench-private production：Cha-Cha Groove render / QA / package。可与 A 并行。

### 对话 C：后续
music-board / publication：等待 P0 发布链闭环后推进。

## Release Train
kit#12 source recovery → test → exact reconciliation → main → consumer readback → kit#14 → kit#15 Phase1 → Phase2 componentization → template lifecycle → daily producer。

## Definition of Done
- [ ] main 包含 width-adaptive 修复。
- [ ] main 包含 public-boundary prevention。
- [ ] consumer 已读取并验证 main SHA。
- [ ] historical single-song runs 不再由 public kit 承担。
- [ ] Data layer 进入稳定主线。
- [ ] branch lifecycle 有 evidence-gated retirement。
- [ ] kit#13 文档口径收敛。
- [ ] candidate/test/main/consumer 状态均可从 GitHub 独立读回。
