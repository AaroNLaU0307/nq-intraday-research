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
| 9 | 2026-08-01 | **RUN_AUTHORIZED** | 08e74235afb4868acc7df80bbe0e0a13a1b5ba5a | Aaron | 启动第一次真实S0，授权trial_id: S0-T001，使用commit: 08e74235afb4868acc7df80bbe0e0a13a1b5ba5a |
| + | 2026-08-01T16:20:47+00:00 | PRE_RUN_ATTEMPT_FAILURE | 08e7423 | main agent (s0_real_run) | [S0-T001] stage B_LOAD_VALIDATE gate 'preflight_assertions_match': RunGateError (incident INC-fa9234e0e541; exposure NOT consumed; artifacts in S0-T001-A20260801T162047Z) |
| 10 | 2026-08-01 | **RUN_AUTHORIZATION_SUPERSEDED** | 08e74235afb4868acc7df80bbe0e0a13a1b5ba5a | main agent（Aaron 批复 DECISION_PACKET_VENDOR_DEGRADED_ANCHOR / IR-26 E2） | [S0-T001] supersedes_event_sequence: 9; superseded_commit: 08e74235afb4868acc7df80bbe0e0a13a1b5ba5a; reason_code: STAGE_B_ANCHOR_SEMANTICS_FIX; incident_id: INC-fa9234e0e541 |
| 11 | 2026-08-01 | **READY_FOR_RUN_AUTHORIZATION** | 6cb7eb718c903d119b7e51c7171e6db6f43aca67 | main agent | IR-26 收口（Aaron E5）：SA-16 只读审计判 IR-26 修复全 CLOSED——八条规则逐条映射核验、真实数据 66 断言 all_pass、18 缺失日与锁定 json 逐字节一致、diagnostic sidecar=6、两判定性变异均红、隔离授权态探针 Stage A 13/13＋Stage B 5/5 全过（含 preflight_assertions_match 66/66）未入 Stage C。SA-16 唯一 OPEN=untracked 评审包会触发 git_clean 门（第三自锁，修复之外）——已随本事件 commit 入库闭合。N1（实施边界无回归守卫）等入 P3 backlog。等待 Aaron 对新 HEAD 发第三次 §10；此前禁真实 S0。S0-T001 未消耗 |
| 12 | 2026-08-13T16:41:04+00:00 | **READY_FOR_RUN_AUTHORIZATION** | 876c1b74131b4ab1a89dce433ecce646ba481f8c | Fable main agent（依 Aaron 具名提示词 START_S0_READY_APPEND_AFTER_CODEX_OPERATIONS_PASS 执行） | [S0-T001] CODEX_OPERATIONS_FINAL_REVIEW=PASS；CODEX_EXACT_TREE_FULL_SUITE=2621/0/0；OUTPUT_ROOTS_ATTESTED=YES；DR5_STATUS=PARTIAL_BY_RULING；DR5_MC_CONSUMER=ABSENT；REAL_S0_NOT_AUTHORIZED；AWAITING_AARON_SECTION_10_EXACT_AUTHORIZATION。本 READY 仅覆盖基础 S0-T001 首次真实运行；不含 MC、策略 build、第二次 trial 或任何运行授权；运行仅由 Aaron §10 精确语句触发。attestation 证据：ops/OUTPUT_ROOTS_READINESS_CHECKLIST.md＋ops/S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md |
| 13 | 2026-08-14 | **RUN_AUTHORIZED** | 876c1b74131b4ab1a89dce433ecce646ba481f8c | Aaron | 启动第一次真实S0，授权trial_id: S0-T001，使用commit: 876c1b74131b4ab1a89dce433ecce646ba481f8c |
| + | 2026-08-13T17:04:32+00:00 | RUN_STARTED | 876c1b7 | main agent (s0_real_run) | [S0-T001] Stage C entry; researcher exposure seq consumed |
| + | 2026-08-13T17:04:32+00:00 | COMPLETED | 876c1b7 | main agent (s0_real_run) | [S0-T001] S0 report sealed |
