# S0_T001_POST_RUN_ATTESTATION（首次真实运行盲式事后证明，2026-08-14）

授权：具名提示词 `START_S0_T001_POST_RUN_BLIND_CLOSEOUT_AFTER_PROMPT_AUDIT`。
本文件**只记录运行与保管事实，零研究数值、零研究结论**。

```
TRIAL_ID=S0-T001
AUTHORIZED_COMMIT=876c1b74131b4ab1a89dce433ecce646ba481f8c
RUN_STAMP=20260813T170432Z
TERMINAL=stage=F_SEALED ok=True exposure_consumed=True kind=success incident=none archive=archive_ok
RESULT_VALUES_VIEWED=NO
RESEARCH_CONCLUSION=SEALED_NOT_REVEALED
```

## 1. 运行时间线（runner 守卫日志，全部状态行）

六阶段顺序完成：A_PRECHECK → B_LOAD_VALIDATE → C_COMPUTE →
D_INTEGRITY → E_REPORT → F_SEALED，各 stage start/end 成对；无 incident；
历史两次尝试分别死于 Stage A（INC-e6fe49ec63de）与 Stage B
（INC-fa9234e0e541），本次两阶段均一次通过。

registry 事件（runner 原子追加，UTC 戳=运行启动整秒）：
`RUN_STARTED @2026-08-13T17:04:32+00:00`（Stage C 入口；exposure slot
sequence 1 正式消耗）、`COMPLETED @同戳`（report sealed）。

## 2. 封存工件（路径、字节数、SHA-256；内容未被任何人查看）

- 运行目录：`C:\Users\Aaron\quant-data\itsf-runs\runs\S0-T001_20260813T170432Z\`
- 归档镜像：`C:\Users\Aaron\quant-data\itsf-runs-archive\S0-T001_20260813T170432Z\`

| 文件 | bytes | sha256 |
|---|---|---|
| HANDOFF_ADMISSION.json | 5026 | 02bf127f9741e82b87265b0b7d3d76e68e4ca4ab2bcee4cd0acc580e5a14e41c |
| MC_HANDOFF_E1_Base.jsonl | 8740320 | 6c174f0379fd76876ebd0010ee9c6848f59f37df826612c137a07c5d7d2c46a5 |
| MC_HANDOFF_E1_Conservative.jsonl | 8770190 | ec440a03d916e0f394660716ba4f3fa575cfd45dc8074448e5f8266ffd14bca4 |
| MC_HANDOFF_E1_Severe.jsonl | 8760654 | db3240e6a20776c5b3d94fbb97047917205ecce90a3f32f32423a135c67f8266 |
| MC_HANDOFF_E1_Stress.jsonl | 8760654 | a3ee13564130393ed9a8dfd3aa0a5b9f8d219cd548f17da249b308011a3422b6 |
| MC_HANDOFF_E2_Base.jsonl | 14108202 | f465a2bdb8d9fcc70d2288cec96b03c42ea20227a982e68bf49169cf5f261cd2 |
| MC_HANDOFF_E2_Conservative.jsonl | 14144250 | d3ddfaa727f31ee60a95ac1d73a23b9025815a9a23d965db52df60c7167c2f1b |
| MC_HANDOFF_E2_Severe.jsonl | 14140719 | f878b1dfaed7f3a7d6d7e75fb2cd0b3504b711eae21b372ad7f50a9fe50ba46b |
| MC_HANDOFF_E2_Stress.jsonl | 14140719 | edf074cf4f471e9cab079f7ce82095fcc09a8c4a2e7c0a5936a21c1209522963 |
| REGISTRY_AFTER_RUN_STARTED.json | 443 | 260578f785f58ef3d2182b86127b898c982a13858585f563fe5cc379455d7a0d |
| S0_REPORT.json | 349111326 | 8b2db7dbb0f678a0c4ed4071303478c26ea5e23fa0db591719e646ba648a90e9 |
| S0_REPORT.md | 559 | 1e1810d15bf4902412f6c210c928a961758b32d40540d19ed732f5d91fbc709d |
| SEED_MANIFEST.json | 673 | df2c4880c599ff1f3cfd251a5022169705ef6fa164ef811ff916ab6d250a3e74 |
| manifest.jsonl | 4345 | 4158696fd9fb4cda9cae7f04351e4f02e83f532e42b5fbaa953e4fcee53fa04c |

（S0_REPORT.md 的 sha 与 runner 日志 `artifact_0011`、S0_REPORT.json 与
`artifact_0012` 逐字相同——渲染时哈希与落盘后独立重算一致。）

## 3. 盲式独立复核（本轮机器重算，仅状态/计数）

```
PARSED_ROWS=17                      # 13 编号行＋2 失败行＋RUN_STARTED＋COMPLETED
AUTHORIZATION_SNAPSHOT_SEQUENCE=15  # 快照记录的 RUN_STARTED 前事件数
RUN_STARTED_COUNT=1
COMPLETED_COUNT=1
FAILED_COUNT=0
REGISTRY_AFTER_RUN_STARTED_SHA_MATCH=YES   # 封存快照 == 现 registry 去 COMPLETED 行
INVENTORY_ERRORS=0
RUN_ARCHIVE_INVENTORY_EQUAL=YES     # 逐文件 路径/类型/字节/sha 相等
FILE_COUNT=14
DIRECTORY_COUNT_INSIDE_RUN=0
CHAIN_RECORDS=13
CHAIN_VALID=YES                     # 含逐文件 hash cross-check 的全链重放
CHAIN_ERRORS=0
validate_formal_payload problems=0  # expected governance 以快照 sequence 15 重建
sealed_body_count=11                # 8 JSONL＋HANDOFF_ADMISSION＋S0_REPORT.md＋SEED_MANIFEST
validate_sealed_files problems=0
validate_dr5_staged_boundary problems=0
ADMITTED_ONLY_SEED_MANIFEST=YES
MC_READY_GATE=REFUSED_AS_DESIGNED   # McConsumerAbsent；MC 消费者继续 fail-closed
```

## 4. exposure 语义（与 EXPOSURE_LEDGER.md 2026-08-14 行同口径）

```
FORMAL_TRIAL_COUNT=1
STAGE_C_EXPOSURE_SLOT_SEQUENCE_1=CONSUMED
RESEARCHER_OUTCOME_VIEWED=NO
RESEARCHER_EXPOSURE_COUNT=0
```

结果**已生成**并封存（outcome_generated=YES）；**无任何人查看任何结果值**
（outcome_seen=NO）。揭盲是独立的重大决定，只能由 Aaron 以口令
`START_S0_T001_RESULT_REVEAL_AND_DECISION_COUNCIL_AFTER_BLIND_CLOSEOUT`
下一轮主动触发；本文件不构成揭盲、MC、策略 build 或任何新授权。
