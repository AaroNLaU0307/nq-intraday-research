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

## 项 1 — supplement day-universe 定义（**样本总体定义，最重量级**）

### 1.1 机械事实（源码核实，未读任何封存数值）

| 事实 | 出处 |
|---|---|
| `ref_dates` = 八个 `MC_HANDOFF_{engine}_{scenario}.jsonl` 的 trade_date 键集；八文件键集必须**完全相同**，否则拒 `record_set_drift_across_files` | `consumer.py:556-560` |
| `day_sequences[θ]` = 逐 θ 的 `sorted(tp_days ∪ fp_days)`，取自 `S0_REPORT.json` 的 `oracle_daily.{θ}.day_universe` | `consumer.py:583-612` |
| **`tp_days ⊆ ref_dates` 被强制**（`tp_day_without_record`） | `consumer.py:610-613` |
| **`fp_days ⊆ ref_dates` 未被任何检查强制** | 同上（只检查 tp） |
| GRID 分层抽样要求 strata 覆盖 `set(d_tp) ∪ set(d_fp)`（**逐 θ**）；**缺键抛错、多余键被容忍** | `gridmix.py:508`＋`gridmix.py:180`；池只由这两个集合构成 `gridmix.py:519-520` |
| θ 通道之间 TP/FP 划分**不同**（同一日可在 θ=0.3 为 TP、在 θ=0.5 为 FP） | 冻结 θ 语义（S0 §7）＋报告结构 |

### 1.2 三个选项

| 选项 | 定义 | 机械后果 |
|---|---|---|
| **A** | `∪θ (tp_days ∪ fp_days)`（oracle day universe 的 θ 并集） | 恰好等于重放所需的最小充分集；生成的结构标签最少（盲式姿态最强）；θ-依赖 |
| **B** | `ref_dates`（八文件记录集结构全池） | θ-无关、面向未来（任何新 θ 或重分类都已覆盖）；但**存在风险**：若有 FP 日不在 `ref_dates`（代码未强制），B 缺该日 strata → 重放时 gridmix 抛错 |
| **C** | `A ∪ B`（并集） | 在 A、B 两种真实关系下都安全（多余键被 gridmix 容忍）；生成的标签最多；掩盖 A/B 差异本身 |

### 1.3 附带请求：结构性关系探针（是否获准）

可运行一个**只输出计数、不输出任何日期或研究值**的机械探针，回答：
`|A|`、`|B|`、`|A\B|`、`|B\A|`（四个整数）。
- 若 `|A\B| == 0` → A ⊆ B 成立，选 B 无缺键风险。
- 该探针需读取封存 `S0_REPORT.json` 与八个 handoff 文件的**键结构**（不读数值）。
- **Aaron 需裁定**：(a) 是否获准运行；(b) 四个计数本身如何计 exposure
  （工程建议：quantity=0 交叉引用行，理由=纯结构计数、零候选关系被查看，
  与 IR-28d 先例同口径——**建议，非裁定**）。

### 1.4 工程建议（**非裁定**）

倾向 **A**：它精确等于冻结重放契约所需（gridmix 的 `all_dates` 就是逐 θ 的
`tp∪fp`），最小化生成的结构信息，符合盲式补充封存的初衷。若 Aaron 希望消除
FP 覆盖风险且不介意多生成标签，**C** 是安全兜底。**B 单独选用需先跑 1.3 探针
确认 `|A\B| == 0`**，否则有真实的重放缺键风险。

```
N-D1.1_RULING=<A|B|C>
N-D1.1_PROBE_AUTHORIZED=<YES|NO>
N-D1.1_PROBE_EXPOSURE=<记账口径>
```

---

## 项 2 — supplement registry 批 1 事件词汇／字段／状态转移

现状：`day_strata_supplement.py:103-122` 的 `authorize_supplement` **无条件拒绝**，
拒绝理由正是"registry 语法中不存在该词表"。批准后方可实现 parser。

提案词表（状态机 `PROPOSED→AUTHORIZED→STARTED→SEALED→INDEPENDENTLY_VERIFIED→
CONSUMED_BY_GRID_REPLAY`，失败族 `ATTEMPT_FAILURE / FAILED / SUPERSEDED`）：

| # | 事件 | 行形状（模板，占位符未填，**模板≠授权**） |
|---|---|---|
| P1 | `SUPPLEMENT_PROPOSED` | `\| <n> \| <UTC> \| **SUPPLEMENT_PROPOSED** \| <commit40> \| main agent \| [MC-DS-S001] 依 IR-29b Option B 提案；schema mc_day_strata_supplement.v1；本行非授权 \|` |
| P2 | `SUPPLEMENT_EXECUTION_AUTHORIZED` | Aaron 逐字发送执行语句（模板见 `ops/MC_DR5_BUILD_PACKET.md` §13.5）；registry 行 note = 该语句逐字 |
| P3 | `SUPPLEMENT_RUN_STARTED` | `\| + \| <UTC> \| SUPPLEMENT_RUN_STARTED \| <commit7> \| main agent (mc_ds_runner) \| [MC-DS-S001] atomic start; structural access begins \|` |
| P4 | `SUPPLEMENT_SEALED` | `\| + \| <UTC> \| SUPPLEMENT_SEALED \| <commit7> \| … \| [MC-DS-S001] sealed sha256=<64hex>; rows_digest=<64hex>; day_universe_digest=<64hex>; n_rows=<int>; archive=<状态> \|` |
| P5 | `SUPPLEMENT_INDEPENDENTLY_VERIFIED` | `\| <n> \| <UTC> \| **SUPPLEMENT_INDEPENDENTLY_VERIFIED** \| <commit40> \| <verifier> \| [MC-DS-S001] 二次重导 rows_digest 复现=YES; headline replay identity=PASS(<n>格); attestation sha=<64hex> \|` |
| P6 | `SUPPLEMENT_CONSUMED_BY_GRID_REPLAY` | 由 MC runner 在 K 证据装配时追加 |
| F1/F2/F3 | `SUPPLEMENT_ATTEMPT_FAILURE` / `SUPPLEMENT_FAILED` / `SUPPLEMENT_SUPERSEDED` | 镜像既有 `PRE_RUN_ATTEMPT_FAILURE`（registry:27,31）与 `RUN_AUTHORIZATION_SUPERSEDED`（:28,32）语法 |

```
N-D1.2_RULING=<逐项批准/修改/否决>
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
   （`outcome_seen=NO`、`formal_trial=NO`、`quantity=0`）——请确认此定性。

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
