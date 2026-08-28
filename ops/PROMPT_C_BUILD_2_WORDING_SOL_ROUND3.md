# C_BUILD_2 措辞复审 · 第 3 轮 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r3
DELIVERY_STATUS=ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 3 轮，裁定 B 的 CONDITIONS 第 3 条）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1 轮 c-build-2-wording 与第 2 轮 c-build-2-wording-r2 的会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**本文件从磁盘读取 —— read this prompt from disk, not from a paste。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

```
REVIEWED_SET_UNCHANGED_SINCE=d34ce7c9d30fa87493123cc12b504c5111418df5
```

> **确认你读的是当前文件**：**line 26 of it must read**
> `REVIEWED_SET_UNCHANGED_SINCE=d34ce7c9d30fa87493123cc12b504c5111418df5`。
> 对不上 ⇒ 你手上是陈旧粘贴 ⇒ **STOP**，回到磁盘重读。

**语义**：该 commit **之后**没有任何 commit 触碰过 §1 表中的参考件。
**它不是也不该是当前分支头。** 本提示自身不在该 range 内（发出 delivery 就是对它的
一次提交，无不动点）；发行字节记在 `ops/ARTIFACTS_UNDER_REVIEW.json` 的
`role: delivery` 条目。

---

## 0. 第 2 轮判 HOLD，四条全中，其中一条把一个更大的洞带了出来

四条都先复现后修。**但请先看这一条**，因为它改变了你该怎么看我给你的每一个锚：

### 我只锚了第一份批准，而当时已经有三份

第 2 轮判「陈旧化保护不成立：追加新批准值不会让 premise test 变红」。
我复现了（追加伪造批准 → 34 条守卫全绿），**然后枚举，发现新批准早就在里面**：

```
R1  0a08319a…  2026-08-20
R2  a3d40b7c…  2026-08-23   R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY
R3  d40ad864…  2026-08-27   R2_STATUS=SUPERSEDED_BY_R3_FOR_P3_AND_F3_ONLY
```

**第 1 轮我把 falsifier 闭合在 R1 的字节上，而 R2、R3 当时就存在。我没注意到。**

逐份重建后核验的结果是好的 —— 三个锚定值在三份里逐字相同，时机词三份各自零命中
—— **但那是运气，没有任何机制在守它。** 现已建守卫（§3 ②）。

### 因此本轮的主要问题（§3 ①）

> **我给你的每一个「锚」，请先问它锚在几份东西的第几份上。**
> 上一轮我以为我锚在「批准原文」上，实际锚在「三份批准里最旧的那份」上，
> 而我毫不知情。**请找第二个这样的锚。**

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `562febeb56c11a5eb75213de97b78dcc0cc583c5dc8523bd2349b2470e7c2cc9` | `61178` | `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `101b6b7b272df2b0f71359a5e4d5310e896d10a27c072d783decbf7c9dfaeb82` | `11888` | `ops/RULING_FABLE_C_BUILD_2_HOOK_2026-08-28.md` |
| `3964c7b8227542bd78c1b7706493dbf16cbf86c30b824a5560bfa505eb174adc` | `11830` | `ops/ND1_PROFILE_RATIFICATION.md` |
| `446ebd4bf51dc797d30566d54076c34d771ccd5114d34e931dc32e189fd3328a` | `47106` | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | `32616` | `src/itsf/mc/supplement_contract.py` |
| `c2987bafbe62e3a16dcc3249016985c91cac8259b04bec4ec959423300d1be95` | `6100` | `tests/test_every_sealed_final_was_read_back.py` |
| `3b8fd362614ee7e7c689bde19d9797b501464de5bc2caa57cb8271963effae50` | `6869` | `tests/test_the_ratified_preimage_is_reconstructible.py` |
| `498421a878abd5c8795d826fc58121c93cfdd192525a86da6bae7e26dc8cb540` | `11552` | `tests/test_every_approval_is_accounted_for.py` |
| `4d4874c5e22b5adff47312bb03c0e405418fb894446b9ecd87a46e7ecef42613` | `11556` | `tests/test_c_build_2_wording_coverage.py` |
| `40f9ecce8b9ecf5835073291a200920316f65478e4188a633d44ed0680a311c0` | `26667` | `tests/test_n09_checkpoint_assertions.py` |

任一条不匹配 ⇒ STOP。

**伴随件（不在受审集内，工作会话应与本提示一并交付）**：
`ops/SELF_REPORT_AUDIT_2026-08-29.md` —— 我自己把 R3 里更早会话的九条「实测」断言
重量了一遍（八条符合、一条陈旧时态），并明写那个方法**查不到 §12.5 那种散文里的偷换**。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得 grep、不得 rglob、不得广域检索。** 需要哪个路径，向工作会话要。

**禁区清单随包**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 是权威登记册，
本 prompt 不复述其内容，你**不得打开它所登记的任何一件**。

【OFF-LIMITS】隔离子树 `ops/outcome_quarantine/**` —— 不得打开、不得搜索、不得列目录，
其中包括 `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`。
outcome-clean 的替代入口是 `ops/RECOVERY_ANCHOR.md`。

【OFF-LIMITS】`ops/EXPOSURE_LEDGER.md`（研究轴）不在你的阅读集内，不得打开。

**`ops/REVIEWER_EXPOSURE_LOG.md`（席位轴）本轮不随包，也不请你读。**

---

## 3. 请重点打的五件

### ① 第二个「锚在最旧那份上」的锚（**主要攻击面，见 §0**）

### ② 新建的批准守卫，本身够不够

`tests/test_every_approval_is_accounted_for.py`：逐份按哈希重建原像 ·
三个锚定值在每份里必须一致 · falsifier 对每份都查 ·
**出现第四份未检查的批准即失败**。

**请判三件**：

1. 「出现未检查的批准即失败」是**真的失败闭合**，还是又一个刚好等于我想到的边界？

   **这一条我本来要问你，写到一半量了，结果是它当时确实漏了一份**（§15.7）：
   `APPROVED_CR1_GRAMMAR_SHA256` —— CR1 语法是第四份已批准工件，
   自成 canonical 块、由 profile 内一行绑定，而守卫的模式只认
   `APPROVED_PROFILE_SHA256`。**为了阻止我锚在子集上而写的守卫，自己锚在了子集上。**
   已放宽为任意 `APPROVED_*SHA256` 并加了种类作用域表。

   **仍未覆盖、我请你判值不值得补的**：批准若**根本不以哈希声明的形式存在**
   —— 例如 Aaron 在消息里口头给出、只被转录进某份记录的散文里 ——
   这个守卫在原理上看不见。`SIGNABLE_RATIFICATION_ROUTES=1`（实测，唯一路线＝
   profile id + sha256 + doc HEAD）是我认为它够用的理由。**请判这个理由。**
2. R3 的原像在 `PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` 里，
   **文件名写着「PROPOSAL」而它承载的是已批准原像**。请判这是否本身就是个问题。
3. 三份的 `SUPERSEDED_..._FOR_P3_ONLY` / `..._FOR_P3_AND_F3_ONLY` 是**有范围的取代**。
   我据此认为 R1 的那三个值仍管本措辞用到的字段。**请判这个推理**，
   而不是采信我核出的「三份逐字相同」这个巧合。

### ③ (a) 的重新分类对不对

第 2 轮判：`FINAL bytes == intended` 无法证明比较曾发生，那是**过程性质**。

我复现了（不读 FINAL 的变异体留下完全相同的调用后状态），
并把 (a) 的检出途径改为**被钉住的机制性质**，同时明写「调用后状态**不能**充当本条途径」。

**请判**：

1. 改后的分类正确吗？
2. **「被钉住的机制性质」这个类别本身，在本设计里是否被滥用**——
   (b) 也是这个类别。两条都归进去之后，还剩几条是真正的文件系统事实？
   若答案是「只剩 (c)」，那 §3 的门学说（门只分类调用结局）是否已经名存实亡？
   **这是我想到的最强反对，我没有答案。**

### ④ 判据 (1) 现在满不满足

第 2 轮判 `(1) NO · (2) YES · (3) YES · (4) NO · (5) YES`，
NO 的两条分别是 (a) 的分类与陈旧化保护，**两条都已处置**。

**请逐条重判。** builder 自评两条已闭合，**明写不自证**。

### ⑤ 那三条我无法自证的历史事实

第 2 轮明列了它无法独立复核的三类（§12.0 的历史搜索、历史变异运行结果、
上一轮 delivery 的旧字节）。**本轮同样无法自证。**

**请判**：这三类**是否需要**被复核，还是它们对当前结论不承重。
若承重，请说需要什么才能让它们可核 —— 那是我下一轮要建的东西。

---

## 4. builder 主动申报的四件

```
一、第 1 轮我给了你的前任一个我自己发明的缺陷（§14 撤回）。
   第 2 轮我又只锚了三份批准里的第一份。**两次都不是别人误读我。**
二、写第 2 轮那条隔离守卫时，我自己先犯了两次同一个病：
   第一版禁止一切递归 —— 在一个**正确的**递归上变红；
   第二版查「文件里有没有读」—— 标记了五处读具名常量的调用。
   第三版才对。规则比它要保护的性质宽，正是这几轮一直在说的那个错。
三、**事故自报**：排查时我的 shell 循环枚举了整个 ops/，
   于是一次内容 grep 落在了隔离件 MC_TO_STRATEGY_MASTER_PLAN.md 上。
   回来的只有一个计数，无 outcome 内容 —— **但那是模式恰好够窄，是运气**。
   恢复锚 §5 记的第 3 个被烧席位就是同一个动作。
   记录：ops/INCIDENT_BUILDER_GREPPED_A_QUARANTINED_FILE_20260829.md
四、我有一条提交是在全量套件红着时打的（空断言探测器抓到我新写的守卫）。
   pre-commit 钩子只跑传输守卫不跑全量，所以没拦住。已修，并记在提交信息里。
```

**列出三、四是因为它们影响你对 builder 纪律的评估**，而那是你判断的输入。

---

## 5. 只读

不修任何代码、不改任何文件；不推送、不打标签、不 amend、不 commit。
**不得代 Aaron 批准新措辞。** 你的 PASS 只满足 CONDITIONS 第 3 条的复审那一半。
**本轮不释放任何 gate。**

---

## 6. 返回格式

```
REVIEW_ID=c-build-2-wording-r3
TRANSPORT_PRECHECK=PASS|STOP
VERDICT=PASS|HOLD
WORDING_MAY_GO_TO_AARON=YES|NO

SECOND_STALE_ANCHOR=<是否找到第二个「锚在最旧那份上」的锚>
APPROVAL_GUARD_ASSESSMENT=<新守卫够不够；三问逐条>
CLASSIFICATION_OF_A=<改后的分类是否正确>
PINNED_MECHANISM_OVERUSE=<「被钉住的机制性质」是否被滥用；门学说是否名存实亡>
CRITERION_1_NOW_MET=YES|NO（逐条）
CONDITIONS_MET=<五条逐条>
HISTORICAL_FACTS_LOAD_BEARING=<那三类无法自证的历史事实是否承重>
UNVERIFIABLE_SELF_REPORTS=<本轮你无法独立复核的>
NEW_DIVERGENCE_SHAPES=
STRONGEST_OBJECTION=<即使 PASS 也要写>
FINDINGS=<逐条，带文件与行号，标 HIGH/MEDIUM/LOW>
SCOPE_CREEP=NO|YES_OUTSIDE_REVIEWED_SET
UNRESOLVED_FOR_AARON=
SEAT_STATUS=BLIND|BURNED
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、实现/修复独立性、设计贡献、模型多样性>
```

**本复核不释放任何 gate，不构成 Aaron 的批准。**
