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

| 4 | 2026-08-01 | **RUNNER_IMPLEMENTED** | 79606038066152c66e63fad9a8184067db170ff1 | main agent | M5-T5 完成：SA-11 八项（N-A..N-H）修复→SA-12 全面审计判 N-B/N-G PARTIAL→二轮修复（§三闭包模块级工厂化＋缺键分支）→SA-13 聚焦复审 ALL_CLOSED（两项判定性变异验收均红、回归扫掠零回归、包哈希 12/12）。电池：pytest 509/509、0 skipped、冻结哈希 OK、三扫描 CLEAN，全 exit-code 门控 |
| 5 | 2026-08-01 | **READY_FOR_RUN_AUTHORIZATION** | 79606038066152c66e63fad9a8184067db170ff1 | main agent | final-readiness 条件全满足（SA-13 ALL_CLOSED @7960603）。等待 Aaron 发 §10 精确语句（含完整 40 位 commit hash）方可进入 RUN_AUTHORIZED；在此之前禁止真实 S0/Oracle/收益/EV/MC/Checkpoint 0。SA-13 留一非阻塞观察（hook 新鲜度子性质非变异判定性，备选一行测试补强）已交 Aaron 记录 |

| 6 | 2026-08-01 | **RUN_AUTHORIZED** | 524c9ab94eea8cbf2e906f3016f63cffde86e2c5 | Aaron | 启动第一次真实S0，授权trial_id: S0-T001，使用commit: 524c9ab94eea8cbf2e906f3016f63cffde86e2c5 |

<!-- 只允许在此表之下追加新事件行；上方内容一经提交不得改动。 -->
| + | 2026-08-01T12:17:30+00:00 | PRE_RUN_ATTEMPT_FAILURE | 524c9ab | main agent (s0_real_run) | [S0-T001] stage A_PRECHECK gate 'full_pytest': RunGateError (incident INC-e6fe49ec63de; exposure NOT consumed; artifacts in S0-T001-A20260801T121730Z) |
| 7 | 2026-08-01 | **RUN_AUTHORIZATION_SUPERSEDED** | 524c9ab94eea8cbf2e906f3016f63cffde86e2c5 | main agent（Aaron 批复 DECISION_PACKET_RUNTIME_SELFBLOCK §三） | [S0-T001] supersedes_event_sequence: 6; superseded_commit: 524c9ab94eea8cbf2e906f3016f63cffde86e2c5; reason_code: RUNTIME_SELFBLOCK_FIX; incident_id: INC-e6fe49ec63de |
| 8 | 2026-08-01 | **READY_FOR_RUN_AUTHORIZATION** | 36c7b581e4d4403d1d03870b12a2400749fa684f | main agent | IR-25 收口（Aaron 批复 §五）：修复 commit 12dd436→SA-14 审计否证运行可满足性（双状态测试自身为第二自锁）→SA-14 验证方案修复于 36c7b58→SA-15 聚焦复审 ALL_CLOSED（布局 A/B 双套件 519 绿、13/13 门全过含 full_pytest、父 commit 证伪复现、布局 C 下次运行真实形态亦绿、包哈希 12/12）。SA-14/15 共六条非阻塞观察入 P3 backlog。等待 Aaron 对新 HEAD 重发 §10 精确语句；此前禁真实 S0/Oracle/收益/EV/MC/CP0。S0-T001 未消耗，仍为首次真实 trial |
