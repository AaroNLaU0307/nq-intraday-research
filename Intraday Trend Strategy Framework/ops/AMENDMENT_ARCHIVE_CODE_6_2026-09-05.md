＃ 修订提案 —— `ARCHIVE_CODES` 增加第六个成员

```ini
AMENDMENT_ID=ARCHIVE-CODE-6
STATUS=PROPOSED —— 未批准，未实现，代码行为一字未动
CANONICAL_SHA256=7c63b3f42456797e9602367c7fc1c11e59f88036ef1cef2d11b152425163c507
BY=Opus 5，builder seat，2026-09-05
BASIS=Aaron 2026-09-05 选「乙」：A1 ＋ 新增一个 archive_code，出口裁为 AX
```

**不占 R 编号。** 本仓的 `R<n>` 命名空间至少被三个系列同时使用
（ND1 修订 R3/R4、Fable 裁定 R1–R5、Sol 复审轮次 R3–R8）。
**我在 BD 编号上已经撞过一次**，这次把编号留给你。

---

## 0. 一件我在你做决定前**没有说清楚**的事

我告诉你「乙」的代价是「加第 6 个词，走一次修订手续」。**那不完整。**

枚举自己的注释写着（逐字）：

> 这五个码**不是发明的名字**：每一个都对应 `ArchiveReport` 的一个
> **结构上可区分的状态**，且 `classify_archive_report` 是产出它们的**唯一**分类器。

**而新码不满足这条**：报告说 `archive_ok`，缺陷由 C_BUILD_3 的重算发现。
**所以修订同时要改这条自述不变量**，否则枚举会对自己断言一句假话。

**这不改变我的推荐**（判 F2 仍然会重建那个已被测试执行出来的 Router 矛盾），
**但「乙」比我告诉你的贵一点，你应该在批准前知道。**

## 1. 待批准的 canonical 块

**下面这一段就是待批准的产物本身。** 它由 `scripts/archive_code_6_block_builder.py`
生成，不是手抄；其 sha256 由同一份字节算出，并由
`tests/test_a_proposal_states_the_hash_of_its_own_block.py` 的同一约定复核。

```
BEGIN_ARCHIVE_CODE_6_CANONICAL_BLOCK
AMENDMENT_ID=ARCHIVE-CODE-6
AMENDS=supplement_contract.ARCHIVE_CODES  (ratified CLOSED enum,
       ND1 §D.3.2 P4 `ARCHIVE_CODE_ENUM`)
STATUS=PROPOSED  (not approved; nothing implemented)

# ---- 1. THE ENUM GAINS ONE MEMBER -------------------------------
ARCHIVE_CODES_BEFORE=inventory_unavailable, file_unreadable,
                     file_digest_mismatch, set_equality_refused,
                     set_equality_unreached
ARCHIVE_CODES_AFTER=inventory_unavailable, file_unreadable,
                    file_digest_mismatch, set_equality_refused,
                    set_equality_unreached, archived_bytes_deleted
NEW_MEMBER=archived_bytes_deleted

# ---- 2. THE ENUM'S DOCUMENTED INVARIANT WIDENS -------------------
# The five existing members carry a stated property: each maps to a
# STRUCTURALLY DISTINGUISHABLE state of an `ArchiveReport`, and
# `classify_archive_report` is the ONE classifier that produces them.
# The new member does NOT satisfy that: the report says `archive_ok`
# while the C_BUILD_3 checkpoint finds bytes archived by an EARLIER
# run are gone. Adding the member without saying so would leave the
# enum asserting something false about itself.
INVARIANT_BEFORE=every member is produced by classify_archive_report
                 from a structurally distinguishable ArchiveReport state
INVARIANT_AFTER=every member is produced EITHER by
                classify_archive_report from a structurally
                distinguishable ArchiveReport state, OR by the C_BUILD_3
                checkpoint from a recomputation the report does not
                cover. Each member names which of the two produces it.
PRODUCER_OF_NEW_MEMBER=C_BUILD_3 checkpoint (day_strata_pipeline
                       .run_c_build_3), NOT classify_archive_report

# ---- 3. THE NEW MEMBER'S ONLY EXIT IS AX -------------------------
# A1 has two exits: A2 (recovered) and AX (permanently failed -> F3).
# A2 asserts `source_and_archive_exact_inventory_match` and
# `per_file_sha256_match` for THIS run's copy, and says nothing about
# bytes an earlier run archived -- so it could declare recovery while
# the loss stands. That must be impossible, not merely discouraged.
A2_FORBIDDEN_FOR=archived_bytes_deleted
AX_IS_THE_ONLY_EXIT_FOR=archived_bytes_deleted
MECHANISM=a new mapping layered OVER the closed enum, in the manner
          `CHECKPOINT_OF` and `ROUTER_OF` already use. The transition
          planner keys on (from_short_id, outcome) and cannot see an
          archive_code today, so the constraint cannot live there
          without changing that signature.

# ---- 4. WHAT IS NOT AMENDED --------------------------------------
EVENTS_TABLE=unchanged
TRANSITION_PLANNER_EDGES=unchanged  (A1 -> AX already exists)
A2_REQUIRED_FIELDS=unchanged
ROUTER_OF=unchanged  (archive_policy_a stays with Router B)
GATE_TABLE=unchanged
VERIFICATION_FAILURE_CODES=unchanged

# ---- 5. WHAT APPROVING THIS DOES NOT AUTHORIZE -------------------
NOT_AUTHORIZED=real Development data read; supplement execution;
               live P2; directory creation under the governed roots;
               strategy build; any registry append
END_ARCHIVE_CODE_6_CANONICAL_BLOCK
```

`CANONICAL_SHA256=7c63b3f42456797e9602367c7fc1c11e59f88036ef1cef2d11b152425163c507`

**约定**：`BEGIN_` 与 `END_` 两行**之间**的行（不含这两行），LF 连接，
LF 结尾，UTF-8，逐行原样。

## 2. 批准之后要做的三件事（现在都没做）

```
一  supplement_contract.ARCHIVE_CODES  5 -> 6，并改写它的自述不变量注释
二  新增一层映射（不动封闭枚举本身，与 CHECKPOINT_OF / ROUTER_OF 同法）
    表达「该码的唯一出口是 AX，A2 对它不可达」
三  接线：新码从 C_BUILD_3 的 outcome 来，**不从 classify_archive_report 来**
    （那个分类器读 ArchiveReport 结构，而本缺陷不在报告里）
```

**第三件是唯一一处我还没有设计的东西。** 它不影响本次批准的内容，
但会在实现时单独提出来。

## 3. 本提案**不**做什么

```
不实现任何东西        代码仍然对该码具名拒绝
不动 EVENTS 表        不动转移规划器的边（A1 -> AX 本来就有）
不动 A2 的必填字段    不动 ROUTER_OF、GATE_TABLE
不授权                真实数据读取 / supplement 执行 / live P2 /
                      目录创建 / 策略 build / 任何登记追加
```

## 4. 仍然未决，明写

```
一  第三件（接线）未设计
二  席位指出：「A2 只校验本次拷贝」是**条件推论**，
    它没有读到 A2 的实际恢复校验器。本提案的第 3 节建立在该推论上——
    **若那份校验器实际上也覆盖历史归档，第 3 节的必要性会下降**
三  本提案未经任何独立席位看过
```

## 5. 批准语的形状（内容由你填）

> 批准 ARCHIVE-CODE-6 —— `ARCHIVE_CODES` 增加第六个成员 `archived_bytes_deleted`，
> 并按块中 §2 widening 该枚举的自述不变量、按 §3 裁定其唯一出口为 AX。
>
> `CANONICAL_SHA256=7c63b3f42456797e9602367c7fc1c11e59f88036ef1cef2d11b152425163c507`
> `EXACT_DOC_HEAD=<你批准当时的 40 位 HEAD>`
>
> 本批准不授权：真实 Development 数据读取、supplement 执行、live P2、
> 目录创建、策略 build、任何登记追加。每一次执行仍需我单独的精确授权语句。

**我不会代你拟这句话的内容。** 上面是形状。
