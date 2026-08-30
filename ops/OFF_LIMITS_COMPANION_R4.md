＃ 禁区清单 · R4 复审随包件

```ini
REVIEW_ID=r4-cr1-anchoring
COMPANION_OF=ops/PROMPT_R4_CR1_ANCHORING_SOL.md
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

## 本轮的特殊许可 —— **registry 仓可读**

```
ALLOWED   C:\Users\Aaron\quant-data\itsf-registry\ 全仓（含 git 历史）
ALLOWED   C:\Users\Aaron\quant-data\registry-witness\itsf\ 见证文件
```

**理由**：R4 的判据就是「冷读者能否只凭持久字节完成跨仓解析」。
不给你读那两处，你无法独立复核证伪器，只能采信我的话 ——
而采信我的话正是本次复审要避免的东西。

**registry 不是 outcome-carrying 件**：它是治理事件链，
不含任何目标绩效数值。若你在里面读到任何看起来像绩效的东西，**那是事故，请立即申报**。

## 禁止的检索动作 —— **由你亲自发起的**

```
框架仓根范围的 grep / rglob / find
ops/ 全目录枚举
```

## 跑治理测试不算违例

下列测试**内部**枚举 `ops/`。**跑它们是被明确允许的**：

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

## 席位

```
SEAT_STATUS 必须报 BLIND
FORBIDDEN_PATHS_OPENED 必须报 NONE，若非 NONE 则逐条列出并立即停
SOURCE_WRITES 必须报 NONE —— 只读复审
PERSISTED_SEARCH_OUTPUT 必须报 NONE
REGISTRY_REPO_READ 请报 YES/NO —— 本轮许可，但仍要记进席位轴台账
```

进程内变异（在内存里改、跑、不落盘）**不算** `SOURCE_WRITES`，是被鼓励的做法。
