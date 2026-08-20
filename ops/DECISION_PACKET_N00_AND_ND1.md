# 决策包 N00 ＋ N-D1（Aaron 专属；本文件不含任何已批准值）

```
PACKET_ID=DECISION_PACKET_N00_AND_ND1
PREPARED_BY=Opus 5 main agent（依 EXECUTE_OPUS5_MC_TO_STRATEGY_MASTER_V1）
PREPARED_FROM_HEAD=c5c819beb5c13e52bcd7ca974a4e40787684b10f
DECISION_STATUS=PROPOSED_NOT_EFFECTIVE
STATUS=AWAITING_AARON_RULING
NOTHING_HEREIN_IS_APPROVED=YES
CURRENT_SECTION=§D + §D.9（2026-08-20；与上文冲突处以编号最高者为准）
RATIFICATION_BLOCK_CURRENT=AARON_ND1_PROFILE_RATIFICATION_V1（§D.10；V1／V2 均已作废）
SIGNABLE_RATIFICATION_ROUTES=1（唯一路线＝profile id + profile sha256 + doc HEAD）
FIRST_DRAFTED_FROM_HEAD=ba7fa4a（N-PLAN 之后；历史，非现势）
```

本包只**呈列选项与机械后果**。带"工程建议"的行是建议，**不是裁定**；未经 Aaron
逐项落笔，相关节点一律 fail-closed。本包不包含任何可执行授权语句。

---

# N00 — Round-4 权威文本入库与三状态裁定

## N00.1 现状（已机械核实）

- 仓库内**只有状态令牌**：`CODEX_REVIEW_PACKET_M6_1_4.md:53,710`、`M6_1_6.md:9`、
  `M6_1_8.md:293-306` 记 `STRATEGY_COUNCIL=LOCKED`；`DECISION_REQUIRED_READY_SUPERSESSION.md:209`
  记 `BLOCKS_STRATEGY_COUNCIL=NO`。
- **权威文本不在仓库**：全库检索无 Round-4 联合矩阵、无候选定义、无
  `Fable continuation` / `Sol failed-break/recapture` 的任何正文（据记载为会话态
  sealed proposal）。
- 因此**目前无法机械回答**"锁定的是什么"。

## N00.2 已知冲突（本轮无法仲裁，须 Aaron 裁决）

| 来源 | 表述 |
|---|---|
| Aaron 具名提示词（架构会议轮） | "不重新选择 Round-4 **已锁定的策略 Primary**" |
| Codex 审核（V1 审核意见 8） | `PRIMARY_SELECTED=NO`；联合锁定仅确认"矩阵准确＋未决台账完整" |

两说对**后续操作的要求一致**（N00 先行、之前零候选特定设计、两候选分立记录），
但对"是否已选定 Primary"的事实判断相反。执行侧已按**最弱读法（未选择）**收口。

## N00.3 请求 Aaron 提供 / 裁定

1. **提供** Round-4 sealed proposal 权威原文（用于逐字转录 →
   `ops/STRATEGY_COUNCIL_ROUND4_LOCK.md` → sha256 → 入 `FREEZE_LOG.md` → 签署）。
2. **裁定三字段**（各自独立，不可合并）：

```
PRIMARY_SELECTED=<YES|NO>
HYPOTHESIS_SELECTED=<YES|NO>
DESIGN_WRAPPER_APPROVED=<YES|NO>
```

3. **确认两候选分立登记**（`Fable continuation` 与 `Sol failed-break/recapture`
   不得被记为同一个 raw variant 的两种写法）。

## N00.4 未裁的后果（机械）

N00 完成前**禁止**任何 candidate-specific 策略代码：taxonomy、eligibility mask、
NA 规则、target-limit、comparator、unique-Primary 约束——全部不可开工。
N18-C / N18-I 两条路径均以 N00 完成为前置。

---

# N-D1 — 决策批 1（阻断 N03 / N04 / N05 / N09）

## 项 1 —（已移除）supplement day-universe 定义

> **本项已从 Aaron 决策批撤回：它不是方法选择，是生产强制的工程等式。**
>
> 上一轮我把它作为 A/B/C 三选一＋计数探针呈交，那是**把工程事实误呈为治理
> 选择**。经 producer 侧（`src/itsf/s0/study.py`）核实：
> `is_direction_tradeable ≡ oracle_candidate`（:335-343）；`_partition` 在
> tradeable 上按 `y_cont ≥ θ` / `< θ` **穷尽二分**，浮点全序无第三桶
> （:346-355）；records 对**每个** engine×scenario 遍历同一个 `usable` 列表
> （:663-671，注释原文 "EVERY constructible day, both engines, every scenario
> (TP and FP alike)"）；每 θ 的 `tp_days`/`fp_days` 都过滤到同一个 `traded_set`
> （:697-699），封存报告并自带守恒布尔 `constructible_equals_tp_plus_fp`
> （:715-716）。
>
> 因此 `ref_dates = traded_set = 每θ(tp_days ∪ fp_days)`，且跨 θ 并集恒等——
> A/B/C 命名的是**同一个集合**，计数探针（`|A\B|` 等四个整数）也不需要，
> 因为 `|A\B| = 0` 由构造保证。
>
> **改由代码强制**（边界修复轮 C6）：consumer 在 prepare 阶段逐 θ 验证
> `set(tp) ∪ set(fp) == ref_dates` 与 `set(tp) ∩ set(fp) == ∅`，并验证所有 θ
> 的并集相同；八 handoff 文件 exact-key-set 检查保留。任何不一致＝
> **sealed-input integrity failure**，在 supplement 构建或运行前 fail-closed，
> **不允许改选另一个 universe 继续**，不产生 exposure 或研究输出。
>
> 本项**无需 Aaron 裁定**，也不再需要任何 exposure 决策。

## 项 2 — supplement registry 批 1 事件词汇／字段／状态转移

现状：`day_strata_supplement.py:103-122` 的 `authorize_supplement` **无条件拒绝**，
拒绝理由正是"registry 语法中不存在该词表"。批准后方可实现 parser。

提案词表（状态机 `PROPOSED→AUTHORIZED→STARTED→SEALED→INDEPENDENTLY_VERIFIED→
CONSUMED_BY_GRID_REPLAY`，失败族 `ATTEMPT_FAILURE / FAILED / SUPERSEDED`）：

| # | 事件 | 行形状（模板，占位符未填，**模板≠授权**） |
|---|---|---|
| P1 | `SUPPLEMENT_PROPOSED` | `\| <n> \| <UTC> \| **SUPPLEMENT_PROPOSED** \| <commit40> \| main agent \| [MC-DS-S001] 依 IR-29b Option B 提案；schema mc_day_strata_supplement.v1；本行非授权 \|` |
| P2 | `SUPPLEMENT_EXECUTION_AUTHORIZED` | `\| <n> \| <UTC> \| **SUPPLEMENT_EXECUTION_AUTHORIZED** \| <commit40> \| Aaron \| [MC-DS-S001] <Aaron 逐字发送的执行语句全文，模板见 BUILD_PACKET §13.5> \|`（actor **必须**为 Aaron，镜像 RUN_AUTHORIZED 先例 registry:24,30,35；编号行非 `+` 行） |
| P3 | `SUPPLEMENT_RUN_STARTED` | `\| + \| <UTC> \| SUPPLEMENT_RUN_STARTED \| <commit7> \| main agent (mc_ds_runner) \| [MC-DS-S001] atomic start; structural access begins \|` |
| P4 | `SUPPLEMENT_SEALED` | `\| + \| <UTC> \| SUPPLEMENT_SEALED \| <commit7> \| main agent (mc_ds_runner) \| [MC-DS-S001] sealed sha256=<64hex>; rows_digest=<64hex>; day_universe_digest=<64hex>; source_input_sha256=<64hex>; method_version=<str>; n_rows=<int>; archive=<archive_ok\|archive_failed:<code>> \|` |
| P5 | `SUPPLEMENT_INDEPENDENTLY_VERIFIED` | `\| <n> \| <UTC> \| **SUPPLEMENT_INDEPENDENTLY_VERIFIED** \| <commit40> \| <verifier> \| [MC-DS-S001] 二次重导 rows_digest 复现=YES; headline replay identity=PASS(<n>格); attestation sha=<64hex> \|` |
| P6 | `SUPPLEMENT_CONSUMED_BY_GRID_REPLAY` | `\| + \| <UTC> \| SUPPLEMENT_CONSUMED_BY_GRID_REPLAY \| <commit7> \| main agent (mc_runner) \| [MC-DS-S001] consumed by <MC run id>; prepared_digest=<64hex>; supplement sha256=<64hex>; K=<int> \|`（由 MC runner 在 K 证据装配时追加；**前置**＝P5 在场且无后继 F3） |
| F1 | `SUPPLEMENT_ATTEMPT_FAILURE`（pre-start，零消耗） | `\| + \| <UTC> \| SUPPLEMENT_ATTEMPT_FAILURE \| <commit7> \| main agent (mc_ds_runner) \| [MC-DS-S001] stage <A_PRECHECK\|B_DERIVE\|C_BUILD> gate '<gate_name>': <ErrClass> (incident <INC-12hex>; nothing consumed; artifacts in <attempts dir>) \|`（镜像 registry:27,31；**supplement 专属 stage/gate 词表须与 N04 runner 同批固定**） |
| F2 | `SUPPLEMENT_FAILED`（post-start） | `\| + \| <UTC> \| SUPPLEMENT_FAILED \| <commit7> \| main agent (mc_ds_runner) \| [MC-DS-S001] post-start failure at <stage>: <ErrClass> (incident <INC-12hex>; residue preserved at <run dir>; NOT deleted) \|` |
| F2v | `SUPPLEMENT_VERIFICATION_FAILED`（P4 之后、P5 之前独立验证失败） | `\| <n> \| <UTC> \| **SUPPLEMENT_VERIFICATION_FAILED** \| <commit40> \| <verifier> \| [MC-DS-S001] <rederivation_mismatch\|headline_replay_mismatch\|s0_sealed_bytes_moved>: <detail>; sealed artifact NOT deleted; supersession required \|`（**新增**：原模板集缺此转移，SEALED→INDEPENDENTLY_VERIFIED 的失败分支此前只能推断） |
| F3 | `SUPPLEMENT_SUPERSEDED` | `\| <n> \| <UTC> \| **SUPPLEMENT_SUPERSEDED** \| <commit40> \| main agent（Aaron 批复 <doc>） \| [MC-DS-S001] supersedes_event_sequence: <n>; superseded_supplement_id: MC-DS-S001; superseded_commit: <commit40>; reason_code: <code>; incident_id: <INC-12hex>; successor_supplement_id: MC-DS-S002 \|`（镜像 registry:28,32；**须明示 supersede 的对象**——是 P2 授权还是 supplement id 本身，两者语义不同，请 Aaron 指定） |
| T1 | `SUPPLEMENT_ID_TRANSFER`（S001→S002） | `\| <n> \| <UTC> \| **SUPPLEMENT_PROPOSED** \| <commit40> \| main agent \| [MC-DS-S002] successor of MC-DS-S001 (superseded at event <n>, reason <code>); schema mc_day_strata_supplement.v1; id 永不重用; 本行非授权 \|`（**新增**：原模板集在项 4.3 引入 S002 却无 id 转移事件；后继件须重走完整 P2 授权） |

```
N-D1.2_RULING=<逐项批准/修改/否决>
ALL_VALUES_STATUS=PROPOSED / AARON_DECISION_REQUIRED   # 本表任何一行都不是已批准语法
```

---

## 项 3 — MC-DS-S001 是否 formal trial

| 主张 | 论据 |
|---|---|
| **否**（工程建议） | 不检验任何假设、零 outcome 生成、零 exposure slot；产出全是结构标签的 custody 工件。Charter 13 的 `formal_trial_count` 语义=预注册研究/假设数量（`EXPOSURE_LEDGER.md:8-10`） |
| **是** | 若 Aaron 认为"任何触碰真实 Development 数据的运行都应占 trial 编号"，则须新编号并占用 registry trial 状态机 |

无论裁定为何，**事件链都必须入 registry**（append-only 审计物不另立平行真相源）。

```
N-D1.3_RULING=<FORMAL_TRIAL_YES|NO>；若 YES，编号=<占位>
```

---

## 项 4 — `SUPPLEMENT_RUN_STARTED`、post-start failure 与重试记账

需裁定四点：

1. `STARTED` 消耗什么序列（run 序列／exposure slot／均不消耗——工程建议：均不，
   理由同项 3）。
2. **pre-start 失败**（Stage-A 门败）：零消耗、记 F1、artifacts 入 attempts 目录、
   修复后是否需 Aaron **重发** P2（工程建议：commit 变化即须重发，镜像 S0 两次
   `RUN_AUTHORIZATION_SUPERSEDED` 先例）。
3. **post-start 失败**（原子事件之后 crash）：残骸永不删除；是否强制启用**新
   supplement id `MC-DS-S002`**（工程建议：是，id 永不重用，镜像 registry:5 的
   "不得重置/重新编号"纪律）。
4. `.partial` 恢复语义：字节恒等则晋升、不等则拒绝并保留残渣
   （现已实现于 `day_strata_supplement.py:383-405`）——是否确认为治理规则。

```
N-D1.4_RULING=<四点逐条>
```

---

## 项 5 — supplement ledger 与 exposure quantity

1. 是否新建 `ops/SUPPLEMENT_LEDGER.md`（现势索引，逐字段可由 registry 事件重建；
   工程建议：建，registry 仍是唯一事件真相源）。
2. EXPOSURE_LEDGER 是否追加 **quantity=0** 行（工程建议：追加，IR-28d 先例格式
   `EXPOSURE_LEDGER.md:15`；累计维持 1575 不变）。
3. 该行的**结构性数据访问**定性：day strata 是结构标签、非 outcome
   （`outcome_seen=NO`、`quantity=0`）——请确认此定性。
   **注意**：台账行里的 `formal_trial=` 字段值**不在本项预填**，它由
   **N-D1.3 的裁定**决定（此前本包在此处预嵌了 `formal_trial=NO`，与项 3 的
   开放 `YES|NO` 相冲突，已撤回）。

```
N-D1.5_RULING=<三点逐条>
```

---

## 项 6 — output root 与 `supplements\` 创建授权

| 选项 | 内容 | 利／弊 |
|---|---|---|
| **A（工程建议）** | 复用既有两根下的子树：`…\itsf-runs\supplements\MC-DS-S001_<UTC>\` ＋ `…\itsf-runs-archive\supplements\MC-DS-S001_<UTC>\` | 运维 attestation 零重做（`ops/OUTPUT_ROOTS_READINESS_CHECKLIST.md` 全项已签）；同卷共模风险已具名接受；archive 机制原样可用。**二级子目录兼容性已核实**：`validate_output_roots` 条件 5 要求 runs_dir/attempts_dir "strictly under" runs_root，实现为 `_strictly_under = child != ancestor and child.is_relative_to(ancestor)`（`runinfra.py:156-159`）——**深度无关**，二级子目录合法（此前 V1.2 §13 列为未决的该项就此收口，N03 仍补一条测试钉死） |
| B | 新建独立根一对 | 命名空间最干净；但须整轮重做操作者创建＋运维 attestation＋同步核验＋签署，冻结常量需扩表 |

**须 Aaron 明示授权**：`supplements\` 中间目录的**首次创建**（既有纪律是"门从不
创建缺失根"，该纪律只覆盖两根本体；本轮**未创建任何目录**）。

```
N-D1.6_RULING=<A|B>；SUPPLEMENTS_DIR_CREATION_AUTHORIZED=<YES|NO>
```

---

## 项 7 — "晚于揭盲生成"的显著披露措辞

事实：MC-DS-S001 生成于 S0-T001 揭盲（2026-08-14）**之后**。派生链为纯结构机器
管道，与已揭盲结果之间无人工选择通道——但该事实必须显著、多处、不可回避地披露。

提案落点（四处，任一入口都撞见）：
1. EXPOSURE_LEDGER 行内；
2. supplement attestation 头部固定行 `GENERATED_AFTER_REVEAL=YES(2026-08-14)`；
3. `ops/SUPPLEMENT_LEDGER.md` 披露标记列；
4. 未来 MC verdict seal 的字段 `grid_authority="SUPPLEMENTAL_POST_REVEAL:MC-DS-S001"`。

请裁定：落点是否足够、措辞是否需 Aaron 亲拟。

```
N-D1.7_RULING=<批准/修改措辞>
```

---

# 未裁前的 fail-closed 状态（机械）

```
N03/N04/N05=BLOCKED_ON_N-D1
N09（supplement 执行）=BLOCKED_ON_N-D1 ＋ N04 ＋ N05 ＋ N06 ＋ Aaron P2 精确授权
N18-C/N18-I=BLOCKED_ON_N00
GRID_REPLAY_STATUS=BLOCKED（K 轴维持终端拒绝）
CHECKPOINT0_VERDICT_REACHABLE=NO
```


---

# §D — 现势修正与完整待裁包（2026-08-20，`PREPARED_FROM_HEAD=c5c819b…`）

```
DECISION_STATUS=PROPOSED_NOT_EFFECTIVE
SECTION_D_IS_CURRENT=YES
NOTHING_IN_SECTION_D_IS_APPROVED=YES
```

> **生效规则（无例外）**：本节全部内容为**提案**。只有 Aaron 在**后续消息**中
> 主动逐字批准，相应项才转为 effective。以下**都不构成批准**：本次执行提示词；
> 本文件被生成或修订这一事实；Aaron 要求准备决策包；Aaron 阅读本文件或终报；
> 任何"工程建议"/`RECOMMENDED_*` 行；任何看起来像条件同意的措辞。
> 权限含糊时取**限制性读法并停止**（QROS §12）。

## §D.1 — N00：区分"状态裁决"与"策略定义权威"

### D.1.1 机械现状（本轮再次核实）

仓库内**只找到状态令牌**：`CODEX_REVIEW_PACKET_M6_1_4.md:53,710`、
`M6_1_6.md:9`、`M6_1_8.md:293-306` 记 `STRATEGY_COUNCIL=LOCKED`；
`DECISION_REQUIRED_READY_SUPERSESSION.md:209` 记 `BLOCKS_STRATEGY_COUNCIL=NO`。
**没有找到足以实现候选的权威 Round-4 正文。**

### D.1.2 三个状态字段（保留，仍待裁）

```
N00_PRIMARY_SELECTED=UNRESOLVED
N00_HYPOTHESIS_SELECTED=UNRESOLVED
N00_DESIGN_WRAPPER_APPROVED=UNRESOLVED
```

**限定（勿省略）**：即使 Aaron 现在把三个字段各裁为某个状态，也**不能替代**
缺失的候选定义与矩阵正文。状态裁决解决的是"当时锁定了没有"，不是"锁定的
内容是什么"。

### D.1.3 `N00_MISSING_AUTHORITY_CHECKLIST`（candidate-specific build 的硬前置）

```
N00_MISSING_AUTHORITY_CHECKLIST（全部 MISSING；本会话不得自行重建或概括）
  [ ] 1. ROUND4_JOINT_MATRIX_FULL_TEXT            = MISSING
  [ ] 2. FABLE_CONTINUATION_CANDIDATE_DEFINITION  = MISSING
  [ ] 3. SOL_FAILED_BREAK_RECAPTURE_DEFINITION    = MISSING
  [ ] 4. PER_CELL_JOINT_SIGNOFF_OR_EQUIVALENT     = MISSING
  [ ] 5. OPTION_C_OR_OTHER_WRAPPER_DEFINITION
         + ITS_AARON_STATE_RULING_SOURCE          = MISSING
```

补交路径（不变）：Aaron 提供 sealed proposal 原文 → 逐字转录至
`ops/STRATEGY_COUNCIL_ROUND4_LOCK.md` → sha256 → 入 `FREEZE_LOG.md` → 签署。
**本会话不得凭记忆、推断或摘要重建任何一项**——重建一份"看起来对"的矩阵
正是本项要防的失败。

```
N00_CANDIDATE_SPECIFIC_BUILD_ALLOWED=NO
BLOCKED_UNTIL=（三状态字段全部裁定）AND（上列 5 项全部 PRESENT 并冻结）
```

两候选必须**分立登记**，不得被记成同一 raw variant 的两种写法。

## §D.2 — 撤回虚假的"样本 A/B/C 选择"，改记为结构恒等式

### D.2.1 撤回什么

以下三项**曾**被作为"请 Aaron 三选一的样本定义"呈交：

- `∪θ(TP∪FP)`
- handoff `ref_dates`
- `traded_set`

**这不是方法选择，是生产强制的工程等式**——三者命名的是同一个集合。
上文"项 1"已作此撤回；本节把它固化为可机械检验的恒等式，并**明确它不是
新的样本裁决**：不改变任何日期、不重建任何数据、不产生任何 exposure。

### D.2.2 结构恒等式（`STRUCTURAL_INTEGRITY_REQUIREMENT`，非样本裁决）

```
FOR_EACH_ENGINE_SCENARIO:
ref_dates == traded_set

FOR_EACH_THETA:
(tp_dates UNION fp_dates) == traded_set
tp_dates INTERSECT fp_dates == EMPTY

CROSS_THETA_POPULATION_IDENTITY=REQUIRED
MISMATCH=SEALED_INTEGRITY_FAILURE
```

违反即 **sealed-input integrity failure**：在 supplement 构建或运行**之前**
fail-closed，**不允许"改选另一个 universe 继续"**，不产生 exposure、不产生
研究输出。

### D.2.3 生产侧依据（本轮机械核实的行号）

| 事实 | 位置 |
|---|---|
| `is_direction_tradeable ≡ oracle_candidate`（方向＋Y_cont 存在） | `src/itsf/s0/study.py:334-343` |
| `_partition` 在 tradeable 上按 `y_cont>=θ` / `<θ` 穷尽二分，浮点全序无第三桶 | `study.py:346-355` |
| records 对**每个** engine×scenario 遍历同一 `usable` | `study.py:663-671` |
| 每 θ 的 tp/fp 都过滤到同一 `traded_set` | `study.py:697-699` |
| 封存报告自带守恒布尔 `constructible_equals_tp_plus_fp` | `study.py:715-716` |

### D.2.4 现行执行点（对上一版说法的**修正**）

上一版把该恒等式记为"待 N03 强制验证"。**机械事实是：它已在现势 HEAD
`c5c819b` 的 prepare 电池中强制执行**，位置 `src/itsf/mc/consumer.py:1148-1240`，
**八个**专属拒绝码：

```
day_universe_missing        day_sequence_not_ascending   tp_fp_overlap
day_sequence_duplicates     tp_day_without_record        fp_day_without_record
theta_population_drift      record_without_oracle_class
```

`theta_population_drift` 在记录侧半边之前先行检查，使跨 θ 漂移以自己的码
现身，而不是被报成某个 θ 的"未分类记录"。

**N03 的剩余义务因此更窄**（不是"实现这个等式"）：把 supplement 路径绑定到
**同一个**恒等式与同一批拒绝码，使补充件不能绕过 prepare 电池自建一个
day universe。这是 N-D1 批准后才可开工的工程项。

```
D2_STATUS=STRUCTURAL_FACT_RECORDED
D2_REQUIRES_AARON_RULING=NO
D2_CHANGES_ANY_DATE_OR_SAMPLE=NO

```

## §D.3 — N-D1 exact registry grammar（完整呈列；**提案，未批准，未实现**）

上一版用"镜像既有语法"这类占位说法带过了细节。**该说法作废。** 本节把每个
拟议事件逐项写死，供 Aaron 逐条批准/修改/否决。

### D.3.0 现行 parser 的机械事实（本轮实测，非提案）

唯一存在的 registry parser 是 `scripts/s0_real_run.py:159-191`
（`parse_registry_events`），其行为：

```
ROW_SHAPE=以 '|' 开头且以 '|' 结尾，strip 后恰好 6 个 cell
CELLS=(seq, utc, event, commit, actor, note)
EVENT_CELL_NORMALISATION=strip('*')   # **BOLD** 与裸词等价
FENCED_CODE_BLOCK_ROWS=IGNORED        # ``` 内的行永远不是事件（IR-25 fixture 4）
PROSE_MENTION=NEVER_AN_EVENT          # 旧的子串测试已废
SEPARATOR_AND_HEADER_ROWS=SKIPPED
CELL_COUNT_NOT_6=SILENTLY_NOT_A_ROW   # 见 D.3.6 已知弱点
```

已有的强校验（`_validate_authorized_row` / `resolve_authorizations`，
`scripts/s0_real_run.py:193-299`）：

```
RUN_AUTHORIZED_NOTE=必须含逐字授权句（AUTHORIZATION_SENTENCE_TEMPLATE，含 trial_id 与 40-hex commit）
COMMIT_REGEX=^[0-9a-f]{40}$
ROW_COMMIT_CELL_MUST_EQUAL_SENTENCE_COMMIT=YES
SUPERSEDE_NOTE_REQUIRED_FIELDS=trial_id, supersedes_event_sequence, superseded_commit(40hex), reason_code([A-Z0-9_]+), incident_id(INC-<12hex>)
SUPERSEDE_FAILS_CLOSED_ON=不可解析 / trial 不符 / 重复 supersede / 目标不存在 / 目标歧义 / 前向引用 / commit 不等
LIVE_SET=format-legal RUN_AUTHORIZED 减去被精确 supersede 的行
ZERO_LIVE=NOT_AUTHORIZED；>1_LIVE=FAIL_CLOSED；任何链缺陷=FAIL_CLOSED
```

**该 parser 是 S0-trial 专用的**（`TRIAL_ID="S0-T001"` 硬编码）。supplement
词表**没有任何 parser**；`authorize_supplement`
（`src/itsf/mc/day_strata_supplement.py:103-122`）无条件拒绝，并且**明确拒绝
best-effort 解析**：registry 文本里植入一个同名 token 会被**点名**并照样拒绝。

### D.3.1 全局语法规则（提案；**只含无争议的格式约束**）

> **单一权威原则（本轮修订的核心）**：每一项治理选择**只能有一个**权威字段。
> 上一版把五项**有争议的治理选择**混进了全局规则，同时又在批准块里给它们
> 各自的 `APPROVED_ND1_*` 字段——Aaron 因此可以填出一份形式完整、语义自相
> 矛盾的批准块。本节现在**只保留格式约束**。

```
SUPPLEMENT_ID_PATTERN=^MC-DS-S[0-9]{3}$
FIRST_ID=MC-DS-S001
ROW_SHAPE=以 '|' 起止，strip 后恰好 6 cell：(seq, utc, event, commit, actor, note)
COMMIT_WIDTH_BY_ROW_CLASS=NUMBERED:40-hex ／ UNNUMBERED:7-hex
CLOSED_TOKEN_ENUM_REQUIREMENT=YES
  （stage / gate_name / failure_code / reason_code / archive_code 全部须为闭合枚举）
UNKNOWN_OR_DUPLICATE_FIELDS=REFUSE
CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION
```

**已从全局规则移出的五项（唯一权威见右列，全局规则不再重复陈述）**：

| 被移出的旧行 | 唯一权威字段 |
|---|---|
| `NUMBERED_EVENTS_SHARE_GLOBAL_REGISTRY_SEQUENCE` | `APPROVED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE` |
| `PRESTART_COMMIT_CHANGE_REQUIRES_REAUTH` | `APPROVED_ND1_PRESTART_COMMIT_CHANGE_REAUTH` |
| `POST_START_RETRY_USES_NEW_ID` | `APPROVED_ND1_POSTSTART_FAILURE_NEW_ID` |
| `ID_NEVER_REUSED` | **派生量**，不单独批准——见 §D.9.2 派生表 |
| supersede 的对象 | `APPROVED_ND1_SUPERSEDE_TARGET` |

**派生量不是可批准字段**：`ID_REUSE_POLICY` 与 `SUCCESSOR_REGISTRATION_REQUIRED`
由上述权威字段机械推导（§D.9.2）。任何试图单独批准派生量的填法，按
`INCONSISTENT_COMBINATION=NOT_EFFECTIVE_AND_FAIL_CLOSED` 处理。

**编号 vs 不编号（沿用既有实史形态，须 Aaron 确认）**：

```
NUMBERED_ROWS（seq = 递增整数，与既有 1..13 同一全局序列）
  = 人类/治理事件：P1、P2、P5、F2v、F3
UNNUMBERED_ROWS（seq = '+'）
  = runner 自动发射的运行时事件：P3、P4、F1、F2

COMMIT_FIELD_WIDTH:
  NUMBERED   -> 完整 40-hex（与既有 RUN_AUTHORIZED / RUN_AUTHORIZATION_SUPERSEDED 一致）
  UNNUMBERED -> runner 7-hex 短哈希（与既有 PRE_RUN_ATTEMPT_FAILURE / RUN_STARTED / COMPLETED 一致）
```

**机械提醒**：`SUPPLEMENT_ID_PATTERN` 是**提案**。现行代码把 id 写死为模块
常量 `SUPPLEMENT_ID = "MC-DS-S001"`（`day_strata_supplement.py:50`）——
`MC-DS-S002` 需要一次**受审的代码改动**，不是配置项。

### D.3.2 逐事件语法

**P1 `SUPPLEMENT_PROPOSED`**

```
TOKEN=SUPPLEMENT_PROPOSED
NUMBERED=YES（占用全局 registry 序列号）
ACTOR=main agent
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, ir_basis, schema, non_authorization_disclaimer]
NOTE_SHAPE=[<supplement_id>] 依 IR-29b Option B 提案；schema mc_day_strata_supplement.v1；本行非授权
PERMITTED_PREDECESSOR=（无）| F3 之后的后继件登记（见 T1）
PERMITTED_SUCCESSOR=P2 | F3
TERMINAL=NO
INCIDENT_FIELD=N/A
```

**P2 `SUPPLEMENT_EXECUTION_AUTHORIZED`**

```
TOKEN=SUPPLEMENT_EXECUTION_AUTHORIZED
NUMBERED=YES
ACTOR=Aaron（**必须**；镜像 RUN_AUTHORIZED 先例 registry 行 6/9/13）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, authorized_commit_40hex, output_root, verbatim_authorization_sentence]
VERBATIM_SENTENCE=§13.5 模板逐字（三字段齐全，缺一即无效）
ROW_COMMIT_CELL_MUST_EQUAL_SENTENCE_COMMIT=YES（镜像 IR-25 fixture 7）
PERMITTED_PREDECESSOR=P1 | P2S（同 supplement_id）
PERMITTED_SUCCESSOR=P3 | F1 | F3
TERMINAL=NO
INCIDENT_FIELD=N/A
LIVE_UNIQUENESS=同一 supplement_id 任一时刻至多一个 live P2
  （live = 已发射且未被 P2S 精确 supersede，且其 id 未被 F3 报废）
```

> **P2 有两个合法前置。** `P1` 是首次授权；`P2S` 是 pre-start 修复改变了
> commit 之后的**重新授权**（§D.3.2 P2S）。上一版只写 `P1`，于是
> `PRESTART_COMMIT_CHANGE_REQUIRES_REAUTH=YES` 在状态机里**无路可走**——
> F1 之后只能去 P3 或 F3，同一 id 永远拿不到新的 P2。本轮补齐。

**P2S `SUPPLEMENT_EXECUTION_AUTHORIZATION_SUPERSEDED`（pre-start 重新授权；本轮新增）**

```
TOKEN=SUPPLEMENT_EXECUTION_AUTHORIZATION_SUPERSEDED
SHORT_ID=P2S
NUMBERED=YES
COMMIT_FIELD=40-hex
ACTOR=Aaron，或 main agent（后者**必须**在 note 内逐字引用 Aaron 的
      supersession 批复出处 <doc>；无逐字出处即非法行）
REQUIRED_FIELDS=[supplement_id,
                 supersedes_event_sequence(int),
                 superseded_authorized_commit(40hex),
                 reason_code([A-Z0-9_]+),
                 incident_id(INC-<12hex>),
                 successor_authorized_commit(40hex),
                 same_id_reauthorization(YES)]
NOTE_SHAPE=
  [<supplement_id>] supersedes_event_sequence: <int>;
  superseded_authorized_commit: <40hex>; reason_code: <CODE>;
  incident_id: INC-<12hex>; successor_authorized_commit: <40hex>;
  same_id_reauthorization: YES; Aaron 批复: <doc>
PERMITTED_PREDECESSOR=F1（同 supplement_id；必须存在一条 live P2 作为 supersede 目标）
PERMITTED_SUCCESSOR=P2（携带 successor_authorized_commit）
TERMINAL=NO
EFFECT_1=被指向的旧 P2 立即**不再 live**
EFFECT_2=supplement_id **不报废**（这正是 P2S 与 F3 的分界）
EFFECT_3=不消耗、不产生任何 exposure；pre-start 语义不变
FORBIDDEN=P2S 不得用于 post-start failure、verification failure 或放弃 id
          ——那三种情形一律走 F3
```

**P2S ≠ F3（务必分清）**

| | P2S | F3 |
|---|---|---|
| 处理什么 | pre-start 修复改变了 commit | 放弃 id / post-start failure / verification failure |
| supplement_id | **保留**，同 id 重新授权 | 按 `APPROVED_ND1_SUPERSEDE_TARGET` 处理（可能永久报废） |
| 后继 | 同 id 的新 P2 | T1 后继件登记 → 新 id 的 P2' |
| 前置 | F1 | F2 \| F2v \| Aaron 主动放弃 |
| 是否要求新 id | 否 | 由 `APPROVED_ND1_POSTSTART_FAILURE_NEW_ID` 决定 |

**parser 对 P2S 的 fail-closed 义务**（与 §D.3.5 同批实现）：

```
P2S_NO_TARGET_P2=REFUSE                 # supersedes_event_sequence 指不到 P2 行
P2S_TARGET_NOT_LIVE=REFUSE              # 目标 P2 已被别的 P2S 或 F3 处理
P2S_TARGET_AMBIGUOUS=REFUSE             # 同序号多行
P2S_FORWARD_REFERENCE=REFUSE            # P2S 必须出现在被 supersede 的行之后
P2S_COMMIT_MISMATCH=REFUSE              # superseded_authorized_commit != 目标行 commit
P2S_SUPPLEMENT_ID_MISMATCH=REFUSE       # P2S 的 id != 目标 P2 的 id
P2S_DUPLICATE_SUPERSEDE=REFUSE          # 同一目标被 supersede 两次
P2S_SUCCESSOR_EQUALS_SUPERSEDED=REFUSE  # 新旧 commit 相同 => 根本没有 commit 变化
P2S_WITHOUT_PRECEDING_F1=REFUSE         # 未失败就"重新授权"
P2S_AFTER_P3=REFUSE                     # 已越过 pre-start 分界
MULTIPLE_LIVE_P2_AFTER_P2S=REFUSE
```

**P3 `SUPPLEMENT_RUN_STARTED`**

```
TOKEN=SUPPLEMENT_RUN_STARTED
NUMBERED=NO（'+' 行）
ACTOR=main agent (mc_ds_runner)
COMMIT_FIELD=7-hex
REQUIRED_FIELDS=[supplement_id, atomic_start_marker]
NOTE_SHAPE=[<supplement_id>] atomic start; structural access begins
PERMITTED_PREDECESSOR=P2（同 id，live 且未被 F3 supersede）
PERMITTED_SUCCESSOR=P4 | F2
TERMINAL=NO
SEQUENCE_CONSUMPTION=见 §D.4.2（**未裁**）
BOUNDARY=P3 是 pre-start / post-start 的**唯一分界**
INCIDENT_FIELD=N/A
```

**P4 `SUPPLEMENT_SEALED`**

```
TOKEN=SUPPLEMENT_SEALED
NUMBERED=NO
ACTOR=main agent (mc_ds_runner)
COMMIT_FIELD=7-hex
REQUIRED_FIELDS=[supplement_id, sealed_sha256(64hex), rows_digest(64hex),
                 day_universe_digest(64hex), source_input_sha256(64hex),
                 method_version, n_rows(int),
                 archive(archive_ok|archive_failed:<code>)]
ARCHIVE_CODE_ENUM=CLOSED（由 `ArchiveReport.status` 的失败码集派生；须与 N04 同批固定）
PERMITTED_PREDECESSOR=P3
PERMITTED_SUCCESSOR=**取决于 `APPROVED_ND1_ARCHIVE_FAILURE_POLICY`，见 §D.3.7**
  政策 A：P4 只在 local_seal_ok AND archive_ok 时发射；
          archive 失败 → A1 `SUPPLEMENT_ARCHIVE_FAILED`（P4 不发射）
  政策 B：P4 可携带 archive_failed；后继由 B 的状态机决定（须 Aaron 补全）
TERMINAL=NO
INCIDENT_FIELD=N/A
```

**A1 `SUPPLEMENT_ARCHIVE_FAILED`（政策 A 专用；本轮新增）**

```
TOKEN=SUPPLEMENT_ARCHIVE_FAILED
NUMBERED=NO（'+' 行）
ACTOR=main agent (mc_ds_runner)
COMMIT_FIELD=7-hex
REQUIRED_FIELDS=[supplement_id, local_seal_sha256(64hex), archive_code,
                 incident_id(INC-<12hex>), local_seal_immutable(YES),
                 archive_root_attempted]
LOCAL_SEAL_REMAINS_IMMUTABLE=YES（本地封存件**永不**重写、重生成或删除）
P5_ALLOWED=NO
PERMITTED_PREDECESSOR=P3
PERMITTED_SUCCESSOR=A2 | AX
ARCHIVE_RETRY_REQUIRES_SEPARATE_EXACT_AUTHORIZATION=YES
TERMINAL=NO
INCIDENT_FIELD=incident_id（必填）
```

**A2 `SUPPLEMENT_ARCHIVE_RECOVERED`（政策 A 专用；本轮新增）**

```
TOKEN=SUPPLEMENT_ARCHIVE_RECOVERED
NUMBERED=YES（治理事件：需要 Aaron 的独立归档重试授权作为前提）
ACTOR=main agent（note 内逐字引用 Aaron 的归档重试授权出处 <doc>）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, recovery_authorization_doc,
                 source_and_archive_exact_inventory_match(YES),
                 per_file_sha256_match(YES), n_files(int),
                 local_seal_sha256_unchanged(YES), incident_id(INC-<12hex>)]
REQUIRES=source_and_archive_exact_inventory_match
LOCAL_ARTIFACT_REWRITTEN=NO（重试只写 archive 侧；本地封存件字节不变，须复核）
PERMITTED_PREDECESSOR=A1
PERMITTED_SUCCESSOR=P5
TERMINAL=NO
INCIDENT_FIELD=incident_id（必填；沿用 A1 的 incident）
```

**AX `SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED`（政策 A 的终局分支；本轮新增）**

```
TOKEN=SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED
NUMBERED=YES
ACTOR=main agent（Aaron 批复 <doc>）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, archive_code, attempts_count(int),
                 incident_id(INC-<12hex>), aaron_ruling_doc,
                 local_seal_sha256(64hex), local_seal_immutable(YES)]
PERMITTED_PREDECESSOR=A1
AX_PERMITTED_SUCCESSOR=F3（**唯一**后继）
AX_TERMINAL=NO
FINAL_FAILURE_TERMINAL=F3
P5_ALLOWED=NO
GRID_REPLAY_CONSUMPTION_ALLOWED=NO
INCIDENT_FIELD=incident_id（必填）
```

> **AX 自身不是终态（本轮修正上一版的自相矛盾）。** 上一版同时写了
> `TERMINAL=YES` 与 `PERMITTED_SUCCESSOR=F3`，两者不能并存。唯一语义：
> AX **只记录**"归档永久失败"这一 Aaron 裁定；正式废弃该 supplement id 的
> 是 **F3**，F3 才是本路径的终态。AX 之后**不得**进入 A2、P5 或任何消费
> 路径；本地 sealed artifact 作为失败证据保留。F3 之后若要继续，只能用
> T1 登记新 id 并重走完整 P2 授权。最终失败路径只能写作 `AX → F3`。

**P5 `SUPPLEMENT_INDEPENDENTLY_VERIFIED`**

```
TOKEN=SUPPLEMENT_INDEPENDENTLY_VERIFIED
NUMBERED=YES
ACTOR=<verifier>（fresh top-level session；不得是产出会话）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, rederivation_reproduced(YES|NO),
                 headline_replay_identity(PASS|FAIL), n_cells(int),
                 attestation_sha256(64hex)]
P5_PERMITTED_PREDECESSOR=P4 | A2        （政策 A 下的两条合法入口）
  P4 → P5   普通路径：本地封存与归档一次成功（archive_ok）
  A2 → P5   恢复路径：归档曾失败（A1），随后取得**独立**归档重试授权并由
            A2 复核通过——A2 必须证明本地 seal digest 未变、source/archive
            inventory 全等、逐文件 SHA 全等
  A1 → P5   **非法**（跳过归档恢复）
  AX → P5   **非法**（归档永久失败之后）
PERMITTED_SUCCESSOR=（N-D1 范围内为终态；原 P6 归 N-D3）
TERMINAL=YES_WITHIN_ND1
INCIDENT_FIELD=N/A
```

> **上一版的契约矛盾**：状态图画了 `A1 → A2 → P5`，而 P5 的逐事件契约只写
> `PERMITTED_PREDECESSOR=P4`——恢复路径在语法层不可达。本轮把 P5 的合法前置
> 明确为 `P4 | A2`，并在状态图、parser 拒绝码、派生量表、profile 自检四处同步。

**F1 `SUPPLEMENT_ATTEMPT_FAILURE`（pre-start，零消耗）**

```
TOKEN=SUPPLEMENT_ATTEMPT_FAILURE
NUMBERED=NO
ACTOR=main agent (mc_ds_runner)
COMMIT_FIELD=7-hex
REQUIRED_FIELDS=[supplement_id, stage, gate_name, error_class,
                 incident_id(INC-<12hex>), consumption_statement, attempts_dir]
STAGE_ENUM=CLOSED: {A_PRECHECK, B_DERIVE, C_BUILD}
GATE_NAME_ENUM=CLOSED（**须与 N04 runner 同批固定；当前为空集——未定义即不得发射**）
CONSUMPTION=nothing consumed
PERMITTED_PREDECESSOR=P2
PERMITTED_SUCCESSOR=
  P3   —— 仅当 commit **未**变化且原 P2 仍 live（直接重试，同 id）
  P2S  —— 当 commit **已**变化（走 §D.3.2 P2S 重新授权，再 P2 → P3）
  F3   —— 放弃该 id
RETRY_ID=同 id 可复用（pre-start 未消耗任何东西）
REAUTH_ON_COMMIT_CHANGE=由 `APPROVED_ND1_PRESTART_COMMIT_CHANGE_REAUTH` 唯一决定；
  若裁 YES 则 F1→P2S→P2 为**唯一**合法路径，F1→P3 在 commit 变化时非法
TERMINAL=NO
INCIDENT_FIELD=incident_id（必填）
```

**F2 `SUPPLEMENT_FAILED`（post-start）**

```
TOKEN=SUPPLEMENT_FAILED
NUMBERED=NO
ACTOR=main agent (mc_ds_runner)
COMMIT_FIELD=7-hex
REQUIRED_FIELDS=[supplement_id, stage, error_class, incident_id(INC-<12hex>),
                 residue_path, residue_preserved(YES)]
RESIDUE=NEVER_DELETED
PERMITTED_PREDECESSOR=P3
PERMITTED_SUCCESSOR=F3（必经；不得就地重试）
RETRY_ID=**必须换新 id**（见 §D.4.2 `ND1_POSTSTART_FAILURE_NEW_ID`）
TERMINAL=NO（但同 id 的执行链到此终止）
INCIDENT_FIELD=incident_id（必填）
```

**F2v `SUPPLEMENT_VERIFICATION_FAILED`（P4 之后、P5 之前）**

```
TOKEN=SUPPLEMENT_VERIFICATION_FAILED
NUMBERED=YES
ACTOR=<verifier>
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, failure_code, detail,
                 sealed_artifact_deleted(NO), supersession_required(YES)]
FAILURE_CODE_ENUM=CLOSED: {rederivation_mismatch, headline_replay_mismatch,
                           s0_sealed_bytes_moved}
PERMITTED_PREDECESSOR=P4
PERMITTED_SUCCESSOR=F3
TERMINAL=NO
INCIDENT_FIELD=（可选；若已开 incident 则必填）
```

**F3 `SUPPLEMENT_SUPERSEDED`**

```
TOKEN=SUPPLEMENT_SUPERSEDED
NUMBERED=YES
ACTOR=main agent（Aaron 批复 <doc>）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supersedes_event_sequence(int), superseded_supplement_id,
                 superseded_commit(40hex), reason_code([A-Z0-9_]+),
                 incident_id(INC-<12hex>), successor_supplement_id]
NOTE_SHAPE（提案，镜像既有 supersede 行的字段序）=
  [<supplement_id>] supersedes_event_sequence: <int>;
  superseded_supplement_id: <id>; superseded_commit: <40hex>;
  reason_code: <CODE>; incident_id: INC-<12hex>;
  successor_supplement_id: <id|NONE>
FAILS_CLOSED_ON=不可解析 / 目标不存在 / 目标歧义 / 前向引用 / 重复 supersede / commit 不等
TERMINAL=YES（对被 supersede 的对象）
INCIDENT_FIELD=incident_id（必填）
```

**F3 悬而未决的语义（须 Aaron 指定，工程侧不得默认）**：

```
ND1_SUPERSEDE_TARGET=UNRESOLVED
  选项 1：SUPERSEDES_P2_AUTHORIZATION_ONLY   授权作废，id 仍可复用
  选项 2：SUPERSEDES_SUPPLEMENT_ID_ITSELF    该 id 永久报废，必须换后继件
  选项 3：BOTH_REQUIRED_AS_TWO_ROWS          两件事各占一行
```

**T1 后继件登记（S001 → S002）**

```
TOKEN=SUPPLEMENT_PROPOSED（复用 P1 词，不新增词表条目）
NUMBERED=YES
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[successor_supplement_id, predecessor_supplement_id,
                 superseded_at_event(int), reason_code, schema,
                 non_authorization_disclaimer]
PERMITTED_PREDECESSOR=F3（同一 predecessor id）
PERMITTED_SUCCESSOR=P2（后继件**必须重走完整 P2 授权**）
ID_REUSE=FORBIDDEN
```

### D.3.3 状态机（提案；**每条边都有唯一合法路径**）

下图按 §D.9 推荐组合（`PRESTART_COMMIT_CHANGE_REAUTH=YES`、
`POSTSTART_FAILURE_NEW_ID=YES`、`ARCHIVE_FAILURE_POLICY=A`）展开。
Aaron 若改任一权威字段，对应分支按 §D.9.2 派生表重导。

```
成功主线
  P1 → P2 → P3 → P4 → P5                     archive_ok；P5 是 N-D1 的合法终态

pre-start 失败（P3 之前；零消耗）
  P2 → F1 ─┬─ commit 未变化，且原 P2 仍 live ──────────────→ P3
           ├─ commit 已变化 ──→ P2S ──→ P2(new commit) ───→ P3
           └─ 放弃该 id ──────────────────────────────────→ F3

post-start 失败（P3 之后；残骸永不删除）
  P3 → F2 → F3 → T1 → P2'（新 id，必须重走完整授权）

归档分支（政策 A）
  P3 ─┬─ archive_ok ─────→ P4 ─┬─→ P5
      │                        └─→ F2v → F3 → T1 → P2'
      └─ archive_failed ──→ A1 ─┬─→ A2 ──→ P5   （恢复成功；须独立归档重试授权）
                                └─→ AX ──→ F3   （归档永久失败；**AX 非终态，F3 才是**）
```

`P5` 有且只有两条合法入口：`P4 → P5` 与 `A2 → P5`。

**两个终态，各自明确**（`AX`、`A1` 都**不是**终态）：

| 终态 | 含义 | 该 id 还能被 GRID replay 消费吗 |
|---|---|---|
| `P5` | 封存 + 归档（`P4` 直达或经 `A2` 恢复）+ 独立验证全过 | 可以（登记事件属 N-D3，见 §D.3.4） |
| `F3` | 该 id 的**唯一**失败终态：放弃、post-start failure（`F2→F3`）、独立验证失败（`F2v→F3`）、归档永久失败（`AX→F3`） | 不可以 |

| 非终态（易被误读） | 为什么不是终态 |
|---|---|
| `A1` | 归档失败待处理；后继必为 `A2` 或 `AX` |
| `AX` | 只记录 Aaron 的"归档永久失败"裁定；废弃 id 的是其唯一后继 `F3` |
| 任何未达 `P5`/`F3` 的中间态 | 链未闭合，不可被消费 |

**不存在的边（parser 须拒绝）**：`F1 → P2`（不经 P2S 就换 commit）、
`A1 → P5`（跳过归档恢复）、`A1 → P4`、`AX → A2`、`AX → P5`、
`AX` 之后除 `F3` 外的任何边、`P2S → P3`（不经新 P2）、
`P3 → P2S`（已越过 pre-start 分界）、`F2 → P3`（post-start 就地重试）、
以及任何 predecessor 既非 `P4` 也非 `A2` 的 `P5`。

### D.3.4 明确留给 N-D3 的事项（**不得偷偷塞进 N-D1**）

```
ND3_DEFERRED=[SUPPLEMENT_CONSUMED_BY_GRID_REPLAY（原 P6）,
              MC-R001 正式事件族,
              未来 MC 批 2 全部事件]
REASON=其生命周期定义（前置/后继/终态/与 MC run 序列的耦合）尚不完整
CONSEQUENCE=在 N-D3 裁定前，supplement 链的合法终态是 P5；"补充件被 GRID 重放
            消费"这一事实无处登记，K 轴维持 k_axis_evidence_blocked_grid_replay
```

### D.3.5 parser fail-closed 要求（提案，须与 N05 实现同批固定）

```
UNKNOWN_EVENT_TOKEN=REFUSE（不得 best-effort 解析；镜像 authorize_supplement 的 lookalike 点名拒绝）
UNKNOWN_FIELD_IN_NOTE=REFUSE
DUPLICATE_FIELD_IN_NOTE=REFUSE
MISSING_REQUIRED_FIELD=REFUSE
STAGE_OR_GATE_TOKEN_OUTSIDE_CLOSED_ENUM=REFUSE
COMMIT_WIDTH_MISMATCH_FOR_ROW_CLASS=REFUSE
NUMBERED_ROW_WITH_PLUS_SEQ=REFUSE
UNNUMBERED_ROW_WITH_INTEGER_SEQ=REFUSE
ILLEGAL_TRANSITION=REFUSE
MULTIPLE_LIVE_P2_FOR_ONE_ID=REFUSE
ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION（不得只忽略坏行）
```

**P2S 专属拒绝码**：见 §D.3.2 的 P2S 块（11 条，此处不重复陈述，避免第二
份权威）。

**归档分支专属拒绝码（政策 A）**：

```
P4_WITH_ARCHIVE_FAILED_UNDER_POLICY_A=REFUSE   # 政策 A 下 P4 只在 archive_ok 时合法
A1_WITHOUT_LOCAL_SEAL_DIGEST=REFUSE
A1_ARCHIVE_CODE_OUTSIDE_CLOSED_ENUM=REFUSE
A2_WITHOUT_PRECEDING_A1=REFUSE
A2_WITHOUT_RECOVERY_AUTHORIZATION_DOC=REFUSE
A2_INVENTORY_MISMATCH_CLAIMED_OK=REFUSE        # 声称 match 但逐文件 sha 表不全
A2_LOCAL_SEAL_DIGEST_CHANGED=REFUSE            # 归档重试改动了本地封存件
AX_WITHOUT_PRECEDING_A1=REFUSE
AX_WITHOUT_AARON_RULING_DOC=REFUSE
P5_PREDECESSOR_NOT_P4_OR_A2=REFUSE             # P5 的合法前置只有 P4 与 A2
P5_AFTER_A1_WITHOUT_A2=REFUSE                  # 跳过归档恢复直接独立验证
P5_AFTER_AX=REFUSE
AX_SUCCESSOR_NOT_F3=REFUSE                     # AX 的唯一后继是 F3
AX_TREATED_AS_TERMINAL=REFUSE                  # AX 之后缺 F3 = 链未闭合
ANY_ARCHIVE_EVENT_UNDER_POLICY_B_WITHOUT_B_STATE_MACHINE=REFUSE
```

### D.3.7 归档失败生命周期（**上一版缺失，本轮补齐；两个完整方案，不预选**）

上一版 P4 同时允许 `archive=archive_ok` 与 `archive=archive_failed:<code>`，
但状态机只写 `P4→P5|F2v`。于是四个问题无解：archive 失败时能否进 P5？归档
重试要不要单独授权？重试会不会动本地封存件？永久失败怎么终局？

**机械背景（非提案）**：`archive_sealed_run` 从不为单文件问题抛异常，而是
返回 `status="archive_failed"` 的 `ArchiveReport`；它**从不改动 runs_dir**，
每一个字节都写在 `archive_root` 之下；`archive_root/<name>/` 已存在时它拒绝
覆盖（`runinfra.py:1619-1656`）。所以"重试只写 archive 侧"在实现上是成立的，
但"允许重试"本身是治理选择。

#### 方案 A（工程推荐）——封存 = 本地封存成功 **且** 归档成功

```
P4_SUPPLEMENT_SEALED_REQUIRES=local_seal_ok AND archive_ok
```

本地 seal 成功但 archive 失败时：

```
TOKEN=SUPPLEMENT_ARCHIVE_FAILED                       （事件 A1，语法见 §D.3.2）
LOCAL_SEAL_REMAINS_IMMUTABLE=YES
P5_ALLOWED=NO
ARCHIVE_RETRY_REQUIRES_SEPARATE_EXACT_AUTHORIZATION=YES
```

恢复成功后：

```
TOKEN=SUPPLEMENT_ARCHIVE_RECOVERED                    （事件 A2）
REQUIRES=source_and_archive_exact_inventory_match
PERMITTED_SUCCESSOR=P5
```

永久失败：

```
TOKEN=SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED           （事件 AX）
AX_PERMITTED_SUCCESSOR=F3（唯一）
AX_TERMINAL=NO
FINAL_FAILURE_TERMINAL=F3
P5_ALLOWED=NO
GRID_REPLAY_CONSUMPTION_ALLOWED=NO
```

**A 的四个硬约束**：① 不得重写或重新生成本地 sealed artifact——重试只写
archive 侧，且 A2 必须复核本地 digest 未变；② 归档重试需要 Aaron 的**单独**
精确授权（原 P2 授权不覆盖它）；③ archive 失败期间 `P5_ALLOWED=NO`，因此该
补充件不可能被后续消费——恢复后经 `A2 → P5` 才重新可达；④ AX 记录裁定但
**不是终态**，其唯一后继 `F3` 才废弃该 id，本地封存件作为失败证据保留但不入
证据链。

**A 的代价**：一次纯运维故障（磁盘满、目标已存在）会把整条链挡在 P5 之前，
需要 Aaron 再发一次授权。这是刻意的——"证据存在两份"是 S0 既有纪律
（`ops/OUTPUT_ROOTS_READINESS_CHECKLIST.md` 全项已签），A 不为运维便利降低它。

#### 方案 B（备选）——允许 P4 携带 `archive_failed`

若 Aaron 选 B，**必须**同时给出下列全部答案，否则 B 的批准无效
（`ANY_ARCHIVE_EVENT_UNDER_POLICY_B_WITHOUT_B_STATE_MACHINE=REFUSE`）：

```
B1  P5 是否只验证本地 seal（archive 不在独立验证范围内）？        =UNRESOLVED
B2  归档恢复是否为独立运维分支（不进 supplement 状态机）？        =UNRESOLVED
    若是：它用什么事件登记？谁是 actor？需要授权吗？
B3  archive 未恢复的补充件，何时才允许被 GRID replay 消费？       =UNRESOLVED
    （选项：允许 / 禁止 / 仅在 N-D3 另行裁定后允许）
B4  永久 archive failure 的终局状态是什么？该 id 是否报废？       =UNRESOLVED
B5  单副本证据与 Charter 数据治理"第二副本"纪律的关系如何披露？   =UNRESOLVED
```

本包**不代填** B1–B5。工程侧对 B 的意见：B 把"证据只有一份"变成一个可以
悄悄通过的状态，而 A 把它变成一个必须被看见的状态。

```
RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY=A
ARCHIVE_POLICY_SOLE_AUTHORITY=ND1_RECOMMENDED_PROFILE_R1 的
  RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY 行（§D.9.3）
CHOOSING_B_REQUIRES=一份新的 R2 profile（§D.10.2 修改路径）＋ B1-B5 全部答案
```
（本节不再提供可填的 `APPROVED_` 字段——单一签署面见 §D.10。）

### D.3.6 已知弱点（诚实披露，供 Aaron 一并裁定）

现行 `parse_registry_events` 对**格数不为 6 的行**是"静默不视为事件"，而不是
拒绝。对 S0 链无害（坏行只会导致找不到授权 → fail-closed），但对 supplement
链是真实风险：一条打错格数的 `SUPPLEMENT_SEALED` 会**消失**而不是报错。

```
ND1_PARSER_MALFORMED_ROW_POLICY=UNRESOLVED
  选项 A：维持现状（静默跳过）——与 S0 一致，但坏行可隐身
  选项 B（工程建议）：supplement 专用 parser 对"含 SUPPLEMENT_ 前缀 token
          但格数/形状非法"的行 REFUSE
```

## §D.4 — Trial / exposure 语义（消除自相矛盾）与全部待裁项

### D.4.1 台账行的 `formal_trial` 字段

任何 ledger 示例行中的 `formal_trial=` **一律不得预填 `NO`**（那与项 3 的开放
`YES|NO` 直接冲突）。正确写法：

```
formal_trial=<N-D1.3_AARON_RULING>
```

推荐栏（**是建议，不是裁定**）：

```
RECOMMENDED_FORMAL_TRIAL=NO
RATIONALE=STRUCTURAL_SUPPLEMENT_NO_HYPOTHESIS_OR_OUTCOME
```

理由：MC-DS-S001 不检验任何假设、零 outcome 生成、产出全是结构标签的 custody
工件；Charter 13 的 `formal_trial_count` 语义＝预注册研究/假设的数量
（`EXPOSURE_LEDGER.md:8-10`）。反方主张见项 3 表格右栏。

**`PROPOSED` 与 `APPROVED` 严格分开**：`RECOMMENDED_*` 行永远不是
`APPROVED_*` 行，也不因 Aaron 阅读、默许或未反对而转化。

### D.4.2 完整待裁项目（全部 `UNRESOLVED`，无隐含默认值）

```
ND1_FORMAL_TRIAL=UNRESOLVED
ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE=UNRESOLVED
ND1_STARTED_CONSUMES_EXPOSURE_SLOT=UNRESOLVED
ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=UNRESOLVED
ND1_PRESTART_COMMIT_CHANGE_REAUTH=UNRESOLVED
ND1_POSTSTART_FAILURE_NEW_ID=UNRESOLVED
```

逐项含义与选项：

| 项 | 问的是什么 | 选项 | 工程建议（非裁定） |
|---|---|---|---|
| `ND1_FORMAL_TRIAL` | MC-DS-S001 是否占一个正式 trial 编号 | `YES`（须给编号）\| `NO` | `NO` |
| `ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE` | P3 是否消耗 S0/MC 共用的 run 序列 | `YES` \| `NO` | `NO`（结构性访问，非研究运行） |
| `ND1_STARTED_CONSUMES_EXPOSURE_SLOT` | P3 是否消耗一个 exposure slot | `YES` \| `NO` | `NO`（`outcome_seen=NO`、`quantity=0`；但**必须登记**，见 §D.7） |
| `ND1_SUPPLEMENT_SEQUENCE_NAMESPACE` | 编号事件用全局 registry 序列还是独立 supplement 序列 | `GLOBAL`（与 1..13 同序）\| `SEPARATE` | `GLOBAL`（单一 append-only 真相源，避免平行编号空间） |
| `ND1_PRESTART_COMMIT_CHANGE_REAUTH` | pre-start 修复改了 commit 后是否必须 Aaron 重发 P2 | `YES` \| `NO` | `YES`（镜像 S0 两次 `RUN_AUTHORIZATION_SUPERSEDED` 先例） |
| `ND1_POSTSTART_FAILURE_NEW_ID` | post-start 崩溃后是否强制换 `MC-DS-S002` | `YES` \| `NO` | `YES`（id 永不重用，镜像 registry 行 5 的"不得重置/重新编号"纪律） |

**注意三轴正交（QROS §1）**：`LANE` / `TRIAL_ACCOUNTING` / `OUTCOME_EXPOSURE`
互不推导。裁 `ND1_FORMAL_TRIAL=NO` **不等于**"没有 exposure 需要登记"，也
**不等于**"这次访问不必进 registry"。事件链无论如何都必须入 registry
（append-only 审计物不另立平行真相源）。

## §D.5 — `.partial` 失败证据规则（**对上一版事实陈述的修正**）

### D.5.1 当前代码的确切事实（本轮实测，`day_strata_supplement.py:339-409`）

上一版（及本次执行提示词）表述为"当前 divergent `.partial` 会被删除"。
**这不准确。** 逐分支的真实行为：

| 分支 | 触发条件 | 当前行为 | 是否删除证据 |
|---|---|---|---|
| A | 终态文件已存在且字节不同 | 抛 `supplement_seal_conflict` | **否**（"a sealed supplement is never overwritten"） |
| B | 终态文件已存在且字节相同 | 幂等返回 sha256 | 否 |
| C | **前次崩溃遗留的 `.partial` 与本次 intended 不同** | 抛 `supplement_partial_residue`，明言"refusing to reuse or silently clobber debris" | **否——残骸保留** |
| D | 前次遗留 `.partial` 与 intended 相同 | 继续晋升，补完前次未完成的 promotion | 否 |
| E | **本次写入后 re-read 与 intended 不符** | `partial.unlink()`（best-effort）后抛 `supplement_partial_verify` | **是** |
| F | `os.replace` 之后 re-read 与 intended 不符 | 抛 `supplement_partial_verify` | 否（终态文件留存） |

**结论**：与"post-start 失败保留证据"提案真正冲突的**只有分支 E**，而且 E 删
的是**本次尝试刚写、刚被证明不可靠**的字节。分支 C——即"前一次尝试的证据"
这一真正要紧的情形——**当前已经保留**。

不过 C 有一个次生问题：残骸保留了，但它把同一路径上的**每一次后续重试
永久堵死**，直到有人手工搬走。这本身值得裁定。

### D.5.2 推荐（提案，未实现）

```
RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY
RECOMMENDED_DIVERGENT_PARTIAL_ACTION=RENAME_TO_.partial.divergent.<incident_id>
RECOMMENDED_SILENT_DELETE=FORBIDDEN（派生量；见 §D.9.2，不单独批准）
IMPLEMENTATION_STATUS=NOT_STARTED
```

适用范围（两处，逐处说明）：

```
BRANCH_E（本次写入自证失败）：把 unlink 换成 rename，保留可诊断的坏字节
BRANCH_C（前次崩溃残骸）  ：保留语义不变，但改为 rename 后放行重试，
                            使"保留证据"与"不永久堵死"两者兼得
```

`SILENT_DELETE=FORBIDDEN` 是全局规则：本模块任何路径都不得在无 incident 记录
的情况下删除已写入的字节。

**本轮不修改实现**（禁止改生产代码）。批准后由 N04 实现并补回归测试。

## §D.6 — 输出根语义

### D.6.1 若 Aaron 裁 Option A，未来的精确路径

```
runs:
C:\Users\Aaron\quant-data\itsf-runs\supplements\<supplement_id>

archive:
C:\Users\Aaron\quant-data\itsf-runs-archive\supplements\<supplement_id>
```

### D.6.2 归档函数的调用口径（机械事实，非提案）

`itsf.s0.runinfra.archive_sealed_run(runs_dir, archive_root)` 把整个 run 目录
复制到 **`archive_root/<run-dir-name>/`**——函数自己会追加 `source_dir.name`
（`runinfra.py:1619-1656`）。因此未来调用时应传入：

```
archive_root = C:\Users\Aaron\quant-data\itsf-runs-archive\supplements
```

**不是**传完整的 `...\supplements\<supplement_id>`——那会得到
`...\supplements\<supplement_id>\<supplement_id>` 的双层路径。

同时已核实（`runinfra.py:156-159`）：`validate_output_roots` 的
"strictly under" 判定是 `child != ancestor and child.is_relative_to(ancestor)`，
**与深度无关**，二级子目录合法。

### D.6.3 目录名的命名口径（**新增待裁，勿默认**）

既有封存件的目录名是 `<id>_<UTC>`（实例：`S0-T001_20260813T170432Z`），
而 §D.6.1 写的是裸 `<supplement_id>`。两者不能都对：

```
ND1_SUPPLEMENT_DIRECTORY_NAME=UNRESOLVED
  选项 1：<supplement_id>            （本提示词所述形态；id 唯一即目录唯一）
  选项 2：<supplement_id>_<UTC>      （镜像 S0-T001 既有先例，可容纳同 id 多次尝试）
```
选项 1 与"post-start 失败必须换新 id"是自洽的；选项 2 与既有运维 attestation
形态一致。请 Aaron 指定，工程侧不默认。

### D.6.4 推荐项（提案；三件事各自独立授权）

```
RECOMMENDED_ND1_OUTPUT_ROOT_OPTION=A
RECOMMENDED_ND1_FUTURE_DIRECTORY_POLICY=REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE
RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED=NO
RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO
SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES   # 不变量，非可选项
```

> **上一版字段名 `ND1_CREATE_TWO_EMPTY_SUPPLEMENTS_DIRECTORIES` 已废弃。**
> 它读起来像"批准即创建"。批准 N-D1 **不创建任何目录**：它只确定未来一旦
> 获得单独授权时，目录应当长成什么样。字段改名为
> `ND1_FUTURE_DIRECTORY_POLICY`，并恒带
> `SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES`。

**目录创建、写探针、执行是三次独立授权，不得合并**。本轮未创建任何目录、
未写任何探针、未执行任何东西（已机械核实两个 `supplements\` 目录均不存在）。

既有纪律"门从不创建缺失根"只覆盖两个**根本体**；`supplements\` 中间目录的
**首次创建**需要 Aaron 明示授权。

## §D.7 — Post-reveal disclosure（建议内容）

MC-DS-S001 生成于 S0-T001 揭盲（2026-08-14）**之后**。该事实必须显著、多处、
不可回避地披露。建议 disclosure 至少包含以下七条：

```
1. S0 outcome 在 Option B 与本 supplement 被提出之前已经揭盲（2026-08-14）
2. 本 supplement 是 post-reveal structural remediation，不是运行时封存
3. 它不读取 target outcome（day strata 是结构标签）
4. 它不新增、不改变任何冻结样本；日集与冻结全池精确相等
5. 它不构成独立复制（QROS §2：EMPIRICAL 独立性不适用）
6. research exposure 累计值不因结构读取自动变化——但
   structural data access 必须单独登记（IR-28d 先例格式）
7. 最终 formal-trial / exposure 字段取值服从 Aaron 的 N-D1 裁决，
   本文件不预填
```

建议落点（四处，任一入口都撞见）：EXPOSURE_LEDGER 行内；supplement attestation
头部固定行 `GENERATED_AFTER_REVEAL=YES(2026-08-14)`；`ops/SUPPLEMENT_LEDGER.md`
披露标记列；未来 MC verdict seal 的字段
`grid_authority="SUPPLEMENTAL_POST_REVEAL:MC-DS-S001"`。

```
RECOMMENDED_ND1_DISCLOSURE_CONTENT=ADOPT_SEVEN_POINTS_AS_WRITTEN
RECOMMENDED_ND1_DISCLOSURE_PLACEMENTS=ADOPT_FOUR_PLACEMENTS_AS_WRITTEN
ND1_DISCLOSURE_WORDING_BY_AARON=UNRESOLVED   # 措辞是否须 Aaron 亲拟
```

## §D.8 — `AARON_ND1_RATIFICATION_BLOCK_V1`（**已作废；正文已移除，勿签**）

```
AARON_ND1_RATIFICATION_BLOCK_V1
STATUS=SUPERSEDED_DO_NOT_SIGN
SUPERSEDED_BY=AARON_ND1_PROFILE_RATIFICATION_V1（§D.10；中间的 V2 亦已作废）
SUPERSEDED_REASON=DUPLICATE_AUTHORITY+PRESTART_REAUTH_PATH_OPEN+ARCHIVE_LIFECYCLE_MISSING
VERBATIM_TEXT_RECOVERABLE_AT=git commit b0d4f86f0e14671fc7eebb17e7ae4588a122bf87
                             （路径 ops/DECISION_PACKET_N00_AND_ND1.md §D.8）
```

作废原因（三项，详见 §D.9 开头的对照表）：

1. `APPROVED_GRAMMAR_GLOBAL_RULES` 一次性批准了四项治理选择，而同一份块里
   又给这四项各自的 `APPROVED_ND1_*` 字段——**重复权威**，可以填出形式完整
   而语义矛盾的批准块；
2. `PRESTART_COMMIT_CHANGE_REQUIRES_REAUTH=YES` 在状态机中**无路可走**
   （F1 之后只能到 P3 或 F3，同一 id 拿不到新 P2）；
3. P4 允许 `archive_failed` 却**没有任何后继定义**。

**正文为什么不原样留在这里**：V1 的字段表里含有 `APPROVED_GRAMMAR_GLOBAL_RULES`、
`APPROVED_SILENT_DELETE`、`APPROVED_DIVERGENT_PARTIAL_ACTION`、
`ND1_CREATE_TWO_EMPTY_SUPPLEMENTS_DIRECTORIES` 等**已被本轮取消的竞争性字段名**。
把它们逐字留在同一份文件里，等于把"每项选择只有一个权威字段"这条原则又打开一个
缺口——有人可以从作废块里复制出一个仍然读得通的字段。逐字文本并未丢失：它在
git 的 `b0d4f86` 提交里，那才是本仓库的不可变记录层。

**唯一可签署的块是 §D.10 的 `AARON_ND1_PROFILE_RATIFICATION_V1`。**

### D.8.1 配套的 N00 批准块（与 N-D1 分开，不可合并）

```
AARON_N00_STATE_RULING_BLOCK_V1
STATUS=PROPOSED_NOT_EFFECTIVE
N00_PRIMARY_SELECTED=UNRESOLVED              # YES | NO
N00_HYPOTHESIS_SELECTED=UNRESOLVED           # YES | NO
N00_DESIGN_WRAPPER_APPROVED=UNRESOLVED       # YES | NO
N00_TWO_CANDIDATES_REGISTERED_SEPARATELY=UNRESOLVED   # YES | NO
STATE_RULING_SETTLES=状态，仅此
STATE_RULING_DOES_NOT_SUPPLY=Round-4 矩阵正文与候选定义（见 §D.1.3 清单）
N00_CANDIDATE_SPECIFIC_BUILD_ALLOWED=NO（清单五项全部 PRESENT 之前恒为 NO）
END_AARON_N00_STATE_RULING_BLOCK_V1
```

### D.8.2 批准之后的精确下一步顺序（**仅为路线，不是授权**）

```
若 AARON_ND1_PROFILE_RATIFICATION_V1（§D.10）获批：
  N03  supplement authority 加固（C3 四层绑定 ＋ 把 §D.2.2 恒等式绑定到
       supplement 路径，复用 consumer.py 的同一批拒绝码）           工程，无数据面
  N04  supplement runner（默认拒绝；F1 的 gate_name 闭合枚举在此固定；
       若 APPROVED_ND1_PARTIAL_RECOVERY_RULE=MODIFY 则在此实现 rename
       并补回归测试）                                              工程，无数据面
  N05  supplement registry grammar ＋ parser（仅实现获批的批 1 词表；
       未获批的一律维持确定性拒绝）                                工程，无数据面
  N06  Codex R3 exact-tree 审查（fresh top-level session）
  → 之后才轮到 N-D2 / N09；N09 另需 Aaron 的 P2 精确授权
N03/N04/N05 三者均**不**触碰真实数据、**不**创建目录、**不**追加 registry 事件。
```

---

## §D.9 — 跨字段一致性、推荐 profile、逐字段参照清单

```
SECTION_D9_IS_CURRENT=YES
SUPERSEDES=§D.8 的 AARON_ND1_RATIFICATION_BLOCK_V1（唯一签署面见 §D.10）
DECISION_STATUS=PROPOSED_NOT_EFFECTIVE
NOTHING_IN_SECTION_D9_IS_APPROVED=YES
```

上一版批准块有三个缺陷，本节逐条修掉：

| 缺陷 | 后果 | 本节的修法 |
|---|---|---|
| `APPROVED_GRAMMAR_GLOBAL_RULES` 一次性批准了四项治理选择，而后面又给它们各自的字段 | Aaron 可以填出**形式完整、语义矛盾**的批准块 | §D.3.1 只留格式约束；每项选择只剩**一个**权威字段；派生量显式标注为不可批准（§D.9.2） |
| `PRESTART_COMMIT_CHANGE_REQUIRES_REAUTH=YES` 在状态机里无路可走 | 同一 id 在 F1 之后永远拿不到新 P2 | 新增 P2S 事件与 `F1 → P2S → P2` 路径（§D.3.2、§D.3.3） |
| P4 允许 `archive_failed` 但无后继定义 | 归档失败后能否进 P5、要不要重新授权、如何终局，全部无答案 | 新增 A1/A2/AX 与两个完整方案（§D.3.7） |

### D.9.1 跨字段一致性规则（**批准块的生效条件，不是建议**）

```
RATIFICATION_VALID_ONLY_IF=ALL_APPROVED_FIELDS_FILLED_AND_CROSS_FIELD_CONSISTENT
INCONSISTENT_COMBINATION=NOT_EFFECTIVE_AND_FAIL_CLOSED
```

即：只要下列任一依赖不满足，**整份批准块不生效**，相关节点维持 fail-closed。
不存在"部分生效"——半份语法比没有语法更危险。

```
C1  APPROVED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL
    ⇒ 全部 numbered supplement 行使用既有全局递增整数序列（现已用到 13），
      与 S0 事件共享同一编号空间，不另立平行序列。

C2  APPROVED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=SEPARATE
    ⇒ 必须同时提供完整的独立序列规范：parser 规则、唯一性规则、排序规则、
      崩溃后的恢复规则（如何判定"下一个编号"）。四者缺一 ⇒ 该选择无效。

C3  APPROVED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES
    ⇒ 必须同时 APPROVED_GRAMMAR_P2S=ADOPT_AS_WRITTEN（或带完整替代文本的
      MODIFY），且状态机含 F1 → P2S → P2(new commit) → P3。
      不得只保留"需要重新授权"这句散文而无事件与转移。

C4  APPROVED_ND1_POSTSTART_FAILURE_NEW_ID=YES
    ⇒ F2 之后的唯一合法路径是 F3 → T1 → P2'（新 id 重走完整授权）。
      同时要求 APPROVED_GRAMMAR_F3 与 APPROVED_GRAMMAR_T1 均已采纳。

C5  APPROVED_ND1_POSTSTART_FAILURE_NEW_ID=NO
    ⇒ 必须附一份完整、无歧义的**同 id 重试状态机**：残骸如何处置、旧
      P2 授权是否仍 live、是否需要新授权、重试次数上限、如何与
      `.partial` 规则协同。缺任一项 ⇒ 该选择无效。

C6  SUPERSEDE_TARGET / ID_REUSE / SUCCESSOR_REGISTRATION 三者必须互洽：
      APPROVED_ND1_SUPERSEDE_TARGET=2（supersede id 本身）
        ⇒ ID_REUSE_POLICY=NEVER 且 SUCCESSOR_REGISTRATION_REQUIRED=YES(T1)
      APPROVED_ND1_SUPERSEDE_TARGET=1（只 supersede P2 授权）
        ⇒ 与 APPROVED_ND1_POSTSTART_FAILURE_NEW_ID=YES **冲突**
          （只废授权而保留 id，就不可能强制换 id）⇒ 组合无效
      APPROVED_ND1_SUPERSEDE_TARGET=3（两行分记）
        ⇒ F3 必须拆成两个事件且各自有独立的前置/后继定义（须附文本）
    详见 §D.9.2 派生表。

C7  任何合法组合下，同一 supplement_id 在任一时刻**至多一个 live P2**。
    P2S 使旧 P2 立即失去 live 身份；F3 使整条链终止。
    parser 侧对应 MULTIPLE_LIVE_P2_FOR_ONE_ID / MULTIPLE_LIVE_P2_AFTER_P2S。

C8  任何 `MODIFY` 选择必须携带**完整替代文本**。只写 `MODIFY` 而不给文本
    的字段视为未填 ⇒ 整块不生效。

C9  APPROVED_ND1_ARCHIVE_FAILURE_POLICY=B
    ⇒ 必须同时给出 §D.3.7 的 B1–B5 全部答案。缺任一项 ⇒ 该选择无效。

C10 APPROVED_ND1_PARTIAL_RECOVERY_RULE=MODIFY
    ⇒ 必须填 APPROVED_ND1_PARTIAL_MODIFY_TEXT（分支 E 与分支 C 的处置各自
      写明）。选 KEEP 时该字段留 N/A，且须知悉：分支 E 仍会删除本次刚写的
      字节（§D.5.1 事实表不变）。
```

### D.9.2 派生量表（**不是可批准字段**）

下列值由权威字段机械推导。Aaron **不填**它们；任何单独填写视为矛盾组合。

| 派生量 | 由谁决定 | 推荐组合下的取值 |
|---|---|---|
| `ID_REUSE_POLICY` | `SUPERSEDE_TARGET` + `POSTSTART_FAILURE_NEW_ID` | `NEVER_AFTER_START`（pre-start 同 id 仍可重试） |
| `SUCCESSOR_REGISTRATION_REQUIRED` | `SUPERSEDE_TARGET` | `YES`（T1 必需） |
| `P2_PERMITTED_PREDECESSOR` | `PRESTART_COMMIT_CHANGE_REAUTH` | `P1 \| P2S` |
| `F1_PERMITTED_SUCCESSOR` | `PRESTART_COMMIT_CHANGE_REAUTH` | `P3（commit 未变）\| P2S（commit 变）\| F3` |
| `P4_PERMITTED_SUCCESSOR` | `ARCHIVE_FAILURE_POLICY` | `P5 \| F2v`（A 下 P4 仅在 archive_ok 发射） |
| `P5_PERMITTED_PREDECESSOR` | `ARCHIVE_FAILURE_POLICY` | `P4 \| A2`（A1、AX 均非法） |
| `P5_REACHABILITY_AFTER_ARCHIVE_FAILURE` | `ARCHIVE_FAILURE_POLICY` | `仅经 A2`；`AX 之后不可达` |
| `AX_TERMINAL` | 语法定义（非选择） | `NO`——唯一后继 `F3`，`F3` 才是终态 |
| `FINAL_ARCHIVE_FAILURE_TERMINAL` | `ARCHIVE_FAILURE_POLICY` | `F3`（经 `AX → F3`） |
| `SILENT_DELETE_FORBIDDEN` | `PARTIAL_RECOVERY_RULE` | `MODIFY ⇒ YES`；`KEEP ⇒ NO（分支 E 仍删）` |
| `NUMBERED_ROW_SEQ_SOURCE` | `SUPPLEMENT_SEQUENCE_NAMESPACE` | 既有全局序列 |

### D.9.3 推荐 profile（一次性填法；**仍不是批准**）

为减少手填数十个字段的出错面，下面给出一份满足 §D.9.1 全部依赖的自洽组合。
Aaron 可以整份采纳，也可以提交一份完整修改版 profile。

```
BEGIN_ND1_RECOMMENDED_PROFILE_R1
PROFILE_ID=ND1_RECOMMENDED_PROFILE_R1
PROFILE_FIELD_PREFIX=RECOMMENDED_（本块内每一行都是提案值；块内不存在任何已批准值）
PROFILE_STATUS=PROPOSED_NOT_EFFECTIVE
RECOMMENDED_GRAMMAR_FORMAT_RULES=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P2S=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P3=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P4=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P5=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_A1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_A2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_AX=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F2V=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F3=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_T1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_STATE_MACHINE=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_PARSER_FAIL_CLOSED_RULES=ADOPT_AS_WRITTEN
RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04
RECOMMENDED_ND1_PARSER_MALFORMED_ROW_POLICY=B_REFUSE
RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL
RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES
RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID=YES
RECOMMENDED_ND1_SUPERSEDE_TARGET=2_SUPERSEDES_SUPPLEMENT_ID_ITSELF
RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY=A
RECOMMENDED_ND1_FORMAL_TRIAL=NO
RECOMMENDED_ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE=NO
RECOMMENDED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT=NO
RECOMMENDED_ND1_SUPPLEMENT_LEDGER_CREATE=YES
RECOMMENDED_ND1_EXPOSURE_ROW_QUANTITY_ZERO=YES
RECOMMENDED_ND1_STRUCTURAL_ACCESS_CHARACTERISATION=STRUCTURAL_LABEL_NOT_OUTCOME
RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY
RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY
RECOMMENDED_ND1_OUTPUT_ROOT_OPTION=A
RECOMMENDED_ND1_SUPPLEMENT_DIRECTORY_NAME=2_ID_UNDERSCORE_UTC
RECOMMENDED_ND1_FUTURE_DIRECTORY_POLICY=REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE
RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED=NO
RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO
RECOMMENDED_ND1_DISCLOSURE_CONTENT=ADOPT_SEVEN_POINTS_AS_WRITTEN
RECOMMENDED_ND1_DISCLOSURE_PLACEMENTS=ADOPT_FOUR_PLACEMENTS_AS_WRITTEN
RECOMMENDED_ND1_DISCLOSURE_WORDING_BY_AARON=YES
RECOMMENDED_ND1_EXECUTION_SENTENCE_BINDS=supplement_id+40hex_commit+output_root
RECOMMENDED_ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY=YES
RECOMMENDED_ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES
PROFILE_CONTAINS_NO_EXECUTION_AUTHORIZATION=YES
PROFILE_CREATES_NO_DIRECTORY=YES
PROFILE_APPENDS_NO_REGISTRY_OR_EXPOSURE_EVENT=YES
END_ND1_RECOMMENDED_PROFILE_R1
```

**规范化与摘要口径**（可被任何冷读者重算）：

```
CANONICAL_BYTES=BEGIN 与 END 两行之间的行（不含这两行），LF 结尾，UTF-8，逐行原样
PROFILE_SHA256=0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5
```

**一致性自检**（本 profile 对 §D.9.1 逐条）：C1 满足（GLOBAL）；C2 不适用；
C3 满足（P2S 已采纳）；C4 满足（NEW_ID=YES 且 F3/T1 已采纳）；C5 不适用；
C6 满足（SUPERSEDE_TARGET=2 ⇒ ID_REUSE=NEVER_AFTER_START、T1 必需，且与
NEW_ID=YES 相容）；C7 满足（P2S/F3 各自使旧 P2 失效）；C8 满足
（唯一的 MODIFY 带完整文本）；C9 不适用（选 A）；C10 满足。

**归档契约自检**（政策 A 下）：`P5_PERMITTED_PREDECESSOR=P4 | A2` 两条入口
均可达（`P4→P5` 与 `A1→A2→P5`）；`AX_TERMINAL=NO` 且其唯一后继为 `F3`；
归档永久失败路径的终态是 `F3`，写作 `AX → F3`。

### D.9.4 `AARON_ND1_RATIFICATION_BLOCK_V2`（**已作废；不可签署**）

```
AARON_ND1_RATIFICATION_BLOCK_V2
STATUS=SUPERSEDED_NOT_SIGNABLE
SUPERSEDED_BY=AARON_ND1_PROFILE_RATIFICATION_V1（§D.10）
SUPERSEDED_REASON=TWO_ROUTES_NEITHER_SATISFIABLE
VERBATIM_TEXT_RECOVERABLE_AT=git commit 9011f5ea38b736b2b99c302c3af691c02e8d21bc
                             （路径 ops/DECISION_PACKET_N00_AND_ND1.md §D.9.4）
```

**作废原因（一处，但足以使整块不可签）**：V2 同时提供"路线 1＝填 profile 三项"
与"路线 2＝逐字段填约 43 个值"，而它自己的头部又写
`RATIFICATION_VALID_ONLY_IF=ALL_APPROVED_FIELDS_FILLED_AND_CROSS_FIELD_CONSISTENT`。
于是**无论选哪条路线，另一条路线的字段都会留在 `UNRESOLVED`**，生效条件永远
不满足——两条路线都签不成。

**修法**：废除"双路线"。唯一可签署对象是 §D.10 的
`AARON_ND1_PROFILE_RATIFICATION_V1`（三个待填值）。逐字段表作为**解释与设计
审计材料**保留在下面的 §D.9.4.1，但**不再是一条替代批准路线**，也不再包含任何
可填的 `APPROVED_` 赋值行。

#### D.9.4.1 逐字段参照清单（**只读，不可签**）

```
FIELDWISE_TABLE_STATUS=REFERENCE_ONLY_NOT_SIGNABLE
FIELDWISE_VALUES_ARE_NOT_AN_ALTERNATIVE_RATIFICATION_ROUTE=YES
SOLE_AUTHORITY_FOR_EVERY_ROW=ND1_RECOMMENDED_PROFILE_R1 的对应 RECOMMENDED_ 行
```

本表说明"存在哪些治理选择、各自的权威在哪一行、推荐值是什么"。它**没有**可填
栏位：任何有效批准都必须对应一份完整、自洽、可哈希的 profile（§D.10.2）。

| 治理选择 | 唯一权威（profile 行） | 推荐值 | 可选值／依赖 |
|---|---|---|---|
| `GRAMMAR_FORMAT_RULES` | `RECOMMENDED_GRAMMAR_FORMAT_RULES` | `ADOPT_AS_WRITTEN` | ADOPT_AS_WRITTEN \| MODIFY(+文本) \| REJECT |
| `GRAMMAR_P1` | `RECOMMENDED_GRAMMAR_P1` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_P2` | `RECOMMENDED_GRAMMAR_P2` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_P2S` | `RECOMMENDED_GRAMMAR_P2S` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_P3` | `RECOMMENDED_GRAMMAR_P3` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_P4` | `RECOMMENDED_GRAMMAR_P4` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_P5` | `RECOMMENDED_GRAMMAR_P5` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_A1` | `RECOMMENDED_GRAMMAR_A1` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_A2` | `RECOMMENDED_GRAMMAR_A2` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_AX` | `RECOMMENDED_GRAMMAR_AX` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_F1` | `RECOMMENDED_GRAMMAR_F1` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_F2` | `RECOMMENDED_GRAMMAR_F2` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_F2V` | `RECOMMENDED_GRAMMAR_F2V` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_F3` | `RECOMMENDED_GRAMMAR_F3` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_T1` | `RECOMMENDED_GRAMMAR_T1` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_STATE_MACHINE` | `RECOMMENDED_GRAMMAR_STATE_MACHINE` | `ADOPT_AS_WRITTEN` | — |
| `GRAMMAR_PARSER_FAIL_CLOSED_RULES` | `RECOMMENDED_GRAMMAR_PARSER_FAIL_CLOSED_RULES` | `ADOPT_AS_WRITTEN` | — |
| `F1_GATE_NAME_ENUM` | `RECOMMENDED_F1_GATE_NAME_ENUM` | `DEFER_TO_N04` | DEFER_TO_N04 \| <闭合枚举文本> |
| `ND1_PARSER_MALFORMED_ROW_POLICY` | `RECOMMENDED_ND1_PARSER_MALFORMED_ROW_POLICY` | `B_REFUSE` | A \| B |
| `ND1_SUPPLEMENT_SEQUENCE_NAMESPACE` | `RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE` | `GLOBAL` | GLOBAL \| SEPARATE(+C2 四项文本) |
| `ND1_PRESTART_COMMIT_CHANGE_REAUTH` | `RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH` | `YES` | YES(⇒C3) \| NO |
| `ND1_POSTSTART_FAILURE_NEW_ID` | `RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID` | `YES` | YES(⇒C4) \| NO(⇒C5 附状态机) |
| `ND1_SUPERSEDE_TARGET` | `RECOMMENDED_ND1_SUPERSEDE_TARGET` | `2_SUPERSEDES_SUPPLEMENT_ID_ITSELF` | 1 \| 2 \| 3（见 C6） |
| `ND1_ARCHIVE_FAILURE_POLICY` | `RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY` | `A` | A \| B(+B1-B5 全部答案) |
| `ND1_FORMAL_TRIAL` | `RECOMMENDED_ND1_FORMAL_TRIAL` | `NO` | YES(+编号) \| NO |
| `ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE` | `RECOMMENDED_ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE` | `NO` | — |
| `ND1_STARTED_CONSUMES_EXPOSURE_SLOT` | `RECOMMENDED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT` | `NO` | — |
| `ND1_SUPPLEMENT_LEDGER_CREATE` | `RECOMMENDED_ND1_SUPPLEMENT_LEDGER_CREATE` | `YES` | — |
| `ND1_EXPOSURE_ROW_QUANTITY_ZERO` | `RECOMMENDED_ND1_EXPOSURE_ROW_QUANTITY_ZERO` | `YES` | — |
| `ND1_STRUCTURAL_ACCESS_CHARACTERISATION` | `RECOMMENDED_ND1_STRUCTURAL_ACCESS_CHARACTERISATION` | `STRUCTURAL_LABEL_NOT_OUTCOME` | — |
| `ND1_PARTIAL_RECOVERY_RULE` | `RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE` | `MODIFY` | KEEP \| MODIFY(⇒C10) |
| `ND1_PARTIAL_MODIFY_TEXT` | `RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT` | `BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY` | MODIFY 时必填；KEEP 时填 N/A |
| `ND1_OUTPUT_ROOT_OPTION` | `RECOMMENDED_ND1_OUTPUT_ROOT_OPTION` | `A` | A \| B |
| `ND1_SUPPLEMENT_DIRECTORY_NAME` | `RECOMMENDED_ND1_SUPPLEMENT_DIRECTORY_NAME` | `2_ID_UNDERSCORE_UTC` | 1 \| 2 |
| `ND1_FUTURE_DIRECTORY_POLICY` | `RECOMMENDED_ND1_FUTURE_DIRECTORY_POLICY` | `REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE` | — |
| `ND1_WRITE_PROBE_AUTHORIZED` | `RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED` | `NO` | — |
| `ND1_SUPPLEMENT_EXECUTION_AUTHORIZED` | `RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED` | `NO` | post-reveal 披露 |
| `ND1_DISCLOSURE_CONTENT` | `RECOMMENDED_ND1_DISCLOSURE_CONTENT` | `ADOPT_SEVEN_POINTS_AS_WRITTEN` | — |
| `ND1_DISCLOSURE_PLACEMENTS` | `RECOMMENDED_ND1_DISCLOSURE_PLACEMENTS` | `ADOPT_FOUR_PLACEMENTS_AS_WRITTEN` | — |
| `ND1_DISCLOSURE_WORDING_BY_AARON` | `RECOMMENDED_ND1_DISCLOSURE_WORDING_BY_AARON` | `YES` | 未来执行授权语句的边界 |
| `ND1_EXECUTION_SENTENCE_BINDS` | `RECOMMENDED_ND1_EXECUTION_SENTENCE_BINDS` | `supplement_id+40hex_commit+output_root` | — |
| `ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY` | `RECOMMENDED_ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY` | `YES` | — |
| `ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE` | `RECOMMENDED_ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE` | `YES` | ==== 生效边界（无论怎么填都成立）===================================== |

派生量不在本表内——见 §D.9.2，它们由上表的权威行机械推导，任何单独指定都是
矛盾组合。

### D.9.5 配套 N00 状态块（不变，与 N-D1 分开，不可合并）

见 §D.8.1 `AARON_N00_STATE_RULING_BLOCK_V1`——本轮未修改，三个字段仍全部
`UNRESOLVED`，`N00_MISSING_AUTHORITY_CHECKLIST`（§D.1.3）五项仍全部
`MISSING`。N00 与 N-D1 是两份独立批准，任一份获批都不影响另一份。

---

## §D.10 — 唯一签署面：`AARON_ND1_PROFILE_RATIFICATION_V1`

```
SECTION_D10_IS_CURRENT=YES
SIGNABLE_RATIFICATION_ROUTES=1
SUPERSEDES=AARON_ND1_RATIFICATION_BLOCK_V1（§D.8）, AARON_ND1_RATIFICATION_BLOCK_V2（§D.9.4）
DECISION_STATUS=PROPOSED_NOT_EFFECTIVE
NOTHING_IN_SECTION_D10_IS_APPROVED=YES
```

本文件到本节为止**只有一个**可签署对象。§D.8 的 V1 与 §D.9.4 的 V2 都是墓碑，
§D.9.4.1 的逐字段清单是只读参照。任何有效批准都必须对应一份完整、自洽、
可哈希的 profile——这样"批准了什么"永远是一个可以逐字节复算的对象，而不是
几十个可能互相矛盾的独立勾选。

### D.10.1 可签署块

```
AARON_ND1_PROFILE_RATIFICATION_V1
STATUS=PROPOSED_NOT_EFFECTIVE
APPROVED_PROFILE_ID=UNRESOLVED
APPROVED_PROFILE_SHA256=UNRESOLVED
APPROVAL_BINDS_DOC_HEAD=UNRESOLVED
```

**恰好三个待填值，没有第四个。** 逐字段表**不需要**、也**不可以**同时填写
（`FIELDWISE_VALUES_ARE_NOT_AN_ALTERNATIVE_RATIFICATION_ROUTE=YES`）。

### D.10.2 合法生效条件

```
RATIFICATION_VALID_ONLY_IF=
  APPROVED_PROFILE_ID == ND1_RECOMMENDED_PROFILE_R1
  AND APPROVED_PROFILE_SHA256 == mechanically_recomputed_profile_sha256
  AND APPROVAL_BINDS_DOC_HEAD == exact_current_40hex_doc_commit
  AND PROFILE_CROSS_FIELD_CHECK == PASS
  AND Aaron actively sends the completed three-line approval in a later message
```

逐条口径：

| 条件 | 如何机械核验 |
|---|---|
| `APPROVED_PROFILE_ID` | 必须逐字等于 §D.9.3 的 `PROFILE_ID`；自拟 id 走 §D.10.3 |
| `APPROVED_PROFILE_SHA256` | 对 `BEGIN`/`END` 之间的行（不含标记行，LF，UTF-8）重算 SHA-256，与 §D.9.3 的 `PROFILE_SHA256` 比对；**不得凭假设沿用**，每次都重算 |
| `APPROVAL_BINDS_DOC_HEAD` | 必须等于承载该 profile 的那一个 doc commit 的完整 40 位哈希；文档一旦再次修改，旧批准即失效，须对新 HEAD 重新批准 |
| `PROFILE_CROSS_FIELD_CHECK` | profile 对 §D.9.1 的 C1–C10 逐条通过（§D.9.3 附自检；实现侧由 N05 的 parser 复算） |
| Aaron 主动发送 | 见下方 `NOT_APPROVAL` 清单 |

```
INCONSISTENT_OR_INCOMPLETE=NOT_EFFECTIVE_AND_FAIL_CLOSED
PARTIAL_EFFECT=DOES_NOT_EXIST（三项缺一即整体不生效）
NOT_APPROVAL=[本执行提示词, 本文件的生成或修订, Aaron 要求准备决策包,
              Aaron 阅读本文件或终报, 任何 RECOMMENDED_* 行, 任何"工程建议",
              profile 的存在, §D.9.4.1 参照清单里的任何值,
              终报中预填了 doc HEAD 这一事实,
              任何读起来像条件同意的措辞, 沉默或未反对]
AMBIGUOUS_PERMISSION=取限制性读法并停止（QROS §12）
```

### D.10.3 修改 profile 的路径（不接受推荐值时的**唯一**走法）

```
MODIFICATION_PATH=
  Aaron specifies requested changes
  → builder produces ND1_RECOMMENDED_PROFILE_R2
  → all cross-field checks rerun
  → new canonical profile SHA-256
  → new doc-only commit
  → Aaron approves R2 profile id + hash + exact doc HEAD
```

**禁止**从 §D.9.4.1 的参照清单里自由挑选若干值直接生效——那正是 V2 的
"双路线"缺陷，会重新打开"形式完整、语义矛盾"的填法。每一次有效批准都对应
一个**完整、自洽、可哈希的 profile**，profile 是批准的最小粒度。

R2 的产出仍是纯文档轮：不创建目录、不追加 registry／exposure 事件、
不执行任何东西。

### D.10.4 生效之后仍然不被授权的事项

```
RATIFICATION_CREATES_NO_DIRECTORY=YES
RATIFICATION_DOES_NOT_AUTHORIZE=[MC 执行, supplement 执行, 策略 build,
                                 真实数据读取, 目录创建, 写探针,
                                 registry/exposure 事件追加, 归档重试,
                                 N00 的候选定义]
EACH_EXECUTION_STILL_NEEDS=Aaron 单独的、绑定完整 40 位 commit 的精确授权语句
SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES
```

### D.10.5 与 N00 的关系（不变）

N00 是另一份独立批准（§D.8.1 `AARON_N00_STATE_RULING_BLOCK_V1`，三字段仍全部
`UNRESOLVED`；§D.1.3 的 `N00_MISSING_AUTHORITY_CHECKLIST` 五项仍全部 `MISSING`）。
两份批准互不影响，也不得合并成一次签署。
