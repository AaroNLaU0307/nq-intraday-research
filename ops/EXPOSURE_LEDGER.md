# EXPOSURE LEDGER — §10.1 合规承载件（ITSF-S0）

```
RECORD_TYPE=EXPOSURE_LEDGER_L6_CONFORMANT
HISTORICAL_ORIGINAL=EXPOSURE_LEDGER.md（仓库根，append-only，逐字未改）
CREATED=2026-08-24，依 Aaron 逐字指示「直接按你建议的做吧，能执行的全执行」
```

**为什么有两份。** 已批准的 §10.1 把行格式固定为六列
`| ts | scope | classification | granularity | artifact_or_pointer | note |`，
而 ITSF 的历史台账是**五列、位于仓库根**。历史台账是 append-only：
「rows never edited or reordered」。**重写它会违反它自己的纪律**，所以没有重写。

本件是**合规承载件**：逐行转录历史台账，权威仍在历史台账。两者行数与计数必须
恒等，由 `tests/test_exposure_ledger_migration.py` 机械守着。

**本件的 `note` 只放指针，不复述被指向内容。** 历史台账的某些行内嵌揭盲后
摘要（故两者均在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 隔离名单上）；转录时
把内容换成指针，是为了不让这份新文件成为第三个暴露面。

NORMALIZATION_RULE: CLASSIFICATION_COLUMN_IS_CANONICAL

classification 由历史行文本判定，规则与历史台账 header 块所声明的一致：

```
TARGET_METRIC  该行记录查看了预注册判定统计量或其派生值
AGGREGATE      该行记录只查看了聚合/摘要值，未及逐候选关系
NONE           该行记录零 outcome 值查看
UNKNOWN        该行文本不足以判定 —— fail-closed，绝不折算为 NONE
```

`数量`（researcher_exposure_count）与 classification **正交**：一行可以
`数量=0` 而 classification 为 `AGGREGATE`。三轴不得互推。

| ts | scope | classification | granularity | artifact_or_pointer | note |
|---|---|---|---|---|---|
| 2026-08-10 | S0 | NONE | structural bar load, no candidate relationship | EXPOSURE_LEDGER.md row 2 · ops/INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md | legacy 数量=0；零候选关系被查看、零 outcome 生成。交叉引用行 |
| 2026-08-14 | S0-T001 | NONE | blind close-out; results sealed and unread | EXPOSURE_LEDGER.md row 3 | legacy 数量=0；outcome_generated=YES 但未查看（盲式收口） |
| 2026-08-14 | S0-T001 | TARGET_METRIC | 1575 preregistered relationship cells, whole manifest, preregistered order | EXPOSURE_LEDGER.md row 4 | legacy 数量=1575；本项目全部 researcher exposure 的唯一来源 |
| 2026-08-14 | S0-T001 | NONE | completion marker for the same reveal | EXPOSURE_LEDGER.md row 5 | legacy 数量=0；与 REVEAL_STARTED 配对，不重复计数 |
| 2026-08-14 | S0-T001 | AGGREGATE | six interpretive corrections over the same already-revealed results | EXPOSURE_LEDGER.md row 6 · ops/S0_T001_RESULT_DECISION_ADDENDUM.md | legacy 数量=0；零新候选关系。内容见指针，不在此复述 |
| 2026-08-24 | S0-T001 | AGGREGATE | builder read the addendum summary embedded in the legacy ledger | EXPOSURE_LEDGER.md row 7 · ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md | legacy 数量=0；outcome_seen=YES，builder 自此非 outcome-blind。内容见指针 |

累计 researcher_exposure_count：1575，全部来自 2026-08-14 那一行
（其余各行贡献 0）。此数与历史台账逐字一致。
