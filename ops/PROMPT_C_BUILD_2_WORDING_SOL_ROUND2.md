# C_BUILD_2 措辞复审 · 第 2 轮 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r2
DELIVERY_STATUS=ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 2 轮，裁定 B 的 CONDITIONS 第 3 条）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1 轮 c-build-2-wording 的会话**；N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**本文件从磁盘读取 —— read this prompt from disk, not from a paste。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND2.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

```
REVIEWED_SET_UNCHANGED_SINCE=427224f15b0d1793a5401ab129ee38d969b9e27c
```

> **确认你读的是当前文件**：**line 25 of it must read**
> `REVIEWED_SET_UNCHANGED_SINCE=427224f15b0d1793a5401ab129ee38d969b9e27c`。
> 对不上 ⇒ 你手上是陈旧粘贴 ⇒ **STOP**，回到磁盘重读。

**语义**：该 commit **之后**没有任何 commit 触碰过 §1 表中的参考件。
**它不是也不该是当前分支头。**

**本提示自身不在该 range 内**（发出 delivery 就是对它的一次提交，无不动点；
见 `tests/test_the_delivery_cannot_pin_itself.py`）。
**发行时的字节记在 `ops/ARTIFACTS_UNDER_REVIEW.json` 中本 review_id 的
`role: delivery` 条目**——去那里比对，不要在本表里找。
（第 1 轮此处写错，声称自身哈希在 §1 表内而表里没有那行，被正确判 `TRANSPORT_PRECHECK=STOP`。）

---

## 0. 第 1 轮的最大发现是：**我给了复审席一个我自己发明的缺陷**

第 1 轮判 HOLD，五条 finding。四条是真的，已闭合。
**第五条（HIGH ②，(a) 不满足覆盖保全）不成立 —— 而它不成立的原因是我。**

我在 §12.5 写下：

> `already_sealed` 分支……**不问出处、从未复读校验**

**「不问出处」是真的。「从未复读校验」是假的。**

```python
if final.exists():
    existing = final.read_bytes()          # 这就是复读
    if existing == intended:               # 这就是校验
        return PartialAction("already_sealed", ...)
```

我把 (a) 的违规类**偷换**成「出处未知的 FINAL 被接受」——我自己引进的更宽的类——
再宣布 (a) 覆盖不了它，再把 (a) 缩窄。

第 1 轮席位的 `STRONGEST_OBJECTION` 引的正是我这句「明确承认」。
**它在给定我的前提下推理完全正确。前提是我供的，前提是假的。**

### 因此这一轮的主要攻击面是（§3 ①）

> **送审包里每一句 builder 自陈，都是复审席无法独立复核的输入。**
> 请把 §12–§14 里所有形如「实测……」「我量到……」的自陈**当作待证而非已证**，
> 挑出你**能**独立复核的，复核它们；对**不能**独立复核的，明说是哪些。

我不知道还有几句是这样的。**这是我请你找的东西。**

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `df3258c425b798b3895b6f43843c3bfd4515db33854b5caa143cee9d2a424046` | `53363` | `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `101b6b7b272df2b0f71359a5e4d5310e896d10a27c072d783decbf7c9dfaeb82` | `11888` | `ops/RULING_FABLE_C_BUILD_2_HOOK_2026-08-28.md` |
| `3964c7b8227542bd78c1b7706493dbf16cbf86c30b824a5560bfa505eb174adc` | `11830` | `ops/ND1_PROFILE_RATIFICATION.md` |
| `446ebd4bf51dc797d30566d54076c34d771ccd5114d34e931dc32e189fd3328a` | `47106` | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | `32616` | `src/itsf/mc/supplement_contract.py` |
| `c2987bafbe62e3a16dcc3249016985c91cac8259b04bec4ec959423300d1be95` | `6100` | `tests/test_every_sealed_final_was_read_back.py` |
| `3b8fd362614ee7e7c689bde19d9797b501464de5bc2caa57cb8271963effae50` | `6869` | `tests/test_the_ratified_preimage_is_reconstructible.py` |
| `1310caa884f9c644f1bd2576227c33b15600251640ceb90283a886033f300809` | `10129` | `tests/test_c_build_2_wording_coverage.py` |
| `40f9ecce8b9ecf5835073291a200920316f65478e4188a633d44ed0680a311c0` | `26667` | `tests/test_n09_checkpoint_assertions.py` |

任一条不匹配 ⇒ STOP。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得 grep、不得 rglob、不得广域检索。** 需要哪个路径，向工作会话要。

**禁区清单随包**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 是权威登记册，
本 prompt 不复述其内容，你**不得打开它所登记的任何一件**。

【OFF-LIMITS】隔离子树 `ops/outcome_quarantine/**` —— 禁区，不得打开、不得搜索、不得列目录，
其中包括 `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`。
outcome-clean 的替代入口是 `ops/RECOVERY_ANCHOR.md`。

【OFF-LIMITS】`ops/EXPOSURE_LEDGER.md`（研究轴）不在你的阅读集内，不得打开。

**`ops/REVIEWER_EXPOSURE_LOG.md`（席位轴）本轮不随包，也不请你读**
（规则见 `tests/test_the_seat_ledger_is_not_shipped_to_seats.py`：
台账只在被裁对象就是它自己时才随包）。

---

## 3. 请重点打的五件

### ① builder 自陈的可复核性（**主要攻击面，见 §0**）

### ② §14 的撤回本身对不对

我用「计数 `Path.read_bytes` 落在 FINAL 名上的次数」证明每条封存路径都复读比对过。

**请判这个证明**：

1. 计数法是否证明了它声称的东西？一次 `read_bytes` 并比对 `intended`，
   与 promote 后那次复读，**在防护强度上真的等价吗**？
   （builder 认为等价：两者都确立「FINAL 的字节 == intended」，
   TOCTOU 风险也相同。**请判这个论证，别采信。**）
2. `retry_permitted` 读 0 次而 builder 说「它没有任何 FINAL 被当作已封存」——
   **请核这句**。
3. **撤回会不会矫枉过正**？第 1 轮席位指出的「出处未知」是真的。
   §14.8 把它改记为「关于机制的独立事实，与判据 (1) 无关」。
   **请判这个改记是诚实划界，还是第二次把缺陷改写成不在范围内。**

### ③ 判据 (1) 现在到底满不满足

(a) 已恢复原措辞；(b)(c) 的实际缺陷已闭合（§13.3、§13.4）。

**请逐条判 CONDITIONS 第 2 条（五判据对照及有效变异证红）现在是否满足。**
builder 自评「(a) 的障碍消失，(b)(c) 已闭合」，**但明写不自证** —— 这是你的事。

### ④ falsifier 的闭合方式

§13.2 重建了批准原像（`803d991` 第 1309 行起 49 行 2527 字节，
SHA256 == `ND1_PROFILE_RATIFICATION.md` 的 `APPROVED_PROFILE_SHA256`），
在其中检索时机类词，仅命中 `RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04`。

**请独立重建并复核**（`tests/test_the_ratified_preimage_is_reconstructible.py` 每轮从 git 重建）。
**关于跨度，我把话说准**：ratification 记录 §2 的「49 行/2527 字节」只是我的**搜索线索**，
真正确认跨度的是**哈希命中** —— 我暴力扫全文找长度 2527 且 SHA256 等于
`APPROVED_PROFILE_SHA256` 的连续片段，命中唯一一处。
**所以即使那份记录的跨度描述有误，原像仍然是对的**，因为原像是被批准哈希选中的。

**请判这个论证。** 唯一性我原本打算作为问题交给你，写到一半停下来量了：
全文扫描（每个起点 × 1–79 行窗口，先按 2527 字节筛再比哈希）**命中恰好 1 处**，
即第 1309 行起 49 行。已钉在
`test_the_ratified_preimage_is_reconstructible.py::test_the_preimage_is_the_only_span_with_that_hash`。

### ⑤ `SILENT_DELETE_FORBIDDEN` 是导出值不是批准值

重建过程中量到：它不在批准原像内，由 `MODIFY ⇒ YES` 经该文件第 1299 行的导出表导出，
**表在原像之外**（原像自 1309 行起）。(b) 的依据行已据此更正。

**请判**：一条依据「有已批准前件的导出值」的断言，
满足判据 (4) 锚定保全吗？还是锚定必须直达批准字节？

---

## 4. builder 主动申报

```
一、§12.5 是我发明的缺陷，§14 是撤回。这不是「发现新事实后修正」，
   是我把一个类偷换成另一个类。与同一天那次 Class B 误分类同形态：
   机械可测的一半量对了，另一半靠断言。
二、第 1 轮的 TRANSPORT_STOP 也是我的错（声称自身哈希在 §1，表里没有那行）。
   两次都不是别人误读我，是我写下了假的东西。
三、因此 §0 那条不是客套：**我不知道 §12–§14 里还有几句是这样的。**
四、机制仍然零改动。本轮所有改动都在测试与记录。
```

---

## 5. 只读

不修任何代码、不改任何文件；不推送、不打标签、不 amend、不 commit。
**不得代 Aaron 批准新措辞** —— 你的 PASS 只满足 CONDITIONS 第 3 条的复审那一半。
**本轮不释放任何 gate。**

---

## 6. 返回格式

```
REVIEW_ID=c-build-2-wording-r2
TRANSPORT_PRECHECK=PASS|STOP
VERDICT=PASS|HOLD
WORDING_MAY_GO_TO_AARON=YES|NO

UNVERIFIABLE_SELF_REPORTS=<§12–§14 里你无法独立复核的自陈，逐条列出>
SELF_REPORTS_YOU_DID_CHECK=<你实际复核了哪些，结果如何>
RETRACTION_ASSESSMENT=<§14 的撤回：成立 | 矫枉过正 | 另有问题>
CRITERION_1_NOW_MET=YES|NO（逐条）
CONDITIONS_MET=<五条逐条>
逐条作答：① 自陈可复核性 · ② §14 撤回 · ③ 判据(1) · ④ falsifier 的锚 · ⑤ 导出值锚定
NEW_DIVERGENCE_SHAPES=
STRONGEST_OBJECTION=<即使 PASS 也要写>
FINDINGS=<逐条，带文件与行号，标 HIGH/MEDIUM/LOW>
SCOPE_CREEP=NO|YES_OUTSIDE_REVIEWED_SET
UNRESOLVED_FOR_AARON=
SEAT_STATUS=BLIND|BURNED
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、实现/修复独立性、设计贡献、模型多样性>
```

**本复核不释放任何 gate，不构成 Aaron 的批准。**
