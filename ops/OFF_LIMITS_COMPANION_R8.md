＃ 禁区清单 · 第 8 轮随包件

```ini
REVIEW_ID=c-build-2-wording-r8
COMPANION_OF=ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md
```

**为什么单独一份**：Review Packet 不得携带禁区清单本身（D-2），
但清单必须随包同行。两份一起读。

## 永不打开

**权威在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。**
下面逐条列出**只是为了标记它们是禁区**，不是引导你去读：

```
OFF-LIMITS   ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
OFF-LIMITS   ops/outcome_quarantine/**   整个子树，不得打开、不得搜索、不得列目录
OFF-LIMITS   ops/EXPOSURE_LEDGER.md      研究轴台账
OFF-LIMITS   EXPOSURE_LEDGER.md          仓根那一份
OFF-LIMITS   ops/OUTCOME_CARRYING_ARTIFACTS.json 的 carries_outcome 下全部路径
```

## 禁止的检索动作 —— **由你亲自发起的**

```
仓根范围的 grep / rglob / find
ops/ 全目录枚举
```

## 更正：**跑治理测试不算违例**

第 7 轮你如实申报了一次检索边界违例 —— 你跑的治理测试内部用了 `ops/` glob，
间接打开了受审集之外的一份 ops 文件。

**成因是我，不是你。** 上一份随包件把「禁止 `ops/` 全目录枚举」写成了对**人**的约束，
而**我要求你跑的测试本身**就在做这件事。
**我要求席位遵守一条我自己的测试代码违反的边界。**

下列测试**内部**枚举 `ops/`。**跑它们是被明确允许的**，
它们的枚举不算你的检索动作：

```
tests/test_ops_index_is_complete.py
tests/test_a_prompts_range_claim_actually_holds.py
tests/test_a_prompts_measured_numbers_are_current.py
tests/test_cited_records_exist.py
tests/test_delivery_names_no_quarantined_path.py
tests/test_issued_deliveries_are_registered.py
tests/test_no_committed_walk_reaches_the_quarantine.py
tests/test_no_settled_question_is_sent_to_adjudication.py
tests/test_the_review_round_cap_is_respected.py
```

**边界约束的是你主动发起的检索，不是被审代码自己的行为。**
若某条测试的输出把一份禁区文件的**内容**带进你的上下文，那才是事件 ——
请申报，并按席位轴处理。

## 席位

```
SEAT_STATUS 必须报 BLIND
FORBIDDEN_PATHS_OPENED 必须报 NONE，若非 NONE 则逐条列出并立即停
SOURCE_WRITES 必须报 NONE —— 本轮为只读复审
PERSISTED_SEARCH_OUTPUT 必须报 NONE
```

进程内变异（在内存里改、跑、不落盘）**不算** `SOURCE_WRITES`，
第 6、7 轮均如此进行，是被鼓励的做法。
