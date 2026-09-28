# lyric-mv-kit / Release Evidence Ledger

> Purpose: 只记录 release train 的最小可验证状态，不替代各业务 Issue。
> 更新规则：任何状态变化都必须携带 exact SHA / absolute evidence；UNKNOWN 不得写成成功。

## 2026-09-23 初始快照

| Item | Canonical Issue | Source | Test | Main | Consumer | 生命周期 | 下一动作 |
|---|---|---|---|---|---|---|---|
| width-adaptive 主行 | #12 | UNKNOWN（历史 `0090b18` 当前不可解析） | — | 7dbdfc3 | — | WAITING_FOR_EVIDENCE | 恢复真实 source |
| public boundary | #14 | UNKNOWN（历史 `2e5e3a8` 当前不可解析） | — | 7dbdfc3 | — | WAITING_FOR_EVIDENCE | 恢复真实 source |
| Data Phase1 | #15 | b8eb5fb1067d664841205b56cb5302aaa34d2d9d | 7dbdfc3 target | 7dbdfc3 | — | SOURCE_SAVED | PR #19 → test |
| branch lifecycle | #16 | n/a | n/a | 7dbdfc3 | — | PLANNED | inventory + dry-run |
| canonical template wording | #13 | n/a | n/a | 7dbdfc3 | — | WAITING_FOR_USER | 用户拍板 A/B/C |

## 关键 SHA

- main: `7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec`
- test: `7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec`
- Phase1 source: `b8eb5fb1067d664841205b56cb5302aaa34d2d9d`
- Phase1 PR: https://github.com/EOMZON/lyric-mv-kit/pull/19
- reconciliation docs PR: https://github.com/EOMZON/lyric-mv-kit/pull/17

## 状态机

SOURCE_SAVED
→ TEST_VERIFIED
→ SEMANTICALLY_RECONCILED
→ MAIN_MERGED
→ MAIN_READBACK
→ CONSUMER_UPDATED
→ ISSUE_CLOSED

## 四层语义

1. Candidate/Source：远端存在可恢复的真实候选。
2. Test：候选已经进入稳定集成候选线，并以固定 SHA 验证。
3. Main：稳定公开发布线已包含候选。
4. Consumer：实际 workbench/consumer 已读取并验证 main/released renderer SHA。

任一层没有证据，停止在该层。

## 相关治理

- Issue Governance：
  https://github.com/EOMZON/codex-skills-private/blob/task/issue-governance-20260920/github-ops/references/issue-governance.md
- Test→Main：
  https://github.com/EOMZON/codex-skills-private/blob/9a8e385ccc98f068b0990133f9a2e80681ffa9ec/github-ops/references/test-main-governance.md
- product-hub#6：
  https://github.com/EOMZON/product-hub/issues/6
- product-hub#11：
  https://github.com/EOMZON/product-hub/issues/11

## 更新纪律

- 不因为 issue comment 中存在某个 SHA 就认为 remote source 存在。
- 不因为 PR 创建成功就认为 test/main 已改变。
- 不因为 main 合并成功就认为 consumer 已更新。
- 不因为 worktree 本地文件存在就认为 GitHub source 可恢复。
- 删除 branch 前必须存在 dry-run evidence；删除后必须 live remote readback。