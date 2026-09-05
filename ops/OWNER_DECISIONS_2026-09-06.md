＃ Owner 裁定 —— 2026-09-06

```
DECIDER=Aaron（本人）
DELEGATED=NO
RECORDED_BY=fresh fable verifier（本轮 MC-DS-S001 P5 独立验证席位），逐字转录他的原话；provenance 为本席位所记，标明
```

---

## OD-1 MC-DS-S001 F3 retirement

### 原话

> 我现在正式作出并授权记录以下 Aaron owner decision：
>
> OD-1 — MC-DS-S001 F3 retirement
>
> DECIDER = Aaron
> DELEGATED = NO
>
> 我裁定：
>
> - supersedes_event_sequence = 22
> - superseded_supplement_id = MC-DS-S001
> - superseded_commit = 3df1656f105b9314235bd28957336a7dec4bde05
> - reason_code = POST_START_FAILURE
> - incident_id = INC-96578a2997e9
> - successor_supplement_id = NONE
>
> 依据：
> seq 22 `SUPPLEMENT_VERIFICATION_FAILED` 已由 fresh independent verifier
> 确认 `headline_replay_identity = FAIL`，因此当前 supplement 必须退休。
>
> 我确认：
> - MC-DS-S001 ID_REUSE = FORBIDDEN；
> - 当前没有注册 successor supplement；
> - 不创建 MC-DS-S002；
> - 不开始 T1；
> - 不修改或删除 sealed supplement；
> - 不修改或删除 archive；
> - 不修改 verifier attestation；
> - 不开始 N10/N11。

### 修正原话（Aaron，2026-09-06，同日；只改 successor 一项）

> 根据你刚刚机械测出的不可逆 parser 语义，我修正 OD-1 中唯一一项 owner ruling：
> `successor_supplement_id = MC-DS-S002`
> 不再使用 `NONE`。
> 理由：
> 本次 retirement 的后续计划是让修正后的 supplement 作为 `MC-DS-S001` 的正式 successor，通过现有 T1 路径登记 lineage，而不是创建一个与 S001 无正式关系的 fresh P1。
> 我明确接受该选择的合同后果：
>
> * `MC-DS-S001` 在 F3 后永久 retired，ID reuse forbidden；
> * `MC-DS-S002` 被 F3 预先绑定为唯一 successor；
> * 后续必须通过 T1 将 `MC-DS-S002` 注册为 S001 的 successor；
> * `MC-DS-S002` 不允许绕过 T1 直接使用 fresh P1；
> * 当前这一步只绑定 successor id，不执行 T1、不修改 S002 代码、不开始 repair。

Aaron 接受该选择会要求后续使用 T1 注册 MC-DS-S002，且禁止 MC-DS-S002 以 fresh P1 绕过 successor lineage。

机械依据（本席位实测，memory-only）：parser 要求 T1 的 predecessor F3 必须点名该 T1 的 id；
F3 写 `NONE` 则日后任何 `T1(MC-DS-S002, predecessor=MC-DS-S001)` 被拒（`t1_predecessor_f3_names_other_successor`），
而 F3 行终态且不可修正；F3 写 `MC-DS-S002` 则 T1 被接受、fresh P1(MC-DS-S002) 被拒（`f3_successor_not_registered_by_t1`）。

### 裁定

```
EVENT                      F3  SUPPLEMENT_SUPERSEDED（NUMBERED，seq 23）
supersedes_event_sequence  22
superseded_supplement_id   MC-DS-S001
superseded_commit          3df1656f105b9314235bd28957336a7dec4bde05   （绑定 seq 22 行的 commit 列）
reason_code                POST_START_FAILURE
incident_id                INC-96578a2997e9
successor_supplement_id    MC-DS-S002   （同日修正；原裁定 NONE，见「修正原话」）
ACTOR                      main agent（Aaron 批复 OWNER_DECISIONS_2026-09-06.md OD-1）
COMMIT 列                  追加时的 framework HEAD（40-hex；本文件提交后重新取得）
ID_REUSE                   FORBIDDEN —— MC-DS-S001 永久报废；MC-DS-S002 由本 F3 预先绑定为唯一 successor，后续必须经 T1 登记 lineage 并重走完整 P2；禁止以 fresh P1 绕过
NOT_DONE_BY_THIS_DECISION  本步只绑定 successor id；不执行 T1；不修改 S002 代码；不开始 repair；不改动 sealed supplement / archive / verifier attestation；不开始 N10/N11
```

### Provenance（本席位所记）

```
触发事件      registry seq 22  SUPPLEMENT_VERIFICATION_FAILED（2026-09-05T18:06:16+00:00，actor fresh fable verifier）
              failure_code headline_replay_mismatch；sealed artifact NOT deleted；supersession required
registry      C:\Users\Aaron\quant-data\itsf-registry  ops/TRIAL_REGISTRY.md
              sha256 0a52352c1c2bb0978e0f5107630274c7617457b3a7efb5810883a5cce6598ffb（11031 bytes，48 行，28 事件）
              repo HEAD 78a2586c3f073d73ff349ed3c0e2351ecff4db6e
witness       registry-witness/itsf/WITNESS_F2V_APPENDED_2026-09-05.json
              sha256 36bf855a2e3c718463b4c68192e80a83107bf47a6d8b8b580c785a69fe60c126
attestation   ops/P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md
              sha256 cc733337ed4fb39c994e11f188f49f20e2239870bbb0d82e645bc974d1c8053a
sealed        DAY_STRATA_SUPPLEMENT.json（MC-DS-S001_20260905T170810Z）
              sha256 f2ecbb9c77d3f2d7d2b555f50cadb6bcafdc979bdcfa4ac5a985e3cf33b9a911；archive 副本字节相同
incident_id   itsf.s0.runner.make_incident_id 生成，parts（"|" 连接）：
              MC-DS-S001 | F3 | SUPPLEMENT_SUPERSEDED | supersedes_event_sequence=22 |
              SUPPLEMENT_VERIFICATION_FAILED | headline_replay_mismatch |
              registry_sha256_after_f2v=0a52352c1c2bb0978e0f5107630274c7617457b3a7efb5810883a5cce6598ffb
preflight     ops/F3_PREFLIGHT_MC_DS_S001_2026-09-06.json（memory-only，0 problems；以本文件提交后的 HEAD 重跑一次）
```

本文件只记录 Aaron 的裁定与其 provenance；不构成对 seq 23 的追加，追加由 Aaron 最终签署。

---

## OD-2 MC-DS-S002 F2 → F3 recovery

### 原话

> OD-2 — MC-DS-S002 F2 → F3 recovery
>
> DECIDER = Aaron
> DELEGATED = NO
>
> F2（runner-emitted，UNNUMBERED）：
> - stage = C_BUILD
> - error_class = DayStrataRowsError
> - incident_id = INC-ae2fe6f555be
> - residue_path = C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S002_20260905T205325Z
> - residue_preserved = YES
>
> F3：
> - supersedes_event_sequence = 25
> - superseded_supplement_id = MC-DS-S002
> - superseded_commit = f49a6770734a8fb1d8b039c057b942ce40eedd87
> - reason_code = POST_START_FAILURE
> - incident_id = INC-ae2fe6f555be
> - successor_supplement_id = MC-DS-S003
>
> 依据：C_BUILD_1 / c_build_1_not_empty 是真实的 post-start / pre-seal
> 失败，P3 已消耗，无合法重跑路径。F2 与 P3 均为 UNNUMBERED，
> F3 只能引用 NUMBERED 行；我指定引用 seq 25（被消耗的那张授权）。
>
> 我确认：
> - MC-DS-S002 ID_REUSE = FORBIDDEN；
> - 残骸目录保留，不删除、不清理；
> - 后续新运行只能使用 MC-DS-S003；
> - 本裁定不授权 T1、不授权任何 P2、不授权运行。

### 为什么引用 seq 25 —— schema 限制，不是事实主张

`_resolve_supersedes` 只在 **NUMBERED** 行里查 `supersedes_event_sequence`。
MC-DS-S002 真正记录失败与启动的两行——F2（`SUPPLEMENT_FAILED`）与
P3（`SUPPLEMENT_RUN_STARTED`）——按合同都是 **UNNUMBERED**，没有序号，
F3 的引用字段**表达不了它们**（实测：引用一个不存在的序号得
`f3_no_target_row`）。

S002 只有两条 NUMBERED 行，二者都能通过全部机械校验：

```
24  T1   仅是 successor proposal
25  P2   本次 P3 实际消耗掉的 execution authorization
```

Aaron 裁定引用 **25**：在当前 schema 能表达的 NUMBERED 行里，它离真实的
失败执行最近。

**这只是 F3 reference-field 的 schema 限制，不代表 F2/P3 没有发生。**
两行都在账本里、都有 witness：
`WITNESS_P3_S002_APPENDED_2026-09-06.json` 与
`WITNESS_F2_S002_APPENDED_2026-09-06.json`。

`superseded_commit` 不是独立选项——`f3_commit_mismatch` 强制它等于被引行的
commit 列，seq 25 的 commit 列即 `f49a6770734a8fb1d8b039c057b942ce40eedd87`。

### 裁定

```
EVENT                      F2  SUPPLEMENT_FAILED（UNNUMBERED，seq 列 "+"）
stage                      C_BUILD          （STAGE_ENUM 闭集无 C_BUILD_1——那是 checkpoint）
error_class                DayStrataRowsError（实际抛出的类）
incident_id                INC-ae2fe6f555be
residue_path               C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S002_20260905T205325Z
residue_preserved          YES
ACTOR                      main agent (mc_ds_runner)   （runner-emitted，_check_actor 要求精确相等；
                                                        actor 记发出角色，不记录入者——先例 S001 的 P4）
COMMIT 列                  f49a677（7-hex；本次失败运行的 framework commit）

EVENT                      F3  SUPPLEMENT_SUPERSEDED（NUMBERED，seq 26）
supersedes_event_sequence  25
superseded_supplement_id   MC-DS-S002
superseded_commit          f49a6770734a8fb1d8b039c057b942ce40eedd87   （绑定 seq 25 行的 commit 列）
reason_code                POST_START_FAILURE
incident_id                INC-ae2fe6f555be
successor_supplement_id    MC-DS-S003
ACTOR                      main agent（Aaron 批复 OWNER_DECISIONS_2026-09-06.md OD-2）
COMMIT 列                  追加时的 framework HEAD（40-hex；本文件提交后重新取得）
ID_REUSE                   FORBIDDEN —— MC-DS-S002 永久报废；MC-DS-S003 由本 F3 预先绑定为唯一 successor，
                           后续必须经 T1 登记 lineage 并重走完整 P2；禁止以 fresh P1 绕过
RESIDUE                    保留，不删除、不移动、不清理
NOT_DONE_BY_THIS_DECISION  不创建 S003 T1；不修改 C_BUILD production code；不运行 N09；不开始 N10/N11
```

### Provenance（builder 所记）

```
触发事件      N09 v2（MC-DS-S002），一次且仅一次，2026-09-05T20:53–20:54Z
              refusal  C_BUILD_1 / c_build_1_not_empty
              detail   archive_root: 1 supplement file(s) present before the first write
              成因     archive 侧的空集断言施加在 planned.archive_parent（归档根本身），
                       runs 侧施加在 planned.runs_target（本次运行目录）；归档根内
                       MC-DS-S001_20260905T170810Z/DAY_STRATA_SUPPLEMENT.json 永久存在
              写入     零 supplement 字节；零 archive 尝试
registry      C:\Users\Aaron\quant-data\itsf-registry  ops/TRIAL_REGISTRY.md
              F2 追加后 sha256 ee1bbeb6f2b425a3ea853d8359938ac73e81321d7955e0c585194ad743a2ff9c
              repo HEAD ec1b9c302bdb45ed7fa55645ec6ab348257564c7
witness       registry-witness/itsf/WITNESS_P2_S002_APPENDED_2026-09-06.json（seq 25）
              registry-witness/itsf/WITNESS_P3_S002_APPENDED_2026-09-06.json（P3，runner 自写）
              registry-witness/itsf/WITNESS_F2_S002_APPENDED_2026-09-06.json（F2）
residue       C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S002_20260905T205325Z
              追加 F2 时实测：存在，且为空
incident_id   INC-ae2fe6f555be（本次运行生成，F2 与 F3 共用同一 incident）
planner       plan_failure_event 无法表示本次失败：gate_outside_closed_enum:
              c_build_1_not_empty。已记为 planner coverage defect；未用假 gate_name 绕过，
              未扩状态机。F2 不携带 gate_name 字段，故行内无缺失
```

本节只记录 Aaron 的裁定与其 provenance；F2 已按本裁定追加，F3 的追加由 Aaron 最终签署。
