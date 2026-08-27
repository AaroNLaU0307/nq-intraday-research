# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** 我说「贴这个给 Sol／Fable」时，指的就是它。
> 你不必再去 `ops/` 里认哪个是最新的 prompt。

```
UPDATED = 2026-08-27 晚（三份裁定全部执行完；两轮 Sol 复审在飞；一条 builder 自纠）
```

---

## 现在挂着两轮 fresh Sol，回来就有活

```
qros-runtime  build-evidence/PROMPT_WINDOW2_SOL_ROUND4.md
              第二维护窗第 4 轮。钉子 095ac4e。前三轮均 HOLD 同一缺陷类，
              本轮送的是**边界裁定 ＋ 按它的实现**，不是第四条规则。
              **开篇披露：渲染层机制出自裁它的那个决裁席，从未经独立审查。**

ITSF          ops/PROMPT_MIGRATION_PLAN_SOL_REVIEW.md
              迁移方案复审。**送审版含一句 builder 写错的话**——勘误已备：
              ops/ERRATUM_TO_MIGRATION_PLAN_REVIEW.md，可直接递给该会话。
```

**两轮都 HOLD 走 reproduce-first，不采信、逐条复现再修。**

---

## 一条 builder 自纠，读裁定之前先读它

`ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`

builder 在至少四份文档里把 L-5 缺陷的**机制**（「会烧掉一次 trial」）写成了
**已发生的事故**。实测：registry 里 `BURNED/ABORTED/VOID` 为 **0**，
S0-T001 成功封存。**从来没有 trial 被烧掉过。**

**它触及两份裁定**：`dec-registry-migration` 拒绝路线 C 的理由之一是
「对一个**已经兑现过的风险**给了过轻的处置」——那句话的事实基础是错的。

**另**：OneDrive 实测处于**休眠**（文件无 `Offline`/`ReparsePoint`，零冲突副本，
主客户端未运行，最后登录 2026-01-06）。但账户仍配置着、Desktop 仍是重解析点
——**一步之遥，不是不可能**。迁移理由仍在，紧迫性下降。

---

## 2026-08-27 一天之内落地的（全部变异证红）

```
R3 批准并转录      CR1 全套 · P3/F3 双向边 · NON_TERMINAL_TRAPS · 三条禁边 ＋ 三个专码
                   11 条禁边专码全部浮出（R-A 条件 2 达成）
R-C                白名单 {P1,P2,F1,T1} ＋ 11 个状态各自具名诊断，未知事件 fail-closed
executor 成文化    actor_form/executor_of 分五形；两类模型（治理时/运行时）精确成立
R3 §2–§3 两层      CHECKPOINT_OF（三个时刻）· ROUTER_OF（修掉 archive_policy_a 发 F2 的活缺陷）
                   已批准 GATE_TABLE 一字未动 —— 叠层，不改枚举
不变量 5           四处路径构造收敛到 registry_boundary 一处
不变量 8           registry 缺失改为 BoundaryError 拒绝
边界② 渲染层       最深既存祖先的最终拼写比较（qros-runtime）
```

**ITSF 4319/0 · qros-runtime 966/22/25。**

---

## 三条裁定共有的独立性缺口 —— 未由任何人判定

```
dec-four-owner · dec-scope-boundary · dec-registry-migration
```

**三份全是 Fable 5**，其中一份收窄了另一份的措辞，另一份对它所裁的方案有实质设计
贡献并自陈失格。**整条链至今没有跨家族独立审查**——两轮在飞的 Sol 是第一次。

三份裁定都写了「Aaron 应知悉后再追认」。**builder 不代判。**

---

## 以下为更早的记录，保留不改

---

## 先读这一段 —— 2026-08-27 之后的状态

**R3 已由 Aaron 批准**（`ops/ND1_PROFILE_RATIFICATION.md` §9，绑 doc HEAD
`2728e43`），**CR1 已转录进生产代码**，Fable 的三项裁定（R-A=FULL、R-B=接受构造、
R-C=PER_ID_ONLY）**能执行的部分全部执行完毕**。ITSF 全量 4290/0。

**builder 这边已经没有可独立推进的 DAG 节点了。** 恢复锚 §4 明写：N09 需 Aaron 的
P2；N10 依赖 N09 的真实执行；N11 从未实现；N13 依赖 N11。

### 只剩四件，全在 Aaron 手上

```
1. P3 与失败事件的写者是谁 —— D-3 的核心矛盾：已批准 actor 表派给 runner，
   而全局边界 4 写「只有主代理写 registry」。两条已批准规则相抵。
   建议交决裁席（提案是 builder 写的，不宜自裁）。
2. 目录创建授权的四要素 —— 来源／actor／精确文本／commit 绑定／有效期。
   builder 可备模板；填写与生效是 Aaron 的。
3. D-3 的五项 UNRESOLVED_FOR_AARON —— 见 ops/RULING_SOL_D3_HOLD_2026-08-26.md。
4. N09 的 P2 —— §D.10.4 要求 Aaron 单独的、绑定完整 40 位 commit 的精确语句。
   builder 不得代填（常设禁令「不填 P2 占位符」未撤销）。
```

**三条独立授权仍不得合并**（ND1）：目录创建 / 写探针 / 执行。
`DIRECTORY_CREATION_AUTHORIZED=NO` 时，签了 P2 也不能建 `supplements\` 子树。

### qros-runtime 第二维护窗：开着，第 3 轮在飞

```
提示词  build-evidence/PROMPT_WINDOW2_SOL_ROUND3.md
钉子    REVIEWED_SET_UNCHANGED_SINCE=7ca707e
状态    第 1、2 轮均 HOLD 并已 reproduce-first 修复；956/22/25 全 PASS
闭窗    未做 —— ITSF 注册表未切、偏离记录未闭合、过渡形 B 继续有效、
        GRAD 试点被互斥挡着。这几项两轮都列为 UNRESOLVED_FOR_AARON
```

---

## 以下为 2026-08-26 的记录，保留不改

---

## 现在挂着的交付

### ①（已完成）八项待裁 —— Fable 已裁，Aaron 已采纳

```
DECISION_ID  dec-eight-open-2026-08-26        DELEGATED=YES
裁定全文     ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md
             sha256 5116f7b03dabe6cc4a8a2357b02b4b30e3a9227d050e41d9c1f0943262ed7dd3
采纳记录     ops/OWNER_DECISIONS_2026-08-26.md（逐项结算表在 OD-2026-08-26-3）
登记表       已清空（十路径解冻）
```

**第 4、5 项已完成**（所欠仅决策记录，且本就零改动）。**其余六项的实质选择已定，
但执行仍欠 Aaron 的具体动作** —— 逐项见 OD-2026-08-26-3 的「还欠」栏。
**八项不解锁 D-3**：其 HOLD 条件 3 继续在 force。

### ② 等 Aaron —— 六个具体动作

1. **全局 `~/.claude/CLAUDE.md` L6 exposure 句的修订授权**（第 1 项）
2. **carve-out 行使 ＋ 迁移执行授权**，并确认 08-25 hold 不覆盖本项（第 2 项）
3. **开启 qros-runtime 维护窗**（第 3 项）
4. **ND1 profile R3 修订的 ratify**，走提案→fresh Sol→Aaron 三步（第 6 项）
5. **见证目录的单独目录创建授权**，若落在 `C:\Users\Aaron\quant-data\` 下（第 7 项）
6. **席位台账分类**：第 3 行终分类、第 4 行 `NOT_EXPOSED` 值的存废、第 5 行终分类

**Aaron 2026-08-26 已把上述 1–6 之外的决定再次委托 Fable**（第 6 项走 Sol 复核，不在委托范围内）。决策包见 `ops/DECISION_PACKET_REMAINING_FABLE.md`。

### 准备进度（Aaron 2026-08-26：「全部都可以开始准备做了」）

| 项 | 备妥了什么 | 落地还欠 |
|---|---|---|
| **1** | `ops/PREP_ITEM1_L6_EXPOSURE_TEXT.md` —— 逐字终稿可整段替换；条件 2 已核验 | 你对全局 `CLAUDE.md` 的修订授权 |
| **7** | `ops/REGISTRY_SYNC_FAILURE_MODEL.md`（边界 3+4）＋ `src/itsf/s0/registry_witness.py`（边界 1+2，13 测试、6 变异全红） | 见证根的目录创建授权；之后才接入生产门 |
| **2** | `ops/PREP_ITEM2_QUARANTINE_MIGRATION.md` —— 可行性已测（生产代码零路径引用，32 条待改全在测试／配置／文档）＋迁移计划 | carve-out 文本、hold 范围确认、**外加仓根台账三选一**（裁定没区分它） |
| **3** | `ops/PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md` —— 补丁设计已出；接缝已在（`required_save_path` 早就收 `repo` 却没用） | 开维护窗，**外加范围三选一**（`header.py:201` 是同一缺陷的第二处，D-4 未点名） |
| **6＋8** | **`ops/PROMPT_ITEM6_SOL_REVIEW.md`** —— 完整 packet＋十条冻结送审集。第一次交付裸文件被判 `REJECTED_INCOMPLETE`（origin=BUILDER），**那是我的错**，本次是补正 | 把提示整份发给新 Sol；Sol 过后你 ratify |

**第 7 项的代码刻意未接入任何门**：`witness_path` 是必填参数、无默认值，模块
永不建目录（变异证红）。接入会改变运行期行为，而运行期行为依赖那个尚未授权的
见证根。

### ③ N09 的 R3 设计 —— **已完成**（2026-08-27）

**这一段此前是错的，2026-08-27 改正。** 原文写「R3 在 ① 返回之前写不了」——
那是对 High #2 的转述，而 Sol 原文说的是 the claimed execution path 建不了，
并明确给出第二分支：`or limit the authorized build explicitly to an
always-refusing scaffold`。五条最小解阻条件里 **1／2／4／5 全是 builder 的活**，
第 3 条自带 builder 可走的分支。裁定全文与逐条复现见
`ops/RULING_SOL_N09_R2_HOLD_2026-08-26.md`。

**R3 已写完**：`ops/N09_EXECUTION_PATH_DESIGN_R3.md`，范围取条件 3 的第二分支
（`BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`），五条最小解阻条件逐条应答：

```
条件 1  三个 checkpoint 各自的副作用断言（R2 那条统一断言对 C_BUILD_2/3 不成立）
条件 2  冻结 A1/F2/indeterminate 矩阵 —— 并暴露一个真实缺陷：archive_policy_a
        是一道门，其拒绝经路由器 A 发 F2，而已批准政策要求这一格发 A1
条件 3  取第二分支：默认拒绝骨架
条件 4  钉死 structural-only 调用图（loader → build_universe →
        build_vol20_regime_mapping_from_universe → build_event_stratum_map），
        AST 层面禁止 build_s0_dataset / compute_day / labels / Oracle / study
条件 5  点名 atoms.canonical_json；落点进封存清单；P3 之前绑定；
        P3 之后落盘失败 = INDETERMINATE 走 Aaron
```

R3 对现有代码的每条断言由 `tests/test_n09_r3_design_facts.py` 机械钉住
（21 项，4 条变异证红）。**仍是设计，`STATUS=NOTHING_IMPLEMENTED`。**

**越过骨架仍需 Aaron 的四项**（R3 §7，builder 不代填）：P3／失败事件的写者、
目录创建授权的四要素、D-3 的五项 `UNRESOLVED_FOR_AARON`、N09 的 P2。

---

## 禁区 —— 任何复审席位交付时必须随附本节

**这一节是本文件存在的第二个理由。** Review Packet 由 `qros packet` 机械生成，
**没有承载禁区清单的字段**；2026-08-26 就因为清单只写在提示词里、而交付的是
packet，烧掉了第二个复审席位。本文件是那份清单的常驻载体。

**交给任何复审席位时，把本节一起给他。**

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它**既是 outcome-carrying，又是本项目的恢复锚**（§1「恢复序」是任何会话定位
状态的标准第一站）。按常规做一次状态定位就会踩中。

**而且「别打开它」还不够。** 第二次暴露的席位**没有打开它**——一次广域符号搜索
把片段带了出来。所以：**不要在本仓做广域检索**。需要什么路径就列出来，由工作
会话提供逐字节内容（Review Packet 的 `PULL_PROTOCOL` 正是这个约定）。

---

## outcome-blind 席位的操作规则（D-2 / S1(b)，2026-08-26 生效）

**这一节必须随每一次复审交付一起给出。** 它不是建议。

### 你可以从哪里开始（许可起点，D-2 条件 4）

```
ops/RECOVERY_ANCHOR.md
```

**outcome-clean，永不隔离，专为 blind 席位可读而写。** 它给出恢复序、两条暴露轴、
禁区清单与本节的检索禁令。只告诉一个席位「不许读什么」而不告诉它「可以从哪开始」，
正是第一个席位自己找路、并因此被烧的原因。

### 规则

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**outcome-blind 席位不得在本仓做任何自主检索**——不 grep、不 rglob、不广域符号
搜索、不「顺手看一眼」。**需要什么路径就列出来，由工作会话提供逐字节内容**
（Review Packet v1 的 `PULL_PROTOCOL` 就是这个约定）。

### 为什么是禁令而不是提醒

两个席位已经烧掉，**第二个从未打开过那份文件**——一次广域符号搜索把隔离锚的
片段带了出来。第三个席位（决裁席）做了**一次单模式定向 grep**，同样触到了。

所以「别打开文件 X」这类围栏**在原理上不够**：只要隔离内容还在席位能检索到的
树里，任何检索都可能带出它。在拆锚（D-2 的 A 半）落地之前，**禁止检索是唯一
真正起作用的那一半**。

### 两条暴露轴，一并告知（D-1 条件 1）

```
研究轴  ops/EXPOSURE_LEDGER.md        —— 研究自由度消耗   【OFF-LIMITS，blind 席位不得读】
席位轴  ops/REVIEWER_EXPOSURE_LOG.md  —— 复审席位被烧；不消耗研究自由度   【可读】
```

**烧掉一个席位不消耗研究自由度**，所以两者分账。要报告自身暴露状态，看席位轴；
要报告研究暴露状态，看研究轴。**两者永不混记。**

### 禁区（S2：本节机械附着于每一种交付载体）

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`，**每一条
路径都当作关闭**。尤其：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它既是 outcome-carrying，又是本项目的恢复锚——按常规做一次状态定位就会踩中。

---

### 交付前必须逐条核对的一件（2026-08-26 加入）

**本次交付点名的每一个路径，都不得出现在 `carries_outcome` 里。**

`ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` 就栽在这上面：它一边写着禁区
清单，一边在呈交格式一节让复审者「形式沿用
`ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`」——**而那份文件在隔离名单
上**。同一份文件里，禁止与指令自相矛盾。Fable 是先查注册表才没被烧，**那是它
谨慎，不是我做对了**。

机械做法：交付前把文件里出现的每个 `ops/...md` 路径与
`OUTCOME_CARRYING_ARTIFACTS.json` 求交集，非空即停。

---

## 已完成（保留最近三次，便于回溯）

| 何时 | 交给谁 | 什么 | 结果 |
|---|---|---|---|
| 2026-08-26 | Fable | 四项待裁决策包 | **全部返回** —— D-1=A、D-2=C、D-3=C（三步之第一步，故成为上面 ①）、D-4=改；裁决全文是隔离件，D-3 一节的干净副本见 `ops/D3_REGISTRY_WRITER_PROPOSAL.md` |
| 2026-08-26 | fresh Sol | R2 设计审（Review Packet v1，`rv-3651f9fe0b68-da56aecb6991`） | **HOLD** —— 三条 High 全部经 builder 独立复核成立；**四条 finding（3 High＋1 Medium）全部经 builder 独立复现成立**；裁定全文记录 `ops/RULING_SOL_N09_R2_HOLD_2026-08-26.md`（此前本格误指 `A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md`，那份装的是 08-25 那轮的六条 REDESIGN）；席位暴露记 `ops/REVIEWER_EXPOSURE_LOG.md` 第 2 行 |
| 2026-08-25 | fresh Sol | MC-REG-COLLISION-001 批准 | **RATIFIED_AS_MODIFIED**（C2 被整条替换）→ 已实现，记录 `ops/RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md` |
| 2026-08-25 | Fable | MC-REG-COLLISION-001 提案 | R2 提案 → 记录 `ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md` |

---

## 交付前 builder 必须做的（清单，不是提醒）

1. 把送审工件**先 commit**，再 `derive_pin()` 派生钉子——钉子不手打。
2. 登记进 `ops/ARTIFACTS_UNDER_REVIEW.json`（含 `unchanged_since`）。
3. **提交之后**再跑一次
   `tests/test_artifacts_under_review_are_frozen.py`——不是提交之前。
4. 把上面「禁区」一节随交付一起给出。
5. **复审一返回，第一件事就是清空登记表** —— 在动任何被冻结的工件之前，不是之后。

   > **两次实测的教训（2026-08-26 迁移、2026-08-27 第六次 HOLD）。** 两次都是
   > 复审已经返回、我直接去改 findings 指出的文件，而那些文件还在冻结集里。
   > 冻结守卫两次都抓到了，但**它只在全套件里跑**——代价是一次 6 分钟的空跑。
   > 顺序对了就零成本：**清表 → 再改**。
   >
   > 改完之后跑的快速子集里**必须包含
   > `tests/test_artifacts_under_review_are_frozen.py`**（0.1 秒），
   > 否则这个错要等到全套件才暴露。
6. **交付说明里的路径一律写绝对路径。** 2026-08-26 实测：决裁席的工作目录在
   `Desktop`、不在仓内，而我给的是仓相对路径 `ops/PROMPT_...md`，它只能**先检索
   才能找到那份写着「不许检索」的文件**——三次文件名操作发生在读到禁令之前
   （席位台账第 5 行）。这次只命中文件名，纯属运气：`ops\PROMPT*` 那一次若有隔离件
   恰好叫 `*PROMPT*`，返回的就是禁区路径。**一个必须先被找到才能读到禁令的文件，
   本身就是缺陷。** 绝对路径形如
   `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\<名>`。

前三条各自对应今天一次真实的失败，逐条写在
`ops/INCIDENT_TRANSPORT_HEAD_PIN_20260825.md` 与
`ops/INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md`。
