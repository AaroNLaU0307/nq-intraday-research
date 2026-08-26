# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** 我说「贴这个给 Sol／Fable」时，指的就是它。
> 你不必再去 `ops/` 里认哪个是最新的 prompt。

```
UPDATED = 2026-08-26（两份交付同时挂着：第 6 项→Sol 复核，其余→Fable 决裁）
```

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

### ③ 等八项落定### ③ 等八项落定### ③ 等 D-3 落定### ③ 等 D-3 落定 —— N09 的 R3 设计

Sol 对 R2 的 High #2 认定：执行路径的可建范围取决于 D-3 怎么裁。**所以 R3 在 ①
返回之前写不了**，现在能建的只有一个永远拒绝的骨架。

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
| 2026-08-26 | fresh Sol | R2 设计审（Review Packet v1，`rv-3651f9fe0b68-da56aecb6991`） | **HOLD** —— 三条 High 全部经 builder 独立复核成立；记录 `ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md` 与 `ops/REVIEWER_EXPOSURE_LOG.md` 第 2 行 |
| 2026-08-25 | fresh Sol | MC-REG-COLLISION-001 批准 | **RATIFIED_AS_MODIFIED**（C2 被整条替换）→ 已实现，记录 `ops/RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md` |
| 2026-08-25 | Fable | MC-REG-COLLISION-001 提案 | R2 提案 → 记录 `ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md` |

---

## 交付前 builder 必须做的（清单，不是提醒）

1. 把送审工件**先 commit**，再 `derive_pin()` 派生钉子——钉子不手打。
2. 登记进 `ops/ARTIFACTS_UNDER_REVIEW.json`（含 `unchanged_since`）。
3. **提交之后**再跑一次
   `tests/test_artifacts_under_review_are_frozen.py`——不是提交之前。
4. 把上面「禁区」一节随交付一起给出。
5. 复审返回后清空登记表。
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
