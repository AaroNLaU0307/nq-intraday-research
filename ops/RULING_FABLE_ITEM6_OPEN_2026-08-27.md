# 第 6 项三个开放项 —— 决裁席裁定（生效）

```
RECORD_TYPE=RULING
REVIEW_ID=dec-item6-open-2026-08-27
SEAT=Fable 5，决裁席，fresh top-level session
DELEGATED=YES —— Aaron 2026-08-27「其余的就按fable推荐的方式做，我同意」
ADOPTED_BY_AARON=2026-08-27「这是fable的结果，我同意」
SEAT_STATUS=BLIND（未触 12 条隔离路径，零检索）
L6_GATE_EFFECT=NONE —— 不释放任何 transition，不是研究授权，不是运行授权
```

## 裁定

| 项 | 裁定 | 置信 |
|---|---|---|
| **R-A** `FORBIDDEN_EDGES` | **FULL** —— 三条全加：`("CR1","P4")` `("CR1","P5")` `("CR1","P3")` | HIGH |
| **R-B** profile 行绑语法块 | **接受该构造**，附三条 CONDITIONS | HIGH（机制本身） |
| **R-C** 悬空 P3 拒绝范围 | **PER_ID_ONLY** | MEDIUM |

**第四项 ratify R3 未裁**，仍是 `STILL_AARON_ONLY`。决裁席明确声明三项裁定**均不以
「R3 会被批准」为前提**：R-A／R-C 是代码层政策参数，R-B 是构造可行性判定，各自独立成立。

---

## 1. 决裁席独立复算的（builder 已逐条复核）

它没有采信本包的任何自报，重算了：R2 块哈希 `a3d40b7c…`（＝ Aaron 2026-08-23 批准值）、
R3 块 60 行／对 R2 恰 13 处编辑（4 改 ＋ 9 加 ＋ 0 删）、CR1 语法块 `c251335f…`、
R3 块 `d40ad864…`、四个 BEGIN/END 标记各恰一次。

**builder 复核结论：全部相符。** 另复算 `removed = 4`，恰为 4 条被改行的原像，纯删除为 0
——与它的报告一致。

---

## 2. R-A 为什么是 FULL，而不是我预想的 ZERO

**builder 起草时给的「不制造第二真相源」这条反对理由，被一个我没查的事实推翻了。**

决裁席逐字核对 `supplement_contract.py:200-293` 的 EVENTS 表后确认：**既有 8 条
`FORBIDDEN_EDGES` 全部与 closed successor list 冗余，无一例外**——
`A1→(A2,AX)`、`AX→(F3,)`、`F2→(F3,)`、`P2S→(P2,)`、`P3→(P4,A1,F2)`、`F1→(P3,P2S,F3)`。

这张表**从来不是强制正确性机制**，它自始就是具名政策层；`:346-347` 的注释自述
「Kept as data so a test can assert the resolver rejects every one of them」。

所以取 ZERO 不是「避免开一个坏先例」，而是**让 CR1 成为全表唯一的例外**。方向反了。

第三条理由更要紧：「崩溃裁定永不复活运行」是本次修订的**承重政策句**，而本项目刚为
「声称已机械化、实则从未有过」付过完整代价（§D.11.3 事件）。ZERO 把这句话留成
「successors 恰好没写」——同一缺陷类的再生产。

**CONDITIONS**：三条边各配专用拒绝码入 `FORBIDDEN_EDGE_CODES` 与 `REFUSAL_CODES`，
`("CR1","P3")` 的码名须点明「崩溃裁定不复活运行」语义；**变异证红须断言具体拒绝码浮出，
不得只断言「发生了拒绝」**——若检查顺序使专码永远被通用 transition 拒绝抢先而无法浮出，
FULL 的全部价值（可命名诊断）为零，**该发现须回报，裁定退回 ZERO**。

---

## 3. R-B 的三条 CONDITIONS —— **已全部执行**

### 条件 1 —— 标记唯一性（关闭决裁席找到的「诱饵块」路径）

它穷举了「语法变而 R3 哈希不变」的路径，内容层四条全闭，但找到一个**位置层软点**：
`_canonical` 用 `text.index()` 只取首个出现，**在文件后部追加第二个
`BEGIN_ND1_CR1_GRAMMAR_R3 … END` 块，所有哈希测试仍绿**，而冷读者可能把诱饵当正典。
「首个出现为正典」这条规则此前只活在测试的实现里，没有断言，`CANONICAL_BYTES` 口径
也没写。

**已执行**：`test_each_canonical_marker_appears_exactly_once`——八个标记（提案里四个
＋决策包里 R1／R2 各两个）逐一断言 `count == 1`。**变异证红：追加诱饵块 → 红。**

### 条件 2 —— doc-only commit 之前修正三处 prose

三处**均经 builder 复核成立**：

| # | 缺陷 | 处置 |
|---|---|---|
| 1 | §六 仍写「R3 对 R2 的十二处编辑」 | 改为 13 |
| 2 | §二.1 写「五条变异全红」而 §六 写「八条」 | **两个数都不对**，见下 |
| 3 | §六 表格把语法块哈希引作陈旧的 `3154ade6…` | 改为 `c251335f…` |

**第 2 条我没有在 5 和 8 之间挑一个——两个都不是测出来的。** 逐条重跑八个变异，
实测 **7 红 ＋ 1 空档**，写进新增的 §二.1c。

**那个空档是真的**：`test_the_ratification_record_carries_the_r2_approval` 是子串
`in` 检查，而 `APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2` 在批准记录里出现**两次**
（第 135、157 行）。翻掉其中一条，另一条仍让断言成立——记录内部自相矛盾而守卫看不见。
**已加计数断言闭合，变异证红。**

### 条件 3 —— correction-only 测试补 removed 侧断言

原实现把 `_removed` 算出来就丢掉，因此**一个既删除已批准赋值、又在别处补够 added 数的
R3′ 会通过一个名叫「correction only」的测试**。已改为：每一条 removed 必须是某条被改行
的原像（同键不同值），纯删除为 0。**变异证红：删一条赋值并补一条填充行 → 红。**

---

## 4. R-C 为什么是 PER_ID_ONLY

四条理由，最要紧的两条：

1. **GLOBAL 的论据与已批准 profile 的爆炸半径不符。** P3 是 `UNNUMBERED`
   （`supplement_contract.py:238`），悬空 P3 不占全局编号序列；
   `RECOMMENDED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT=NO`、
   `EXPOSURE_ROW_QUANTITY_ZERO=YES` ——不占暴露槽。悬空 P3 的一手事实是**该 id 的
   生命周期未闭，不是 registry 完整性事件**。
2. **GLOBAL 想要的政策，Aaron 今天就机械地持有。** P2 的 actor 是 `ACTOR_AARON`
   （`:210`）——每次新运行本就以他的逐次授权为瓶颈；**事故期间不签 P2 即是 GLOBAL**，
   且随时可反悔，无需解楔裁定。把这层裁量硬编码，买到的唯一新东西是「解除也要走裁定」
   ——而那正是提案 Part B 自己点名的死法：「楔死催生绕行文化，而绕行文化才是不变量
   真正的死法」。

**CONDITIONS 之一必须留在记录里**：**GLOBAL-by-governance 仍然可用**——Aaron 在任何
事故期间扣发全部新 P2 即达成全局阻断，零代码、零解楔裁定。**本裁定拒绝的是把它硬编码，
不是这层裁量本身。** 且不削弱任何条件触发的全局 fail-closed（witness 超集判据失败、
registry 解析失败等一律保持）。

**新增 FALSIFIER**：真实事故显示崩溃损害跨越了 `supplement_id` 边界（如共享输出根，
或 registry 被损而 witness 判据未捕获），且另一 id 的运行经 per-id 门放行
⇒ PER_ID_ONLY 被证伪，范围须扩大。

---

## 5. 决裁席自陈的最弱处（逐字要点）

> 对 R-C。PER_ID_ONLY 的论证链里最弱的一环是：崩溃进程对 registry 之外共享磁盘状态
> （输出根）的副作用，在崩溃时点定义上不可全知；引用的条件触发层（witness、
> A_PRECHECK）只覆盖 registry 文件本身。抵消它的是每次运行的授权语句逐次绑定
> `output_root` 且 P2 由 Aaron 逐次签发——**但这是治理缓解，不是机械排除。**

这是 `CONFIDENCE=MEDIUM` 而非 HIGH 的原因，也是新增 FALSIFIER 的由来。

**独立性的一处如实申报**：该席位预载了持久记忆索引（harness 常设行为），含 ITSF 的
摘要级历史，**因此不主张对先前 Fable 裁定的完全经验独立**。其中无任何目标绩效数值，
outcome-blind 不受影响。

---

## 6. 尚未执行的，以及为什么

| 事项 | 状态 | 原因 |
|---|---|---|
| R-A 的三条禁边转录进 `FORBIDDEN_EDGES` | **未做** | 裁定明写「转录发生在 Aaron ratify R3 之后」（§四.B 顺序） |
| R-A 的三个专用拒绝码 | **未做** | 同上 |
| R-C 的 per-id 门实施 | **未做** | 需先有 `ABANDONED_RUN` 专名诊断，而它需 CR1 裁定 |
| **R3 的 ratify 本身** | **未做，且不可代做** | `STILL_AARON_ONLY`；§7 路径终点是「Aaron 批准 id ＋ hash ＋ 精确 doc HEAD」 |

**R-B 的三条 CONDITIONS 已全部执行**，因为它们是 doc-only commit 的前置，且全是测试与
prose，不触碰任何已批准字节——`d40ad864…` 与 `c251335f…` 均未变。
