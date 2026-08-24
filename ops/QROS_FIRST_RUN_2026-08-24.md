# qros CLI 首次对 ITSF 运行 — 输出存档（2026-08-24）

```
# 探针用 lane=FULL / workflow_stage=C 试填；两者仍待 Aaron 声明
# 探针文件跑完即删，从未落在 repo root 作为 qros-state.yaml
```

## qros check
```
TABLE_SINGLE_SOURCE_MODE=ACTIVE (derived)   BOOTSTRAP_MODE=BOOTSTRAP (recorded binding)
BOOTSTRAP EVIDENCE RECORD (§7.5.6) — reported, never repaired, never written
  present=True  malformed=False
  bundle identity recorded=5008F5253E47F2196B5DA541038DB08C7B096C0C2D8F65FFD2507404F3637B5F
  bundle identity current =5008F5253E47F2196B5DA541038DB08C7B096C0C2D8F65FFD2507404F3637B5F
  every required identity matches and every required result passes (§7.5.6 rule 4)

PROJECT <--state>
  SEAL=VERIFIED — the preregistration bytes at 89e250592834 equal HEAD
  INPUT_FRESHNESS
    exposure_record    FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
    prereg             FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
    trial_accounting   FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
  REJECT  UNDECLARED_NORMALIZATION_RULE: ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
  TRIGGERS  matched=0  path-clear=0  unassessed=14
    TBL-TRIGGERS.R01       UNASSESSED   changes to sample splitting
    TBL-TRIGGERS.R02       UNASSESSED   leakage-sensitive code
    TBL-TRIGGERS.R03       UNASSESSED   transaction-cost / price-unit / execution-model changes
    TBL-TRIGGERS.R04       UNASSESSED   futures roll / expiry logic
    TBL-TRIGGERS.R05       UNASSESSED   multiple-testing framework changes
    TBL-TRIGGERS.R06       UNASSESSED   portfolio accounting
    TBL-TRIGGERS.R07       UNASSESSED   large cross-file architecture changes on evidence-critical paths
    TBL-TRIGGERS.R08       UNASSESSED   static prose in generated artifacts
    TBL-TRIGGERS.R09       UNASSESSED   promotion decision
    TBL-TRIGGERS.R10       UNASSESSED   `falsified` decision
    TBL-TRIGGERS.R11       UNASSESSED   unresolved builder/reviewer disagreement
    TBL-TRIGGERS.R12       UNASSESSED   a finding propagating to many downstream cards
    TBL-TRIGGERS.R13       UNASSESSED   flagship / public release
    TBL-TRIGGERS.R14       UNASSESSED   high-value final audit
    GAP: no canonical path map is configured, so every path trigger renders UNASSESSED. `PATH_CLEAR` and `UNASSESSED` never render as "no trigger".
  state-file legality, partition discipline and packet-record integrity: no rejection
```

## qros status
```
TABLE_SINGLE_SOURCE_MODE=ACTIVE (derived)   BOOTSTRAP_MODE=BOOTSTRAP (recorded binding)

PROJECT ITSF-S0
  LANE=FULL  STAGE=C  repo=C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework
  SEAL=VERIFIED — the preregistration bytes at 89e250592834 equal HEAD
  WORKTREE_BASIS  observation #1: 467 tracked paths compared against 1f1026abc127, worktree not clean
  INPUT_FRESHNESS
    exposure_record    FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
    prereg             FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
    trial_accounting   FRESH          row=TBL-FRESHNESS.R01    BASIS=HEAD
  OUTCOME_EXPOSURE=UNKNOWN  scope=CURRENT_REVIEW_SCOPE  EXPOSURE_CONFLICT=NO  (UNPARSABLE_OR_NO_RULE)
  REVIEW_SATISFACTION
    A2                    NOT_SATISFIED   (§5.5.6 Step 5 row 4)
        zero applicable candidates among 0 effective outcome(s) bound to this gate
    STAGE_I               NOT_SATISFIED   (§5.5.6 Step 5 row 4)
        zero applicable candidates among 0 effective outcome(s) bound to this gate
  TRANSITION_ELIGIBILITY
    A → A2   ELIGIBLE
    A2 → B   HOLD
        TBL-PRECONDITIONS.R01: REVIEW_SATISFACTION(A2)=NOT_SATISFIED — zero applicable candidates among 0 effective outcome(s) bound to this gate
    B → C    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
        TBL-PRECONDITIONS.R10: the worktree is clean [observation #1: 467 tracked paths compared against 1f1026abc127, worktree not clean]
    C → D    ELIGIBLE
    D → E    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    E → F    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    F → G    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    G → H    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    H → I    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    I → J    HOLD
        TBL-PRECONDITIONS.R04: REVIEW_SATISFACTION(STAGE_I)=NOT_SATISFIED — zero applicable candidates among 0 effective outcome(s) bound to this gate
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
        TBL-PRECONDITIONS.R10: the worktree is clean [observation #1: 467 tracked paths compared against 1f1026abc127, worktree not clean]
    J → K    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
    K → L    HOLD
        TBL-PRECONDITIONS.R08: OUTCOME_EXPOSURE=UNKNOWN (UNPARSABLE_OR_NO_RULE) — ledger header is 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注; ratified §10.1 fixes | ts | scope | classification | granularity | artifact_or_pointer | note |
  TRIGGERS  matched=0  path-clear=0  unassessed=14
    TBL-TRIGGERS.R01       UNASSESSED   changes to sample splitting
    TBL-TRIGGERS.R02       UNASSESSED   leakage-sensitive code
    TBL-TRIGGERS.R03       UNASSESSED   transaction-cost / price-unit / execution-model changes
    TBL-TRIGGERS.R04       UNASSESSED   futures roll / expiry logic
    TBL-TRIGGERS.R05       UNASSESSED   multiple-testing framework changes
    TBL-TRIGGERS.R06       UNASSESSED   portfolio accounting
    TBL-TRIGGERS.R07       UNASSESSED   large cross-file architecture changes on evidence-critical paths
    TBL-TRIGGERS.R08       UNASSESSED   static prose in generated artifacts
    TBL-TRIGGERS.R09       UNASSESSED   promotion decision
    TBL-TRIGGERS.R10       UNASSESSED   `falsified` decision
    TBL-TRIGGERS.R11       UNASSESSED   unresolved builder/reviewer disagreement
    TBL-TRIGGERS.R12       UNASSESSED   a finding propagating to many downstream cards
    TBL-TRIGGERS.R13       UNASSESSED   flagship / public release
    TBL-TRIGGERS.R14       UNASSESSED   high-value final audit
    GAP: no canonical path map is configured, so every path trigger renders UNASSESSED. `PATH_CLEAR` and `UNASSESSED` never render as "no trigger".
  EXECUTOR_ESCALATION=NONE   (routing only, never a review requirement — §3.2)
  FLAGS  DEGRADED_REVIEWER=NO  OWNER_HOLD=NO  DORMANT=NO
  commits_since_declaration=0   (a labelled observation; it holds nothing — §2.3)

QUEUE
  ITSF-S0                  LANE=FULL         STAGE=C   eligible=2/12
K-STAGE PENDING
  none
CONFLICTS
  none detected
```
