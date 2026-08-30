＃ R4 复审 —— CR1 语法块的仓锚定 · fresh Sol

```ini
REVIEW_ID=r4-cr1-anchoring
DELIVERY_STATUS=RETURNED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（R4 修订案复审）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；ops/RULING_FABLE_S5_AND_R4_2026-08-27 的决裁席（Fable 5）；
            迁移方案 Route A 的前序复审会话；c-build-2-wording* 任何轮次的会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**READ THIS PROMPT FROM DISK, not from a paste.**
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_R4_CR1_ANCHORING_SOL.md`

框架仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
registry 仓根：`C:\Users\Aaron\quant-data\itsf-registry`（**本轮许可读**，见随包件）

禁区清单随包交付：`ops/OFF_LIMITS_COMPANION_R4.md`，请一并读。
**权威登记册**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。

---

## 0. 这一轮和措辞那八轮不是同一件事

那八轮审的是**仪器**。这一轮审的是一个**canonical 块的修订** ——
它会作废一个已批准的哈希并换上新的，然后解开「禁止追加任何 CR1 行」的冻结令。

**判据来自决裁，不是我定的**（`ops/RULING_FABLE_S5_AND_R4_2026-08-27`，在受审集内）。
它给了三条条件与一条证伪器。本包按那四条组织。

---

## 1. 证伪器：我跑了，未触发 —— **请你独立重跑**

裁定：

> 若 R4 起草时发现 S4 交叉互钉不足以让冷读者单凭字节完成跨仓解析
> （即桥必须引入 S4 之外的新钉法），本裁定「桥引用 S4 即可」的前提即被证伪，
> 桥的设计须回到决裁层重裁而非在 R4 内自行扩权。

我的复算，起点只有「框架仓在哪」一个事实，此外只用盘上字节与 git 对象：

```
1  框架仓 ops/TRIAL_REGISTRY.md 是墓碑（REGISTRY_MOVED_NOT_A_REGISTRY）
2  墓碑点名 REGISTRY_REPO / N1 e71e54fe… / SHA0 ee9da33f…
3  O1 b8bc8665… 的 commit message 重复同一个 N1（committed 字节）
4  到 registry 仓：N1 存在，blob 的 sha256 == SHA0
5  N1 的 message 回指 O0 51fa5192…，且 O0 的 blob 是同一批字节
```

**这一步不要采信我。** 随包件已许可你读 registry 仓与见证根，
就是为了让你能自己走一遍。若你认为其中任何一步依赖了 S4 之外的东西，
**证伪器就触发了，本提案作废，桥回决裁层。**

---

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=4c536a2550086a795cb518279d28b413925c7fee
```

**语义**：该 commit 之后没有任何 commit 触碰过下表的参考件。
本提示自身不在该 range 内（发出 delivery 就是对它的一次提交，无不动点）。

| sha256 | bytes | 路径 |
|---|---|---|
| `9f1269f1c8e8e88767d14d87ed36169240729e806d253bfd01b1e13dab4e2cec` | 8866 | `ops/R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md` |
| `5a30398b8d6dbd35bc702362e458d6c10c135d3c692082d1c71819136db400c5` | 15702 | `ops/RULING_FABLE_S5_AND_R4_2026-08-27.md` |
| `2dac910421ec3d6ba94c2cb94f5a20ba6f16e0584fbdfdebb36f0f31f9a69a33` | 21471 | `ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md` |
| `fdb18eb71273a4eb8a08adbda885f5f66531292bb8c1be2a4aa4f35063a747e1` | 3690 | `ops/MIGRATION_ROUTE_A_COMPLETED_2026-08-31.md` |
| `eb8b6567d99760ee7438e8105e08f48a0584e0798175a9a236a6be5bf73b96b0` | 37109 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` |
| `bf96a2861f64d0b5251696f01dd130d983e57cd4da815ade6ed4cef6ff25a0ae` | 2608 | `ops/TRIAL_REGISTRY.md` |
| `1cf258afd4e56dd3b37fb1c84adaaa635f55aec13c01092c919ad7851e00f17c` | 12939 | `src/itsf/mc/registry_boundary.py` |
| `a54eea0d2bf03d46a19959ed4d041e1671f70b162727609e7274de84dc5a6057` | 7665 | `tests/test_registry_absence_refuses.py` |
| `52cb18c008b032bbe273670261870eeb70136a508482ebd948799193a74bb246` | 10548 | `tests/test_registry_path_single_construction.py` |
| `783e32567a501ba52742a39654ba6ab2f7612e5ef0fe00b718d43c3dccc64c30` | 19411 | `tests/test_registry_boundary.py` |
| `0937332c368287bf89614f2f278dc876faf79569ef266059e4917c6ce163e9fb` | 13289 | `tests/test_registry_witness.py` |
| `7f83623d06b573217b6926ba2c4acba9a2bb502ad908de680354648ece9bad21` | 2642 | `ops/OFF_LIMITS_COMPANION_R4.md` |

**delivery**：`ops/PROMPT_R4_CR1_ANCHORING_SOL.md`，字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**核对你读的是当前文件**：line 67 of it must read
`REVIEWED_SET_UNCHANGED_SINCE` 那一行。对不上 ⇒ 陈旧粘贴 ⇒ **STOP**，回磁盘重读。

**受审集里那份 `ops/TRIAL_REGISTRY.md` 是墓碑，不是 registry。** 它在集内，
因为墓碑的内容就是桥的第一跳。真 registry 在另一个仓，路径见 §0。

```
核验  python -m pytest tests/test_registry_absence_refuses.py -q
预期  11 passed
核验  python -m pytest tests/test_registry_path_single_construction.py -q
预期  7 passed
核验  python -m pytest tests/test_registry_boundary.py -q
预期  14 passed
```

---

## 3. 提案改了什么 —— 两处，且只有两处

逐字全文在 `ops/R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md`。摘要：

```
新增   CR1_REGISTRY_REPOSITORY_ANCHOR   锚点是 S4 的 commit 对，不是路径
改     CR1_REGISTRY_INTACT_PREIMAGE     点明「在 registry 仓里的那一份」
改     CR1_REGISTRY_INTACT_COLD_RECOMPUTE  点明 git history 是两段，N1 是分界
不动   CRITERION · UNRESOLVED · REQUIRED_FIELDS · 三条 FIELD_DOMAIN
       · CONTAINS_NO_EXECUTION_AUTHORIZATION      —— 逐字复述在提案 §2.4
```

**起草时才看清的那一条**（原文没给冷读者的信息）：

> 迁移之后，`ops/TRIAL_REGISTRY.md` 的 git history 是**两段**，分界点是 N1。
> N1 之前追加的 CR1 行，其前像在**框架仓**的历史里；之后的在 **registry 仓**。
> 两段都没有被重写（S5 是 GIT_ONLY，旧 blob 原样留在 O0 上），所以两段都仍可读 ——
> **但原文没有告诉冷读者去哪一段读。**

只改 `COLD_RECOMPUTE` 不改 `PREIMAGE`，会在同一个块里留下两条不同的解析规则，
而那正是裁定 ① 点名禁止的。

---

## 4. 请你正面确认的三件（条件 (b) 逐字要求）

```
PREIMAGE 读取口径    除仓锚定外逐字义不变？
                     （一次读 · 追加之前 · 不规范化 · 值不在自己前像里）
CRITERION 超集判据   逐字未动？
UNRESOLVED TOCTOU    逐字未动，且未被悄悄改窄？
```

**TOCTOU 那条我特别请你盯**：它仍然**没有**被关掉，本次修订也**没有**碰它。
一条被悄悄改窄的已知缺陷，正是「未实质削弱原批准」这个确认要挡的东西。

---

## 5. **一个我判断对自己有利、因此不该由我定的问题**

我在 `PREIMAGE` 末尾加了一句：

> A file at that relative path in any OTHER repository is NOT the registry:
> the framework repository's copy is a tombstone, and a tombstone parses
> cleanly to zero event rows, so reading it yields an INTACT-looking preimage
> of an empty registry

**它是「澄清」还是「新增判据」？**

我认为是澄清 —— 它描述既有事实的后果，不改变 INTACT 的判定条件。
**但这个判断由我作出，而且它对我有利**（澄清不算实质修订，新判据算）。
所以它需要一个不是我的人来判。

**它不是凭空加的**：S7 当天，三个测试正是这样读到墓碑而**平凡通过**的 ——
墓碑解析干净、零事件行，看起来就是一份完好的空 registry。

---

## 6. 请攻击这里

1. **§1 的冷读，你自己走一遍。** 有没有哪一步其实依赖了 S4 之外的东西？
2. **锚点选 commit 对而不是路径，够不够？** 若两个仓都被移动，
   冷读者手上只剩内容寻址的 commit —— 他还能找到仓吗？若不能，这是不是新钉法？
3. **两段历史的分界。** N1 是分界这句话，对**恰好在 N1 那一刻**追加的行成立吗？
4. **§5 那个判断。** 澄清还是新判据。
5. **有没有第三处该改而我没改的？** 我声称「两处，且只有两处」。

---

## 7. 交付要求

```
VERDICT=                      PASS|HOLD
FALSIFIER_INDEPENDENTLY_RUN=  YES|NO —— 你自己走冷读了吗？结论？
REVISION_WEAKENS_ORIGINAL=    NO|YES —— 条件 (b) 要的正面结论，逐条给 §4 三项
CLARIFICATION_OR_NEW_CRITERION= §5 那句，你的判定
ANCHOR_SUFFICIENT=            锚点是 commit 对，够不够？
THIRD_FIELD_MISSED=           有没有第三处该改而未改？
SEAT_STATUS= / FORBIDDEN_PATHS_OPENED= / SOURCE_WRITES= / PERSISTED_SEARCH_OUTPUT=
REGISTRY_REPO_READ=           YES|NO（本轮许可，但要记进席位轴台账）
```

**HOLD 受欢迎。** 这是一个会作废已批准哈希、并解开冻结令的修订 ——
它宁可多审一轮，也不该带着一条我自己判给自己的「澄清」出去。
