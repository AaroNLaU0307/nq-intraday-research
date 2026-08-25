# REVIEWER EXPOSURE LOG（复审席位暴露台账）

```
RECORD_TYPE=REVIEWER_EXPOSURE_LOG
CREATED=2026-08-26
APPEND_ONLY=YES —— 行只追加，永不编辑、永不重排
AUTHORITY=本件是**席位**暴露的记录，不是研究 exposure 记账
```

## 为什么另立一份，而不是记进 `ops/EXPOSURE_LEDGER.md`

Aaron 于 2026-08-26 授权把 2026-08-25 的复审席位暴露事件入账。照办时发现
**记进那份台账会出三重错**：

1. `ops/EXPOSURE_LEDGER.md` 是**合规承载件**，逐行转录仓库根的历史台账，
   权威在后者；`tests/test_exposure_ledger_migration.py` 机械守着两者**逐行
   恒等**。只追加承载件会立刻破坏该恒等。
2. 同一测试文件里 `test_exactly_one_row_carries_the_target_metric_exposure`
   要求 `REVEALED_TARGET_METRIC` **恰有一行**。再加一行会打破它。
3. 更要紧的是**第三条**：那份台账记的是**研究者对 S0 outcome 的暴露**——它消耗
   研究自由度，累计值 1575 是它的量纲。而本次事件是**一个复审席位读到了治理
   文档里的 verdict token**。**烧掉一个席位不消耗研究自由度。** 把两者记成同
   一轴，会让研究的 exposure 记账凭空多出一次「研究者暴露于目标统计量」。

所以本件另立。**L6「无账即 UNKNOWN，绝不为 NONE」的要求由本件满足**——事件有
了durable 记录，状态不再未知。

**是否另需在 `ops/EXPOSURE_LEDGER.md` 留一条只含指针的行**（指向本件、
classification 用不冲突的值），**归 Aaron**：那要动一份 append-only 的权威台账
与一条已批准的「恰一行」不变量，builder 不自行处置。

---

## 台账

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-25 | Codex GPT-5.6 Sol，fresh session（review N09-EXECUTION-PATH-A2） | `ops/MC_TO_STRATEGY_MASTER_PLAN.md`（在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 名单上） | verdict token ＋ exposure count（**席位自陈**；未读真实 Development 数据，未读目标绩效数值） | `REVEALED_TARGET_METRIC`（**席位自评，builder 未下调**） | 该会话不得再承担 outcome-blind Stage I | builder 未在复审提示词中给出 outcome-carrying 禁区清单 |

| 2 | 2026-08-26 | Codex GPT-5.6 Sol，fresh session（review `rv-3651f9fe0b68-da56aecb6991`，R2 设计审） | 被隔离的 outcome-carrying **恢复锚**（席位自陈：a broad symbol search surfaced snippets from a quarantined outcome-carrying recovery anchor） | 该锚的片段（**未刻意打开该文件**——是一次广域符号搜索带出来的） | `TARGET_METRIC`（**席位自评，builder 未下调**） | 该会话不得再承担 outcome-blind Stage I | builder 的禁区清单只存在于**提示词**里，而本次交付载体是 **Review Packet**——清单没有随之传递 |

| 3 | 2026-08-26 | Fable 5，决裁席（四项待裁决策包 D-1..D-4） | 被隔离的累计 exposure 计数值（出现在**未登记**的决策包与席位台账中）；另一次定向 grep 触到隔离锚中一行治理边界文本 | 该计数值；一行治理边界文本（**不含还原内容**）。席位自陈：未见 verdict token、spread、cell count 或任何目标绩效数值 | **`PENDING_AARON`** —— 席位自陈「按现行类别定义不再自证完全 outcome-blind」，并把终分类留给 Aaron，因为它取决于「累计计数是否属该类别」的裁定 | 待终分类后确定 | builder 让该值扩散进 10 份未登记文件（含 3 份测试，在那里它被断言为不变量）——见 `ops/FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md` §2.2 |

### 第 1 行的补充说明

- **分类沿用席位自评。** 按 §3.4B 的字面定义，「verdict token」属「预注册判定
  统计量的派生值」。builder 不下调他人对自身暴露的自陈。
- **本次未移动 `N_trials`**，也未改变研究 exposure 累计值。
- **成因是结构性的，不是这一次的偶然**：`ops/MC_TO_STRATEGY_MASTER_PLAN.md`
  既是 outcome-carrying，又是本项目的**恢复锚**（其 §1「恢复序」是任何会话定位
  状态的标准第一站）。**任何 outcome-blind 复审者做一次完全正常的状态定位就会
  踩中。** 处置见
  `ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md` §1.3（拆锚 vs 禁区清单，
  归 Aaron）。
- **已落地的机械缓解**：
  `tests/test_artifacts_under_review_are_frozen.py::test_a_live_prompt_names_the_outcome_carrying_artifacts_as_off_limits`
  强制任何活跃 review 的提示词点名登记表与恢复锚。
- **Review Packet v1 的 `PULL_PROTOCOL` 是更强的结构性缓解**：复审者**列出**
  它需要的路径，由工作会话提供逐字节内容——它不自己导航，因而不会走到禁区。
  R1 那轮用的是散文提示词，没有这层保护。

---

## 第 2 行的补充说明 —— 与第 1 行**不是**同一个原因

第 1 行的成因是「提示词没写禁区清单」。第 2 行**写了**，但**清单没有到达复审者**：

```
禁区清单出现在 ops/N09_EXECUTION_PATH_A2_SOL_PROMPT.md : 1 处
禁区清单出现在 交付给 Sol 的 Review Packet            : 0 处
三条相关守卫扫描的范围                                : ops/*PROMPT*.md
```

**交付载体从散文提示词换成 Review Packet 时，缓解措施静默失效了。** packet 由
`qros packet` 机械生成，没有承载禁区清单的字段；而守卫只扫 `*PROMPT*.md`，本次
没有活跃提示词，于是它**通过了，且什么也没保护**——今日第三次同一形状。

### 一条比「别打开那个文件」更强的事实

席位自陈它**不是刻意打开**恢复锚的：**一次广域符号搜索把片段带了出来**。

这意味着「禁区清单」这类缓解**在原理上就不够**：只要复审者在仓内做任何广域检索，
被隔离的内容就可能进入它的上下文。**唯一能真正消除它的是让那些内容不在会被检索
到的地方**——即 D-2 的选项 A（拆锚）。

这条事实已随 `ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` 的 D-2 一并交 Fable，
但它**在本记录写下时才出现**，故补记于此：**两个席位已被烧掉，第二个甚至没有
打开那个文件。**


---

## 第 4 行 —— **一个没有被烧掉的席位**（2026-08-26）

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 4 | 2026-08-26 | Codex GPT-5.6 Sol，fresh session（review `rv-f4207865a116-c004854e6828`，D-3 registry 写者裁定复核） | 只按提示逐条打开了送审集的六个路径＋packet＋提示词本身，另加两份 `Quant trade\` 下的 doctrine 文件与自身的 verification skill（全部**不在**隔离名单上） | 无隔离内容 | **`NOT_EXPOSED`**（席位自陈 `SEAT_STATUS=BLIND`：未打开隔离件，未做任何 grep／rg／rglob／符号检索） | 该会话**仍可**承担 outcome-blind 角色 | —— 无事故 |

### 为什么把一个「没发生的事」记进暴露台账

**这一行不是暴露事件，它是缓解措施是否奏效的量度。** 前三个席位分别死于：
旧恢复序引路、一次广域符号搜索、一次单模式定向 grep。此后落地了四件东西——
拆锚（`ops/RECOVERY_ANCHOR.md`）、检索禁令（S1(b)）、禁区清单的常驻载体
（`ops/NEXT_HANDOFF.md`）、以及交付前的隔离交集守卫
（`tests/test_delivery_names_no_quarantined_path.py`）。

**第四个席位是这四件东西全部就位之后的第一次交付，它活下来了。** 三烧一活不构成
统计证据，但「没有记录 ⇒ UNKNOWN，绝不为 NONE」对**未发生**同样适用：不记的话，
将来没人能说清缓解到底有没有起过作用。

**归 Aaron 裁**：本台账原本只记暴露事件，`NOT_EXPOSED` 是 builder 新引入的
classification 值。若认为不该混记，请裁，我按 append-only 追加更正行，**不改本行**。


---

## 第 5 行 —— 约束之前的三次定位操作（2026-08-26）

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 5 | 2026-08-26 | Fable 5，决裁席（`dec-eight-open-2026-08-26`，八项待裁） | **零文件内容**。三次仅触文件名的操作，全部发生在**读到检索禁令之前**：① 全仓 glob 搜 `PROMPT_EIGHT_OPEN_FABLE.md`（超时，零返回）；② 列出 `Quant trade\` 顶层目录名；③ 列出 `ops\PROMPT*` 文件名（返回两个文件名） | 文件名，零内容。**未命中任何隔离内容** | **席位自评 `BLIND`；终分类归 Aaron**（先例：第 3 行以「一行治理文本」得 `PENDING_AARON`；本次连一行文本都没有） | 待终分类后确定 | **builder 的交付说明只给了仓相对路径，而决裁席的工作目录在 `Desktop`、不在仓内** —— 一个必须先被找到才能读到「不许找」的文件 |

### 这一行为什么重要，即使代价为零

**成因不是席位不谨慎，是我的交付说明有缺陷。** 提示词与 `ops/NEXT_HANDOFF.md`
里给的都是仓相对路径；决裁席在仓外，只能先找。**它读到禁令时，三次检索已经发生了。**

**这是第 2、3 席位被烧的同一形状：检索先于约束。** 那两次的内容命中是隔离片段，
这次只是文件名，纯属运气好——`ops\PROMPT*` 那次要是我把某个隔离件命名成
`*PROMPT*`，返回的就是禁区路径。

**已修**：交付说明改带**绝对路径**，并把「先给路径、再给禁令」写成交付前必核的一条。
见 `ops/NEXT_HANDOFF.md` 的 builder 清单。

**席位自评从严、披露从宽**：Fable 主动在开工第一段申报了这三次操作，未被问及。
按台账惯例**自评不下调**，终分类归 Aaron。
