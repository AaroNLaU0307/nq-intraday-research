＃ R4 提案 —— CR1 语法块的仓锚定

```ini
RECORD_TYPE=PROPOSAL（不是批准；本文件不生效、不追加任何 CR1 行）
BY=Opus 5，builder seat，2026-08-31
BASIS=ops/RULING_FABLE_S5_AND_R4_2026-08-27（RULING=必须 R4，DELEGATED=YES）
TIMING=迁移执行完成之后起草 —— 裁定的附带时序，已满足（S7 PASS，2026-08-31）
STATUS=待 fresh Sol 复审 → Aaron 批准（§D.10.3 原路，不加新门类）
FREEZE=R4 ratify 之前，「禁止追加任何 CR1 行」持续在 force
```

---

## 0. 证伪器：**已执行，未触发**

裁定附了一条证伪器：

> 若 R4 起草时发现 S4 交叉互钉不足以让冷读者单凭字节完成跨仓解析
> （即桥必须引入 S4 之外的新钉法），本裁定「桥引用 S4 即可」的前提即被证伪，
> 桥的设计须回到决裁层重裁而非在 R4 内自行扩权。

**我把它跑了，而不是论证它。** 起点只有一个事实：框架仓在哪。此外只用盘上字节与
git 对象，不用 chat、不用记忆、不用迁移自己提交之外的任何散文：

```
1  框架仓 ops/TRIAL_REGISTRY.md 是墓碑                       ✅
2  墓碑点名 REGISTRY_REPO / N1 / SHA0                        ✅
3  O1 的 commit message 重复同一个 N1（committed 字节，非工作区）✅
4  到被点名的仓：N1 存在，且其 blob 的 sha256 == SHA0        ✅
5  N1 的 message 回指 O0，且 O0 的 blob 是同一批字节          ✅
```

**未触发。桥引用 S4 即可，不需要新钉法。** 本提案据此进行。

---

## 1. 要改什么 —— 两处，且只有两处

迁移之后，**两个仓在同一相对路径 `ops/TRIAL_REGISTRY.md` 上各有一个东西**：
新仓的真 registry，与旧仓的墓碑。原块里有两条硬依赖因此变得有歧义。

### 1.1 `CR1_REGISTRY_INTACT_PREIMAGE`

**原文逐字**：

```
the complete on-disk bytes of ops/TRIAL_REGISTRY.md, read once, immediately
BEFORE the CR1 row is appended; no normalization, no encoding change, no
line-ending rewrite; the value is therefore never part of its own preimage
```

**问题**：「the complete on-disk bytes of `ops/TRIAL_REGISTRY.md`」不再指向唯一一个东西。
按字面，墓碑也满足这个描述 —— 而墓碑**解析干净、零事件行**。
这不是理论风险：S7 那天，三个测试正是这样读到墓碑而**平凡通过**的。

### 1.2 `CR1_REGISTRY_INTACT_COLD_RECOMPUTE`

**原文逐字**：

```
the preimage is recoverable from git history of ops/TRIAL_REGISTRY.md at the
commit preceding this row, and the witness file is append-only, so a cold
reader can recompute both sides
```

**问题比 §1.1 深一层，而这是起草时才看清楚的**：

> **「git history」在迁移之后是两段，分界点是 N1。**

```
在 N1 之前追加的 CR1 行   其前像在**框架仓**的历史里（O0 及更早）
在 N1 之后追加的 CR1 行   其前像在**registry 仓**的历史里
```

**两段都没有被重写**（不变量：不得要求任何历史重写；S5 是 GIT_ONLY，
旧仓的 blob 原样留在 O0 上）。所以两段都仍可读 —— **但冷读者必须知道去哪一段读**，
而原文没有给他这个信息。

**只改 `COLD_RECOMPUTE` 而不改 `PREIMAGE` 会在同一个块里留下两条不同的解析规则** ——
这正是裁定 ① 明令不许的。

---

## 2. 提议的修订块

**改动仅限仓锚定。** `CRITERION`、`UNRESOLVED`、`REQUIRED_FIELDS`、
三条 `FIELD_DOMAIN`、`CONTAINS_NO_EXECUTION_AUTHORIZATION` **逐字不动**
（条件 (b) 要求 Sol 正面确认这一点）。

### 2.1 新增一个字段：锚点

```
CR1_REGISTRY_REPOSITORY_ANCHOR=the registry repository is the one reached by the
S4 cross-pin ruled in dec-registry-migration-2026-08-27: the framework
repository's ops/TRIAL_REGISTRY.md holds a tombstone bearing the marker
REGISTRY_MOVED_NOT_A_REGISTRY which names commit N1; N1 exists in the registry
repository, carries ops/TRIAL_REGISTRY.md, and its own message names the
framework repository's pre-migration HEAD O0. A FILESYSTEM PATH IS NOT THE
ANCHOR — a path is machine-specific and moves without leaving a record. The
commit pair is the anchor, and it is recomputable from persistent bytes alone
```

**为什么锚点是 commit 对而不是路径**：路径是机器局部的，换台机器就不成立，
且移动它不留任何记录。commit 对是内容寻址的，冷读者能只凭字节复算它。
墓碑与 N1 的 message 里都写着路径，那是**便利**，不是判据。

### 2.2 `PREIMAGE`（改仓锚定，其余逐字不动）

```
CR1_REGISTRY_INTACT_PREIMAGE=the complete on-disk bytes of
ops/TRIAL_REGISTRY.md IN THE REGISTRY REPOSITORY (CR1_REGISTRY_REPOSITORY_
ANCHOR), read once, immediately BEFORE the CR1 row is appended; no
normalization, no encoding change, no line-ending rewrite; the value is
therefore never part of its own preimage. A file at that relative path in any
OTHER repository is NOT the registry: the framework repository's copy is a
tombstone, and a tombstone parses cleanly to zero event rows, so reading it
yields an INTACT-looking preimage of an empty registry
```

**加的最后一句不是修辞。** 它是 S7 当天实测到的失败模式的名字。

### 2.3 `COLD_RECOMPUTE`（改仓锚定，其余逐字不动）

```
CR1_REGISTRY_INTACT_COLD_RECOMPUTE=the preimage is recoverable from git
history of ops/TRIAL_REGISTRY.md at the commit preceding this row, and the
witness file is append-only, so a cold reader can recompute both sides. WHICH
history: the registry repository's for rows appended at or after N1, and the
framework repository's for rows appended before it — the migration rewrote no
history, so each half remains readable where it was written, and N1 is the
boundary between them. Both repositories are reachable from either one by the
S4 cross-pin (CR1_REGISTRY_REPOSITORY_ANCHOR)
```

### 2.4 未改动的字段，逐字复述以便 Sol 逐条比对

```
CR1_REQUIRED_FIELDS=supplement_id|dangling_event|incident_id|crash_evidence_summary|recovery_authorization_doc|registry_intact_verification|registry_witness_ref
CR1_FIELD_DOMAIN_dangling_event=P3
CR1_FIELD_DOMAIN_registry_intact_verification=SHA256_HEX64_OF_REGISTRY_BYTES_AS_READ_BEFORE_THIS_ROW_IS_APPENDED
CR1_FIELD_DOMAIN_registry_witness_ref=THE_LATEST_WITNESS_RECORD_THE_READ_WAS_CHECKED_AGAINST
CR1_REGISTRY_INTACT_CRITERION=the read is INTACT iff it is a superset of the witness named by registry_witness_ref: its event count is not lower and the witnessed last row is still present. A digest alone proves only that bytes were hashed; the witness is what it is hashed AGAINST
CR1_REGISTRY_INTACT_UNRESOLVED=TOCTOU between the read and the append is NOT closed by this grammar; it is the same critical-section gap the D-3 review named, and no lease exists
CR1_GRAMMAR_CONTAINS_NO_EXECUTION_AUTHORIZATION=YES
```

**`UNRESOLVED` 特别说明**：TOCTOU 仍然**没有**被关掉，本次修订**没有**碰它。
迁移不缩小也不扩大那个缝。把它写在这里，是因为条件 (b) 要求 Sol 正面确认
「修订未实质削弱原批准」，而一条被悄悄改窄的已知缺陷正是那种确认要挡的东西。

---

## 3. 条件 (a)：作废 `c251335f…`

```
VOIDED_APPROVAL_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
VOIDING_REASON=所指重绑定，判据未变
```

**逐字展开**：`c251335f…` 批准时，`ops/TRIAL_REGISTRY.md` 与「git history」
在框架仓内各指向唯一一个东西。迁移之后两者各有两个候选。
**该批准的判据一个字都没变** —— 超集判据、前像读取口径、TOCTOU 披露全部原样。
变的只是那些句子指向谁。这与 R3 弧线「每版作废前版哈希」的既有惯例同形。

---

## 4. 条件 (b)：请 fresh Sol 正面确认的三件

```
PREIMAGE 读取口径   除仓锚定外逐字义不变？（一次读、追加之前、不规范化、值不在自己前像里）
CRITERION 超集判据  逐字未动？
UNRESOLVED TOCTOU   逐字未动，且未被悄悄改窄？
```

**并请他判一件本提案自己拿不准的**：§2.2 末尾那句关于墓碑的补充，
是**澄清**还是**新增判据**？我认为是澄清（它描述的是既有事实的后果，
不改变 INTACT 的判定条件），**但这个判断由我作出、对我有利，所以它需要独立复核**。

## 5. 条件 (c)：批准路径不变

```
§D.10.3 原路：id + sha256 + 精确 doc HEAD。不加新门类。
```

---

## 6. 本提案不做什么

不批准任何东西；不追加任何 CR1 行（冻结令在 force）；不重写任何历史；
不改 `CRITERION`／`UNRESOLVED`／必填字段／字段值域；
**不自行认定 §4 那个「澄清 vs 新判据」的问题** —— 那是送 Sol 的原因。
