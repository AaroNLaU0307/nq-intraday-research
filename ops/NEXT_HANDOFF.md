# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** 我说「贴这个给 Sol／Fable」时，指的就是它。
> 你不必再去 `ops/` 里认哪个是最新的 prompt。

```
UPDATED = 2026-08-26（D-3 已返回 HOLD；**当前没有挂着的交付**）
```

---

## 现在挂着的交付

### ①（已完成）D-3 registry 写者裁定复核 —— **fresh Sol 返回 HOLD**

```
REVIEW_ID  rv-f4207865a116-c004854e6828   GATE=TIER1_DISCRETIONARY
VERDICT    HOLD          SEAT_STATUS=BLIND（席位未烧，第一个活下来的）
记录       ops/RULING_SOL_D3_HOLD_2026-08-26.md
           sha256 5f533347622156932fce5c35f11ffa2b089771eba0f2dd6157b7bb2f801a00ff
登记表     已清空（六路径解冻）
```

**四条 High ＋ 一条 Medium，builder 已逐条复现（无一采信）**：读—校验—追加之间
没有临界区，writer 是无锁 `open("a")`；失败事件条款与已批准 actor 合同相抵三行；
崩溃／陈旧租约无状态机，且当前根本没有 MC 生产执行路径可审；never-re-read 只是
结构＋注释；OneDrive 原子性无法靠读代码排除。

**这不否掉 Fable 的提案**——P3 那一半与已批准 actor 表一致；被质疑的是它的安全
前提（租约、临界区、原子性）尚不存在，以及失败事件那一半与合同相抵。

### ② 等 Aaron —— 现在共 **八项**，全在你的权限内

**原三项**：D-1 条件 3（把全局 L6「每次 exposure 事件都追加」收窄到研究轴）、
D-2 的 S1(a)＋registry 豁免、D-4 的 runtime `_SAVE_DIR` 工作项。

**D-3 新增五项**（Sol 的 `UNRESOLVED_FOR_AARON`，原文见裁定记录 §一）：
actor 是否同时表达执行者／是否加独立 executor provenance；保留 A1／F1／F2 的
runner actor 还是修订已批准 profile＋planner＋生产先例；P3 后硬崩溃该产生什么
事件、由谁追加、恢复写入的授权条件；registry 是否继续在主动同步的 OneDrive 树中
作为 canonical 写入面；租约回收能否自动执行还是必须 fail-closed 等人裁。

**Sol 给了一个较窄且与现有合同一致的解释供你参考**（它明说采不采用归你）：
运行器存活并捕获到的 A1／F1／F2 仍由运行器追加；硬崩溃后的检测／恢复由主代理
负责，用你批准的独立恢复语义。

### ③ 等 D-3 落定### ③ 等 D-3 落定 —— N09 的 R3 设计

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
ops/MC_TO_STRATEGY_MASTER_PLAN.md
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
ops/MC_TO_STRATEGY_MASTER_PLAN.md
```

它既是 outcome-carrying，又是本项目的恢复锚——按常规做一次状态定位就会踩中。

---

### 交付前必须逐条核对的一件（2026-08-26 加入）

**本次交付点名的每一个路径，都不得出现在 `carries_outcome` 里。**

`ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` 就栽在这上面：它一边写着禁区
清单，一边在呈交格式一节让复审者「形式沿用
`ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`」——**而那份文件在隔离名单
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

前三条各自对应今天一次真实的失败，逐条写在
`ops/INCIDENT_TRANSPORT_HEAD_PIN_20260825.md` 与
`ops/INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md`。
