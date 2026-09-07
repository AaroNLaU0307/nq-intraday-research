> **2026-09-07 · QROS-CF (DEC-0001):** this list is no longer a source of blockers or pending items. Everything in it was triaged into `ops/BACKLOG.md` (blocker set §1, backlog §2, closed items §3); the current stage is `ops/RESEARCH_STATE.md`. Kept unchanged below as history.

# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** Aaron 说「把这个给审阅席位」时，指的就是它。
> 席位是哪个模型族系由 Aaron 决定，本文件不假设。
> 它是**禁读清单的载体**：Review Packet 没有承载它的字段，
> 而两个审阅席位正是因为清单没有随包同行而被烧掉。

```
UPDATED   = 2026-09-07
ACTIVE    = **NONE —— 当前没有待派发的审阅席位**
LAST      = QROS-CF-FINAL-CLOSURE-CHECK-001 —— 已以 **PASS** 归还
            （A1–A6 / B1–B4 / S 全 PASS；`I1/I2 SAFE TO ACTIVATE`；
             `QROS-CF GOVERNANCE WINDOW CLOSED`）
STATE     = QROS-CF 治理窗口 **CLOSED**；研究在 **N10 → N11 → N13** 恢复
            权威状态见 ops/RESEARCH_STATE.md，裁定行见 ops/DECISIONS.md
DISPATCH  = 由 Aaron 派发。builder 不得自行调用任何审阅席位；
            **QROS-CF 不得自动重开**（重开条件见 RESEARCH_STATE §3）
```

---

## 0. 给席位的第一段话（请原样带上）

### 0.1 先读这条，在你做任何事之前

**不要检索这个仓库。** 不要 grep、不要递归列目录、不要广域符号搜索，
**也不要为了「先搞清楚项目状况」而浏览相邻文件**。

这不是保密要求，是**保住你自己的资格**。本项目已有三个审阅席位被烧毁，
而**其中两个从未刻意打开任何禁读文件**：

```
第 2 个  一次广域符号搜索，片段被带出来
第 3 个  一次单模式定向 grep，一次就触到
```

**一次意外命中就让这次复审作废。** 你需要的每一个字节，
本文件与包里都点名给出；**缺什么向 Aaron 要，不要自己找。**

### 0.2 然后

**从磁盘读取，不要用聊天里贴过来的字节。**
包与被审文件都已提交并登记在 `ops/ARTIFACTS_UNDER_REVIEW.json`，
每一条带 `sha256`；开工前请重算并比对，不符即 STOP 并报告。

**本次是 outcome-blind 复审。** 下面三条是硬约束，违反其一即应停止并说明。

## 1. 禁读：outcome-carrying 清单

**权威来源是 `ops/OUTCOME_CARRYING_ARTIFACTS.json`**（12 条，机器可读）。
包的 §1 有逐字表格。**以那个 JSON 为准，不要凭记忆。**

### 1.1 那个结构性陷阱 —— 请特别注意

【OFF-LIMITS】下面这一条是 outcome-carrying，**绝对不要打开**：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

**它既是 outcome-carrying，又曾经是项目的「恢复锚点」——
一个正常定位状态的审阅者会正面撞上去。**
2026-08-25 一个 fresh Sol 会话正是这样打开它、看到 verdict 与曝光计数，
就此永久失去 outcome-blind 资格。

**不要打开它。** 不要为了「先搞清楚项目状态」而打开它。

### 1.2 允许的入口

```
ops/RECOVERY_ANCHOR.md      <- outcome-clean，这是你唯一该用的定位入口
```

需要背景就读它。**它是为这件事专门保持干净的。**

### 1.2b 两根曝光台账 —— 知道它们存在，但**不要打开研究轴那根**

【OFF-LIMITS】下表第一行是 outcome-carrying，本次**禁读**；第二行可读。

```
研究轴  ops/EXPOSURE_LEDGER.md        消耗研究自由度 —— 禁读
seat 轴 ops/REVIEWER_EXPOSURE_LOG.md  记录哪个审阅席位被烧掉
                                      **本次的行在你归还之后才追加**
                                      **你不需要打开它**，也不必去核对
```

**两根轴永不合并。** 你这次被派发本身就是一次 seat 轴事件。台账的行记录的是
**席位归还时的自陈**，所以本次那一行在你的结论回来之后才由 builder 追加——
现在还没有那一行，本文件不声称有。**它不会动研究轴一格**。

告诉你这件事，是为了让你不必去「查一下曝光状态」——
那正是会撞上研究轴台账的动作。

### 1.3 `BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY`

**不要在仓库里自由检索。** 不要 grep verdict / 曝光 / 结果类词，
不要遍历 `ops/outcome_quarantine/`，不要「顺便看看」相邻文件。

理由不是保密，是**你的资格**：一次意外命中就把这个席位烧掉，
而烧掉席位不消耗研究自由度，却让这次复审作废。

**需要什么材料，向 Aaron 要，不要自己找。**

## 2. 本次要审什么

一句话：

> **同一条 F01–F06 谱系的第二轮修复,请给最终认证判决。**

原始的六条 BLOCKING finding 定义在
`ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md`。
**F04 已由你的上一轮 CLOSED,不重开**;本轮的退出判据是余下五条:
**F01 · F02 · F03 · F05 · F06**。

包的 §4 点出四个**请特别用力**的方向。它们不是提示,是本席位认为自己最可能
仍然错的地方。

### 2.1 轮次 —— **请先读这一条**

`ops/REVIEWER_CONTRACT.md` 第 23 行:**每条 issue 谱系两轮**,跨改名与阶段
连续计数。这条谱系已经用掉两轮:

```
第 1 轮  P2 门禁复审        -> HOLD,六条 BLOCKING
第 2 轮  定向复审(修复后)   -> HOLD,F04 CLOSED,五条 STILL_BLOCKING
第 3 轮  本次               -> 合同预算之外
```

**所以本轮不是合同允许的一轮,而是 Aaron 明确授权的一次业主例外。**
把它写在这里,是因为你完全有理由在自己发现合同被突破时 STOP——
那样做是对的,而让你自己去发现则是本席位的失职。

**这是本谱系的最后一轮。** 若本轮仍为 HOLD,按 Aaron 的指示回到 Aaron,
不再有第四轮,也不再有 builder 的自动修复循环。

### 2.2 基准怀疑度

**builder 在这条谱系上已经错了两次,而且是同一形态**:第一轮的每一条修复都
通过了自己写的结算测试,你仍然在其中五条上复现了反例。两次的共同形态是
**声称宽于事实**——机制做到的比文档说的窄。

包的 §3 与 §5 逐条给出本席位自报的证据。**请当作待验证的声明。**

## 3. 明确不在范围内

```
不是 A2         不是 Stage I        不解开任何 QROS 门
不审研究结论    不审样本/成本/Primary 指标/promotion-falsified
只读            发现即报告,不修复。修复需 Aaron 另行授权
F04             已 CLOSED,不重开(除非本轮改动使其失效——那本身是 finding)
F07 / F08       非阻断,已是 B-22 / B-23,不得用来阻挡本轮退出
```

**本次 PASS 不等于 ① 被批准。** ①(何时读真实 Development 数据)只有 Aaron 能批。
本次认证的是**执行安全与数据身份**,不是任何研究结论。

## 4. 席位预算

```
一个 fresh 席位,一轮。不需要 workflow,不需要切分
只读起步:发现即报告,不修复
不得追加任何 registry 事件,不得执行 qros,不得写入仓库
```

## 5. 回来时请给

```
判决              PASS / PASS_WITH_BACKLOG / HOLD —— 用 REVIEWER_CONTRACT.md 的词表
Critical/High     放最前
每条 BLOCKING     恰好一个威胁(T1–T6) + 一条具体失败路径 + 证据类别
证据类别          REPRODUCED / REASONED / SELF-REPORTED —— 三者不可混
区分              「你复现的事实」 vs 「本包自述的内容」
四个方向          包 §4 的四条,请逐条明确作答
```

**判决归你,签署归 Aaron。** 本席位写了被审的修复,不得自审通过。
