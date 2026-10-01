# N09 执行路径设计 R2 —— fresh Sol 复审结果 = HOLD

```
RECORD_TYPE=REVIEW_OUTCOME_RECORD
REVIEW_ID=rv-3651f9fe0b68-da56aecb6991
SUBJECT=ops/N09_EXECUTION_PATH_DESIGN_R2.md（设计，未实现）
SEAT=Codex GPT-5.6 Sol，fresh top-level session，ROLE=FORMAL_REVIEWER_SEAT
VERDICT=HOLD（4 material findings：3 High ＋ 1 Medium）
L6_GATE_EFFECT=NONE —— 不释放任何 transition
OUTCOME_EXPOSED=TARGET_METRIC（席位自评；见 ops/REVIEWER_EXPOSURE_LOG.md 第 2 行）
RECORDED=2026-08-27，builder seat
```

## 为什么这份记录到 2026-08-27 才存在 —— 一条 builder 自纠

**这轮裁定此前只活在聊天里。** `ops/NEXT_HANDOFF.md` 的复审表把它的记录指向
`ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md`，**而那份装的是 08-25 那轮
非正式 REDESIGN 的六条修改，不是本轮的四条 finding**。指错了。

发现方式：Aaron 于 2026-08-27 批「可以做」后，builder 去读那份被引的记录准备开工，
发现它根本不含所述内容。

**这违反本项目自己的常设规则**——「chat 里的字节永远不是真相源」。一份复审的裁定
若只存在于聊天，下一个会话就只能靠转述去建东西，而转述已经错了一次（见 §3）。

本记录逐字转录裁定原文，并附 builder 的逐条复现。

---

## 1. 裁定原文（逐字，英文原文不译）

> **VERDICT: HOLD**
>
> **STRONGEST_OBJECTION**: R2 requires `C_BUILD_2` to run during staging and
> `C_BUILD_3` after an archive attempt, while also requiring every C_BUILD
> rejection to prove there were no file writes or archive attempts. Those
> requirements cannot simultaneously be implemented or tested. See R2 line 33
> and R2 line 80. The existing staging mechanism necessarily writes `.partial`
> bytes before it can verify them (`supplement_runner.py:846`).
>
> **Material findings:**
>
> * **High** — Archive failures are not consistently routed. R2 describes gates
>   as classifying production exceptions into F1/F2, but the ratified state
>   machine requires an ordinary post-seal archive failure to emit A1, not F2.
>   Existing code correctly returns A1 (`supplement_runner.py:791`); the
>   contract separately defines A1 and F2 (`supplement_contract.py:238`).
>   R2 needs an explicit A1/F2/indeterminate routing matrix.
> * **High** — Essential authorization semantics remain undefined. R2 leaves the
>   P3/failure-event writer undecided and proposes checking a directory-creation
>   "token" without defining its source, actor, exact text, commit/path binding,
>   or lifetime (R2 §6–7, line 148). Current ratification explicitly says
>   directory creation and registry appends are unauthorized
>   (`ND1_PROFILE_RATIFICATION.md:73`). **A default-refuse scaffold could be
>   built, but not the claimed execution path without Aaron's decisions or an
>   explicit narrower build scope.**
> * **High** — The allowed `day_rows` call path is insufficiently pinned.
>   "Reuse the production S0 universe/data assembly path" could reasonably mean
>   reusing `RealChain._ensure`, which invokes `build_s0_dataset`
>   (`scripts/s0_real_run.py:2650`). That function computes outcome labels and
>   Y6 deciles (`src/itsf/s0/dataset.py:215`), contrary to the supplement's
>   structural-only boundary. R2 must name the exact allowed loader →
>   `build_universe` → vol/event mapping path and explicitly prohibit
>   `build_s0_dataset`, `compute_day`, label, Oracle, and study construction.
> * **Medium** — The precheck evidence lifecycle is incomplete. R2 requires the
>   recomputed bundle table to persist as run evidence, but does not define its
>   canonical serialization, destination, sealing/inventory coverage, or what
>   happens if persistence fails around P3. That leaves the builder to invent
>   evidence-critical behavior.
>
> **Minimum unblock conditions:**
>
> 1. Rewrite the side-effect assertions separately for `C_BUILD_1`,
>    `C_BUILD_2`, and `C_BUILD_3`.
> 2. Freeze the A1/F2/indeterminate transition matrix.
> 3. Obtain Aaron's P3/failure-writer and directory-authorization decisions,
>    **or limit the authorized build explicitly to an always-refusing scaffold.**
> 4. Pin the structural-only `day_rows` call graph.
> 5. Define the bundle-precheck evidence format and persistence timing.

**席位自陈的验证局限（逐字）**：

> `qros`/pytest could not be executed because no Python interpreter is available
> on PATH. Builder-reported test results were therefore treated as unverified
> and were not needed to establish the contradictions above.
> No files were changed and no `PACKET_OUTCOME` was appended. This HOLD releases
> no transition.

**独立性（逐字要点）**：新顶层会话；未撰写／修复／实现任何被审工件；
**模型多样性在 R2 的 checkpoint、snapshot、`day_rows`、precheck 四组规则上缺失
——本复审在这些设计元素上明确非独立，不得作为它们的唯一独立认证**；
outcome 暴露 `TARGET_METRIC`，该会话不得再承担 outcome-blind Stage I。

---

## 2. builder 的逐条复现 —— **不采信，自己打开代码看**

`REPRODUCED` ＝ builder 独立打开被引位置、看到同一事实。

| # | finding | 结论 | 复现到的字节 |
|---|---|---|---|
| 0 | 最强反对：staging 必然先写 `.partial` | **REPRODUCED** | `resolve_partial` 的 docstring 首行即 "Stage `intended` into `<filename>.partial` and decide what happens." —— 写在决策之前 |
| 1 | archive 失败应发 A1 而非 F2 | **REPRODUCED** | `decide_after_seal` 的 docstring：「A local seal that succeeded while the archive failed does NOT become a P4 — it becomes A1, and P5 stays unreachable until A2.」；`supplement_contract.py` 中 P3 的 successors 为 `("P4", "A1", "F2")`——A1 与 F2 是**并列的不同后继** |
| 2 | 授权语义未定义 | **REPRODUCED** | `ops/ND1_PROFILE_RATIFICATION.md` §4 效力边界逐条为 `NO`：`SUPPLEMENT_EXECUTION_AUTHORIZED` / `REAL_DATA_READ_AUTHORIZED` / `DIRECTORY_CREATION_AUTHORIZED` / `WRITE_PROBE_AUTHORIZED` / `REGISTRY_EVENT_APPEND_AUTHORIZED` / `EXPOSURE_EVENT_APPEND_AUTHORIZED` / `MC_EXECUTION_AUTHORIZED` / `STRATEGY_BUILD_AUTHORIZED` |
| 3 | `day_rows` 调用路径未钉死 | **REPRODUCED** | `RealChain._ensure` 内三行 import：`DevelopmentSignalLoader`、`build_universe`、**`build_s0_dataset`**；而 `dataset.py` 的 `compute_day` 调 `labels_mod.d_open_from_ret_open30` —— 确实算 label |
| 4 | precheck 证据生命周期不完整（Medium） | **REPRODUCED**（读 R2 §该节，确无序列化格式、落点、封存覆盖、失败处置） | —— |

**四条全部成立。** 与 08-25 那轮一样，Sol 指出的都是 builder 设计里的真实空洞。

---

## 3. 一条比裁定本身更值得记的东西

**builder 此前对 High #2 的转述是错的。** `ops/NEXT_HANDOFF.md:55` 写的是：

> Sol 对 R2 的 High #2 认定：执行路径的可建范围取决于 D-3 怎么裁。**所以 R3 在
> ① 返回之前写不了**，现在能建的只有一个永远拒绝的骨架。

**原文并没有说 R3 写不了。** 原文说的是「the claimed execution path」建不了，
并**明确给出第二个分支**：`or limit the authorized build explicitly to an
always-refusing scaffold`。而五条最小解阻条件里：

```
条件 1  拆 C_BUILD_1/2/3 的副作用断言       builder 的活，不需要 Aaron
条件 2  冻结 A1/F2/indeterminate 转移矩阵    builder 的活，不需要 Aaron
条件 3  Aaron 的两项裁定  或  限定为拒绝骨架  ← 自带 builder 可走的分支
条件 4  钉死 structural-only 调用图          builder 的活，不需要 Aaron
条件 5  定义 precheck 证据格式与落盘时机      builder 的活，不需要 Aaron
```

**五条里四条是 builder 的活。** 转述把一条「范围受限」读成了「整件事被阻断」，
于是一件本可推进的工作被自己挂了一天。

这与本轮的另外两次错是**同一个毛病的三种形态**：转述代替原文、指错记录、
把 chat 当真相源。**修法不是提醒自己小心，是让裁定必须落盘**——本记录即是。

`ops/NEXT_HANDOFF.md` 的对应两处已改正，指向本记录。
