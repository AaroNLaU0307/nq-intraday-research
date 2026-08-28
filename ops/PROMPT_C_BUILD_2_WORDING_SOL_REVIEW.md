# C_BUILD_2 新措辞复审 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording
DELIVERY_STATUS=ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审，裁定 B 的 CONDITIONS 所要求的那一道）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            N09 R2/R3 的任何前序复审会话；qros-runtime 第二维护窗的任何会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A（本件是执行路径设计，不是预注册）
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_REVIEW.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

```
HEAD=3aa5663
REVIEWED_SET_UNCHANGED_SINCE=<见冻结登记册 ops/ARTIFACTS_UNDER_REVIEW.json>
```

---

## 0. 你被叫来判什么 —— 以及为什么必须是你

裁定 `dec-c-build-2-hook-2026-08-28` 裁了 B（措辞修正），并在 CONDITIONS 里
明写：新措辞**须经 fresh Sol 复审、Aaron 批准后方生效**。你就是那一道。

**决裁席自陈了一处独立性折减，原文如下** ——

> 本席给出了 ② 的五条判据与 CONDITIONS 中「新措辞须明写门在调用边界上运行」这一约束。
> 判据是审断标准而非措辞，但那条约束实质上限定了未来接线的形态
> ——**本席对采用该形态之措辞的未来复审独立性相应折减**。

也就是说：**你要审的这份措辞，它的形态是被裁它的那一席限定的。**
请把这一点当成攻击面，而不是背景说明：

> **请判：五条判据 ＋「必须写成调用边界」这条约束，
> 是否已经把结论预先决定，使得任何满足它们的措辞都自动通过？**
> 若是，那这道复审就是形式的，而这正是它存在的理由被掏空的样子。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `2572e35d744e3978321503f4684aeb1020e3429413b92be7b2e42b030f1166f6` | `33551` | `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `101b6b7b272df2b0f71359a5e4d5310e896d10a27c072d783decbf7c9dfaeb82` | `11888` | `ops/RULING_FABLE_C_BUILD_2_HOOK_2026-08-28.md` |
| `80e6c91e4f5f28273bc0dcc1db95586b0aae12dec079badf95210b419c8b16d7` | `8831` | `ops/DECISION_PACKET_C_BUILD_2_HOOK.md` |
| `446ebd4bf51dc797d30566d54076c34d771ccd5114d34e931dc32e189fd3328a` | `47106` | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | `32616` | `src/itsf/mc/supplement_contract.py` |
| `b9482fcad3dd5091d0a062af65036154cbb7445099f79450c902e2673573cf89` | `20233` | `tests/test_n09_checkpoint_assertions.py` |
| `3dc719db3f34e8a60a0f71fb5b1c6f31e8a9bf32f655063b3c2d2aa9f4ab7d13` | `36141` | `tests/test_mc_supplement_runner.py` |

任一条不匹配 ⇒ STOP。

**受审的措辞在 `ops/N09_EXECUTION_PATH_DESIGN_R3.md` 的 §12**（`STATUS=DRAFT`）。
文件其余部分随包是因为 §1（原措辞）、§10、§11 是它的上下文，不是要你重审它们。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得 grep、不得 rglob、不得广域检索。** 需要哪个路径，向工作会话要，由
`PULL_PROTOCOL` 提供字节 ＋ SHA256。

**隔离子树 `ops/outcome_quarantine/**` —— 禁区，不得打开、不得搜索、不得列目录。**
`MC_TO_STRATEGY_MASTER_PLAN.md` 在其中。outcome-clean 的替代入口是
`ops/RECOVERY_ANCHOR.md`。

**`ops/EXPOSURE_LEDGER.md`（研究轴）不在你的阅读集内。**
`ops/REVIEWER_EXPOSURE_LOG.md`（席位轴）可读 —— 但注意：
决裁席已申报**席位轴台账的序言携带研究轴累计数值（1575）**，
按已裁定依据（C-1：累计/计数类属 TRIAL_ACCOUNTING 轴）自评不烧 outcome-blind 资格，
**终分类让渡 Aaron**。你读它之前先知道这件事，并在 `SEAT_STATUS` 里照此申报。

---

## 3. 请重点打的六件

### ① 判据是否已预先决定结论（**主要攻击面，见 §0**）

### ② FALSIFIER 的核验，builder 做的那次算不算数

裁定的 falsifier 是：若已批准的 ND1/N-D2 原文**以批准值**规定该门必须
「在 staging 期间」运行，则 B 触及批准实质、裁定作废。

builder 在 §12.0 报告核验结果为「未触发」，理由是三个相关批准值
（`ND1_PARTIAL_RECOVERY_RULE` · `ND1_PARTIAL_MODIFY_TEXT` · `SILENT_DELETE_FORBIDDEN`）
**都规定「分歧字节怎么处置」，无一规定门何时运行**。

**请独立复核这一条。** 它是整份裁定唯一的外部依赖：**若它错了，B 整个作废。**
builder 的搜索面自陈为 `ops/*.md`（非隔离）＋ `src/itsf/mc/*.py` ——
**请判这个搜索面本身够不够**，特别是批准值是否可能落在这两个面之外。

### ③ (a) 的更正与它明写的残余（§12.5 —— builder 自纠，先读它）

**这一条原本是交给你的问题，我量了 30 秒发现是缺陷，于是它变成了申报。**
原稿的 (a) 声称防的违规类是「一份没被复读校验过的 FINAL 被当作已封存」，
而检出途径只是「FINAL 在场则字节 == intended」。**实测**：

```
FINAL 由本机制之外的东西写出（手抄／备份还原／旧版本）
resolve_partial -> already_sealed（只做了一次相等比较，从未复读校验）
(a) 的检出途径 -> 通过
```

**声称的类严格宽于检出途径能看见的集合。** 已按此更正措辞并明写残余（§12.5）。

**请判三件**：

1. 更正后的 (a)（「字节与 intended 不符的 FINAL 不会被当作已封存」）
   现在是否满足判据 (1) 覆盖保全 —— 还是我只是把类缩到刚好等于我能检的东西，
   而**真正该防的违规类因此无人再防**。
2. 明写残余而不关闭，是否是这里的正确处置。
   我的理由是：关闭它需要机制现在没有的 provenance 记录，而造一份是设计变更，
   CONDITIONS 明令本稿机制零改动。**请判这个理由成立，还是它是「把缺陷改写成不在范围内」。**
3. **(b)(c) 我也查了，同一个病，见 §12.6 与 §12.7** —— (b) 的扫描面只有一个函数体；
   (c) 的路线写「两条分歧结局」而实测是四条。三条自纠的共同形态写在 §12.8。
   **请判 §12.8 那个诊断本身对不对**，以及三次更正之后
   **是否还剩第四条我没拿尺子量过的东西**。

### ④ (b) 的更正与它明写的残余（§12.6 —— 同样是自纠，先读它）

**这一条也从问题变成了申报。** 我按 §12.5 的尺子量了 (b)，同一个病，且更硬：
旧检查只扫 `resolve_partial` 一个函数体，而**把一句删除搬进 `_preserve`
就完整通过** —— `_preserve` 在两条分歧分支上都被调用。局部别名同样看不见。

已把扫描面放宽到可达调用图，并明写它仍看不见什么（方法体内 / 导入模块内 / 经由值到达）。
变异证红实测：两种绕法在旧检查下全绿、在新检查下全红。

**请判两件**：

1. 「可达的模块级函数」这个扫描面，是不是又一个**刚好等于我想到的那些绕法**的边界。
   我加了 `test_the_walk_actually_reaches_the_helpers` 防它空转，
   但**防不了它漏掉第四种绕法** —— 请找第四种。
2. §12.6 明写的三类「看不见」，**是诚实划界还是把缺陷改写成不在范围内**。
   （姊妹仓的第 7 轮判过同型问题，你可参照但不必遵从。）

### ⑤ BRANCH_C / BRANCH_E 的标签，两处曾互相矛盾

决裁席报告过：R3 §1(c)、§11.2 与测试注释把「陈旧 `.partial` 改名移开＋允许重试」
称作 BRANCH_E，而 runner 的 docstring 把同一行为标注为 branch C。
**行为两处钉得都对，唯标签归属互相矛盾。**

builder 已按批准值 `ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY`
做了核正：**E 命名改名目标，C 加「允许重试」。**

**请核这次核正对不对**，以及 §12.1 的 (c) 现在两条结局的标签是否与批准值一致。

### ⑥ 决裁席自己的 STRONGEST_OBJECTION，你同不同意它的回应

原文：

> B 把「运行时中途不变量检查」换成了「测试钉死的机制性质」。测试钉的是今天的字节；
> 将来在执行授权后的改动压力下，代码与测试可能被一并弱化……
> **B 的保护强度以「变异证红纪律持续被执行」为前提，该前提本身没有机械守卫。**

**builder 要报一件与此直接相关的**：该前提现在有**部分**机械守卫 ——
`tests/test_no_vacuous_guards.py`（空断言探测器）。
但它检的是「断言是否可被任何输入满足」，**不是**「这条断言有没有配变异证据」。
**请判这个部分守卫是否改变决裁席的结论，还是它离那个前提还差得远。**

---

## 4. builder 主动申报的三件

```
一、§12.3 的变异清单第一次跑的时候把草稿自己驳回了。(a) 那条最初是绿的 ——
   删掉 promote 后的复读校验，套件里没有任何东西发现。补了新测试才红。
   **一条没有变异证据的子句不满足判据 (2)** —— 我差点把它当成满足了。
二、(c) 只覆盖 branch C 那条结局，branch E 同样留下分歧件而此前无测试。
   同样是写对照表时才发现的，不是设计时想到的。
三、我在同一天犯过一次 Class B 误分类：把三条「提案」判成了「被引用但从未存在」——
   机械可测的一半（历史中不存在）量对了，意图的一半靠断言，
   而那正写在一份论证「意图不能机械推断」的文档里。
   **列出是因为它影响你对我自报证据的信任度**，而那是你判断的输入。
```

---

## 5. 只读

不修任何代码、不改任何文件；不推送、不打标签、不 amend、不 commit。
**不得代 Aaron 批准新措辞** —— 你的 PASS 只满足 CONDITIONS 的复审那一半，
采纳仍是 Aaron 的事（决裁席已列入 `STILL_AARON_ONLY`）。
**本轮不释放任何 gate**：§5.5.6 satisfaction predicate 仍是唯一放行机制。

---

## 6. 返回格式

```
REVIEW_ID=c-build-2-wording
HEAD=<你实测的>
TRANSPORT_PRECHECK=PASS|STOP
VERDICT=PASS|HOLD
WORDING_MAY_GO_TO_AARON=YES|NO

CRITERIA_PREDETERMINE_OUTCOME=<五判据＋调用边界约束是否已预先决定结论>
FALSIFIER_INDEPENDENTLY_CHECKED=<你自己核的结果，以及 builder 的搜索面够不够>
逐条作答：① 判据 · ② FALSIFIER · ③ (a) 防的是哪个违规类 · ④ (b) 的 AST 途径 ·
         ⑤ BRANCH 标签核正 · ⑥ 变异纪律的部分机械守卫
CONDITIONS_MET=<CONDITIONS 五条逐条：met | not met>
NEW_DIVERGENCE_SHAPES=<新发现的>
STRONGEST_OBJECTION=<即使 PASS 也要写>
FINDINGS=<逐条，带文件与行号，标 HIGH/MEDIUM/LOW>
SCOPE_CREEP=NO|YES_OUTSIDE_REVIEWED_SET
UNRESOLVED_FOR_AARON=<你与 builder 都不得替他决定的>
SEAT_STATUS=BLIND|BURNED（含席位轴台账序言那 1575 的自评与让渡）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、实现/修复独立性、设计贡献、模型多样性>
```

**本复核不释放任何 gate，不构成 Aaron 的批准。**
