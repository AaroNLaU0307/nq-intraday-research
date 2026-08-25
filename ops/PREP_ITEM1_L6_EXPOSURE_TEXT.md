# 第 1 项交付物 —— 全局 L6 exposure 句的逐字终稿

```
RECORD_TYPE=PREPARED_ARTIFACT
ITEM=1（dec-eight-open-2026-08-26）
STATUS=已备妥，**未落地**
RULED=Fable 5，2026-08-26，`DELEGATED=YES`；Aaron 已采纳（OD-2026-08-26-2）
NEEDS=Aaron 对全局 `C:\Users\Aaron\.claude\CLAUDE.md` 的**修订授权**
WHY_NOT_DONE=全局文件的写入需要一次单独的明示授权；「可以开始准备做」是准备，
             不是那次授权。builder 不代写全局文件。
OUTCOME_CLEAN=是
```

> **本件就是 Fable 条件 3 要的东西**：「决策记录记录改写后句子的**逐字终稿**，
> 不是『已批准』三个字」。下面 §2 可直接整段替换。

---

## 1. 现状（`CLAUDE.md` 第 90 行，逐字）

```
  5. Exposure: append every exposure event to the project's `ops/EXPOSURE_LEDGER.md` (append-only; normalization rule in its header) even when `N_trials` does not move. No ledger/record ⇒ `UNKNOWN`, never `NONE`.
```

**问题**：这句只认一条轴。席位烧毁按字面也得记进
`ops/EXPOSURE_LEDGER.md`【OFF-LIMITS】，而那会凭空制造一次「研究者暴露于目标
统计量」——三条机械不变量已把这条路堵死（见 §3）。

## 2. 逐字终稿（整段替换第 90 行）

```
  5. Exposure — two axes, never merged. RESEARCH axis: append every researcher/statistical exposure event to the project's `ops/EXPOSURE_LEDGER.md` (append-only; normalization rule in its header) even when `N_trials` does not move. SEAT axis: append every reviewer-seat exposure event to the project's `ops/REVIEWER_EXPOSURE_LOG.md` (append-only); burning a seat consumes no research degrees of freedom and never enters the research ledger. Per axis: no ledger/record ⇒ that axis is `UNKNOWN`, never `NONE`. An event that cannot be assigned to an axis fails closed into the seat ledger marked `PENDING_AARON`. A project's `qros-state.yaml` `outcome_exposure` block must name both ledgers.
```

**改了什么、没改什么**：

- **保住**了 `append every … event`、`even when N_trials does not move`、
  `append-only`、`no record ⇒ UNKNOWN, never NONE` —— L6 的 fail-closed 内核
  一字未失，只是**逐轴**成立。
- **新增**了席位轴的对应义务（原句根本没有），以及不可归轴事件的 fail-closed
  去向。**这不是放宽，是把一句话拆成两句同样严的话。**
- Fable 条件 1 点名必须保住的两个子句都在：「任一轴无记录⇒该轴 UNKNOWN」与
  「不可归轴⇒席位台账＋`PENDING_AARON`」。

## 3. 条件 2 的核验证据（builder 已做）

Fable 条件 2：「两份台账字节、迁移恒等测试语义、恰一行不变量零改动；
`tests/test_exposure_discoverability.py` 保持绿且语义不动」。

```
ops/EXPOSURE_LEDGER.md     最后触碰 5d35741 (2026-08-24)   —— 本轮八项期间零改动
EXPOSURE_LEDGER.md         最后触碰 5d35741 (2026-08-24)   —— 同上
tests/test_exposure_ledger_migration.py  9 项含
    test_the_carrier_has_one_row_per_real_legacy_event   （逐行恒等）
    test_exactly_one_row_carries_the_target_metric_exposure （恰一行）
    test_both_files_state_the_same_total
tests/test_exposure_discoverability.py   4 项，语义未动
实测：两文件合计 9 passed / 0 failed
```

**两份台账自 2026-08-24 起字节未动**，本轮八项的全部工作没有触碰过它们。

## 4. 落地时怎么做（Aaron 授权后）

1. 用 §2 整段替换 `C:\Users\Aaron\.claude\CLAUDE.md` 第 90 行。
2. 在 `ops/OWNER_DECISIONS_2026-08-26.md` 追加一条，**把 §2 的句子逐字抄进去**
   （Fable 条件 3 要的是终稿，不是「已批准」）。
3. 重跑 `tests/test_exposure_ledger_migration.py` 与
   `tests/test_exposure_discoverability.py`，两者必须仍绿且语义未动。
4. **不动** `Quant trade\L6_RUNTIME_SPEC.md` 的已批准字节 —— 若要正式修那份
   doctrine，走它自己 ratification 记录的 append 通道，那是另一件事。

## 5. FALSIFIER（继承 Fable 原文）

新措辞生效后任一会话按文档化程序查询暴露状态仍答错——席位台账有行却自陈
`OUTCOME_EXPOSED=NONE`，或一次研究轴暴露因被读成「只记席位」而漏账
⇒ **措辞失败，回退未限缩读法并重裁。**
