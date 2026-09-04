# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** Aaron 说「把这个给 Sol／Fable」时，指的就是它。
> 它是**禁读清单的载体**：Review Packet 没有承载它的字段，
> 而两个审阅席位正是因为清单没有随包同行而被烧掉。

```
UPDATED   = 2026-09-02
REVIEW_ID = ENG-SAFETY-PRE-REAL-DATA-001
PACKET    = ops/REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md
SEAT      = Fable（对抗性工程安全席位）
DISPATCH  = 由 Aaron 派发。builder 不得自行调用任何审阅席位
```

---

## 0. 给席位的第一段话（请原样带上）

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
                                      本次派发已由 builder 追加一行
                                      **你不需要打开它**，也不必去核对
```

**两根轴永不合并。** 你这次被派发本身就是一次 seat 轴事件，
已由 builder 追加到 seat 台账；**它不会动研究轴一格**。

告诉你这件事，是为了让你不必去「查一下曝光状态」——
那正是会撞上研究轴台账的动作。

### 1.3 `BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY`

**不要在仓库里自由检索。** 不要 grep verdict / 曝光 / 结果类词，
不要遍历 `ops/outcome_quarantine/`，不要「顺便看看」相邻文件。

理由不是保密，是**你的资格**：一次意外命中就把这个席位烧掉，
而烧掉席位不消耗研究自由度，却让这次复审作废。

**需要什么材料，向 Aaron 要，不要自己找。**

## 2. 本次要审什么

包里有完整版。一句话：

> **真实 Development 数据之前的最后一次工程安全复审。**
> 只审工程安全、边界、fail-closed 行为与现存 residual。

四块，按承重：

```
R1  resolve_partial 第 8 轮后的修复 —— 从未被独立席位看过，承重刚增加两层
R2  编排层 supplement_chain.py
R3  输入装配层 supplement_inputs.py
R4  loader 边界 —— builder 自称的一条安全属性被证明是错的
```

**并请攻击 builder 自报的四条弱点**（包 §3）——那是自述证据，不是复现事实。

## 3. 明确不在范围内

```
不是 A2         不是 Stage I        不解开任何 QROS 门
不审研究结论    不审样本/成本/Primary 指标/promotion-falsified
只读            发现即报告，不修复。修复需 Aaron 另行授权
一轮            不开无限复审循环（Aaron 2026-09-02）
```

**本次 PASS 不等于 ① 被批准。** ①（何时读真实 Development 数据）只有 Aaron 能批。

## 4. Fable 预算（Aaron 的规矩）

```
第一波最多 3 个 workflow，且范围必须互不重叠
建议切法   W1 = R1        W2 = R2 + R3        W3 = R4
等一波跑完，主会话去重与综合，再决定是否开第二波
默认总预算 3，硬上限 6（超出需 Aaron 明批）
子 workflow 不得再生 workflow；并行前先声明文件租约
```

## 5. 回来时请给

```
verdict           PASS / HOLD
Critical/High     放最前
区分              「复现的事实」 vs 「builder 自述的证据」
必答四问          见包 §5（其中 Q3：是否存在阻断 ① 的工程发现）
```
