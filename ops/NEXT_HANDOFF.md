# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** 我说「贴这个给 Sol／Fable」时，指的就是它。
> 你不必再去 `ops/` 里认哪个是最新的 prompt。

```
UPDATED = 2026-08-26（D-3 复审已挂出）
```

---

## 现在挂着的交付

### ① 交 fresh Sol —— D-3 registry 写者裁定复核

```
提示   ops/PROMPT_D3_SOL_REVIEW.md          ← 整份贴给一个新的 Sol 会话
packet ops/packets/rv-f4207865a116-c004854e6828.packet
提案   ops/D3_REGISTRY_WRITER_PROPOSAL.md   （Sol 自己按提示从磁盘打开）
门     TIER1_DISCRETIONARY   REVIEW_ID=rv-f4207865a116-c004854e6828
状态   已就绪，未发出
```

**要裁什么**：边界第 4 条「registry 只允许主代理单写」，与已完成真实运行中运行器
自行追加 `RUN_STARTED` 的先例相抵。Fable 提案拆开裁——P3 由运行器自追加（受托
单写限缩解释），失败事件仅主代理追加。Sol 判这个构造安不安全。

**出提示的过程中实测到一件改变问题性质的事**：已批准的 `ND1_RECOMMENDED_PROFILE_R2`
（sha256 `a3d40b7c…`，2026-08-23 批准）actor 表把 **P3／P4／A1／F1／F2 全判给
`main agent (mc_ds_runner)`**，只把 A2／AX／F3 判给 `main agent`。所以提案的 P3 一半
与已批准文本**一致**，失败事件一半与已批准文本**相抵三行**（A1／F1／F2）。
另有 `src/itsf/s0/runner.py:725` 今天就在跨过不可逆点后追加 `FAILED`。
写入提案 §2.5–2.7 并加了第五个猎取点，**未替 Sol 也未替 Aaron 收口**。

**PASS 不授权任何写入**：条件 3 明写，Sol PASS ＋ Aaron 授权之前，生产代码不得
获得任何 registry 写能力。Sol 返回之后仍需 Aaron 终裁。

**送审集已冻结**（`ops/ARTIFACTS_UNDER_REVIEW.json`，六条，钉子
`7b582b1240e4a9d93cd8c9d9ac470ca98525ce02` 由 `derive_pin()` 派生）：
在 Sol 返回前**不要动**这六个路径——
`ops/D3_REGISTRY_WRITER_PROPOSAL.md`、`src/itsf/mc/supplement_contract.py`、
`src/itsf/s0/runner.py`、`src/itsf/mc/registry_boundary.py`、
`src/itsf/mc/supplement_runner.py`、`scripts/s0_real_run.py`。

### ② 等 Aaron —— 另外三项裁定的后续

D-1 条件 3（把全局 L6「每一次 exposure 事件都要追加」一句收窄到研究轴）、
D-2 的 S1(a) ＋ registry 豁免、D-4 的 runtime `_SAVE_DIR` 工作项——**都要 Aaron
本人动全局文件或运行时仓，builder 不能代劳**。

### ③ 等 D-3 落定 —— N09 的 R3 设计

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
研究轴  ops/EXPOSURE_LEDGER.md        —— 研究自由度消耗（累计量在此）
席位轴  ops/REVIEWER_EXPOSURE_LOG.md  —— 复审席位被烧；不消耗研究自由度
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
