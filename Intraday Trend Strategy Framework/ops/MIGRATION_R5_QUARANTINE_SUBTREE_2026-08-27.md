# R5 迁移执行记录 —— 隔离子树（A′：10 迁 2 留）

```
RECORD_TYPE=MIGRATION_EXECUTION
ITEM=R5（dec-remaining-2026-08-26），范围锁定 R1 的 A′
AUTHORIZED_BY=Fable 决裁席（`DELEGABLE=YES`）；Aaron 采纳（OD-2026-08-26-7）
EXECUTED=2026-08-27
PRE_MIGRATION_HEAD=e8243c9
OUTCOME_CLEAN=是
```

---

## 1. 做了什么

`git mv` **10 条**进 `ops/outcome_quarantine/`；**2 条留在原地**（两份
`EXPOSURE_LEDGER.md`，R1 裁 A′）。注册表 `path` 字段同 commit 随迁，
**条目数 12 → 12，不减**。

**R5 条件 1（逐文件 SHA-256 迁移前后相等）—— 10/10 全部相等**，逐条见提交 diff。

## 2. **三处与裁定条件的偏离，逐条公开**

### 2.1 条件 1 与条件 3 对「被迁文件之间的互相引用」直接冲突

条件 1 要求迁移**字节不变**；条件 3 要求改写引用。而 **7 份被迁文件互相引用**
（主计划 7 条、旧 ND2/ND3 裁决 3 条、决策包 2 条……）。改它们的引用就会改字节。

**取条件 1 优先**：被迁文件内容**一字未动**，它们内部指向兄弟隔离件的旧路径
**保持陈旧**。理由：它们全部在隔离名单上，**没有任何席位被允许打开它们**，
陈旧链接因此不指向任何人；而字节改变会毁掉「迁移是纯位移」这一可验证性质。

### 2.2 条件 3 与 append-only 保护对三份台账冲突

`ops/REVIEWER_EXPOSURE_LOG.md`（2 条）、两份 `EXPOSURE_LEDGER.md`（共 3 条）
都引用了被迁路径，但三者的**既有行不得改动**（R1 COLLATERAL 明列）。

**取 append-only 优先**：三份台账**一字未动**，其中的旧路径引用保持陈旧。

### 2.3 我给 Fable 的引用计数用了不完整的测法

我在 `ops/PREP_ITEM2_QUARANTINE_MIGRATION.md` 里报「32 条引用、生产代码零引用」，
用的是**字面全路径子串**检索。它**漏掉了构造式路径**（`REPO / "ops" / "NAME"`）。

重测后：漏掉的是 **`tests/test_governance_docs.py`** 一个文件、两条引用。
**生产代码零引用的结论不变**（重测后仍为 0），但**Fable 是基于一个不完整的测法
给出的裁定**，这一条必须记下。

## 3. 实际改写了哪些引用

| 类别 | 处理 |
|---|---|
| 注册表 `ops/OUTCOME_CARRYING_ARTIFACTS.json` | `path` 随迁（carve-out 覆盖） |
| **硬编码全路径的测试** 3 处 | `test_recovery_anchor_is_clean.py`、`test_governance_docs.py`×2 —— 已改 |
| **活件**（操作中的文档） | `README.md`、`NEXT_HANDOFF.md`、`RECOVERY_ANCHOR.md`、活跃提示与决策包 —— 已改 |
| 生产代码 | **零改动**（断言，非假设：重测后引用数 0） |
| 被迁文件自身 · 三份 append-only 台账 · 历史文档 | **未改**，理由见 §2.1／§2.2 |

## 4. 顺带发现的两件

### 4.1 索引守卫一直只 glob 顶层，13 份治理记录从未入索引

迁移逼着把 `test_ops_index_is_complete.py` 扩到 `ops/**/*.md`。扩完立刻照出
**13 份从来没进过索引的文件**——不是被排除，是守卫根本看不见它们：

```
ops/M4_TASKBOARD/        TASKBOARD.md · SA1_F10_CALENDAR.md ·
                         SA2_DEV_BOUNDARY.md · SA3_S0_INPUT_PREFLIGHT.md
ops/M5_RUNNER_TASKBOARD/ TASKBOARD.md · M5_T0_INTERFACE_AUDIT.md ·
                         SA4_S0_CORE.md · SA5_RUN_INFRA.md ·
                         SA6_AUDIT_FINDINGS.md · SA7_RUNNER_HARDENING.md ·
                         SA8_CORE_HARDENING.md · SA9_IR22_23_24.md
ops/M6_TASKBOARD/        M6_DESIGN.md
```

全部已入索引（`README.md` §8.6）。

### 4.2 我为 R5 条件 2 写的守卫，第一版有个致命缺陷

它按 **basename** 建索引，而 `EXPOSURE_LEDGER.md`（仓根）与
`ops/EXPOSURE_LEDGER.md` **basename 相同**——一条覆盖了另一条。变异测试实测：
落在被覆盖那条上的两种变异（掏空 `restates`、把 path 改到前缀之外）**都 PASS**。

**一个看不见 12 条里 2 条的守卫，比没有更糟**——它会对另外 10 条给出自信的报告。
改为按**全路径做双射**后，六条变异全红，**首尾两条都验过**。

## 5. **一处我造成的真损害：一份活跃复审的送审集被我弄失效**

`ops/OUTCOME_CARRYING_ARTIFACTS.json` **同时是两处**：

- 第 6 项第三次交付（`rv-2469d0cff91a-31fed17a5401`）**冻结送审集里的一件**；
- 本次迁移**必须改**的注册表。

迁移改了它 ⇒ **那份复审的送审集当场失效**，冻结守卫立刻打红并点名了它：

```
ops/OUTCOME_CARRYING_ARTIFACTS.json: sent 6bcafa9c… to fresh Sol（第三次交付），
now a61c125b…
```

**守卫做对了；错的是我。** 我在 `ops/NEXT_HANDOFF.md` 里写过「你不用等 Sol 返回，
这两件互不依赖」——**那句话是错的**，两件共用这一个文件。Fable 的 R5 条件没提到
这一层，我也没想到。

**后果**：若 Aaron 已把第三次交付发出，那个 Sol 会话的复核会 STOP。**必须重发。**

**已做**：登记表中该 review 的 11 条解除登记；第 6 项按新钉子重出（见
`ops/PROMPT_ITEM6_SOL_REVIEW.md` 的最新版本）。

**教训写成规矩**：**迁移／改注册表这类横切动作，与任何在外的复审互斥。**
下次要么先等复审返回，要么把注册表从送审集里排除并在提示里说明它可能变动。
