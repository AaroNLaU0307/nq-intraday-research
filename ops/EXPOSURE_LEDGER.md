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
恒等**至历史前缀（首七行）**；自 2026-09-07（OD-CF-4，DEC-0004）起仓根台账冻结为历史，研究轴新行只追加于本件。前缀恒等与只增不减由 `tests/test_exposure_ledger_migration.py` 机械守着。

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
| 2026-09-07 | HISTORICAL_CUMULATIVE | NO_OUTCOME | builder read 3 DAG table rows (N10, N11, N13) extracted mechanically; 0 headed sections matched; 0 lines redacted by the six outcome patterns | ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md (OFF-LIMITS) §N10/N11/N13 rows and headed sections only; extract scanned with the six outcome patterns before reading; ops/DECISIONS.md DEC-0005 | 数量=0；DEC-0005（OD-CF-5 甲）授权的有界读取；未见 verdict、累计计数或任何揭盲值；builder 自 2026-08-24 起本已非 outcome-blind（row 7） |
累计 researcher_exposure_count：1575，全部来自 2026-08-14 那一行
（其余各行贡献 0）。此数与历史台账逐字一致。
| 2026-09-07 | HISTORICAL_CUMULATIVE | NO_OUTCOME | builder bounded read for **N11 only**: 9 lines mentioning N11 / GridReplayAuthority / KReplayEvidence extracted mechanically; **0 lines redacted** by the six outcome patterns. Disclosed honestly: an earlier `grep --include=*.md .` reached the same file and surfaced 4 of those same 9 lines BEFORE the bounded extractor was used; those 4 were re-checked against the six patterns and match none | `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md` (OFF-LIMITS) — only lines naming N11 or its two components; every extracted line scanned with `tests/test_review_artifacts_are_outcome_clean.OUTCOME_RESTATEMENTS` before display; `ops/DECISIONS.md` DEC-0005 | 数量=0；DEC-0005（OD-CF-5 甲）授权范围内的有界读取（N10/N11/N13 定义）；未见 verdict、累计计数或任何揭盲值；builder 自 2026-08-24 起本已非 outcome-blind（row 7）。本次读取用于判定 N11 契约，未消耗任何研究自由度 |
| 2026-09-08 | HISTORICAL_CUMULATIVE | NO_OUTCOME | builder bounded read for the **N11 DESIGN CONTRACT**, authorized by Aaron this session: 215/988 lines of the master plan, 175/769 of the DR5 build packet, 155/505 of the ND2/ND3 decision packet (key-matching lines plus key-headed sections), then a second pass over the ratified M6-M10 rulings (60 lines) and the CANNOT_DECIDE appendix (6 lines). **3 lines redacted** by the six outcome patterns and never displayed (1 `revealed verdict` in the plan, 2 inside the M10 ruling). The `S0_T001_RESULT_*` files were NOT opened — they are the outcome material itself | `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`, `MC_DR5_BUILD_PACKET.md`, `DECISION_PACKET_ND2_ND3.md`, `RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md` (all OFF-LIMITS) — scoped to N11 / GridReplayAuthority / KReplayEvidence / GRID->K wiring / rule (a)-(d) / replay identity / the N11 closure condition; every extracted line scanned with `tests/test_review_artifacts_are_outcome_clean.OUTCOME_RESTATEMENTS` BEFORE display; `ops/DECISIONS.md` DEC-N11-READ-1 | 数量=0；本次为设计契约读取，未见 verdict、累计计数或任何揭盲值（3 行匹配者已机械遮蔽）；M1-M5 的 feasibility 阈值内容**未提取**（不在授权范围）；builder 自 2026-08-24 起本已非 outcome-blind（row 7）。未消耗任何研究自由度 |
| 2026-09-08 | HISTORICAL_CUMULATIVE | NO_OUTCOME | builder bounded read for the **B-27 K-ENUMERATION AUTHORITY LOOKUP** — one question only: does any authoritative text define how the K inner draws are enumerated relative to the MC phase paths. Extracted mechanically: lines naming N13 (±2) plus lines carrying a K-draw term AND a phase/enumeration term TOGETHER, across the master plan, the DR5 build packet, the ND2/ND3 decision packet and the ratified ruling proposal. 94 lines shown, **2 redacted** by the six outcome patterns and never displayed (1 addendum feasibility assertion, 1 revealed verdict inside the M10 ruling). The `S0_T001_RESULT_*` files were NOT opened | `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`, `MC_DR5_BUILD_PACKET.md`, `DECISION_PACKET_ND2_ND3.md`, `RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md` (all OFF-LIMITS); every extracted line scanned with `tests/test_review_artifacts_are_outcome_clean.OUTCOME_RESTATEMENTS` BEFORE display; access path `ops/DECISIONS.md` DEC-0005 (OD-CF-5, which names N13 explicitly) | 数量=0；约束于一个语义问题的授权读取（DEC-0005 已具名 N13）；未见 verdict、累计计数或任何揭盘值（2 行匹配者已机抰遮蔽）；M1-M5 阀值内容未提取；本次读取未消耗任何研究自由度，未作任何实现 |
| 2026-09-10 | HISTORICAL_CUMULATIVE | NO_OUTCOME | builder bounded read for the **N14 NODE CONTRACT**, authorized by Aaron this session (DEC-N14-READ-1). Located first from metadata alone (heading index + line positions of the 4 `N14` mentions; no bodies displayed), then read as small contiguous regions: the Canonical DAG block carrying the N14 row and its neighbours, the DAG column header, section 6's N14->N15 transition text, section 15.12's one mention, the two lines pairing a review term with an exact-tree/HEAD term, and section 10's ledger rule plus section 16's statement of what remains authoritative. **~75 of 988 lines displayed; 0 lines redacted** -- the six outcome patterns matched nothing in what was read, which is not a claim that the rest of the file is clean. **Disclosed honestly:** the DAG is a table, so reading N13/N14/N15/N16 in it meant reading the whole `N-PLAN...N19` block (lines 82-107) -- every other node's row was seen, all structural, none matching a pattern; and section 10's 6-line window included 2 unrelated node-status rows (N-PLAN, N02). The `S0_T001_RESULT_*` files were NOT opened; section 5's undecided-decision list, section 7's reveal order, and sections 11-15's recovery anchors were NOT read beyond their headings | `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md` (OFF-LIMITS) -- lines 78-110, 221-240, 272-277, 933-937, 967-972, plus lines 91 and 492; every extracted line scanned with `tests/test_review_artifacts_are_outcome_clean.OUTCOME_RESTATEMENTS` BEFORE display; `ops/DECISIONS.md` DEC-N14-READ-1 | 数量=0；本次为节点契约读取，未见 verdict、累计计数或任何揭盲值（0 行匹配六模式）；未开启任何结果件；未消耗任何研究自由度，未执行任何 MC，未追加任何 registry 行 |
