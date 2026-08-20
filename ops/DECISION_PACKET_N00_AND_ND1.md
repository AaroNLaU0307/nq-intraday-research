# 决策包 N00 ＋ N-D1（Aaron 专属；本文件不含任何已批准值）

```
PACKET_ID=DECISION_PACKET_N00_AND_ND1
PREPARED_BY=Opus 5 main agent（依 EXECUTE_OPUS5_MC_TO_STRATEGY_MASTER_V1）
PREPARED_FROM_HEAD=c5c819beb5c13e52bcd7ca974a4e40787684b10f
DECISION_STATUS=PROPOSED_NOT_EFFECTIVE
STATUS=AWAITING_AARON_RULING
NOTHING_HEREIN_IS_APPROVED=YES
CURRENT_SECTION=§D（2026-08-20 现势修正；与上文冲突处以 §D 为准）
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
六个专属拒绝码：

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

### D.3.1 全局语法规则（提案）

```
SUPPLEMENT_ID_PATTERN=^MC-DS-S[0-9]{3}$
FIRST_ID=MC-DS-S001
ID_NEVER_REUSED=YES
POST_START_RETRY_USES_NEW_ID=YES
PRESTART_COMMIT_CHANGE_REQUIRES_REAUTH=YES
NUMBERED_EVENTS_SHARE_GLOBAL_REGISTRY_SEQUENCE=YES
RUNNER_STAGE_AND_GATE_TOKENS=CLOSED_ENUMS
UNKNOWN_OR_DUPLICATE_FIELDS=REFUSE
```

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
PERMITTED_PREDECESSOR=P1（同 supplement_id）
PERMITTED_SUCCESSOR=P3 | F1 | F3
TERMINAL=NO
INCIDENT_FIELD=N/A
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
PERMITTED_PREDECESSOR=P3
PERMITTED_SUCCESSOR=P5 | F2v
TERMINAL=NO
INCIDENT_FIELD=N/A
```

**P5 `SUPPLEMENT_INDEPENDENTLY_VERIFIED`**

```
TOKEN=SUPPLEMENT_INDEPENDENTLY_VERIFIED
NUMBERED=YES
ACTOR=<verifier>（fresh top-level session；不得是产出会话）
COMMIT_FIELD=40-hex
REQUIRED_FIELDS=[supplement_id, rederivation_reproduced(YES|NO),
                 headline_replay_identity(PASS|FAIL), n_cells(int),
                 attestation_sha256(64hex)]
PERMITTED_PREDECESSOR=P4
PERMITTED_SUCCESSOR=（N-D1 范围内为终态；原 P6 归 N-D3）
TERMINAL=YES_WITHIN_ND1
INCIDENT_FIELD=N/A
```

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
PERMITTED_SUCCESSOR=P3（修复后重试，同 id）| F3
RETRY_ID=同 id 可复用（pre-start 未消耗任何东西）
REAUTH_ON_COMMIT_CHANGE=YES（见 §D.4.2）
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

### D.3.3 状态机（提案）

```
P1 → P2 → P3 → P4 → P5              成功路径（N-D1 到 P5 为止）
     └→ F1 → P3                     pre-start 失败，同 id 重试
             └→ F3                  放弃
          P3 └→ F2  → F3 → T1 → P2' post-start 失败，必须换 id
          P4 └→ F2v → F3 → T1 → P2' 独立验证失败，封存件不删
```

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
ND1_PARTIAL_RECOVERY_RULE=MODIFY
DIVERGENT_PARTIAL_ACTION=RENAME_TO_.partial.divergent.<incident_id>
SILENT_DELETE=FORBIDDEN
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
ND1_OUTPUT_ROOT_OPTION=A
ND1_CREATE_TWO_EMPTY_SUPPLEMENTS_DIRECTORIES=PROPOSED
ND1_WRITE_PROBE_AUTHORIZED=NO
ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO
```

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
ND1_DISCLOSURE_CONTENT=PROPOSED
ND1_DISCLOSURE_PLACEMENTS=PROPOSED
ND1_DISCLOSURE_WORDING_BY_AARON=UNRESOLVED   # 措辞是否须 Aaron 亲拟
```

## §D.8 — `AARON_ND1_RATIFICATION_BLOCK_V1`（逐字批准块）

```
AARON_ND1_RATIFICATION_BLOCK_V1
STATUS=PROPOSED_NOT_EFFECTIVE
EFFECTIVE_ONLY_IF=Aaron 在后续消息中主动逐字批准本块并填写全部 APPROVED_* 字段
NOT_APPROVAL=[本执行提示词, 本文件的生成或修订, Aaron 要求准备决策包,
              Aaron 阅读本文件或终报, 任何 RECOMMENDED_* 行, 任何"工程建议",
              任何读起来像条件同意的措辞, 沉默或未反对]
AMBIGUOUS_PERMISSION=取限制性读法并停止（QROS §12）

# ---- 1. registry grammar（§D.3）----------------------------------------
RECOMMENDED_GRAMMAR_GLOBAL_RULES=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_GLOBAL_RULES=UNRESOLVED          # ADOPT_AS_WRITTEN | MODIFY | REJECT
RECOMMENDED_GRAMMAR_P1_PROPOSED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_P1_PROPOSED=UNRESOLVED
RECOMMENDED_GRAMMAR_P2_EXECUTION_AUTHORIZED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_P2_EXECUTION_AUTHORIZED=UNRESOLVED
RECOMMENDED_GRAMMAR_P3_RUN_STARTED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_P3_RUN_STARTED=UNRESOLVED
RECOMMENDED_GRAMMAR_P4_SEALED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_P4_SEALED=UNRESOLVED
RECOMMENDED_GRAMMAR_P5_INDEPENDENTLY_VERIFIED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_P5_INDEPENDENTLY_VERIFIED=UNRESOLVED
RECOMMENDED_GRAMMAR_F1_ATTEMPT_FAILURE=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_F1_ATTEMPT_FAILURE=UNRESOLVED
RECOMMENDED_GRAMMAR_F2_FAILED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_F2_FAILED=UNRESOLVED
RECOMMENDED_GRAMMAR_F2V_VERIFICATION_FAILED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_F2V_VERIFICATION_FAILED=UNRESOLVED
RECOMMENDED_GRAMMAR_F3_SUPERSEDED=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_F3_SUPERSEDED=UNRESOLVED
RECOMMENDED_GRAMMAR_T1_SUCCESSOR_REGISTRATION=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_T1_SUCCESSOR_REGISTRATION=UNRESOLVED
RECOMMENDED_GRAMMAR_STATE_MACHINE=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_STATE_MACHINE=UNRESOLVED
RECOMMENDED_GRAMMAR_PARSER_FAIL_CLOSED_RULES=ADOPT_AS_WRITTEN
APPROVED_GRAMMAR_PARSER_FAIL_CLOSED_RULES=UNRESOLVED
RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04（与 runner 同批固定）
APPROVED_F1_GATE_NAME_ENUM=UNRESOLVED

RECOMMENDED_ND1_SUPERSEDE_TARGET=SUPERSEDES_SUPPLEMENT_ID_ITSELF
APPROVED_ND1_SUPERSEDE_TARGET=UNRESOLVED    # 1 | 2 | 3（见 §D.3.2 F3）

RECOMMENDED_ND1_PARSER_MALFORMED_ROW_POLICY=B_REFUSE
APPROVED_ND1_PARSER_MALFORMED_ROW_POLICY=UNRESOLVED         # A | B

# ---- 2. trial / exposure 记账（§D.4）------------------------------------
RECOMMENDED_ND1_FORMAL_TRIAL=NO
APPROVED_ND1_FORMAL_TRIAL=UNRESOLVED                        # YES(+编号) | NO
RECOMMENDED_ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE=NO
APPROVED_ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE=UNRESOLVED
RECOMMENDED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT=NO
APPROVED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT=UNRESOLVED
RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL
APPROVED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=UNRESOLVED       # GLOBAL | SEPARATE
RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES
APPROVED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=UNRESOLVED
RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID=YES
APPROVED_ND1_POSTSTART_FAILURE_NEW_ID=UNRESOLVED

# ---- 3. supplement ledger 与 exposure 行（原项 5）------------------------
RECOMMENDED_ND1_SUPPLEMENT_LEDGER_CREATE=YES
APPROVED_ND1_SUPPLEMENT_LEDGER_CREATE=UNRESOLVED
RECOMMENDED_ND1_EXPOSURE_ROW_QUANTITY_ZERO=YES
APPROVED_ND1_EXPOSURE_ROW_QUANTITY_ZERO=UNRESOLVED
RECOMMENDED_ND1_STRUCTURAL_ACCESS_CHARACTERISATION=STRUCTURAL_LABEL_NOT_OUTCOME
APPROVED_ND1_STRUCTURAL_ACCESS_CHARACTERISATION=UNRESOLVED
LEDGER_ROW_FORMAL_TRIAL_FIELD=<N-D1.3_AARON_RULING>   # 永不预填

# ---- 4. .partial 失败证据（§D.5）----------------------------------------
RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY
APPROVED_ND1_PARTIAL_RECOVERY_RULE=UNRESOLVED               # KEEP | MODIFY
RECOMMENDED_DIVERGENT_PARTIAL_ACTION=RENAME_TO_.partial.divergent.<incident_id>
APPROVED_DIVERGENT_PARTIAL_ACTION=UNRESOLVED
RECOMMENDED_SILENT_DELETE=FORBIDDEN
APPROVED_SILENT_DELETE=UNRESOLVED
IMPLEMENTATION_STATUS=NOT_STARTED

# ---- 5. 输出根（§D.6）---------------------------------------------------
RECOMMENDED_ND1_OUTPUT_ROOT_OPTION=A
APPROVED_ND1_OUTPUT_ROOT_OPTION=UNRESOLVED                  # A | B
RECOMMENDED_ND1_SUPPLEMENT_DIRECTORY_NAME=OPTION_2_ID_UNDERSCORE_UTC
APPROVED_ND1_SUPPLEMENT_DIRECTORY_NAME=UNRESOLVED           # 1 | 2
RECOMMENDED_ND1_CREATE_TWO_EMPTY_SUPPLEMENTS_DIRECTORIES=PROPOSED
APPROVED_ND1_CREATE_TWO_EMPTY_SUPPLEMENTS_DIRECTORIES=UNRESOLVED
RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED=NO
APPROVED_ND1_WRITE_PROBE_AUTHORIZED=UNRESOLVED
RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO
APPROVED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=UNRESOLVED

# ---- 6. post-reveal 披露（§D.7）----------------------------------------
RECOMMENDED_ND1_DISCLOSURE_CONTENT=ADOPT_SEVEN_POINTS_AS_WRITTEN
APPROVED_ND1_DISCLOSURE_CONTENT=UNRESOLVED
RECOMMENDED_ND1_DISCLOSURE_PLACEMENTS=ADOPT_FOUR_PLACEMENTS_AS_WRITTEN
APPROVED_ND1_DISCLOSURE_PLACEMENTS=UNRESOLVED
RECOMMENDED_ND1_DISCLOSURE_WORDING_BY_AARON=YES
APPROVED_ND1_DISCLOSURE_WORDING_BY_AARON=UNRESOLVED

# ---- 7. 后续精确执行授权语句的边界（master plan §5 N-D1 第 7 项）--------
RECOMMENDED_ND1_EXECUTION_SENTENCE_BINDS=[supplement_id, 40hex_commit, output_root]
APPROVED_ND1_EXECUTION_SENTENCE_BINDS=UNRESOLVED
RECOMMENDED_ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY=YES
APPROVED_ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY=UNRESOLVED
RECOMMENDED_ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES
APPROVED_ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=UNRESOLVED

# ---- 生效边界（无论上面怎么填都成立）------------------------------------
RATIFICATION_DOES_NOT_AUTHORIZE=[MC 执行, supplement 执行, 策略 build,
                                 真实数据读取, 目录创建, 写探针,
                                 registry/exposure 事件追加, N00 的候选定义]
EACH_EXECUTION_STILL_NEEDS=Aaron 单独的、绑定完整 40 位 commit 的精确授权语句
END_AARON_ND1_RATIFICATION_BLOCK_V1
```

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
若 AARON_ND1_RATIFICATION_BLOCK_V1 获批：
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
