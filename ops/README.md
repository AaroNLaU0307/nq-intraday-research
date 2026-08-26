# `ops/` 索引

**找要贴的东西？→ [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md)。那个文件名永远不变。**

本目录有 50+ 份治理记录，**其中 47 份被别处引用**（22 份被代码／测试／状态文件
按路径硬引用）。**所以这里不搬家，只建索引**——移动一份被 `src/` 引用的文件会
直接弄断生产代码。哪些不能动，见最后一节。

---

## 1. 现势入口（从这里开始）

| 文件 | 是什么 |
|---|---|
| [`RECOVERY_ANCHOR.md`](RECOVERY_ANCHOR.md) | **任何会话从这里开始**（D-2 拆锚，2026-08-26）。outcome-clean，永不隔离，blind 席位可安全读 |
| [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md) | **下一份要交出去的东西**，固定文件名；同时是复审禁区清单的常驻载体 |
| `MC_TO_STRATEGY_MASTER_PLAN.md` | DAG、节点状态、租约、停止点的**权威**，§ 编号最高者为准。**恢复入口已于 §16 迁至 `RECOVERY_ANCHOR.md`**。**⚠ OFF-LIMITS —— outcome-carrying，blind 席位不得读**（此处刻意不给链接） |
| [`TRIAL_REGISTRY.md`](TRIAL_REGISTRY.md) | 事件真相源，append-only。S0／supplement／MC 三个生命周期共用一份 |
| [`DECISION_PACKET_REMAINING_FABLE.md`](DECISION_PACKET_REMAINING_FABLE.md) | **现在挂着的交付**——其余十项决定交 Fable，`dec-remaining-2026-08-26`。每项先答 `DELEGABLE`：Fable 上轮自己把多数划为 Aaron-only |
| [`PROMPT_ITEM6_SOL_REVIEW.md`](PROMPT_ITEM6_SOL_REVIEW.md) | **现在挂着的交付** —— ND1 R3 提案复核第二次交付，`rv-6cd8abb41a43-1ddf0617d52e`。第一次因缺 packet／哈希被判 REJECTED_INCOMPLETE（origin=BUILDER） |
| [`ARTIFACTS_UNDER_REVIEW.json`](ARTIFACTS_UNDER_REVIEW.json) | 谁手上正拿着什么；空表是常态 |
| [`OUTCOME_CARRYING_ARTIFACTS.json`](OUTCOME_CARRYING_ARTIFACTS.json) | **隔离名单**。给复审席位之前必读 |

## 2. 现势未决

| 文件 | 是什么 |
|---|---|
| [`DECISION_PACKET_FOUR_OPEN_2026-08-26.md`](DECISION_PACKET_FOUR_OPEN_2026-08-26.md) | 四项待裁。Fable 已裁，但**裁决工件不在盘上**——见下一行 |
| [`RULING_FABLE_FOUR_OPEN_2026-08-26.md`](outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md) | **Fable 对 D-1..D-4 的裁决全文**，逐字节转录，SHA256 `90CC7110…749B86` 已复核 **⚠ outcome-carrying**（自身携带累计 exposure 计数，转录同时已隔离） |
| [`FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md`](FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md) | **传输 STOP**：四项裁决未转录未执行；另含两条已复核的 builder 自身缺陷（指令指向隔离件；隔离值扩散进 10 份未登记文件，其中 3 份是测试） |
| [`PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md`](PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md) | **第 3 项交付物**：`_SAVE_DIR` 配置化设计 ＋ **范围发现**——同一缺陷在 `header.py:201` 还有第二处，D-4 未点名 |
| [`PREP_ITEM2_QUARANTINE_MIGRATION.md`](PREP_ITEM2_QUARANTINE_MIGRATION.md) | **第 2 项交付物**：迁移可行性实测（生产代码零路径引用）＋计划。**发现裁定未区分仓根台账**，三选一待 Aaron |
| [`PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md`](PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md) | **第 6＋8 项交付物**：ND1 profile R3 修订提案（三步之第一步）。含 builder 实测的**第二个缺口**——闭合检查生产零调用，悬空 P3 今天会过 A_PRECHECK |
| [`PREP_ITEM1_L6_EXPOSURE_TEXT.md`](PREP_ITEM1_L6_EXPOSURE_TEXT.md) | **第 1 项交付物**：全局 L6 exposure 句的逐字终稿，可整段替换。**未落地**——全局文件写入需 Aaron 单独授权 |
| [`REGISTRY_SYNC_FAILURE_MODEL.md`](REGISTRY_SYNC_FAILURE_MODEL.md) | **第 7 项边界 (3)(4)**：registry 在同步树内的故障模型与恢复程序。含 builder 复核出的第二条致命通道（裁定文本少算的那条） |
| [`D124_RULINGS_CLEAN_EXTRACT.md`](D124_RULINGS_CLEAN_EXTRACT.md) | **D-1／D-2／D-4 裁决的 outcome-clean 逐字副本**（原件是隔离件）＋ builder 已落地部分的对照。三项未决部分即八项待裁的前三项 |
| [`D3_REGISTRY_WRITER_PROPOSAL.md`](D3_REGISTRY_WRITER_PROPOSAL.md) | **D-3 提案**：谁向 registry 追加 P3 与失败事件。待 fresh Sol 批准 → Aaron 终裁。outcome-clean（裁决全文是隔离件，故另立可读副本）。**§2.5–2.7 是 builder 实测**：已批准的 ND1 actor 表把 A1／F1／F2 都判给运行器，与提案「失败事件仅主代理」相抵三行 |
| [`N09_EXECUTION_PATH_DESIGN_R2.md`](N09_EXECUTION_PATH_DESIGN_R2.md) | N09 执行路径设计 R2 —— **Sol 判 HOLD**，R3 待 Fable 裁定后再写 |
| [`N08_SCOPE_UNRESOLVED.md`](N08_SCOPE_UNRESOLVED.md) | N08 范围无法重建的实测记录（节点已由 Aaron 裁 DROP） |
| [`PENDING_ANCHOR_UPDATES.md`](PENDING_ANCHOR_UPDATES.md) | 已并入主计划 §15.1，**保留为历史，勿再并一次** |

## 3. 裁定与决策（authority）

| 文件 | 是什么 |
|---|---|
| [`OWNER_DECISIONS_2026-08-26.md`](OWNER_DECISIONS_2026-08-26.md) | **Aaron 采纳八项**＋逐项结算表（哪几项完成了、其余还欠他哪个具体动作） |
| [`OWNER_DECISIONS_2026-08-25.md`](OWNER_DECISIONS_2026-08-25.md) | **Aaron 本人**四项裁定，`DELEGATED=NO` |
| [`DELEGATED_RULINGS_2026-08-24.md`](DELEGATED_RULINGS_2026-08-24.md) | N06 终态 ＋ N-D2/N-D3 共 32 项，Sol 委托裁定 `DELEGATED=YES` |
| [`RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md`](RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md) | MC-REG-COLLISION-001 批准（C2 被整条替换） |
| [`RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md`](RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md) | 上一条的 Fable 提案 |
| [`RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`](outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md) | N-D2/N-D3 的 Fable 提案 **⚠ outcome-carrying** |
| [`ND1_PROFILE_RATIFICATION.md`](ND1_PROFILE_RATIFICATION.md) | N-D1 profile 批准。**目录创建／写探针／执行是三次独立授权** |
| [`DECISION_PACKET_N00_AND_ND1.md`](DECISION_PACKET_N00_AND_ND1.md) | N00 与 N-D1 决策包，含 `N00_MISSING_AUTHORITY_CHECKLIST` 与 §D.3.4 |
| [`DECISION_PACKET_ND2_ND3.md`](outcome_quarantine/DECISION_PACKET_ND2_ND3.md) | N-D2/N-D3 合并决策包 **⚠ outcome-carrying** |
| [`ND2_ND3_RULING_REVIEW_FINDINGS.md`](outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md) | 对上一条裁定的复核发现 **⚠ outcome-carrying** |
| [`DECISION_MC_REGISTRY_COLLISION.md`](DECISION_MC_REGISTRY_COLLISION.md) | 两份已批准工件相抵的记录；末尾 STATUS 段为收口 |
| [`S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md`](S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md) | L-5 输出根运维决策 |

## 4. 交给别的席位的提示词（历史）

> **要贴的那份永远在 [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md)。** 下面是已用过的。

| 文件 | 交给谁 / 结果 |
|---|---|
| [`PROMPT_EIGHT_OPEN_FABLE.md`](PROMPT_EIGHT_OPEN_FABLE.md) | Fable 决裁席，八项，**已全部裁定并经 Aaron 采纳**；席位自评未烧 |
| [`PROMPT_D3_SOL_REVIEW.md`](PROMPT_D3_SOL_REVIEW.md) | Sol，D-3 复核，**已返回 HOLD**，席位未烧 |
| [`N09_EXECUTION_PATH_A2_SOL_PROMPT.md`](N09_EXECUTION_PATH_A2_SOL_PROMPT.md) | Sol，两次 TRANSPORT_STOP 后被 Review Packet 取代 |
| [`MC_REG_COLLISION_SOL_RATIFICATION_PROMPT.md`](MC_REG_COLLISION_SOL_RATIFICATION_PROMPT.md) | Sol，已 RATIFIED_AS_MODIFIED |
| [`MC_REGISTRY_COLLISION_FABLE_PROMPT.md`](MC_REGISTRY_COLLISION_FABLE_PROMPT.md) | Fable，已出提案 |
| [`ND2_ND3_FABLE_DECISION_PROMPT.md`](outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md) | Fable，32 项 **⚠ outcome-carrying** |
| [`N06_DISPOSITION_AND_ND2_ND3_RATIFICATION_SOL_PROMPT.md`](N06_DISPOSITION_AND_ND2_ND3_RATIFICATION_SOL_PROMPT.md) | Sol，N06 终态＋32 项批准 |
| [`N06_ROUND2_SOL_PROMPT.md`](N06_ROUND2_SOL_PROMPT.md) · [`N06_ROUND3_SOL_PROMPT.md`](N06_ROUND3_SOL_PROMPT.md) · [`N06_ROUND4_SOL_PROMPT.md`](N06_ROUND4_SOL_PROMPT.md) | N06 二/三/四轮 |
| [`N06_REVIEW_HANDOFF.md`](N06_REVIEW_HANDOFF.md) | N06 首轮交接 |

## 5. 复审结果与证据

| 文件 | 是什么 |
|---|---|
| [`RULING_FABLE_REMAINING_2026-08-26.md`](RULING_FABLE_REMAINING_2026-08-26.md) | **其余十项裁定全文**（R1–R10，逐字）＋ builder 审核。R4／R6／R7 判 `DELEGABLE=NO`，仍等 Aaron；两条机械条件已跑，均成立 |
| [`RULING_FABLE_EIGHT_OPEN_2026-08-26.md`](RULING_FABLE_EIGHT_OPEN_2026-08-26.md) | **八项裁定全文**（逐字）＋ builder 逐条复现审核；含一处经复核的论证更正 |
| [`RULING_SOL_D3_HOLD_2026-08-26.md`](RULING_SOL_D3_HOLD_2026-08-26.md) | **D-3 复核结果 = HOLD**（4 High／1 Medium，五项留给 Aaron）＋ builder 逐条复现记录。outcome-clean |
| [`A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md`](A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md) | N09 首轮：席位暴露 ＋ 非正式 REDESIGN |
| [`N09_EXECUTION_PATH_DESIGN.md`](N09_EXECUTION_PATH_DESIGN.md) | R1（已被 R2 取代，正文保留原样） |
| [`N06_HOLD_RED_PROOF.md`](N06_HOLD_RED_PROOF.md) | N06 四个 High 的红证 |
| [`N06_HOLD_REPAIR_EVIDENCE.md`](N06_HOLD_REPAIR_EVIDENCE.md) · [`N06_ROUND2_HOLD_REPAIR_EVIDENCE.md`](N06_ROUND2_HOLD_REPAIR_EVIDENCE.md) · [`N06_ROUND3_HOLD_REPAIR_EVIDENCE.md`](N06_ROUND3_HOLD_REPAIR_EVIDENCE.md) | 各轮修复证据 |
| [`MC_FACTORY_BOUNDARY_STAGE_I.md`](outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md) | factory boundary 的 Stage I 记录 **⚠ outcome-carrying** |
| [`ND1_ENGINEERING_EVIDENCE_PACKET.md`](ND1_ENGINEERING_EVIDENCE_PACKET.md) | N-D1 工程证据 |
| [`N00_N08_PROVENANCE_AUDIT_2026-08-25.md`](N00_N08_PROVENANCE_AUDIT_2026-08-25.md) | N00／N08 只读 provenance 审计 |

## 6. 事故记录（每一份都换来了一条机械守卫）

| 文件 | 换来了什么 |
|---|---|
| [`INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824.md`](INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824.md) | 冻结登记表 |
| [`INCIDENT_TRANSPORT_HEAD_PIN_20260825.md`](INCIDENT_TRANSPORT_HEAD_PIN_20260825.md) | 不会过期的 `REVIEWED_SET_UNCHANGED_SINCE` |
| [`INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md`](INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md) | 钉子从 git 派生，不手打；含「声明本身靠粘贴传递」的补记 |
| [`INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md`](INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md) | 送审集 outcome-clean 检查 |
| [`INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md`](INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md) | 结构性测试载荷事故（历史） |
| [`REVIEWER_EXPOSURE_LOG.md`](REVIEWER_EXPOSURE_LOG.md) | **复审席位暴露台账**（已烧两个席位）。与研究 exposure 是两条轴 |

## 7. 台账与登记表（append-only，行只增不改）

| 文件 | 是什么 |
|---|---|
| [`TRIAL_REGISTRY.md`](TRIAL_REGISTRY.md) | 事件真相源 |
| [`EXPOSURE_LEDGER.md`](EXPOSURE_LEDGER.md) | §10.1 合规承载件，逐行转录仓根权威台账 **⚠ outcome-carrying** |
| [`REVIEWER_EXPOSURE_LOG.md`](REVIEWER_EXPOSURE_LOG.md) | 席位暴露，**不是**研究 exposure |
| [`FEASIBILITY_ERRATA_REGISTER.md`](FEASIBILITY_ERRATA_REGISTER.md) | feasibility 历史文档勘误 |
| [`OUTPUT_ROOTS_READINESS_CHECKLIST.md`](OUTPUT_ROOTS_READINESS_CHECKLIST.md) | 输出根就绪证明记录 |

## 8. 规范、证明与其他

| 文件 | 是什么 |
|---|---|
| [`MC_DR5_BUILD_PACKET.md`](outcome_quarantine/MC_DR5_BUILD_PACKET.md) | MC/DR-5 build packet，含 §13.5 的 P2 授权模板 **⚠ outcome-carrying** |
| [`MC_DR5_CONSUMER_SOURCE_MATRIX.md`](MC_DR5_CONSUMER_SOURCE_MATRIX.md) | consumer 的来源矩阵 |
| [`MC_COST_PROBE_FINDINGS.md`](MC_COST_PROBE_FINDINGS.md) | N16 单位成本实测 |
| [`RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`](RUNTIME_DEVIATION_PACKET_SAVE_DIR.md) | 对 qros-runtime 硬编码 `_SAVE_DIR` 的偏离记录 |
| [`QROS_FIRST_RUN_2026-08-24.md`](QROS_FIRST_RUN_2026-08-24.md) | 本项目首次接入 L6 runtime |
| [`S0_T001_POST_RUN_ATTESTATION.md`](S0_T001_POST_RUN_ATTESTATION.md) | S0-T001 盲式收口 attestation（哈希被代码 pin） |
| [`S0_T001_RESULT_DECISION_ADDENDUM.md`](outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md) | S0 结果裁决 addendum **⚠ outcome-carrying** |
| [`S0_T001_RESULT_REVEAL_ATTESTATION.md`](outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md) | 揭盲 attestation **⚠ outcome-carrying** |

| [`MIGRATION_R5_QUARANTINE_SUBTREE_2026-08-27.md`](MIGRATION_R5_QUARANTINE_SUBTREE_2026-08-27.md) | **R5 迁移执行记录**：10 迁 2 留、三处条件偏离、以及我把一份活跃复审弄失效的记录 |

## 8.5 隔离子树 `outcome_quarantine/`（R5 迁移，2026-08-27）

**该前缀下一切路径关闭。** 权威判据仍是
[`OUTCOME_CARRYING_ARTIFACTS.json`](OUTCOME_CARRYING_ARTIFACTS.json)——
**前缀是便利，不是替代**：注册表 12 条里有 **2 条不在这个前缀下**（两份
`EXPOSURE_LEDGER.md`，R1 裁 A′ 留在原地）。只查前缀会漏掉它们。

```
outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md          DAG／节点台账（旧恢复入口）
outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md   D-1..D-4 裁决全文
outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md
outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md
outcome_quarantine/DECISION_PACKET_ND2_ND3.md
outcome_quarantine/MC_DR5_BUILD_PACKET.md
outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md
outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md
outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md
```

## 8.6 子任务板里的三份（扩大索引守卫后才发现从未入索引）

**共 13 份，全部此前不在索引里** —— 不是因为被排除，而是因为守卫只 glob 顶层
`ops/*.md`。R5 迁移逼着把守卫扩到 `ops/**/*.md`，才把它们照出来。

**`ops/M4_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `TASKBOARD.md` | M4 任务板 |
| `SA1_F10_CALENDAR.md` | SA1 F-10 日历 |
| `SA2_DEV_BOUNDARY.md` | SA2 Development 边界 |
| `SA3_S0_INPUT_PREFLIGHT.md` | SA3 S0 输入 preflight |

**`ops/M5_RUNNER_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `TASKBOARD.md` | M5 runner 任务板 |
| `M5_T0_INTERFACE_AUDIT.md` | T0 接口审计 |
| `SA4_S0_CORE.md` · `SA5_RUN_INFRA.md` | S0 核心／运行基础设施 |
| `SA6_AUDIT_FINDINGS.md` | SA6 审计发现 |
| `SA7_RUNNER_HARDENING.md` · `SA8_CORE_HARDENING.md` | runner／核心加固 |
| `SA9_IR22_23_24.md` | IR-22／23／24 |

**`ops/M6_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `M6_DESIGN.md` | M6 设计 |

## 9. 非 md

`packets/`（Review Packet v1，`ops/` 而非 runtime 默认的 `runs/`，原因见
`RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`）· `M4_TASKBOARD/` · `M5_RUNNER_TASKBOARD/` ·
`M6_TASKBOARD/` · `S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl` ·
`SECOND_COPY_ATTESTED.flag` · `physical_copy_attestation.json` ·
`mc_cost_probe_2026-08-24.json`

---

## 10. 不能动的（移动 = 弄断生产代码或测试）

被 `src/`、`tests/`、`scripts/`、`qros-state.yaml` 或 `ops/*.json` **按路径**
引用，共 22 份。这里只列文件名以说明「不能移动」，**不是让你去开**；要读哪一份
先查 `OUTCOME_CARRYING_ARTIFACTS.json`。
**下表含隔离件，一律按 OFF-LIMITS 对待：**

```
TRIAL_REGISTRY.md                    EXPOSURE_LEDGER.md
MC_TO_STRATEGY_MASTER_PLAN.md        DECISION_PACKET_N00_AND_ND1.md
ND1_PROFILE_RATIFICATION.md          S0_T001_POST_RUN_ATTESTATION.md
S0_T001_RESULT_DECISION_ADDENDUM.md  S0_T001_RESULT_REVEAL_ATTESTATION.md
OUTPUT_ROOTS_READINESS_CHECKLIST.md  S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md
FEASIBILITY_ERRATA_REGISTER.md       DECISION_MC_REGISTRY_COLLISION.md
DELEGATED_RULINGS_2026-08-24.md      MC_DR5_BUILD_PACKET.md
MC_FACTORY_BOUNDARY_STAGE_I.md       DECISION_PACKET_ND2_ND3.md
ND2_ND3_FABLE_DECISION_PROMPT.md     ND2_ND3_RULING_REVIEW_FINDINGS.md
RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md
A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md
INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md
```

另有 25 份被其他 md 引用——移动它们只会留下断链，收益为零。

**本索引由 `tests/test_ops_index_is_complete.py` 机械守着**：`ops/` 下每新增
一份 `.md`，不写进本文件就会红。索引会烂掉，除非有东西盯着它。
