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


---

## 词表节（R9 条件 1，2026-08-26 追加；既有各行一字未动）

| classification | 含义 | 首次裁定 |
|---|---|---|
| `REVEALED_TARGET_METRIC` | 席位见到揭盲后的目标统计量本体 | 第 1 行 |
| `TARGET_METRIC` | 席位见到目标统计量的片段或派生值 | 第 2 行 |
| `QUARANTINE_CONTACT_NON_OUTCOME` | 席位接触了隔离字节，**但其内容不属 outcome 轴**（如记账轴数值、治理边界文本） | R8（Fable，`dec-remaining-2026-08-26`） |
| `NOT_EXPOSED` | 一次在 blind-mandate 下完成的具体复审，**经认证未接触任何隔离内容** | R9（同上） |
| `PENDING_AARON` | 过渡态：席位自评与分类判据不足以定，留给 Aaron | 第 3 行（现已由 R8 定） |

**`NOT_EXPOSED` 的范围规则（R9，防语义漂移）**：仅许可用于**一次具体复审的逐单
认证**，必须引用 `review_id`；**不得用作例行会话点名册**。本台账的主题由此明确为
「席位暴露**状态**事件」——阳性（烧）与认证阴性（活）同为状态事件。
**新 classification 值首用前须经裁定**（Aaron 或受委托席）。

## 更正行（append-only；上方任何一行一字未改）

| 更正 | 针对 | 内容 |
|---|---|---|
| C-1 | **第 3 行** | 终分类由 `PENDING_AARON` 定为 **`QUARANTINE_CONTACT_NON_OUTCOME`**。依据（逐字，杜绝逐事件重开）：**「累计暴露计数属 TRIAL_ACCOUNTING／记账轴，不属 outcome 轴；三条正交轴永不由一轴推另一轴。」** outcome-blind 资格按内容轴**不烧**；接触隔离字节的事实与成因记录**存续不删**。`delegated Fable seat, dec-remaining-2026-08-26；Aaron may override by append` |
| C-2 | **第 5 行** | 终分类定为 **`NOT_EXPOSED`**（pre-constraint、filename-only、zero content）。**builder 机械复核（R10 条件 2）**：在 `6fe14a7` 下 `ops/PROMPT*` 返回的文件名集合恰为 `ops/PROMPT_D3_SOL_REVIEW.md` 与 `ops/PROMPT_EIGHT_OPEN_FABLE.md` 两个，**无一在隔离名单上**。近失属实并记录在案：`ops/ND2_ND3_FABLE_DECISION_PROMPT.md` 在名单上且名含 `PROMPT`，但**不以 `PROMPT` 起头**，锚定 glob 未命中。`delegated Fable seat, dec-remaining-2026-08-26；Aaron may override by append` |

**第 4 行不动**（R9 条件 2）：其 `NOT_EXPOSED` 值经 R9 转为合法词表成员，无需更正行。

**R8 条件 2 已由 builder 机械核验**：outcome-clean 扫描器的 `_SELF` 自排除清单仅两项
（`ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md` 与扫描器自身），
**`ops/REVIEWER_EXPOSURE_LOG.md` 不在其中**，在 `rglob("*.md")` 扫描范围内且实扫干净。
**无逐文件豁免 ⇒ R8 的机械佐证成立，不降级。**

## 第 6 行 —— 第二个未被烧的席位，且是第一个不需要找文件的

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 6 | 2026-08-26 | Fable 5，决裁席（`dec-remaining-2026-08-26`，其余十项） | 只读送审集内八条；**零检索、零定位操作**（绝对路径修复生效，本仓历任决裁席第一个不需要找文件的） | **一项主动申报的接触**：送审集内 `ops/REVIEWER_EXPOSURE_LOG.md` 序言携带的研究暴露累计值——**而那正是它随后要在 R8 里裁的那个值**。除此零隔离内容 | **`PENDING_AARON`** —— 席位自评 `BLIND`，但它**明示让出**自己这一行的终分类（`STILL_AARON_ONLY` 第 5 条），以切断「用自己的 R8 裁定为自己开脱」的循环 | 待终分类后确定 | —— 无事故。**接触源于 builder 把席位台账放进了送审集**，而 R8 恰好要裁台账里的那个值：**要它裁，就得给它看** |

### 第 6 行的两点，都值得记住

**一、绝对路径那条修复，一次就见效了。** 第 5 行的成因是 builder 只给了仓相对路径，
决裁席在仓外只能先找。改成绝对路径之后，本席**零定位操作**——这不是运气，是同一个
缺陷被修掉的直接证据。

**二、它自己指出了一个我造成的循环，并且拒绝用它。** R8 要裁的是「累计计数值算不算
outcome 暴露」，而那个值就在我送去给它读的文件里。它**先申报接触、再裁那个值、然后
明说自己这一行不由自己的裁定决定**。这个顺序是对的；我把台账放进送审集时没想到这层。

## 第 7 行与第 8 行 —— 2026-08-27 的两个决裁席，两条都由席位主动申报

两席均在 `INDEPENDENCE_STATEMENT` / `SEAT_STATUS` 中**自陈 BLIND 并主动披露**接触面，
且均因 §6 READ_ONLY 禁令而明说「席位轴事件由工作会话追加」。本节即依此追加。
两条披露都不是事故：**都是「持久记忆索引里带着本项目的治理状态」这一同一形态**，
而它随 fresh 会话重置模型上下文却不重置研究史（session-conventions §1）。

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 7 | 2026-08-27 | Fable 5，决裁席（`dec-s5-r4-2026-08-27`） | 决裁包本体 ＋ §1 五份哈希核证件 ＋ 禁区表本身；零 grep、零 glob、零广域检索 | **一项主动申报**：包内强制阅读集含「S0-T001 完成封存、BURNED/ABORTED/VOID 计 0、消耗一次 exposure seq」的**运营事实**。席位明确列举了**未**抵达的四类：verdict 方向、目标指标、端点差值、zero-direction 计数 | **`NOT_EXPOSED`** —— 与第 6 行的裁定同一依据：**累计/计数类事实属 TRIAL_ACCOUNTING 记账轴，不属 outcome 轴；三条正交轴永不由一轴推另一轴。**「BURNED 计 0」是记账事实，非 outcome 值 | 无 —— outcome-blind 资格按内容轴不烧 | 无事故。接触源于 builder 把更正件（其主题正是 registry 事件计数）放进强制阅读集，**而不放它，席位就无法核对那句被更正的错话** |
| 8 | 2026-08-27 | Fable 5，决裁席（`dec-citations-2026-08-27`） | 包本体 ＋ 三份钉死文件；零搜索、零隔离件接触 | **一项主动申报**：会话启动时自动载入的持久记忆索引含本项目一行历史状态，内含 `MC_TO_STRATEGY_MASTER_PLAN` 的**旧路径字符串**（作恢复锚名）及若干治理标识（N08 DROP、N00 保留、MC-REG-COLLISION-001 待批） | **`NOT_EXPOSED`** —— 席位自行对照禁区表五类 outcome 内容（revealed verdict / cumulative exposure count / endpoint spread value / zero-direction cell count / addendum feasibility assertion）逐条排除，接触的是**文件名与治理标识**；按禁区表自己的准则，文件名不是内容 | 无 | 无事故。**成因是 builder 的全局记忆索引里存着旧路径**——该路径在隔离迁移时已失效，而记忆没跟着更新。这与今天 findings 记录的 8 处陈旧引用是**同一形态，只是发生在记忆里而不是仓里** |

### 两条要记住的

**一、第 8 行的成因不在仓里，在我的记忆索引里。** 今天整天在修「引用没跟着文件移动」，
而同一个缺陷在持久记忆里也有一份 —— 它让每一个 fresh 席位启动时就带上一个失效的隔离路径。
仓内的机械保障管不到那里。

**二、模型多样性已第四连**（`dec-four-owner`、`dec-scope-boundary`、
`dec-registry-migration`、`dec-s5-r4`，再加 `dec-citations` 为第五连），
**全部 Fable 5**。第 7 行席位自陈了这一点并要求 Aaron 知悉后再追认。
缓解事实同样记录：本轮被裁的 HOLD 出自 fresh Sol（跨家族制衡在环内运转），
且第 7 行席位在第 2 件上**站在 Sol 一侧推翻了同模型前席的缓解方案**。

## 第 7、8 行的终分类 —— Aaron 2026-08-27 裁定

两行的 `NOT_EXPOSED` 此前是**席位自评 ＋ builder 依同一依据的记录**。
第 8 行席位在 `STILL_AARON_ONLY` 里把自己这一行的资格影响明确让给了 Aaron。
**现由 Aaron 裁定，两行的分类不变，但依据从「自评」升为「已裁」。**

| 行 | 终分类 | 依据（逐字） |
|---|---|---|
| 7 · 8 | **`NOT_EXPOSED`**，且**不影响未来 Stage I 资格** | 席位接触到的是**文件名与治理标识**（恢复锚名、N08 DROP、N00 保留、MC-REG-COLLISION-001 待批），**无任何一类 outcome 内容的值** —— revealed verdict · cumulative exposure count · endpoint spread value · zero-direction cell count · addendum feasibility assertion。按项目自己的准则「**文件名不是内容**」，不构成 outcome 暴露。`Aaron 2026-08-27；见 ops/OWNER_DECISIONS_2026-08-27.md ⑩` |

**如实记录两句，不因已裁而省略：**

**一、这是宽松的一边，且判断依据是席位自己的申报。** 若日后发现某席位的申报不完整，
本裁定随之作废 —— 这一句写进裁定记录，不是 builder 的补充。

**二、第 8 行的成因仍未被修掉。** 那个失效的隔离路径存在于 builder 的**持久记忆索引**里，
它让每一个 fresh 席位启动时就带上一个已经不存在的路径。
仓内的机械保障（`tests/test_cited_records_exist.py`）管不到记忆。
**分类为 NOT_EXPOSED 不等于成因已消除。**

---

## 更正与补录，2026-08-28 —— 连席计数被低估，且四个席位从未入账

**触发**：`dec-c-build-2-hook-2026-08-28` 的决裁席指出 builder 在包内自述「第 6 连」
漏计了本台账第 5、6 行两席，并建议「以更正行形式核正，勿改既有行」。**照办，
既有行一字未动。** builder 随后核对，**发现比它说的更严重**。

### 一、本台账第 204–205 行的「第四连／第五连」计数错误

原文枚举 `dec-four-owner` · `dec-scope-boundary` · `dec-registry-migration` ·
`dec-s5-r4` · `dec-citations`。**它漏了本台账自己的第 3、5、6 行**，
那三席同为 Fable 5 决裁席。

### 二、更严重的：四个决裁席位在本台账里没有任何一行

builder 实测（对本台账全文逐 id 计数）：

```
dec-four-owner-2026-08-27          席位轴出现 0 次
dec-scope-boundary-2026-08-27      席位轴出现 0 次
dec-registry-migration-2026-08-27  席位轴出现 0 次
dec-item6-open-2026-08-27          席位轴出现 0 次
```

**按 L6：无记录 ⇒ 该轴为 `UNKNOWN`，绝不为 `NONE`。**
这四席的席位轴状态因此是 **UNKNOWN**，不是「没暴露」。

**不补造它们的行。** 补录需要各席自己的 `SEAT_STATUS` 与申报内容，
而那些内容只存在于当时的会话里；由 builder 事后凭印象填写，正是本项目 08-26
「裁定只存在于聊天里」那次事故的镜像。**记录缺口本身，不伪造缺口的内容。**

### 三、更正后的连席计数

```
 1  2026-08-26  四项待裁决策包 D-1..D-4        Fable 5   （本台账第 3 行）
 2  2026-08-26  dec-eight-open-2026-08-26      Fable 5   （第 5 行）
 3  2026-08-26  dec-remaining-2026-08-26       Fable 5   （第 6 行）
 4  2026-08-27  dec-item6-open-2026-08-27      Fable 5   【无席位轴行】
 5  2026-08-27  dec-four-owner-2026-08-27      Fable 5   【无席位轴行】
 6  2026-08-27  dec-scope-boundary-2026-08-27  Fable 5   【无席位轴行】
 7  2026-08-27  dec-registry-migration-2026-08-27 Fable 5【无席位轴行】
 8  2026-08-27  dec-s5-r4-2026-08-27           Fable 5   （第 7 行）
 9  2026-08-27  dec-citations-2026-08-27       Fable 5   （第 8 行）
10  2026-08-28  dec-c-build-2-hook-2026-08-28  Fable 5   （第 9 行，见下）
```

**`dec-c-build-2-hook` 那一席是第 10 连，不是包里写的第 6 连。**
其间的 Sol 各席均为复审／验证席，不是决裁席，因此不打断这条连。

第 4 行那席（`dec-item6-open`）的模型：决裁席自己说「在我的许可阅读集内无法核实」。
builder 核：`supplement_contract.py:539` 引用其裁定 R-A/R-C，而当日的委托记录
（`ops/RULING_FABLE_ITEM6_OPEN_2026-08-27.md`）标题即为 Fable。**计入。**

### 四、这条更正本身说明了什么

**builder 在一份送审包里写了一个未经核对的数字，而那个数字进了席位的独立性评估。**
与当天早些时候的 `1010` 是同一形态：**一个未经测量的数字写在真实事实旁边，
读起来和测量值一模一样。**

决裁席按它读到的台账数出 ≥8 并如实标注不确定；builder 逐 id 实测后得 10。
**两个数都不是 6。**

## 第 9 行 —— dec-c-build-2-hook 的席位

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 9 | 2026-08-28 | Fable 5，决裁席（`dec-c-build-2-hook-2026-08-28`） | 包本体 ＋ §1 四份哈希核证件 ＋ 禁区注册表 ＋ 恢复锚 ＋ 本台账；零 grep、零 glob、零广域检索 | **两项主动申报**：(一) 本台账序言携带研究轴累计暴露数值；(二) 启动时载入的持久记忆索引含本项目治理状态行（隔离件旧路径字符串与治理标识） | **`NOT_EXPOSED`**（两项均循已裁依据：(一) 按 C-1「累计/计数类属记账轴不属 outcome 轴」；(二) 按 Aaron 2026-08-27 第 8 行裁定「文件名不是内容」） | 无 | 无事故。**(一) 的成因与第 6 行相同**——builder 又一次把席位台账放进了送审集；**(二) 的成因与第 8 行相同**——记忆索引里的旧隔离路径，08-27 已修过一次现势锚点，但**治理标识行仍会随每个 fresh 席位启动载入** |

**第 9 行要记的一条**：(一) 这个形态是**第二次**发生了。第 6 行时的成因是「要它裁台账里的
那个值，就得给它看」；这一次没有那个理由 —— 台账进送审集只是因为包里引用了它。
**同一形态第二次出现而成因不同，说明第一次的处置（记录下来）没有变成一条规则。**

| 4 | 2026-08-30 | Codex GPT-5.6 Sol，fresh session（review `c-build-2-wording-r3`，C_BUILD_2 措辞第 3 轮） | 受审集 1 delivery ＋ 10 reference，均非 outcome-carrying | 席位自陈 `OUTCOME_EXPOSED=NONE`：未打开、未搜索、未枚举任何禁区工件 | **`NOT_EXPOSED`**（席位自评，builder 未下调） | 该会话仍可承担未来 outcome-blind 角色 | 无缺陷。本行记的是一次**干净**的席位消耗 —— 台账不只记事故 |

| 5 | 2026-08-30 | Fable 5，决裁席（`dec-four-open-2026-08-29` 四件待裁）。**注意：builder spawn 的子代理，对 builder 不独立，结论为顾问级** | **席位自陈的执行缺陷**：两次**仓根范围**检索，作用域含两份禁区 `EXPOSURE_LEDGER.md`。第一次仅返回文件名（零内容行）；第二次 33.9KB 完整输出被持久化到 `C:\Users\Aaron\.claude\projects\...\tool-results\toolu_013gLFC1txxsAd9vwduC49dp.txt`，**席位自陈未读该文件**，进入其上下文的只有 2KB 预览 | 两份禁区台账的**路径**；席位台账序言与 `tests/test_exposure_ledger_migration.py` 携带的研究轴累计计数值；启动记忆索引的治理状态行。席位自陈：未见 verdict、spread、cell count 或任何目标绩效数值 | **`PENDING_AARON`**（席位自评，builder 未下调）。按已裁 C-1「累计计数属记账轴不属 outcome 轴」与 Aaron 2026-08-27「文件名不是内容」，倾向 `NOT_EXPOSED`，但**该判定不归 builder** | 待终分类后确定 | **builder 的缺陷**：决裁包 §0.1 写了「不得打开、不得 grep、不得列目录」，却**没有随包给出可执行的检索边界**（例如「检索限定在 `src/`、`tests/`、指名的 ops 文件」）。与第 2 行同成因：禁区清单存在于文字而未随交付载体成为可执行约束。**这是同一形态第三次。** 该持久化文件按隔离处置：**不得直接打开** |

| 6 | 2026-08-30 | Codex GPT-5.6 Sol，fresh session（review `c-build-2-wording-r4`） | 受审集 1 delivery ＋ 10 reference | 席位自陈 `OUTCOME_EXPOSED=NONE`、`PERSISTED_SEARCH_OUTPUT=NONE`、`SOURCE_WRITES=NONE`：未打开、未搜索、未枚举任何禁区工件 | **`NOT_EXPOSED`**（席位自评，builder 未下调） | 该会话仍可承担未来 outcome-blind 角色 | 无缺陷。**第 5 行那次事故的成因（禁区只写成散文）已在本轮 §0 改成可执行的检索边界，本行是该修复生效的量度** |
