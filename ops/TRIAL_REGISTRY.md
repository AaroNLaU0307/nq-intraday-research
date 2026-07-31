# TRIAL REGISTRY（append-only 事件链）

规则（Aaron 2026-07-31 修订批复）：既有事件记录**永不修改**；每次状态
变化以新事件行追加（UTC 时间＋commit＋actor＋原因）；勘误以新事件追加
并引用被勘误事件；trial 不得重置、删除或重新编号；失败 trial 永久保留。
状态机见 S0_REAL_RUN_AUTHORIZATION_PACKET.md §0：
PACKET_DRAFTED → PACKET_APPROVED → RUNNER_IMPLEMENTED →
READY_FOR_RUN_AUTHORIZATION → RUN_AUTHORIZED → RUNNING → COMPLETED/FAILED。
Stage A/B 失败记 PRE_RUN_ATTEMPT_FAILURE（不消耗 exposure、不换编号）；
RUN_STARTED 事件 = 进入 Stage C = exposure 正式消耗。

## S0-T001（FIRST_REAL_S0_FULL_DEVELOPMENT_RUN，exposure_seq 1）

| # | utc | event | commit | actor | 原因/备注 |
|---|---|---|---|---|---|
| 1 | 2026-07-31 | TRIAL_REGISTERED | 79d7ca3 | main agent | 授权包起草，登记 S0-T001，状态 PACKET_DRAFTED |
| 2 | 2026-07-31 | GOVERNANCE_FRAMEWORK_APPROVED | （本次修订 commit） | Aaron（main agent 代录） | Aaron 批准治理框架＋八条修订；包状态保持 PACKET_DRAFTED，待 runner 落地后重渲染最终包 |

| 3 | 2026-07-31 | **PACKET_APPROVED** | （M5-T0 commit） | Aaron | "Approved for runner implementation only"；real_s0 = REAL_S0_NOT_AUTHORIZED；PACKET_APPROVED != RUN_AUTHORIZED——仅允许实现与测试 runner，禁止真实 S0/Oracle/收益/EV/MC/Checkpoint 0 |

<!-- 只允许在此表之下追加新事件行；上方内容一经提交不得改动。 -->
