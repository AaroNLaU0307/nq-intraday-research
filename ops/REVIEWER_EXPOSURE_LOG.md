# REVIEWER EXPOSURE LOG（复审席位暴露台账）

```
RECORD_TYPE=REVIEWER_EXPOSURE_LOG
CREATED=2026-08-26
APPEND_ONLY=YES —— 行只追加，永不编辑、永不重排
AUTHORITY=本件是**席位**暴露的记录，不是研究 exposure 记账
```

## 为什么另立一份，而不是记进 `ops/EXPOSURE_LEDGER.md`

Aaron 于 2026-08-26 授权把 2026-08-25 的复审席位暴露事件入账。照办时发现
**记进那份台账会出三重错**：

1. `ops/EXPOSURE_LEDGER.md` 是**合规承载件**，逐行转录仓库根的历史台账，
   权威在后者；`tests/test_exposure_ledger_migration.py` 机械守着两者**逐行
   恒等**。只追加承载件会立刻破坏该恒等。
2. 同一测试文件里 `test_exactly_one_row_carries_the_target_metric_exposure`
   要求 `REVEALED_TARGET_METRIC` **恰有一行**。再加一行会打破它。
3. 更要紧的是**第三条**：那份台账记的是**研究者对 S0 outcome 的暴露**——它消耗
   研究自由度，累计值 1575 是它的量纲。而本次事件是**一个复审席位读到了治理
   文档里的 verdict token**。**烧掉一个席位不消耗研究自由度。** 把两者记成同
   一轴，会让研究的 exposure 记账凭空多出一次「研究者暴露于目标统计量」。

所以本件另立。**L6「无账即 UNKNOWN，绝不为 NONE」的要求由本件满足**——事件有
了durable 记录，状态不再未知。

**是否另需在 `ops/EXPOSURE_LEDGER.md` 留一条只含指针的行**（指向本件、
classification 用不冲突的值），**归 Aaron**：那要动一份 append-only 的权威台账
与一条已批准的「恰一行」不变量，builder 不自行处置。

---

## 台账

| # | ts | seat | artifact_read | what_was_seen | classification | consequence | cause |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-25 | Codex GPT-5.6 Sol，fresh session（review N09-EXECUTION-PATH-A2） | `ops/MC_TO_STRATEGY_MASTER_PLAN.md`（在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 名单上） | verdict token ＋ exposure count（**席位自陈**；未读真实 Development 数据，未读目标绩效数值） | `REVEALED_TARGET_METRIC`（**席位自评，builder 未下调**） | 该会话不得再承担 outcome-blind Stage I | builder 未在复审提示词中给出 outcome-carrying 禁区清单 |

### 第 1 行的补充说明

- **分类沿用席位自评。** 按 §3.4B 的字面定义，「verdict token」属「预注册判定
  统计量的派生值」。builder 不下调他人对自身暴露的自陈。
- **本次未移动 `N_trials`**，也未改变研究 exposure 累计值。
- **成因是结构性的，不是这一次的偶然**：`ops/MC_TO_STRATEGY_MASTER_PLAN.md`
  既是 outcome-carrying，又是本项目的**恢复锚**（其 §1「恢复序」是任何会话定位
  状态的标准第一站）。**任何 outcome-blind 复审者做一次完全正常的状态定位就会
  踩中。** 处置见
  `ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md` §1.3（拆锚 vs 禁区清单，
  归 Aaron）。
- **已落地的机械缓解**：
  `tests/test_artifacts_under_review_are_frozen.py::test_a_live_prompt_names_the_outcome_carrying_artifacts_as_off_limits`
  强制任何活跃 review 的提示词点名登记表与恢复锚。
- **Review Packet v1 的 `PULL_PROTOCOL` 是更强的结构性缓解**：复审者**列出**
  它需要的路径，由工作会话提供逐字节内容——它不自己导航，因而不会走到禁区。
  R1 那轮用的是散文提示词，没有这层保护。
