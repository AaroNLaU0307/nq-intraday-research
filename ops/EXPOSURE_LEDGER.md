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

**词汇是 runtime 的，不是我发明的。** 第一版转录我用错了两处，记在这里：
`scope` 我填了研究名（`S0-T001`），但 §3.4A 的 scope 是**值算在哪个总体上**，
合法值只有 `HISTORICAL_CUMULATIVE` 与 `CURRENT_REVIEW_SCOPE`；
`classification` 我填了 `NONE/AGGREGATE/TARGET_METRIC`，那是 §1 的**贡献**轴，
不是 §3.4B 的 classification 名。两者「never conflated」。

§3.4B classification（列取字面值）及其对归一化值的贡献：

```
NO_OUTCOME               -> NONE          未生成也未查看 outcome
GENERATED_NOT_SEEN       -> NONE          已生成、封存未看（盲式收口正是此类）
REVEALED_AGGREGATE       -> AGGREGATE     只看了聚合/摘要值
REVEALED_TARGET_METRIC   -> TARGET_METRIC 看了预注册判定统计量或其派生值
```

`数量`（researcher_exposure_count）与 classification **正交**：一行可以
`数量=0` 而 classification 为 `REVEALED_AGGREGATE`。三轴不得互推。

| ts | scope | classification | granularity | artifact_or_pointer | note |
|---|---|---|---|---|---|
| 2026-08-10 | HISTORICAL_CUMULATIVE | NO_OUTCOME | structural bar load, no candidate relationship | EXPOSURE_LEDGER.md row 2 · ops/INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md | legacy 数量=0；零候选关系、零 outcome 生成 |
| 2026-08-14 | HISTORICAL_CUMULATIVE | GENERATED_NOT_SEEN | S0-T001 first real run, results sealed and unread | EXPOSURE_LEDGER.md row 3 | legacy 数量=0；outcome_generated=YES 而未查看 —— 这一行正是该 class 存在的理由 |
| 2026-08-14 | HISTORICAL_CUMULATIVE | REVEALED_TARGET_METRIC | 1575 preregistered relationship cells, whole manifest, preregistered order | EXPOSURE_LEDGER.md row 4 | legacy 数量=1575；本项目全部 researcher exposure 的唯一来源 |
| 2026-08-14 | HISTORICAL_CUMULATIVE | NO_OUTCOME | completion marker for the same reveal | EXPOSURE_LEDGER.md row 5 | legacy 数量=0；与 REVEAL_STARTED 配对，不重复计数 |
| 2026-08-14 | HISTORICAL_CUMULATIVE | REVEALED_AGGREGATE | six interpretive corrections over the same already-revealed results | EXPOSURE_LEDGER.md row 6 · ops/S0_T001_RESULT_DECISION_ADDENDUM.md | legacy 数量=0；零新候选关系。内容见指针，不在此复述 |
| 2026-08-24 | HISTORICAL_CUMULATIVE | REVEALED_AGGREGATE | builder read the addendum summary embedded in the legacy ledger | EXPOSURE_LEDGER.md row 7 · ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md | legacy 数量=0；outcome_seen=YES，builder 自此非 outcome-blind。内容见指针 |
累计 researcher_exposure_count：1575，全部来自 2026-08-14 那一行
（其余各行贡献 0）。此数与历史台账逐字一致。
