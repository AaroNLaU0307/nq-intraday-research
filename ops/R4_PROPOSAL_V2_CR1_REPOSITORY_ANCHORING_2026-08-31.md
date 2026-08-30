＃ R4 提案 v2 —— CR1 语法块的仓锚定

```ini
RECORD_TYPE=PROPOSAL（不是批准；本文件不生效、不追加任何 CR1 行）
SUPERSEDES=ops/R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md（v1，HOLD）
BY=Opus 5，builder seat，2026-08-31
BASIS=ops/RULING_FABLE_S5_AND_R4_2026-08-27 · ops/RULING_SOL_R4_HOLD_2026-08-31
OWNER_DECISION=OD-5（Aaron 选「甲」：收窄主张并把分岔交下一席位判）
STATUS=待 fresh Sol 复审 → Aaron 批准（§D.10.3 原路）
FREEZE=R4 ratify 之前，「禁止追加任何 CR1 行」持续在 force（实测 CR1 行数 0）
```

---

## 0. v1 被 HOLD 的四条，逐条怎么处理的

```
① 锚点主张过宽      我把「发现」与「验证」混为一谈，并用加粗否定句否掉了
                    真正承重的那一半。v2 分开写，并把「仓被移动即找不到」
                    留成明写的残留 —— 不解决它
② 那句话的定性      席位判「仓选择判据」，我判「澄清」判错了。v2 按仓选择判据写
   ＋用词错误        并删掉「INTACT-looking」：墓碑 0 事件 vs 见证 17，
                    按未改判据它**并不 INTACT**，只是可解析为空
③ 块不完整          v1 漏了 8 个字段，不构成可哈希的块。v2 给出**完整块**
④ 分界失败          N1 的父提交无该文件，N1 也未追加任何行。改 strictly after
```

**②的机制订正值得单独说**：S7 那天三个测试通过，**不是因为墓碑看起来完好**，
而是因为**它们根本没有应用见证判据**。判据是好的；漏的是调用它的人。
我把危险描述错了机制，v2 按实际机制写。

---

## 1. 完整 canonical 块 —— 这一份就是待批准的产物

**口径不是猜的**：`CANONICAL_BYTES=BEGIN 与 END 两行之间的行（不含这两行），
LF 结尾，UTF-8，逐行原样`。把它施于 R3 块**复算出 `c251335f…` 分毫不差**，
下面的新哈希由**同一段代码**算出。

```
BEGIN_ND1_CR1_GRAMMAR_R4
CR1_SHORT_ID=CR1
CR1_TOKEN=SUPPLEMENT_RUN_CRASH_RESOLVED
CR1_ROW_CLASS=NUMBERED
CR1_ACTOR=main agent
CR1_TERMINAL=NO
CR1_INCIDENT_REQUIRED=YES
CR1_PERMITTED_PREDECESSOR=P3
CR1_PERMITTED_SUCCESSOR=F3
CR1_REQUIRED_FIELDS=supplement_id|dangling_event|incident_id|crash_evidence_summary|recovery_authorization_doc|registry_intact_verification|registry_witness_ref
CR1_FIELD_DOMAIN_dangling_event=P3
CR1_FIELD_DOMAIN_registry_intact_verification=SHA256_HEX64_OF_REGISTRY_BYTES_AS_READ_BEFORE_THIS_ROW_IS_APPENDED
CR1_FIELD_DOMAIN_registry_witness_ref=THE_LATEST_WITNESS_RECORD_THE_READ_WAS_CHECKED_AGAINST
CR1_REGISTRY_INTACT_PREIMAGE=the complete on-disk bytes of ops/TRIAL_REGISTRY.md IN THE REGISTRY REPOSITORY (CR1_REGISTRY_REPOSITORY_ANCHOR), read once, immediately BEFORE the CR1 row is appended; no normalization, no encoding change, no line-ending rewrite; the value is therefore never part of its own preimage. WHICH REPOSITORY is a repository-selection criterion, not a restatement of the intact criterion: a file at the same relative path in the framework repository is the tombstone, which parses as an empty registry and would therefore FAIL the intact criterion against any non-empty witness rather than pass it. The hazard is not that a tombstone looks intact - it is that a reader who never applies the witness criterion never finds out
CR1_REGISTRY_REPOSITORY_ANCHOR=the registry repository is identified in TWO parts and they are not the same thing. DISCOVERY: the framework repository's ops/TRIAL_REGISTRY.md is a tombstone bearing REGISTRY_MOVED_NOT_A_REGISTRY and stating where the registry repository is; that stated location is the ONLY means of finding it, it is machine-specific, and if the repository is moved without the tombstone being updated a cold reader cannot find it - this residual is NOT closed by this grammar and moving the repository is therefore a governed act that must update the tombstone. VERIFICATION: once found, the repository is confirmed by the S4 cross-pin ruled in dec-registry-migration-2026-08-27 - it contains commit N1 carrying ops/TRIAL_REGISTRY.md, and N1's message names the framework repository's pre-migration HEAD O0. A commit hash confirms identity inside an object database already located; it cannot locate one
CR1_REGISTRY_INTACT_CRITERION=the read is INTACT iff it is a superset of the witness named by registry_witness_ref: its event count is not lower and the witnessed last row is still present. A digest alone proves only that bytes were hashed; the witness is what it is hashed AGAINST
CR1_REGISTRY_INTACT_COLD_RECOMPUTE=the preimage is recoverable from git history of ops/TRIAL_REGISTRY.md at the commit preceding this row, and the witness file is append-only, so a cold reader can recompute both sides. WHICH history: N1 is the commit that first carries the file in the registry repository, its parent carries no such file, and N1 appended no CR1 row - it moved a file. So rows appended STRICTLY AFTER N1 recompute in the registry repository, and rows appended at or before O0 recompute in the framework repository, whose blobs remain in place because the migration rewrote no history
CR1_REGISTRY_INTACT_UNRESOLVED=TOCTOU between the read and the append is NOT closed by this grammar; it is the same critical-section gap the D-3 review named, and no lease exists
CR1_GRAMMAR_CONTAINS_NO_EXECUTION_AUTHORIZATION=YES
END_ND1_CR1_GRAMMAR_R4
```

```ini
CANONICAL_BYTES=同上口径
R4_CANONICAL_SHA256=6e62fd2dc349468fd3bd1fdd8c5f2ef20b5b4cfade215eba07609107ca0f5233
R4_CANONICAL_BYTE_COUNT=3384
LINES=18（R3 为 17）
VERBATIM_CARRIED=15 / 17
CHANGED=CR1_REGISTRY_INTACT_PREIMAGE · CR1_REGISTRY_INTACT_COLD_RECOMPUTE
ADDED=CR1_REGISTRY_REPOSITORY_ANCHOR
```

**「15 逐字保留」是机械得出的，不是我复述的** —— v1 正是死在复述上
（漏 8 个字段）。生成脚本逐行比对 R3 与 v2，只有上列两行不同。

---

## 2. 条件 (a)：作废 `c251335f…`，以及绑定怎么更新

```
VOIDED_APPROVAL_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
VOIDING_REASON=所指重绑定，判据未变
REPLACEMENT_SHA256=6e62fd2dc349468fd3bd1fdd8c5f2ef20b5b4cfade215eba07609107ca0f5233
```

**绑定如何更新（v1 完全没写，这是 THIRD_FIELD_MISSED 的一半）**：

```
承载旧值的记录   ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md 的 CR1_GRAMMAR_SHA256
                 ops/DECISION_PACKET_ITEM6_OPEN_FABLE.md 的 RECOMMENDED_CR1_GRAMMAR_SHA256
更新方式         **本提案不改它们**。R4 一经按 §D.10.3 批准，
                 该批准记录即为新绑定的权威；上述两份是**历史记录**，
                 按既有惯例保持原样并由 R4 的批准块引用作废
为什么不就地改   它们是已批准/已返回的记录。就地改一个已批准的哈希，
                 等于让记录说它当时说的不是它说的话
```

---

## 3. 仍然未解决的，明写

```
仓被移动          若 registry 仓移动而墓碑未更新，冷读者无法发现它。
                  **本语法不关闭这条**；它把「移动 registry 仓」定为
                  必须同时更新墓碑的受治理动作
TOCTOU            逐字未动，仍未关闭，仍无 lease
```

---

## 4. **一个分岔，请下一席位判 —— 不由我判**

上一席位说我的锚点主张**触发了证伪器**（须回决裁层）。分岔是：

```
甲  收窄主张：承认路径做发现、commit 对做验证，把移动残留写明。
    桥仍只引用 S4，**没有引入任何新钉法** —— 我认为证伪器不触发
乙  解决它（加一个仓发现机制）—— 那才是 S4 之外的新钉法，触发，回决裁层
```

**v2 走的是甲**（Aaron OD-5 选定）。

**但我不主张甲是对的。** 我上一次自己判「澄清 vs 新判据」判偏了，
而且偏向对我有利的一边；**甲同样对我有利**（不用回决裁层）。
所以这个判断请你做：**收窄主张算不算「在 R4 内自行扩权」？**

若你判触发，v2 作废，桥回决裁层 —— 那是正确结果，不是坏结果。

---

## 5. 本提案不做什么

不批准任何东西；不追加任何 CR1 行；不重写任何历史；
不改 `CRITERION`／`UNRESOLVED`／必填字段／字段值域（15 行逐字保留，机械可验）；
**不改任何已批准或已返回的历史记录**；
**不自行认定 §4 的分岔**。
