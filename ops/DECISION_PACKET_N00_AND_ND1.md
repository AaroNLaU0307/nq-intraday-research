# 决策包 N00 ＋ N-D1（Aaron 专属；本文件不含任何已批准值）

```
PACKET_ID=DECISION_PACKET_N00_AND_ND1
PREPARED_BY=Opus 5 main agent（依 EXECUTE_OPUS5_MC_TO_STRATEGY_MASTER_V1）
PREPARED_AT_HEAD=ba7fa4a（N-PLAN 之后）
STATUS=AWAITING_AARON_RULING
NOTHING_HEREIN_IS_APPROVED=YES
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
