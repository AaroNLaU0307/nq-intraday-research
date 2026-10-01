# B0 — S0 FORMAL REPORT SOURCE-LINEAGE MATRIX

**Milestone**: M6.1.4 (prerequisite lane B0, READ-ONLY)
**Repo HEAD**: `1e188b54ace011bb4c2ab7356f775af6d32aab37`
**Tree state**: clean (`git status --porcelain` = 0 lines; `git diff | sha256` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, the empty-input digest)
**Status of this document**: DESIGN CONTRACT for the S1/S2/S3 implementation lanes of M6.1.4. It describes lineage as it stands at this HEAD. It proposes no algorithm and rules no open research question.

---

## 0. How to read this matrix

### 0.1 Scope

Every row is one **decision-bearing leaf** of the sealed formal payload (`S0_REPORT.json`) or of the sealed MC-handoff artifact set: a number, a date, a date list, or a flag that a reviewer or an MC consumer would rely on. Prose/disclosure strings are included **only** where the string is load-bearing at a gate (e.g. `estimator_status`, `regions.status`, `theoretical_oracle.note`), because those strings gate sealing.

Leaves that repeat across a frozen axis are written once with the axis in angle brackets. The frozen axes are:

| axis | values | cardinality |
|---|---|---|
| `<theta>` | `theta_0.5`, `theta_0.3` (`study.FROZEN_THETAS`) | 2 |
| `<eng>` | `E1`, `E2` (`study.ENGINES`) | 2 |
| `<scn>` | `Base`, `Conservative`, `Stress`, `Severe` | 4 |
| `<era>` | `counterfactual_micro_execution`, `actual_micro_available_era` | 2 |
| `<blk>` | `5`, `21` (`FROZEN_BLOCKS`) | 2 |
| `<seed>` | `7`, `13`, `31` (`contracts.RESEARCH_BOOTSTRAP_SEEDS`) | 3 |
| `<qr>` | 63 grid points, `gridmix.Q_GRID_MILLIS` x `R_GRID_MILLIS` | 63 |
| `<epoch>` | `2010-2013`, `2014-2017`, `2018-2021`, `outside_epochs` | 4 |
| `<year>` | data-dependent (2010..2021) | ~12 |

An axis-expanded row therefore stands for many physical values; the **lineage** is identical across the axis, which is what this matrix contracts on.

### 0.2 Atomic-source families (mandated taxonomy)

| code | family | concrete carrier at this HEAD | survives to the sealed set? |
|---|---|---|---|
| **AF1-DAY** | dataset/day/sample/label/NA atomic facts | `S0Dataset.records` (`DayRecord`: `trade_date`/`year`/`era`/`features`/`labels`/`direction_status`/`*_na_reasons`/`sidecar`), `ds.na_table` (`dataset.build_na_table`), `ds.funnel_counts` (`context.EligibilityFunnel`), `ds.f10_counts` / `ds.f10_raw_membership_counts`, `ds.label_anchor_availability`, IR-23 `labels.d_open` column | **NO** — lives only on `internal["dataset"]`, a live object dropped by `split_envelope`. Only *aggregates* are copied into `structural`. |
| **AF2-PATH** | frozen §10.1 `TradePathRecord` | built by `oracle.executable_run` -> `paths.build_record`; held at `study["records"][eng][scn]` = `internal["records"]` | **YES** — serialized by `report.record_to_formal_dict` to the 8 `MC_HANDOFF_<eng>_<scn>.jsonl` files. This is the only atomic family that reaches disk intact. |
| **AF3-BAR** | theoretical-oracle per-day evidence; raw 1-minute bars | `bars_by_date` (`RealChain._bars`, from `DevelopmentSignalLoader`), `StudyDayInput.pm_bars`, `or_high`/`or_low` from the OBS window; the theoretical oracle emits a **bare float** per day (`oracle.theoretical_oracle`) with no record object | **NO** — no record class exists; bars are process-local and never captured as evidence. |
| **AF4-COST** | cost & method/config identity | `CostScenarioParams` x 4 (`costs.build_scenarios(*config.spread_scalars)`), `StudyConfig`, `ResolvedS0Methods`, `spread_scalars` triple, `S0_PLATFORM_FEE_RT_USD`, `MNQ_POINT_VALUE_USD`/`MNQ_TICK_POINTS` | **PARTIAL** — only the `spread_scalars` triple is copied (`disclosures.method_conventions.spread_scalars_used`). The four `CostScenarioParams` objects (spread_points / slippage_ticks_per_side / adverse_slippage_ticks / friction_multiplier / platform_fee_rt_usd) never enter the payload. |
| **AF5-STRATA** | volatility/event strata, era/epoch/direction membership | `config.vol_axis_of(d)` (blocked: `_approved_injectables()` returns `None`), `config.regime_of(d)` (same), `event_of` from `r.features.is_event_day` + `_event_stratum`, `strata = {d: (year, regime, event)}` built inline in `build_full_study_result`, era from `dataset._era`, epoch from `stability.EPOCHS` | **NO** — the `strata` mapping and the `vol_axis` mapping are constructed as locals and discarded. Era/epoch/direction *are* re-derivable (era from the date + frozen `MICRO_ERA_BOUNDARY`; year from `date[:4]`; direction from AF2 `record.direction`). |
| **AF6-BOOT** | bootstrap inputs & RNG identity | series `[d_tp[d] for d in sorted(d_tp)]`; seeds `{7,13,31}` (`contracts.RESEARCH_BOOTSTRAP_SEEDS`); `stats.STATS_STREAM_TAG = 9001`; `stats.block_stream_key(block)`; `n_boot=10_000`; `ci_level=0.95`; `stats.PERCENTILE_METHOD` | **PARTIAL** — the seeds/tags are frozen constants (re-derivable), the series is only re-derivable *given a declared `tp_days`*, and the series itself is never digested or pinned. |
| **AF7-GRID** | grid per-seed selection ledger | `np.random.default_rng([master, gridmix.GRID_STREAM_TAG=9002, q_mil, r_mil])`; `tp_pools`/`fp_pools` (stratum key -> sorted date tuple); `tp_avail`/`fp_avail`; `allocate()` output; `_select()` draws | **PARTIAL** — `allocation_tp`/`allocation_fp` and the resulting `tp_dates`/`fp_dates` *are* in the payload; the **pools** (the preimage the RNG draws from) are not, so no replay is possible. |
| **AF8-GOV** | governance snapshot | `ops/TRIAL_REGISTRY.md` bytes, `parse_registry_events`, `find_authorization_event`, `guards.FROZEN_HASHES` (a hardcoded dict), `TRIAL_ID`, `ENGINEERING_SEED` | **YES** — `governance` section, plus `RealChain.authorization_snapshot()` written to `attempts/`. The only family with a genuinely external primary source. |

### 0.3 Verifier codes (what recomputation exists TODAY, and what it anchors on)

| code | verifier | anchors on |
|---|---|---|
| VF-1 | `report._check_series_block` — recomputes `n`/`sum_usd`/`mean_usd` from the block's own pair list; ghost-date check | **inside the checked subtree**: the block's own `daily_pnl_usd`, and `theta_unions` derived from the payload's own `day_universe` |
| VF-2 | `report._check_p1_le_p5` | the pair itself (ordering invariant only; never the estimator) |
| VF-3 | `report` day-universe rules: `n_tp == len(tp_days)`, no dup, TP/FP disjoint, cross-theta union equality, theta nesting hi ⊆ lo, empty-universe floor | the payload's own two lists; **no external truth** |
| VF-4 | `report` sizing rows: `len(rows) == day_universe.n_tp` | the payload's own `n_tp` |
| VF-5 | `report` stability conservation recompute: `sum(cell.n) == n_tp`, `loyo[y].n == n_tp - by_year[y].n` | the payload's own `n_tp` and its own `by_year` |
| VF-6 | `report` bootstrap: cross-seed `mean` equality, `quoted == per_seed[7]`, `n_boot == 10000`, `block_len == blk`, `lo <= hi`, `quoted_seed == 7` | **peer cells in the same subtree**; `ci_lo`/`ci_hi` are never recomputed |
| VF-7 | `report._check_feasibility_cell`: `n_tp_target` via `gridmix.floor_n_tp`, `n_fp_target` via `gridmix.n_fp_for`, `F_expected` via `gridmix.f_expected`, realized precision/recall and `n_tp_actual`/`n_fp_actual` from the seed entry's own date lists | the cell's own `n_tp_available`, the **payload's own** `frequency[<theta>].pooled.continuation_base_rate_p`, and the seed entry's own `tp_dates`/`fp_dates`. **No RNG replay.** |
| VF-8 | `report` A11: `per_table_total_na[t] == sum(structural.na_table.per_field[t][*].na)` | the payload's own `structural` section |
| VF-9 | `report` A9 records conservation: `counts[eng][scn].n_records == n_tp + n_fp` | the payload's own `day_universe` |
| VF-10 | `report.validate_sealed_files`: sha256 of actual bytes; line-count triple equality; per-line field set + leaf types; `engine`/`cost_scenario` == file identity; per-file `trade_date` uniqueness; per-file date set == universe; `sealed_files` completeness + `_ALLOWED_SELF_EXCLUDED` | **actual bytes** vs payload claims (a genuine external anchor for bytes); but the date **universe** is payload-derived, and in production the renderer passes `trade_date_universe=univ` explicitly, so the validator's own fallback derivation is never exercised |
| VF-11 | `report.reconcile_with_internal` (wired into `render_s0_report`): (a) stability buckets recomputed from `internal["study"][...]["d_tp"]` + `day_meta` from `internal["dataset"].records`; (b) oracle pooled series population+values vs the same `d_tp`; (c) manifest counts vs `len(records[eng][scn])`; (d) NA totals vs `internal["reported_total_na"]` | **producer aggregates** (`study[...]["d_tp"]`) and the live dataset object — **not** AF2 records. (c) is a **count-only** touch of AF2; no record VALUE is ever read. Explicitly out of scope: percentiles, LOYO, `vol_terciles`, `theoretical_oracle`, `sizing_outputs`, `frequency`, `bootstrap_ci`, `feasibility_grid`. |
| VF-12 | `handoff.formal_seal_admission` + `_validate_seed_manifest_content` — seeds REBUILT from `contracts.RESEARCH_BOOTSTRAP_SEEDS`, stream tags REBUILT from `stats.STATS_STREAM_TAG`/`gridmix.GRID_STREAM_TAG` | **module constants** (genuinely independent of the artifact) — the one place admission recomputes a value rather than a schema |
| VF-13 | `runinfra.check_na_conservation` (Stage D + restated in `_na_conservation_block`) | `na_reason_counts` and `reported_total_na`, **both derived from the same `ds.na_table` preimage** in `stage_c_result` |
| VF-14 | `s0_real_run._expected_governance()` | `ops/TRIAL_REGISTRY.md` bytes re-read + `guards.FROZEN_HASHES` module dict |
| VF-15 | `guards.verify_frozen_hashes()` (inside `assert_real_run_allowed`, Stage-A gate `real_run_allowed`) | **re-hashes the 7 frozen files on disk** — real, but not bound into the Stage-E seal |
| VF-16 | `structural_actuals_from(ds, universe)` + `runinfra.compare_preflight_assertions` (Stage B) | the **hash-locked** `S0_INPUT_PREFLIGHT.json` (`LOCKED["preflight_json"]`) — a genuine external anchor, but covering only the assertion families `funnel.*`, `f10.<final category>`, `feature.F1..F11.*`, `na_reason.*`, `anchor.*`, `label.*` |
| VF-0 | *(none)* | no recomputation of any kind exists for this leaf today |

### 0.4 `currently_reconstructible` semantics (used consistently below)

- **YES** — a pure deterministic reducer exists over atoms the chain provably holds at seal time (the sealed JSONL AF2 records, frozen module constants, or an independently re-derivable primary source such as the registry bytes), and no unruled definitional choice sits inside the reducer.
- **PARTIAL** — an authoritative atom exists in memory at compute time (AF1 dataset records / `study[...]["d_tp"]` / AF3 bars / AF4 scenario objects / AF5 strata locals) but is **not carried into any sealed evidence object**, so a post-seal auditor cannot re-derive the leaf; or the reducer needs exactly one un-captured input.
- **NO** — no authoritative atom exists anywhere in the chain, even at compute time, and none can be captured without a research ruling first.

### 0.5 `production_consumer` vocabulary

`renderer` (`render_s0_report` reads it to build files/manifest) · `seal` (`validate_sealed_files` / `sealed_files` integrity) · `MC` (named by MC_METHOD_SPEC §1/§3/§5 as an MC input) · `validator-only` (only `validate_formal_payload` touches it) · `reviewer` (human report reader — the contract's audience) · `none`.

---

## Table 1 — A1 `structural`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L001 | `structural.funnel_counts.L0_scheduled_trading_days` … `.L4_final_feature_construction_dates` (5) | AF1 — `context.EligibilityFunnel` date tuples (`scheduled`/`observed_rth`/`regular`/`structurally_eligible`/`final_dates`) | `EligibilityFunnel.counts()` (existing) | VF-16 (compared against locked `S0_INPUT_PREFLIGHT.json` at Stage B); `report` adds a monotonicity check L0>=L1>=…>=L4 | PARTIAL — counts have a locked external anchor, but the **date lists** behind them are never sealed, so an auditor cannot re-derive a single level | NONE | reviewer | PARTIAL |
| L002 | `structural.f10_counts.<CPI\|NFP\|FOMC\|none\|NA_multi_event>` | AF1 — `EventCalendar` + `S0Universe.f10_exclusive_counts()`; per-day `features.is_event_day` | `S0Universe.f10_exclusive_counts()` (existing) | VF-16 (`f10.<category>` is in the assertion set) | PARTIAL — count anchored externally; per-date membership never sealed | NONE (IR-12/13/18 already ruled) | reviewer | PARTIAL |
| L003 | `structural.f10_raw_membership_counts.<category>` | AF1 — `S0Universe.raw_category_membership_counts()` (IR-12 sidecar population) | `raw_category_membership_counts()` (existing) | **VF-0** — `structural_actuals_from` emits only `ds.f10_counts`; the raw membership family is **not** in `translate_preflight_assertions`' key set | NO — producer claim only; no verifier, no per-date evidence | NONE | reviewer | PARTIAL |
| L004 | `structural.na_table.population` | AF1 — `len(records)` | `dataset.build_na_table` (existing) | VF-0 at Stage E (implicitly consistent with L001 L4 only by construction) | PARTIAL | NONE | reviewer, VF-8 input | PARTIAL |
| L005 | `structural.na_table.per_field.features.<field>.na` / `.not_na` | AF1 — per-day `DayRecord.feature_na_reasons` bijection | `dataset.build_na_table` (existing) | VF-16 (`feature.<F>.constructible`/`.na`) | PARTIAL — externally anchored counts, no per-date evidence | NONE | reviewer, VF-8 | PARTIAL |
| L006 | `structural.na_table.per_field.features.<field>.reasons.<approved_reason>` | AF1 — `DayRecord.feature_na_reasons` values | `build_na_table` Counter (existing) | VF-16 (`na_reason.<F>.<reason>` after `translate_na_reason`) | PARTIAL | NONE (IR-15/19/20/22/24 ruled) | reviewer | PARTIAL |
| L007 | `structural.na_table.per_field.labels.<field>.na` / `.not_na` / `.reasons.*` | AF1 — `DayRecord.label_na_reasons` bijection (`_attribute_label_na`, IR-23) | `build_na_table` (existing) | **VF-0** — the preflight assertion set carries `label.<Y>.available/unavailable` (anchor availability) but **no label NA-by-reason family** | NO — producer claim only | NONE (IR-23 ruled) | reviewer, VF-8 | PARTIAL |
| L008 | `structural.na_table.direction.{directional, zero_direction_day_l82, direction_undeterminable_na}` | AF1 — `DayRecord.direction_status` (IR-24 Option B) | `build_na_table` Counter (existing) | VF-0 | PARTIAL — `d_open` sign is on AF2 for traded days only; the *undeterminable/zero* classes have no atom in the sealed set at all | NONE (IR-24 ruled) | reviewer | PARTIAL |
| L009 | `structural.na_table.diagnostics.opening_numerator_zero_ret_open30_undefined` | AF1 — `DayRecord.sidecar[DIAG_OPENING_NUMERATOR_ZERO]` | `build_na_table` (existing) | Stage-B `ir24_f8_divergence_empty` gate (blocking, requires `== 0`) | PARTIAL — gate is real but pre-seal; no per-date evidence sealed | NONE (IR-24) | Stage-B gate, reviewer | PARTIAL |
| L010 | `structural.na_table.totals_by_reason.<reason>` | AF1 — union of feature+label reason counters | `build_na_table` (existing) | VF-0 (the A11 recompute uses `per_field`, not this) | PARTIAL | NONE | reviewer | PARTIAL |
| L011 | `structural.na_table.checks.<5 flags>` | AF1 — arithmetic over the same counters | `build_na_table` (existing) | VF-0 — `validate_formal_payload` never inspects `checks`; a `False` here does not block sealing | NO — self-declared flag with no consumer | NONE | none | **DECISION_REQUIRED** (engineering: unconsumed conservation flag; same defect class as the pre-M6.1.2 `stability.conservation_ok`) |
| L012 | `structural.label_anchor_availability.<y_cont\|y1\|y2_de_pm\|y3_close_pos_pm\|y4_mfe\|y5_mae>.available_days` / `.unavailable_days` | AF1 — `dataset._label_anchor_availability` over `S0Universe.summaries` + `adr14` + `direction_status` | `_label_anchor_availability` (existing) | VF-16 (`label.<Y>.available/unavailable`) | PARTIAL — externally anchored count; per-date availability booleans never sealed | NONE (IR-23 dependency sets) | reviewer | PARTIAL |
| L013 | `structural.eras.<era>[]` (full date lists) | AF1 — `DayRecord.era`, itself `date < context.MICRO_ERA_BOUNDARY` | `dataset._eras` (existing) | VF-0 | **YES** — era is a pure function of `trade_date` against the frozen `MICRO_ERA_BOUNDARY = "2019-05-06"`; the date population is itself sealed here and in `groups.by_year` | NONE (frozen §6 L109-115) | reviewer, downstream by_era slicing | OK |
| L014 | `structural.groups.by_year.<year>[]` | AF1 — `DayRecord.year` = `trade_date[:4]` | `dataset._groups` (existing) | VF-0 | **YES** — pure function of the date list | NONE | reviewer | OK |
| L015 | `structural.groups.leave_one_year_out.<year>[]` | AF1 — complement of L014 | `dataset._groups` (existing) | VF-0 | **YES** — pure complement of L014 | NONE | reviewer | OK |
| L016 | `structural.groups.stability_epochs.<epoch>[]` | AF1 + AF5 — `dataset.STABILITY_EPOCHS` half-open string ranges | `dataset._groups` (existing) | VF-0 | **YES** from L014 — **but** see CR-4: this is one of **four** independent implementations of the epoch boundary in the tree, and it is the only half-open one | NONE (frozen §2) | reviewer | PARTIAL (consistency risk) |

*Note on L013–L016:* these are the only place the sealed payload carries the **complete structurally-eligible day population as dates**. Several downstream reconstructions below depend on that fact.

---

## Table 2 — A2 `oracle_daily`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L017 | `oracle_daily.<theta>.day_universe.theta` | AF4 — `study.FROZEN_THETAS` | literal copy (`build_study`) | `report` theta-axis equality against `_EXPECTED_THETA_KEYS` | YES — frozen constant | NONE (frozen §7 L133) | validator-only | OK |
| L018 | `oracle_daily.<theta>.day_universe.n_directional_tradeable` | AF1 — `study.is_direction_tradeable(r)` = `d_open ∈ {±1}` AND `y_cont is not None` | `len(tradeable_days)` in `build_study` | VF-0 | **NO** — `y_cont` exists on no sealed artifact; `d_open` exists on AF2 only for the *traded* subset | NONE (frozen §5 + App A) | reviewer, frequency denominator | PARTIAL |
| L019 | `oracle_daily.<theta>.day_universe.n_trade_constructible` | AF1 + AF3 — `_collect_day_inputs` usable set (needs entry/exit bar presence + finite OR levels) | `len(usable)` (existing) | VF-0 | PARTIAL — equals the distinct `trade_date` count of any sealed JSONL file, so it **is** cross-checkable against AF2 today; nothing does it | NONE | reviewer | PARTIAL |
| L020 | `oracle_daily.<theta>.day_universe.n_untradeable_disclosed` | AF1 + AF3 — `_collect_day_inputs` disclosure rows | `len(disclosure)` (existing) | VF-3 only via the `conservation` flags (which are themselves producer output) | PARTIAL | NONE | reviewer | PARTIAL |
| L021 | `oracle_daily.<theta>.day_universe.n_tp` / `.n_fp` | AF1 — `labels.y_cont` per day vs `theta` (`study._partition`, inclusive on TP side) | `len(tp_days)` / `len(fp_days)` | VF-3 (count == list length, from the payload's own lists) | **NO** — `y_cont` is nowhere in the sealed set. The TP/FP partition is a pure producer claim. | NONE (frozen App A / §7 L133) | renderer (`univ`), VF-4, VF-5, VF-9, reviewer, MC | PARTIAL |
| L022 | `oracle_daily.<theta>.day_universe.n_tp_labelled` / `.n_fp_labelled` | AF1 — `_partition(tradeable_days, theta)` before the constructibility filter | `len(tp_all)` / `len(fp_all)` | VF-0 | **NO** — same `y_cont` gap, and no date list is emitted for these | NONE | reviewer | PARTIAL |
| L023 | `oracle_daily.<theta>.day_universe.tp_days[]` / `.fp_days[]` | AF1 — `study._partition` over `labels.y_cont` | list comprehension in `build_study` | VF-3 (dup/disjoint/cross-theta union/theta nesting — all payload-internal) | **NO** — the single highest-leverage unreconstructible leaf in the whole report | NONE | renderer, seal (VF-10 universe), VF-1 ghost-date set, MC | PARTIAL |
| L024 | `oracle_daily.<theta>.day_universe.conservation.<4 flags>` | AF1 — count arithmetic in `build_study` | inline booleans (existing) | `report` requires each literally `True`; but the flags are computed by the same function that computed the counts | **NO** — a self-attested flag over unverifiable counts | NONE | validator-only | PARTIAL |
| L025 | `oracle_daily.<theta>.executable.<eng>.<scn>.pooled.n` | AF2 — one record per `tp_day` | `study._series_block` `len(pairs)` | VF-1 (recomputed from the block's own pairs); VF-11(b) compares the pair set against `study[...]["d_tp"]` — a **producer aggregate**, not AF2 | PARTIAL — recomputable from AF2 JSONL **given** L023 | NONE | reviewer | PARTIAL |
| L026 | `oracle_daily.<theta>.executable.<eng>.<scn>.pooled.daily_pnl_usd[[date, usd]]` | AF2 — `TradePathRecord.final_pnl_per_contract` keyed by `trade_date` | `[(d, pnl[d]) for d in tp_days]` (existing, `build_study`) | VF-1 (own subtree); VF-11(b) vs `d_tp` aggregate | PARTIAL — **values** are exactly `final_pnl_per_contract` on the sealed JSONL, so the value layer is AF2-derivable; the **date population** is not (L023) | DR-1 (every USD figure inherits the unruled spread reduction + IR-7 adverse vector) | reviewer, MC | **DECISION_REQUIRED** (DR-1) |
| L027 | `oracle_daily.<theta>.executable.<eng>.<scn>.pooled.sum_usd` / `.mean_usd` | AF2 (same as L026) | `_series_block` sum / sum-over-n | VF-1; VF-11(b) only compares the *series*, never the scalars | PARTIAL (same split as L026) | DR-1 | reviewer | **DECISION_REQUIRED** (DR-1) |
| L028 | `oracle_daily.<theta>.executable.<eng>.<scn>.pooled.min_usd` / `.max_usd` | AF2 | `min(vals)` / `max(vals)` | VF-1 recomputes only n/sum/mean — **min/max are leaf-typed but never recomputed** (blind-audit D3 class) | PARTIAL | DR-1 | reviewer | PARTIAL |
| L029 | `oracle_daily.<theta>.executable.<eng>.<scn>.pooled.worst_day_pnl_percentiles.P1` / `.P5` | AF2 + AF4 — the D_TP value multiset + an estimator choice | `study._worst_day_percentiles` -> `np.percentile(..., method="linear")` | VF-2 (P1<=P5 ordering only). VF-11 **deliberately excludes** percentiles (`_recompute_cell_stats` docstring) | PARTIAL — values derivable from AF2 given L023, **but the estimator is unapproved** | **DR-8 (DR-M6-H)** | reviewer | **DECISION_REQUIRED** (DR-8) |
| L030 | `oracle_daily.<theta>.executable.<eng>.<scn>.by_era.<era>.<7 fields>` | AF2 + AF1 `era` (= pure function of the date, L013) | `study._by_era_and_pooled` filtering by `era_of[d]` | VF-1 per era block | PARTIAL — era slicing itself is YES; the underlying series inherits L026 | DR-1; DR-8 for the percentile fields | reviewer | **DECISION_REQUIRED** |
| L031 | `oracle_daily.<theta>.executable.<eng>.<scn>.worst_day_report.frozen_mandatory` | AF4 — `engine == "E2"` | literal (`build_study`) | VF-0 (allowed-key check only) | YES — pure function of the axis key | NONE (frozen §7 table) | reviewer | OK |
| L032 | `oracle_daily.<theta>.executable.<eng>.<scn>.worst_day_report.percentile_estimator` (string) | AF4 — `study.PERCENTILE_METHOD` | f-string (existing) | VF-0 — **never cross-asserted against `e2_worst_days.estimator_status`** (packet P-6 / blind-audit G1-G2) | PARTIAL — the constant exists, the binding does not | DR-8 | reviewer | **DECISION_REQUIRED** (DR-8) |
| L033 | `oracle_daily.<theta>.executable.<eng>.<scn>.worst_day_report.pooled.P1/.P5` and `.by_era.<era>.P1/.P5` | AF2 (same multiset as L029) | copies of `block[...]["worst_day_pnl_percentiles"]` | VF-2 | PARTIAL — an exact duplicate of L029/L030 values, **never cross-checked against them** (CR-6) | DR-8 | reviewer | **DECISION_REQUIRED** (DR-8) |

---

## Table 3 — A3 `theoretical_oracle`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L034 | `theoretical_oracle.<theta>.scenario` | AF4 — `study.BASE_SCENARIO_NAME` | literal | `report` requires `== "Base"` | YES — frozen constant | NONE (frozen §7) | validator-only | OK |
| L035 | `theoretical_oracle.<theta>.note` (string) | — | literal in `build_study` | `report` requires non-blank str (M6.1.3 A52 fix) | YES | NONE | reviewer | OK |
| L036 | `theoretical_oracle.<theta>.pooled.daily_usd[[date, usd]]` | **AF3** — `oracle.theoretical_oracle(pm_bars, d_open, base_scn)`: entry at the 10:00 bar open, exit at the most favourable in-window price (long: `max(high)`, short: `min(low)`), minus Base costs, fee once | `theoretical_usd = {d: float(oracle.theoretical_oracle(...))}` then `[(d, theoretical_usd[d]) for d in tp_days]` | **VF-0** — VF-1 recomputes n/sum/mean **from this very list**; VF-11 has no `theoretical_oracle` branch at all (packet blind-audit G4) | **PARTIAL** — the true atom is 1-minute bar data (`StudyDayInput.pm_bars`); no record object is produced and the bars are process-local. Post-seal this leaf is **unfalsifiable**. Needs **EV-2**. | DR-1 (Base cost identity) | reviewer | PARTIAL |
| L037 | `theoretical_oracle.<theta>.pooled.n` / `.sum_usd` / `.mean_usd` | AF3 (via L036) | `_series_block` | VF-1 (recomputed **from L036 itself** — the textbook RC-1 anchor defect) | PARTIAL — inherits L036 | DR-1 | reviewer | PARTIAL |
| L038 | `theoretical_oracle.<theta>.pooled.min_usd` / `.max_usd` | AF3 | `min`/`max` | VF-0 (leaf-typed only) | PARTIAL | DR-1 | reviewer | PARTIAL |
| L039 | `theoretical_oracle.<theta>.pooled.worst_day_pnl_percentiles.P1/.P5` | AF3 + estimator | `study._worst_day_percentiles` | VF-2 only | PARTIAL | **DR-8** | reviewer | **DECISION_REQUIRED** (DR-8) |
| L040 | `theoretical_oracle.<theta>.by_era.<era>.<7 fields>` | AF3 + AF1 era (pure function of date) | `_by_era_and_pooled` | VF-1 per block | PARTIAL — inherits L036 | DR-1; DR-8 for percentiles | reviewer | PARTIAL |

---

## Table 4 — A4 `e2_worst_days`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L041 | `e2_worst_days.<theta>.<scn>.frozen_mandatory` | AF4 — copied from `executable["E2"][scn]["worst_day_report"]` | dict spread in `build_full_study_result` | VF-0 (allowed-key only) | YES (always `True` here, since the source is E2) | NONE | reviewer | OK |
| L042 | `e2_worst_days.<theta>.<scn>.percentile_estimator` | AF4 — `study.PERCENTILE_METHOD` | copy | VF-0 | PARTIAL (see L032) | DR-8 | reviewer | **DECISION_REQUIRED** (DR-8) |
| L043 | `e2_worst_days.<theta>.<scn>.pooled.P1` / `.P5` | AF2 — E2 `final_pnl_per_contract` over `tp_days` | `np.percentile(method="linear")` via `_worst_day_percentiles` | VF-2 (ordering). **No recompute** — this is a byte copy of L033, never cross-checked against it | PARTIAL — values derivable from AF2 given L023; estimator unapproved | **DR-8** | reviewer (this is the frozen §7 mandatory report) | **DECISION_REQUIRED** (DR-8) |
| L044 | `e2_worst_days.<theta>.<scn>.by_era.<era>.P1` / `.P5` | AF2 + era | same | VF-2 | PARTIAL | **DR-8** | reviewer | **DECISION_REQUIRED** (DR-8) |
| L045 | `e2_worst_days.<theta>.<scn>.estimator_status` | AF4 — `config.methods.worst_day_estimator is not None` | ternary in `build_full_study_result` | `report` requires exactly `"resolved"` to seal; producer emits `"unresolved_DR-M6-H"` today, so **sealing fail-closes** | PARTIAL — the flag is derived only from *non-None-ness*, never from the estimator actually used (`PERCENTILE_METHOD`) | **DR-8** | seal gate | **DECISION_REQUIRED** (DR-8) |

---

## Table 5 — A5 `sizing_outputs`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L046 | `sizing_outputs.<theta>.rows.<eng>.<scn>[i].trade_date` / `.engine` / `.cost_scenario` / `.direction` | AF2 — `rec.trade_date` / `.engine` / `.cost_scenario` / `.direction` | `study._sizing_row` field copies | VF-4 (row **count** only); no field is ever compared against AF2 | **YES** — verbatim AF2 fields on the sealed JSONL | NONE | reviewer, MC (sizing) | OK |
| L047 | `sizing_outputs.<theta>.rows.<eng>.<scn>[i].era` / `.year` | AF1 `day.era`/`day.year` — both pure functions of `trade_date` | `_sizing_row` copies | VF-0 | **YES** (frozen `MICRO_ERA_BOUNDARY`, `date[:4]`) | NONE | reviewer | OK |
| L048 | `…[i].stop_level_points` | **AF3** — `StudyDayInput.anchor_stop` = `or_low` (long) / `or_high` (short), computed from the 09:30-09:59 OBS window in `make_day_inputs` | `inp.anchor_stop` (existing) | `_sizing_row` cross-checks `rec.planned_stop == stop_level` **for E1 only**; nothing checks E2 | **PARTIAL, engine-split**: **E1 = YES** (equals sealed `planned_stop`); **E2 = NO** — `planned_stop` is stored `None` for E2, so the opening-range level reaches no sealed artifact. Needs **EV-3**. | NONE (frozen §7 / MC §3) | reviewer, MC | PARTIAL |
| L049 | `…[i].counterfactual_anchor` | AF4 — `rec.engine == "E2"` | boolean | VF-0 | YES | NONE | reviewer | OK |
| L050 | `…[i].stop_distance_points` | AF2 `entry_fill` + AF3 `anchor_stop` | `abs(entry_fill - stop_level)` | VF-0 | PARTIAL — E1 YES, E2 NO (inherits L048) | NONE | reviewer, MC §3 sizing | PARTIAL |
| L051 | `…[i].risk_usd_per_1_MNQ_planned` | AF2 — `rec.sizing_anchor_usd` (a sealed §10.1 field) | `float(rec.sizing_anchor_usd)` | VF-0 | **YES** — verbatim AF2 | DR-1 (the anchor embeds `side_friction_points(adverse=True)` and the fee) | reviewer, MC §3 `n = floor(budget / sizing_anchor)` | **DECISION_REQUIRED** (DR-1) |
| L052 | `…[i].risk_usd_per_1_MNQ_realized` | AF2 — `-rec.final_pnl_per_contract` iff `engine=="E1" and stop_triggered` else `None` | `_sizing_row` ternary | VF-0 | **YES** — all three inputs are sealed AF2 fields | DR-1 | reviewer, MC | **DECISION_REQUIRED** (DR-1) |
| L053 | `…[i].cost_usd_per_1_MNQ` | **AF4** — `costs.round_turn_cost_usd(scenario, stop_exit)` over `CostScenarioParams` | `round_turn_cost_usd` (existing) | VF-0 | **PARTIAL** — the four `CostScenarioParams` objects are never sealed; only the 3 `spread_scalars` are, and `adverse_slippage_ticks`/`friction_multiplier`/`platform_fee` are not. Needs **EV-4**. | **DR-1** (reduction rule + IR-7 adverse vector) | reviewer | **DECISION_REQUIRED** (DR-1) |
| L054 | `…[i].cost_as_pct_of_R` | AF4 + AF2 — `cost / sizing_anchor_usd`, `None` when non-positive | `_sizing_row` | VF-0 | PARTIAL (inherits L053) | **DR-1** | reviewer | **DECISION_REQUIRED** (DR-1) |
| L055 | `…[i].minimum_1_contract_risk` | AF2 — identical to L051 by construction | `planned` | VF-0 — the identity `minimum_1_contract_risk == risk_usd_per_1_MNQ_planned` is **never asserted** | YES | DR-1 | reviewer | PARTIAL (redundant leaf, unchecked identity) |
| L056 | `…[i].stop_triggered` | AF2 — `rec.stop_triggered` | copy | VF-0 | YES | NONE | reviewer, MC | OK |
| L057 | `…[i].nonpositive_planned_risk` | AF2 — `sizing_anchor_usd <= 0` | boolean | VF-0 | YES | NONE | reviewer | OK |
| L058 | `sizing_outputs.<theta>.coverage.<eng>.<scn>.n_trades` | AF2 — `len(rows)` | `study._coverage` | VF-0 — the identity `n_trades == len(rows) == day_universe.n_tp` is **never asserted** (VF-4 checks only `len(rows)`) | YES given L023 | NONE | reviewer | PARTIAL (unchecked identity, CR-5) |
| L059 | `sizing_outputs.<theta>.coverage.<eng>.<scn>.by_budget_usd.<50\|75\|100\|150>.n_covered` | AF2 — count of `sizing_anchor_usd <= budget` | `_coverage` comprehension | VF-0 | **YES** — recomputable from the sealed JSONL `sizing_anchor_usd` field alone | NONE (budgets frozen §8, descriptive-only) | reviewer, MC (descriptive) | PARTIAL (no verifier despite being fully AF2-derivable) |
| L060 | `…by_budget_usd.<budget>.fraction` | AF2 — `n_covered / n_trades` | `_coverage` | VF-0 | YES (from L058/L059) | NONE | reviewer | PARTIAL |
| L061 | `sizing_outputs.<theta>.coverage.<eng>.<scn>.note` (string) | — | literal | VF-0 | YES | NONE | reviewer | OK |

---

## Table 6 — A6 `frequency`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L062 | `frequency.<theta>.denominator_definition` / `.note` (strings) | — | literals in `study._frequency_block` | VF-0 | YES | NONE | reviewer | OK |
| L063 | `frequency.<theta>.pooled.n_days_in_sample` (and `.by_era.<era>`, `.by_year.<year>`) | AF1 — `{r.trade_date for r in slice_records}` | `_frequency_cell` | VF-0 | **YES** — the slice date sets are exactly `structural.groups.by_year` / `structural.eras` / their union (L013-L015) | NONE | reviewer | PARTIAL (fully derivable, zero verification) |
| L064 | `frequency.<theta>.<slice>.n_months_in_slice` | AF1 — `{r.trade_date[:7]}` | `_frequency_cell` | VF-0 | **YES** — from the same date lists | NONE | reviewer | PARTIAL |
| L065 | `frequency.<theta>.<slice>.n_directional_tradeable` | AF1 — `is_direction_tradeable` = `d_open ∈ {±1}` AND `y_cont is not None` | `len(dates & tradeable)` | VF-0 | **NO** — requires `y_cont` per day for the **whole** eligible population (a superset of the days that have AF2 records). Needs **EV-1**. | NONE (frozen §5 + §10.5) | reviewer; **denominator of L067/L068** | PARTIAL |
| L066 | `frequency.<theta>.<slice>.n_trade_constructible` | AF1+AF3 — `traded_set` = days with a constructible trade | `len(dates & traded)` | VF-0 | PARTIAL — equals the distinct `trade_date` set of any sealed JSONL file, so AF2-derivable today; nothing checks it | NONE | reviewer | PARTIAL |
| L067 | `frequency.<theta>.<slice>.n_continuation_days_labelled` / `.n_continuation_days_traded` | AF1 — `y_cont >= theta` (labelled) / that ∩ `traded_set` | `len(dates & tp_labelled)` / `len(dates & tp_traded)` | VF-0 | **NO** for labelled (needs `y_cont`); PARTIAL for traded (derivable from L023, itself a claim) | NONE | reviewer | PARTIAL |
| L068 | `frequency.<theta>.<slice>.continuation_base_rate_p` | AF1 — `n_continuation_days_labelled / n_directional_tradeable` | `_frequency_cell` | **VF-0 — and this leaf is itself the trusted ANCHOR for VF-7's `F_expected` recompute** (`report._frequency_pooled_p`). An unverified leaf verifies another leaf. | **NO** — needs **EV-1** | NONE (frozen §10.5) | reviewer, **VF-7 input**, MC (App A `F = p·r·N/q`) | PARTIAL — **highest-leverage unverified anchor in the report** |
| L069 | `frequency.<theta>.<slice>.continuation_base_rate_p_traded_only` | AF1 — `n_trd / n_dir` | `_frequency_cell` | VF-0 | NO (same denominator gap) | NONE | reviewer | PARTIAL |
| L070 | `frequency.<theta>.<slice>.oracle_monthly_frequency` / `.oracle_monthly_frequency_labelled` | AF1 — `n_trd / n_months` and `n_lab / n_months` | `_frequency_cell` | VF-0 | PARTIAL / NO respectively | NONE (frozen §10.5 月均频率) | reviewer, MC feasibility | PARTIAL |

---

## Table 7 — A2b `stability_views`

Population caveat that applies to **every row in this table**: `build_stability_views` slices `per_theta_block["d_tp"][engine][scenario]` — the **D_TP-conditional** series. Whether §2's views should be computed on that series or on the full structurally-eligible series is **DR-7 (DR-M6-G), unruled**. Every `n`, `sum_usd`, `mean_usd`, `n_positive`, … in this table therefore carries an unruled population definition.

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L071 | `stability_views.<theta>.<eng>.<scn>.epochs.<epoch>.n` / `.sum_usd` / `.mean_usd` / `.best_day` / `.worst_day` / `.n_positive` / `.n_negative` / `.n_zero` | AF2 values + AF5 epoch-from-year | `stability._cell` after `_epoch_axis` bucketing | **VF-11(a)** recomputes exactly these 8 fields — but from `internal["study"][...]["d_tp"]` (a producer aggregate) and `internal["dataset"].records`, **never from AF2**. VF-5 additionally recomputes `sum(n) == n_tp` from the payload's own `n_tp`. | PARTIAL — bucketing is YES (year from date, epoch from frozen bounds); values are AF2-derivable given L023; the current verifier never reaches AF2 | **DR-7** | reviewer | **DECISION_REQUIRED** (DR-7) |
| L072 | `stability_views.<theta>.<eng>.<scn>.epochs.<epoch>.worst_day_pnl_percentiles.P1/.P5` | AF2 + estimator | `stability._percentile` (a **second** `PERCENTILE_METHOD` constant) | VF-2 only; **VF-11 deliberately excludes percentiles** | PARTIAL | **DR-8**, DR-7 | reviewer | **DECISION_REQUIRED** |
| L073 | `stability_views.<theta>.<eng>.<scn>.epochs.conservation_ok` | AF2 — `sum(cell.n) == len(pnl)` | `_epoch_axis` | `report` requires literally `True` **and** independently re-derives the sum (VF-5) against the payload's own `n_tp` | PARTIAL | DR-7 | validator-only | PARTIAL |
| L074 | `stability_views.<theta>.<eng>.<scn>.by_year.<year>.<9 fields>` + `.conservation_ok` | AF2 + `year = date[:4]` | `_by_year_axis` + `_cell` | VF-11(a) (aggregate-anchored); VF-5 | PARTIAL | DR-7; DR-8 for percentiles | reviewer | **DECISION_REQUIRED** |
| L075 | `stability_views.<theta>.<eng>.<scn>.leave_one_year_out.<year>.<9 fields>` | AF2 — complement re-aggregation | `_loyo_axis` + `_cell` | VF-5 recomputes only `n` (`loyo[y].n == n_tp - by_year[y].n`). **VF-11 explicitly excludes LOYO**; `sum_usd`/`mean_usd`/`best`/`worst`/`n_positive`/… are **never recomputed** | PARTIAL | DR-7; DR-8 | reviewer | PARTIAL |
| L076 | `stability_views.<theta>.<eng>.<scn>.leave_one_year_out.conservation_ok` | AF2 | `_loyo_axis` | `report` requires literally `True` | PARTIAL | DR-7 | validator-only | PARTIAL |
| L077 | `stability_views.<theta>.<eng>.<scn>.by_direction.<+1\|-1>.<9 fields>` + `.conservation_ok` | **AF2 — `record.direction` is a sealed §10.1 field** | `_direction_axis` + `_cell` | VF-11(a) buckets by `day_meta[d]["d_open"]` derived from `internal["dataset"].records` — i.e. AF1, not AF2, even though AF2 carries `direction` verbatim | PARTIAL — the **only** stability axis whose bucketing key is fully sealed; values still need L023 | DR-7; DR-8 | reviewer | **DECISION_REQUIRED** (DR-7) |
| L078 | `stability_views.<theta>.<eng>.<scn>.vol_terciles.<tercile>.<9 fields>` | **AF5 — does not exist**. `vol_axis={d: str(config.vol_axis_of(d))}`; `config` cannot be derived (`_approved_injectables()` returns `None`); no 20-day realized-volatility computation exists anywhere in the tree | `stability._vol_axis` + `_cell` (structure only; the labels are opaque) | VF-0. `report` fail-closes on `status == "unresolved"` (`vol_axis_unresolved`) and, when resolved, requires 3 terciles + `vol_na` + `conservation_ok is True`. **VF-11 explicitly excludes `vol_terciles`** (blind-audit G3) | **NO** — no atom exists at any point in the chain | **DR-2 (DR-M6-B-v2)** — window / close source / return basis / ddof / roll-crossing / tercile-bounding population / NA rule, all unruled | reviewer, and (shared mapping) AF7 grid stratification | **DECISION_REQUIRED** (DR-2) |
| L079 | `stability_views.<theta>.<eng>.<scn>.vol_terciles.vol_na.<9 fields>` | AF5 — reserved bucket for dates absent from `vol_axis` | `_vol_axis` | `report` requires the `vol_na` key present when resolved | NO (same as L078) | **DR-2** | reviewer | **DECISION_REQUIRED** (DR-2) |
| L080 | `stability_views.<theta>.<eng>.<scn>.vol_terciles.status` / `.reason` | AF5 — `vol_axis is None` | `_vol_axis` early return | `report` treats `status == "unresolved"` as a sealing blocker | YES (today's value is structural) | **DR-2** | seal gate | **DECISION_REQUIRED** (DR-2) |

---

## Table 8 — A7 `bootstrap_ci`

Cell key format: `<theta>|<eng>|<scn>|block<blk>` (2·2·4·2 = 32 cells).

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L081 | `bootstrap_ci.<cell>.per_seed.<seed>.mean` | AF2 + AF6 — sample mean of `[d_tp[d] for d in sorted(d_tp)]` | `stats._bootstrap_mean_ci_unchecked`: `float(values.mean())` (numpy), computed once and copied to all three seeds | VF-6 — **cross-seed equality only** (blind-audit A29/C14). Never compared to `oracle_daily…pooled.mean_usd`, which is the same statistic computed by a **different** reducer (`sum/len` in `_series_block`) | PARTIAL — AF2-derivable given L023 | **DR-4.3** (statistic: per-trading-day mean vs per-oracle-day mean) | reviewer | **DECISION_REQUIRED** (DR-4) |
| L082 | `bootstrap_ci.<cell>.per_seed.<seed>.ci_lo` / `.ci_hi` | AF2 + AF6 — 10,000 stationary-bootstrap resamples per seed via `default_rng([seed, 9001, block_stream_key])` -> `mc.bootstrap.stationary_bootstrap_indices` -> `np.percentile(method="linear")` | `stats.bootstrap_mean_ci` (existing, fully deterministic) | **VF-0** — no endpoint is ever recomputed; only `lo <= hi` and the literal `n_boot`/`block_len` pins | PARTIAL — **exactly replayable** given L023 + sealed AF2 + the frozen seeds/tags (deterministic PCG64), at a cost of 32 cells × 3 seeds × 10,000 resamples. Nothing captures the input series digest, so a replay cannot prove it used the same series (**EV-7**). | **DR-4 (D4.1-D4.7)** — population, NA-day rule, statistic, 10,000 attribution, quoted seed, percentile interpolation, CRN scope | reviewer; MC §5(b) seed-agreement counterpart | **DECISION_REQUIRED** (DR-4) |
| L083 | `bootstrap_ci.<cell>.per_seed.<seed>.n_boot` | AF6 — `FROZEN_N_BOOT = 10_000` | literal passthrough | `report` pins int-typed `== 10000` | YES — frozen constant | DR-4.4 (per-seed vs pooled attribution) | validator-only | **DECISION_REQUIRED** (DR-4.4) |
| L084 | `bootstrap_ci.<cell>.per_seed.<seed>.block_len` | AF6 — `FROZEN_BLOCKS = (5, 21)` | literal passthrough | `report` pins int-typed `== blk` parsed from the cell key | YES — frozen constant | NONE (frozen §9) | validator-only | OK |
| L085 | `bootstrap_ci.<cell>.convergence.max_abs_ci_lo_diff` / `.max_abs_ci_hi_diff` | AF6 — `max(los) - min(los)` over the three seeds | `_bootstrap_mean_ci_unchecked` | VF-0 — presence-checked only; **never recomputed from the payload's own `per_seed` endpoints**, which it trivially could be | PARTIAL — derivable from L082 in the same subtree | DR-5 / MC §5(b) (the tolerance itself is MC's; S0 reports the spread only) | reviewer, MC | PARTIAL |
| L086 | `bootstrap_ci.<cell>.quoted_seed` | AF6 — `seeds[0]` = 7 | `_bootstrap_mean_ci_unchecked` | `report` pins `== 7` | YES — frozen convention | DR-4.5 (formal confirmation of the fixed-first-seed convention) | validator-only | **DECISION_REQUIRED** (DR-4.5) |
| L087 | `bootstrap_ci.<cell>.quoted` (block) | AF6 — `per_seed[7]` verbatim | dict alias | `report` requires exact equality with `per_seed[7]` (M6.1.3) | YES (given L082) | DR-4.5 | reviewer | PARTIAL |
| L088 | `bootstrap_ci.<cell>.method` (string) | AF6 — `stats._method_string` | f-string over the frozen constants | VF-0 — allowed-key only; the disclosed `PERCENTILE_METHOD` inside is never cross-asserted | YES | DR-4.6 | reviewer | PARTIAL |

---

## Table 9 — A8 `feasibility_grid`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L089 | `feasibility_grid.cells.<theta\|eng\|scn>.n_tp_available` / `.n_fp_available` | AF1 — `len(tp_pnl)` / `len(fp_pnl)` = the theta partition sizes | `_build_grid_unchecked` | VF-7 **trusts this value as its own recompute basis**; it is **never** compared to `oracle_daily.<theta>.day_universe.n_tp`/`.n_fp`, which is the same quantity by a different route (blind-audit A34/A46-A51) | **NO** — inherits L021's `y_cont` gap | NONE | VF-7 input, reviewer, MC | PARTIAL — **unchecked cross-section identity (CR-3)** |
| L090 | `feasibility_grid.cells.<…>.method` (string) | AF7 — `gridmix._method_string(seeds, n_year)` | f-string over frozen constants | VF-0 (leaf-typed `str` only) | YES | DR-2, DR-3, DR-5 (the string *describes* unruled choices) | reviewer | PARTIAL |
| L091 | `feasibility_grid.cells.<…>.grid.<qr>.target_precision` / `.target_recall` | AF7 — `q_mil/1000`, `r_mil/1000` from `Q_GRID_MILLIS`/`R_GRID_MILLIS` | `_grid_point` | VF-7 recomputes from `_FEASIBILITY_GRID_KEY_TO_MILLIS` (derived from gridmix's own axes) | **YES** — frozen constants, genuinely externally anchored | NONE (frozen App A) | reviewer, MC | OK |
| L092 | `feasibility_grid.cells.<…>.grid.<qr>.n_tp_target` | AF7 — `floor(r × N_TP_available)` | `gridmix.floor_n_tp(r_mil, n_tp_available)` | VF-7 recomputes via gridmix's own integer arithmetic — but against the cell's **own** `n_tp_available` (L089) | PARTIAL — the arithmetic is verified; its input is not | NONE (frozen App A 取整) | reviewer, MC | PARTIAL |
| L093 | `feasibility_grid.cells.<…>.grid.<qr>.n_fp_target` | AF7 — `round_half_up(n_tp × (1−q)/q)` in exact Decimal | `gridmix.n_fp_for(n_tp_target, q_mil)` | VF-7 (same anchor caveat) | PARTIAL | NONE (frozen App A) | reviewer, MC | PARTIAL |
| L094 | `feasibility_grid.cells.<…>.grid.<qr>.F_expected` | AF7 + AF1 — `p·r·N/q`, `N = 252` | `gridmix.f_expected(base_rate_p, r, q, N)` | VF-7 recomputes — reading `p` **from the payload's own `frequency[<theta>].pooled.continuation_base_rate_p`** (L068), itself unverified (blind-audit A54/G6) | PARTIAL — formula verified, `p` is a claim | NONE for the formula; L068's gap propagates | reviewer, MC | PARTIAL |
| L095 | `feasibility_grid.cells.<…>.grid.<qr>.infeasible_by_sample` | AF7 — `n_fp_target > n_fp_available` | `_grid_point` early return | VF-7 checks the *shape* consequences (empty `per_seed`, `infeasible_reason` present) but **never recomputes the predicate itself** | PARTIAL — recomputable from L089+L093 in the same subtree | DR-3 (whether the FP basis changes availability semantics) | reviewer, MC | PARTIAL |
| L096 | `feasibility_grid.cells.<…>.grid.<qr>.infeasible_reason` (string) | AF7 | f-string | `report` requires presence on infeasible points | YES | NONE | reviewer | OK |
| L097 | `feasibility_grid.cells.<…>.grid.<qr>.per_seed.<seed>.tp_dates[]` / `.fp_dates[]` | **AF7 + AF5** — `_select(pools, alloc, default_rng([seed, 9002, q_mil, r_mil]))`, TP stream first then FP, strata visited in ascending key order | `gridmix._select` (existing, deterministic) | VF-7 checks only self-consistency (`n_*_actual == len(*_dates)`); handoff `verify_handoff_conservation` would cross-check against DAY_STRATA, **but neither DAY_STRATA nor GRID_SAMPLES is produced by any production caller** (packet P-4) | **NO** — replay needs `tp_pools`/`fp_pools` (stratum key -> sorted dates), which requires the per-day strata map (AF5), which is a discarded local. Needs **EV-5 + EV-6**. | **DR-2** (vol regime), **DR-6/DR-M6-F** (event stratum), **DR-3/DR-M6-C** (FP allocation basis) | **MC — frozen App A step 4 names the day-marker sequence as an MC input** | **DECISION_REQUIRED** (DR-2, DR-3, DR-6) |
| L098 | `feasibility_grid.cells.<…>.grid.<qr>.per_seed.<seed>.n_tp_actual` / `.n_fp_actual` | AF7 — `len(tp_dates)` / `len(fp_dates)` | `_seed_report` | VF-7 recomputes from the entry's own lists | PARTIAL (self-consistency only) | inherits L097 | reviewer, MC | PARTIAL |
| L099 | `…per_seed.<seed>.realized_precision` / `.realized_recall` | AF7 — `n_tp/(n_tp+n_fp)` and `n_tp/n_tp_available` | `_seed_report` | VF-7 recomputes from the entry's own dates and the cell's own `n_tp_available` | PARTIAL | inherits L097 | **MC — App A step 4: "MC 使用实际抽到的交易数与 realized 值"** | PARTIAL |
| L100 | `…per_seed.<seed>.target_precision` / `.target_recall` / `.F_expected` | AF7 — duplicates of L091/L094 at seed level | `_seed_report` | VF-7 recomputes; **the point-level vs seed-level duplicates are never compared to each other** | PARTIAL | inherits L094 | reviewer | PARTIAL (CR-8) |
| L101 | `…per_seed.<seed>.day_markers[[date, "tp"\|"fp"]]` | AF7 — `sorted([(d,"tp")…] + [(d,"fp")…])` | `_seed_report` | **VF-0** — never cross-checked against `tp_dates`/`fp_dates`, which it is a pure re-encoding of | NO (inherits L097) | inherits L097 | **MC — the "交易日标记序列" of frozen App A step 4** | PARTIAL (CR-8) |
| L102 | `…per_seed.<seed>.mixture_mean_pnl` | AF2 + AF7 — `mean([tp_pnl[d] for d in tp_dates] + [fp_pnl[d] for d in fp_dates])` | `_seed_report` | VF-0 | PARTIAL — AF2-derivable **given** L097's dates (which are not reproducible) | DR-1 (USD layer), inherits L097 | reviewer | PARTIAL |
| L103 | `…per_seed.<seed>.allocation_tp.<stratum_key>` / `.allocation_fp.<stratum_key>` | AF7 — `gridmix.allocate(n_target, avail)` + `largest_remainder` (seed-independent) | `allocate` (existing) | VF-7 leaf-types them as non-negative int maps; **never recomputes, and never checks `sum(allocation) == n_*_target`** | **NO** — recompute needs `tp_avail`/`fp_avail` per stratum (AF5/EV-6). Note the **stratum keys themselves leak the unruled vocabulary** (`year\|regime\|event`) into the sealed payload. | **DR-2, DR-3, DR-6** | reviewer | **DECISION_REQUIRED** |
| L104 | `feasibility_grid.regions.status` | — | literal `"pending_mc"` | `report` requires exactly `"pending_mc"` | YES | NONE (frozen App A step 5 — regions are MC's) | seal gate, MC | OK |

---

## Table 10 — A9 `mc_handoff_manifest`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L105 | `mc_handoff_manifest.counts.<eng>.<scn>.n_records` | AF2 — `len(study["records"][eng][scn])` | dict comprehension in `build_full_study_result` | **VF-11(c)** vs `len(internal["records"][eng][scn])` (a real AF2 touch, count-only); **VF-9** vs the payload's own `n_tp + n_fp`; **VF-10** triple equality vs actual JSONL line count | **YES** — the sealed JSONL line count is the atom | NONE | seal gate, MC | OK |
| L106 | `mc_handoff_manifest.files.<eng\|scn>.file` | AF2 — `f"MC_HANDOFF_{eng}_{scn}.jsonl"` | f-string in `render_s0_report` | VF-10 (file must exist in the written set) | YES | NONE | seal gate | OK |
| L107 | `mc_handoff_manifest.files.<eng\|scn>.n_records` | AF2 — `len(recs)` | `render_s0_report` | VF-10 triple equality (manifest vs bytes vs `counts`) | YES | NONE | seal gate, MC | OK |
| L108 | `mc_handoff_manifest.files.<eng\|scn>.sha256` | AF2 — `sha256(body.encode("utf-8"))` | `render_s0_report` | VF-10 re-hashes the **actual bytes** | YES — genuinely externally anchored | NONE | seal gate | OK |
| L109 | `mc_handoff_manifest.sealed_files.<name>.sha256` / `.bytes` | the written file bodies | `render_s0_report` dict comprehension | VF-10 re-hashes and re-measures every entry; plus the `uncovered = set(files) - set(sealed_files) - self_excluded` completeness reconciliation | YES | NONE | seal gate | OK |
| L110 | `mc_handoff_manifest.self_excluded[]` | — | literal `["S0_REPORT.json"]` | VF-10 caps it to the module-frozen `_ALLOWED_SELF_EXCLUDED` | YES | NONE | seal gate | OK |

---

## Table 11 — A10 `era_axis`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L111 | `era_axis.axes[]` | AF1 — `list(ds.eras)` (key order of `dataset._eras`) | `build_full_study_result` | `report` requires the exact 2-element set, no duplicate | YES — frozen `ERA_PROXY`/`ERA_ACTUAL` | NONE (frozen §6 L109-115) | reviewer | OK |
| L112 | `era_axis.counterfactual_disclosure` (string) | — | literal | `report` requires non-blank str | YES | NONE | reviewer | OK |

---

## Table 12 — A11 `disclosures`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L113 | `disclosures.na_conservation.per_table_total_na.features` / `.labels` | AF1 — `stage_c_result` totals, `totals[f"{t}.{f}"] = int(ds.na_table["per_field"][t][f]["na"])` | `_na_conservation_block` prefix sum | **VF-8** vs `structural.na_table.per_field` (payload-internal) **and VF-11(d)** vs `internal["reported_total_na"]` — **both trace to the same `ds.na_table` preimage**, so the "independent" recompute is not independent | PARTIAL — needs **EV-8** (a structurally different NA observation, e.g. a raw null scan of `features_table`/`labels_table`) | NONE | reviewer, seal gate | PARTIAL — **illusory independence (CR-1)** |
| L114 | `disclosures.na_conservation.conservation_ok` / `.conserved` | AF1 — `runinfra.check_na_conservation(...).ok` | `_na_conservation_block` | `report` requires literally `True`, and (M6.1.3 A56) refuses contradiction with the richer evidence keys | PARTIAL — inherits L113 | NONE | seal gate | PARTIAL |
| L115 | `disclosures.na_conservation.reported_total_na.<table.field>` | AF1 — `stage_c_result` totals | int copy | VF-13 (itemized sum == total, both from the same preimage) | PARTIAL | NONE | reviewer | PARTIAL |
| L116 | `disclosures.na_conservation.itemized_reason_counts.<col>.<reason>` | AF1 — `DayRecord.*_na_reasons` counters | `stage_c_result` + copy | VF-13 (`reason ∈ APPROVED_NA_REASONS`, sum identity) | PARTIAL | NONE | reviewer | PARTIAL |
| L117 | `disclosures.na_conservation.per_column_ok.<col>` / `.unregistered_reasons[]` / `.miscounted_columns[]` | AF1 via `NAConservationResult` | `_na_conservation_block` | `report` refuses `conservation_ok=True` alongside a non-empty/false value here | PARTIAL | NONE | seal gate | PARTIAL |
| L118 | `disclosures.na_conservation.checker` (string) | — | literal naming `runinfra.check_na_conservation` | VF-0 (allowed-key only) | YES | NONE | reviewer | OK |
| L119 | `disclosures.untradeable[]` rows: `.trade_date` / `.year` / `.era` / `.d_open` / `.y_cont` / `.reason` | AF1 + AF3 — `study._collect_day_inputs` disclosure | list build in `build_study` | **VF-0** — no shape, count, or vocabulary check whatsoever; `report` never inspects this key beyond the allowed-key set | PARTIAL — note this is the **only** place `y_cont` reaches the sealed payload, and only for the (normally empty) untradeable set | NONE | reviewer | PARTIAL |
| L120 | `disclosures.pending_method_decisions[]` | AF4 — `ResolvedS0Methods.pending_fields()` (derived, never hand-written) | `pending_fields()` | `report` distinguishes *missing key* from *non-empty*; non-empty blocks sealing | YES — derived from the single method source | all 8 DRs (this list **is** the DR ledger) | seal gate | **DECISION_REQUIRED** (all DRs) |
| L121 | `disclosures.methods_test_only` | AF4 — `config.methods.test_only` | bool copy | `_validated_config` refuses a `test_only` config on the production path | YES | NONE | reviewer | OK |
| L122 | `disclosures.method_conventions.quoted_seed_convention` / `.stream_tags` (strings) | AF6 — prose restating `STATS_STREAM_TAG=9001` / `GRID_STREAM_TAG=9002` | literals | VF-0 — the prose is **not** built from the module constants, so it can drift from `stats.STATS_STREAM_TAG`/`gridmix.GRID_STREAM_TAG` (unlike SEED_MANIFEST, which VF-12 rebuilds) | NO — hand-written duplicate of a constant | DR-4.5 | reviewer | PARTIAL (CR-9) |
| L123 | `disclosures.method_conventions.spread_scalars_used[]` | AF4 — `config.spread_scalars` triple `(median, P90, P95)` | `list(config.spread_scalars)` | VF-0 — `StudyConfig.__post_init__` enforces `0 <= median <= P90 <= P95`, but nothing re-derives them from `spread_cost_table.csv` | PARTIAL — the reduction rule that produces them is unruled and `_approved_injectables()` returns `None` today | **DR-1 (DR-M6-A-v2)** | reviewer | **DECISION_REQUIRED** (DR-1) |

---

## Table 13 — A12 `governance`

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L124 | `governance.trial_id` | AF8 — `s0_real_run.TRIAL_ID` module constant | literal | `report` requires exact equality with `expected_governance["trial_id"]` — **which is the same module constant**, so the cross-check is tautological | YES | NONE | seal gate, reviewer | PARTIAL (tautological verifier) |
| L125 | `governance.authorized_commit` | AF8 — the 40-hex commit parsed out of the verbatim packet-§10 sentence in `ops/TRIAL_REGISTRY.md` | `find_authorization_event` -> `_validate_authorized_row` (IR-25 supersede resolution) | VF-14 re-reads the registry file and re-parses at seal time (catches mutation between compute and seal); Stage-A `head_matches_authorized_commit` compares it to `git rev-parse HEAD` | **YES** — genuine external primary source | NONE (IR-25 ruled) | seal gate, reviewer | OK |
| L126 | `governance.engineering_seed` | AF8 — `s0_real_run.ENGINEERING_SEED = 20260731` | literal | tautological (same constant on both sides); the real pin is the Stage-A `frozen_constants_in_process` gate | YES | NONE (DR-02: never a research seed) | seal gate | PARTIAL (tautological verifier) |
| L127 | `governance.frozen_hashes.<7 paths>` | AF8 — **the on-disk bytes of the 7 frozen files** | `dict(guards.FROZEN_HASHES)` — a **hardcoded dict**, not a re-hash | `report` requires exactly 7 entries, 64-hex each, and exact equality with `expected_governance["frozen_hashes"]` — **also `dict(guards.FROZEN_HASHES)`**, so the seal-boundary check is tautological. The real re-hash is **VF-15**, at the Stage-A `real_run_allowed` gate, and it is not bound into the seal. | PARTIAL — the atom (file bytes) exists and VF-15 reads it, but the seal never binds to that reading | NONE | seal gate, reviewer | PARTIAL — **tautological at the seal boundary** |
| L128 | `governance.registry_sequence_snapshot` | AF8 — `len(parse_registry_events(registry_text))` | `parse_registry_events` | VF-14 re-reads and re-parses the file at seal time. Same parser both sides (shared implementation), but **different reads of the file**, so registry mutation between compute and seal *is* caught. Additionally covered by `pre_exposure_recheck` (registry sha256 + event count + commit). | YES | NONE (IR-25) | seal gate | OK |

---

## Table 14 — MC-handoff artifacts (sealed set beyond `S0_REPORT.json`)

| # | formal_leaf | authoritative_atomic_source | pure_reducer | independent_verifier | currently_reconstructible | research_definition_dependency | production_consumer | status |
|---|---|---|---|---|---|---|---|---|
| L129 | `MC_HANDOFF_<eng>_<scn>.jsonl` line `.trade_date` / `.engine` / `.cost_scenario` / `.direction` | **AF2** — `TradePathRecord` identity fields | `report.record_to_formal_dict` (exact field-set equality vs `FORMAL_RECORD_FIELDS`) | VF-10: field set, leaf types, `direction ∈ {+1,-1}` as int, engine/scenario == file identity, per-file date uniqueness, per-file date set == the (payload-derived) universe | YES — this **is** the atom | NONE (frozen §10.1) | **MC (primary input)**, seal gate | OK |
| L130 | line `.entry_timestamp` / `.exit_timestamp` | AF2 — `paths.build_record`: `entry_row["ts"].isoformat()` / `exit_row["ts"]` | rename `entry_ts`->`entry_timestamp` (`_TS_RENAME`) | VF-10 leaf-types as `str`; `_INTERNAL_NAME_LEAK` refuses the internal names. **No check that `entry_timestamp` is the 10:00 bar** or that `exit_timestamp` is at/after it | PARTIAL — the value is the atom, but the frozen §3 entry/exit-time invariant is never asserted on the sealed line | NONE (frozen §3) | MC | PARTIAL |
| L131 | line `.entry_fill` / `.exit_fill` | AF2 + AF3 + AF4 — `costs.scenario_entry_fill(bar_open, d, scn)`, `scenario_timed_exit_fill` / `scenario_stop_fill` | `paths.build_record` | VF-10 leaf-types as finite number only | PARTIAL — re-deriving from the raw bar reference price requires AF3 bars **and** the `CostScenarioParams` (EV-3/EV-4) | **DR-1** | MC | **DECISION_REQUIRED** (DR-1) |
| L132 | line `.final_pnl_per_contract` | AF2 — `d*(exit_fill − entry_fill)*MNQ_POINT_VALUE_USD − platform_fee_rt_usd` | `paths.build_record` | **VF-0** — no verifier anywhere recomputes this from `entry_fill`/`exit_fill`/`direction`, all three of which sit on the **same sealed line** | PARTIAL — trivially recomputable from the line's own fields; nothing does it | DR-1 | **MC (the value every S0 P&L leaf reduces from)**, and the value layer of L026/L027/L071/… | PARTIAL — **the single most-consumed atom, with zero internal recompute** |
| L133 | line `.mtm_close_pnl_1m[]` / `.mtm_adverse_pnl_1m[]` | AF2 + AF3 — per-minute marks vs the friction-inclusive entry fill; adverse = minute low (long) / high (short); stop bar truncates | `paths.build_record` loop | VF-10 requires a **non-empty** list of finite numbers. No length agreement between the two arrays, no consistency with `entry_fill`/`exit_fill`, no check that the last element equals `final_pnl_per_contract + fee` | PARTIAL — needs AF3 bars to re-derive | NONE (frozen §10.1) | **MC §3 — adverse-path breach checking on both platforms** | PARTIAL |
| L134 | line `.max_adverse_pnl` / `.time_of_max_adverse` | AF2 — `min(mtm_adverse)` and its first-occurrence bar timestamp | `paths.build_record` | **VF-0** — `max_adverse_pnl` is trivially `min(mtm_adverse_pnl_1m)` **on the same line** and is never checked against it | PARTIAL — recomputable from the line itself | NONE (frozen §10.1) | MC §3 | PARTIAL |
| L135 | line `.max_favourable_pnl` | AF2 — extreme-based running max (ruling R4/IR-2), realized-only credit on stop/exit bars | `paths.build_record` | VF-0 | PARTIAL — **not** recomputable from `mtm_close`/`mtm_adverse` alone (needs the favourable extremes, i.e. AF3 bars) | NONE (IR-2 ruled `diagnostic_only`) | reviewer (diagnostic only — must never enter a verdict) | PARTIAL |
| L136 | line `.planned_stop` / `.actual_stop_fill` / `.stop_triggered` | AF2 + AF3 — E1 live stop = opening-range opposite extreme; `None` for E2 | `paths.build_record` | VF-10 leaf-types; `_sizing_row` cross-checks E1 `planned_stop == anchor_stop` **at compute time only** | PARTIAL — E1 `planned_stop` is the sealed proxy for the opening-range level; E2's is deliberately `None` (EV-3 gap) | NONE (frozen §7) | MC §3 | PARTIAL |
| L137 | line `.sizing_anchor_usd` | AF2 + AF3 + AF4 — `paths.sizing_anchor_usd(entry_fill, planned_stop, d, scn)` incl. adverse friction + fee once (IR-4) | `paths.sizing_anchor_usd` | VF-0 | PARTIAL — recomputable for E1 from the line + EV-4; for E2 needs EV-3 as well | **DR-1** (adverse friction) | **MC §3 — `n = floor(risk_budget / sizing_anchor_usd)`**; A5 L051 | **DECISION_REQUIRED** (DR-1) |
| L138 | line `.ambiguous_stop_vs_floor` | AF2 — hardcoded `False` in `paths.build_record` (stop-vs-MLL ordering is MC's concern) | literal | VF-10 leaf-types as bool | YES (constant) | NONE (frozen §10.1 dual-scenario rule is MC-side) | MC §3 | OK |
| L139 | `SEED_MANIFEST.json.research_bootstrap_seeds[]` | AF6 — `contracts.RESEARCH_BOOTSTRAP_SEEDS` | `handoff.build_seed_manifest` (asserts object **identity** with the contracts tuple) | **VF-12 REBUILDS the value** from `contracts.RESEARCH_BOOTSTRAP_SEEDS` and refuses a mismatch regardless of the artifact's own flag | **YES** — the one artifact leaf with a true value recompute | NONE (frozen §9 / App A step 3) | MC replay | OK |
| L140 | `SEED_MANIFEST.json.stream_tags.stats_stream_tag` / `.grid_stream_tag` | AF6/AF7 — `stats.STATS_STREAM_TAG` / `gridmix.GRID_STREAM_TAG` | `build_seed_manifest` | VF-12 rebuilds from the owning modules' constants | YES | NONE (disclosed engineering convention) | MC replay | OK |
| L141 | `SEED_MANIFEST.json.k_policy` | AF7 — **unresolved**; emitted as `"UNRESOLVED_DR-M6-E"` | `handoff._unresolved("DR-M6-E")` | VF-12 `_marker_problems` flags any UNRESOLVED marker -> artifact **withheld** from the sealed set today (`admitted=[]`) | NO | **DR-5 (DR-M6-E)** — K per seed, k start index, θ-in-stream, convergence rule, max doublings | MC replay | **DECISION_REQUIRED** (DR-5) |
| L142 | `SEED_MANIFEST.json.crn_scope` | AF6 — emitted as the bare `"UNRESOLVED"` sentinel | `str(UNRESOLVED)` | VF-12 (same) | NO | **DR-4.7** (S0-internal engine×scenario CRN; the cross-platform/policy CRN is already frozen in MC §5) | MC replay | **DECISION_REQUIRED** (DR-4.7) |
| L143 | `SEED_MANIFEST.json.formal_sealable` | derived — `not (_is_unresolved(k_policy) or _is_unresolved(crn_scope))` | `build_seed_manifest` | VF-12 **recomputes the verdict from content** and refuses a `True` flag whose content is not sealable (contradiction path) | YES (as a derivation) | inherits DR-4.7 / DR-5 | seal admission gate | **DECISION_REQUIRED** |
| L144 | `DAY_STRATA.days.<date>.{micro_execution_era, stability_epoch, year, d_open, event_flag_final, event_na, event_stratum, vol_status, tp_fp_class.<theta>}` | AF1 + AF5 — per-day classification | `handoff.build_day_strata` (exists; validates era/epoch distinctness, year/date agreement, year/epoch agreement, F10 vocabulary, theta-nesting monotonicity) | `_validate_day_strata_content` exists (13/13 fake-artifact cases caught per the packet), **but `event_stratum` is always `"UNRESOLVED_DR-M6-F"`, so the artifact can never be sealable** | **NOT PRODUCED** — `render_s0_report` never calls `build_day_strata`; the candidate set is `{"SEED_MANIFEST.json"}` only (packet P-4, disclosed in `HANDOFF_ADMISSION.json`) | **DR-6 (DR-M6-F)** for `event_stratum`; **DR-2** for `vol_status`; DR-7 indirectly | MC (would be the per-day stratum ledger) | **DECISION_REQUIRED** (DR-6, DR-2) |
| L145 | `GRID_SAMPLES.cells.<qr>.{per_seed.<seed>.{tp_dates, fp_dates, markers, realized_*, target_*}, infeasible_by_sample, q_mil, r_mil}` and `.replay.{stream_formula, grid_stream_tag, k_policy, crn_scope}` | AF7 | `handoff.build_grid_samples` (exists; `q_mil`/`r_mil` recovered as the exact inverse of gridmix's `q_mil/1000.0`) | `_validate_grid_samples_content` exists (axis locks, per-cell seed set, cross-check against a co-supplied SEED_MANIFEST); `replay_status` is hardcoded `PARTIAL_single_stratum_only`, and `REPLAY_STATUS_CLOSED` is **deliberately unreachable** | **NOT PRODUCED** — no production caller | **DR-2 + DR-6** (multi-stratum replay is blocked on the stratum vocabulary), **DR-5** (`k_policy`) | MC replay | **DECISION_REQUIRED** (DR-2, DR-5, DR-6) |
| L146 | `HANDOFF_ADMISSION.json.{schema_version, admitted[], withheld{}, note}` | derived from `formal_seal_admission` | `_partition_admission` (injective `"{name}: "` attribution; unattributable problems fail the render closed) | the renderer raises on a colliding candidate name or a stray problem string | YES | inherits every artifact's DRs | reviewer, seal gate | OK |
| L147 | `S0_REPORT.md` body (index of the sealed set) | — | literal lines in `render_s0_report` | covered by `sealed_files` sha256/bytes (L109) | YES | NONE | reviewer | OK |
| L148 | `S0_REPORT.json` bytes | the validated formal payload | `report.to_formal_json` (`sort_keys=True, indent=1, allow_nan=False`, `_clean` walk, no `default=str`) | **self-excluded** from `sealed_files` (it carries the manifest); Stage F's chain seal is the stated cover | PARTIAL — the file's own integrity depends on a Stage-F mechanism outside this boundary | NONE | seal gate, reviewer, MC | PARTIAL |

---

# Closing summary

## S1. Counts by status

| status | rows | share |
|---|---|---|
| **OK** | 37 | 25.0% |
| **PARTIAL** | 73 | 49.3% |
| **DECISION_REQUIRED** | 38 | 25.7% |
| **total leaf rows** | **148** | 100% |

By `currently_reconstructible` (as defined in §0.4):

| value | rows |
|---|---|
| YES | 56 |
| PARTIAL | 70 |
| NO | 20 |
| NOT PRODUCED (artifact has no production caller — L144, L145) | 2 |

**Verifier coverage — the RC-1 measurement.** 52 of 148 rows (35%) carry `independent_verifier = VF-0` and nothing else: no recomputation of any kind exists for them. A further 5 rows cite VF-0 alongside a partial check (e.g. a presence-only or leaf-type-only rule).

Of the 96 rows that do carry some verifier, **only 14 anchor on something outside the subtree being checked**:

- **VF-16, the hash-locked `S0_INPUT_PREFLIGHT.json`** — L001, L002, L005, L006, L012 (5 rows, all in A1, and only at Stage B, never re-asserted at seal);
- **VF-10, the actual sealed bytes** — L105, L107, L108, L109 (4 rows: manifest counts and integrity digests), plus the per-line identity checks on L129;
- **VF-14, the re-read `ops/TRIAL_REGISTRY.md` bytes** — L125, L128 (2 rows);
- **VF-12, the owning modules' constants rebuilt from source** — L139, L140 (2 rows).

Every other verifier in the tree anchors on the payload's own claims (VF-1, VF-3, VF-4, VF-5, VF-6, VF-7, VF-8, VF-9) or on a producer aggregate (VF-11). **That distribution is RC-1 stated as a number: 14 of 148 decision-bearing leaves have any anchor a synchronized tampering could not move.**

## S2. Leaves NOT reconstructible today — the `CanonicalS0Evidence` field list

Each entry names the exact evidence object that must be captured **at compute time** (inside `build_full_study_result` / `build_study` / `make_day_inputs`, where the atom is still in scope) for the dependent leaves to become derivable. None of these proposes an algorithm; each records what is currently thrown away.

| id | evidence object | fields to capture | unblocks | blocked by a ruling? |
|---|---|---|---|---|
| **EV-1** | `CanonicalDayFact` — one row per **structurally eligible** day (not just per traded day) | `trade_date`, `year`, `era`, `d_open`, `y_cont`, `y_cont_available`, `direction_status`, `oracle_candidate`, `tradeable_direction`, `trade_constructible`, `untradeable_reason`, `is_event_day` (final F10) | L018, L021, L022, **L023**, L024, L065, L067, L068, L069, L070, L089 — i.e. the **entire θ partition and the whole A6 frequency block** | No — capture is unblocked today |
| **EV-2** | `TheoreticalPathRecord` — one per TP day, per theta (the §7 economic-upper-bound analogue of `TradePathRecord`) | `trade_date`, `direction`, `scenario_name`, `entry_ref_price` (10:00 bar open), `entry_fill`, `favourable_extreme_price`, `favourable_extreme_ts`, `exit_fill`, `pnl_per_contract`, `platform_fee_rt_usd` | L036, L037, L038, L039, L040 — all of A3, which is **entirely unfalsifiable post-seal today** | No |
| **EV-3** | `OpeningRangeFact` — one per trade-constructible day | `trade_date`, `or_high`, `or_low`, `n_obs_bars`, `anchor_stop`, `d_open` | L048, L050, L136 (E2 branch), L137 (E2 branch), L131 — **every E2 sizing figure**, whose anchor level reaches no sealed artifact because `planned_stop` is stored `None` for E2 | No |
| **EV-4** | `CostScenarioSnapshot` — one per cost scenario (4) | `name`, `spread_points`, `slippage_ticks_per_side`, `adverse_slippage_ticks`, `friction_multiplier`, `platform_fee_rt_usd`, plus the `spread_scalars` triple and the id of the reduction rule that produced it | L053, L054, L131, L137, and the *cost layer* of every USD leaf | Capture: no. Values: **DR-1** |
| **EV-5** | `DayStratumFact` — one per day (this is `build_day_strata`'s payload, which no production caller builds) | `trade_date`, `year`, `volatility_regime_label`, `vol_status`, `event_flag_final`, `event_stratum`, `tp_fp_class.<theta>` | L078, L079, L097, L103, L144 — the A8 replay and the A2b vol axis | Capture: no. **Vocabulary: DR-2 + DR-6** |
| **EV-6** | `GridPoolFact` — one per (theta, engine, scenario) | `tp_pools` and `fp_pools` as `stratum_key -> sorted date tuple`, `tp_avail`, `fp_avail`, and per `(q,r)` the `tp_alloc`/`fp_alloc` (the latter two are already in `per_seed`) | L097, L101, L103 — makes `default_rng([master, 9002, q_mil, r_mil])` **exactly replayable**, which is the one thing the current grid checks cannot do | Capture: no. Pool *contents*: **DR-2, DR-3, DR-6** |
| **EV-7** | `BootstrapInputFact` — one per `bootstrap_ci` cell key (32) | the ordered `(date, usd)` series digest (sha256 of a canonical serialization), `n`, `seeds`, `stats_stream_tag`, `block_stream_key`, `n_boot`, `ci_level`, `percentile_method_id` | L082, L085 — lets a replay prove it consumed the same series, which today is unprovable | Capture: no. Series definition: **DR-4.1/4.2** |
| **EV-8** | `NAObservationFact` — a **second, structurally different** NA observation | per column, a raw null count taken from `features_table`/`labels_table` (a different code path from `DayRecord.*_na_reasons`), plus the observation method id | L113–L117 — makes `runinfra.check_na_conservation`'s "independently observed total" actually independent | No |
| **EV-9** | `FunnelFact` — the funnel as membership, not counts | the L0..L4 **date tuples** already held on `context.EligibilityFunnel` (`scheduled`/`observed_rth`/`regular`/`structurally_eligible`/`final_dates`) plus `exclusion_reason` per excluded date | L001 — turns the funnel from an externally-anchored count into a re-derivable set chain | No |
| **EV-10** | `F10MembershipFact` | per date: the raw category **set** and the final exclusive category | L002, L003 — L003 currently has **no verifier at all** | No (IR-12/13/18 already ruled) |
| **EV-11** | `LabelAvailabilityFact` | per date, per label: the five dependency booleans (`o1000`, `c1544`, `pm_ok`, `adr_ok`, `dir_ok`) already computed inside `_label_anchor_availability` | L012, and the label half of L007 | No (IR-23 ruled) |
| **EV-12** | `EstimatorIdentityFact` | the actual estimator string used at compute time by each of `study.PERCENTILE_METHOD`, `stability.PERCENTILE_METHOD`, `stats.PERCENTILE_METHOD`, bound into the payload and cross-asserted against `e2_worst_days.estimator_status` | L032, L042, L045 — closes packet P-6 / blind-audit G1-G2 | Value: **DR-8**. The *binding* is unblocked |
| **EV-13** | `FrozenHashObservationFact` | the `verify_frozen_hashes()` re-hash **result** (path -> freshly computed digest + read timestamp) carried from the Stage-A gate into the governance block | L127 — replaces a tautological equality with a byte-anchored one | No |

## S3. Leaves whose reducer needs a research ruling (`DECISION_REQUIRED`)

Leaf sets below are the **exact** rows whose `research_definition_dependency` column names that DR (grep-verified against this document, not hand-listed).

| DR id | short name | n | leaves gated | blast radius note |
|---|---|---|---|---|
| **DR-1 (DR-M6-A-v2 + IR-7)** | spread reduction rule + adverse-slip vector | 18 | L026, L027, L028, L030, L036, L037, L038, L040, L051, L052, L053, L054, L055, L102, L123, L131, L132, L137 | **Largest radius in the report.** Because `spread_scalars` and `adverse_slippage_ticks` are unruled and `_approved_injectables()` returns `None`, *every USD figure in the sealed report* has an unruled input at the cost layer — including the AF2 atom itself (L132). Nothing can be numerically final before this lands. |
| **DR-2 (DR-M6-B-v2)** | 20-day realized volatility + tercile axis | 8 | L078, L079, L080, L090, L097, L103, L144, L145 | Feeds **two** consumers with one definition: the §2 stability vol axis and the App-A stratification key. Sealing already fail-closes via `vol_axis_unresolved`. |
| **DR-3 (DR-M6-C)** | FP allocation basis (A / B / C) | 4 | L090, L095, L097, L103 | Registered `unresolved_disagreement` (Fable=B, Sol=A). Changes the D_FP mixture composition and therefore the grid EV region shape. |
| **DR-4 (DR-M6-D, items 4.1–4.7)** | bootstrap population / NA-day rule / statistic / 10k attribution / quoted seed / percentile interpolation / CRN scope | 9 | L081, L082, L083, L086, L087, L088, L122, L142, L143 | The **entire A7 section**. Note L081's statistic definition (4.3) also determines whether `bootstrap_ci…mean` and `oracle_daily…mean_usd` are even the same quantity (see CR-2). |
| **DR-5 (DR-M6-E)** | grid K-repeat and convergence policy | 5 | L085, L090, L141, L143, L145 | Blocks `GRID_SAMPLES` from ever reaching `REPLAY_STATUS_CLOSED`. |
| **DR-6 (DR-M6-F)** | event-NA -> App-A stratum mapping | 4 | L097, L103, L144, L145 | `event_stratum` is unconditionally `"UNRESOLVED_DR-M6-F"`, so `DAY_STRATA` can never be sealable. The producer-side blocker in `build_full_study_result._event_stratum` already raises. |
| **DR-7 (DR-M6-G)** | stability-view population (D_TP-conditional vs full eligible) | 8 | L071, L072, L073, L074, L075, L076, L077, L144 | Every A2b number is computed on a population whose definition is unruled. **Not currently fail-closed** — A2b seals with the D_TP-conditional reading silently adopted. This is the one DECISION_REQUIRED family that does *not* block sealing today. |
| **DR-8 (DR-M6-H)** | E2 worst-day P1/P5 sample-quantile estimator | 14 | L029, L030, L032, L033, L039, L040, L042, L043, L044, L045, L072, L074, L075, L077 | Sealing already fail-closes via `worst_day_estimator_unresolved`. Note the estimator is instantiated in **three** independent module constants (CR-5); a ruling must bind all three (EV-12). |
| **all 8** | — | 1 | L120 (`pending_method_decisions`) | Non-empty -> Stage E refuses to seal. This single leaf is what makes every other DR fail-closed. |

89 of the 148 leaf rows carry `research_definition_dependency = NONE`; the remaining 59 name at least one DR (rows appear under more than one DR where more than one applies — e.g. L097 under DR-2, DR-3 and DR-6).

## S4. Consistency risks — two leaves claiming the same atom via DIFFERENT reducers

| id | atom | competing reducers | why it matters |
|---|---|---|---|
| **CR-1** | `ds.na_table` per-field NA counts | (a) `structural.na_table` (direct copy), (b) `stage_c_result` -> `reported_total_na` -> `_na_conservation_block`, (c) `runinfra.check_na_conservation` itemized sums, (d) VF-8's re-sum, (e) VF-11(d)'s re-sum by table prefix | **All five trace to one preimage.** Four "independent" recomputes verify a single producer output against itself. `check_na_conservation`'s docstring calls `reported_total_na` "independently observed"; at this HEAD it is not. Needs EV-8. |
| **CR-2** | the sample mean of the D_TP series | (a) `study._series_block`: `sum(vals)/len(vals)`; (b) `stability._cell`: `sum(vals)/n`; (c) `stats._bootstrap_mean_ci_unchecked`: `numpy.ndarray.mean()` (pairwise summation) | Three implementations, three float accumulation orders. `oracle_daily…pooled.mean_usd` and `bootstrap_ci…per_seed.mean` are the same statistic over the same series and are **never compared**; a divergence at the 1e-12 level would be invisible, and a divergence at any level would be too. |
| **CR-3** | the θ partition size | (a) `oracle_daily.<t>.day_universe.n_tp/.n_fp` (from `study._partition`); (b) `feasibility_grid.cells.<t\|e\|s>.n_tp_available/.n_fp_available` (from `len(tp_pnl)` in `_build_grid_unchecked`); (c) `sizing_outputs.<t>.coverage.<e>.<s>.n_trades` (from `len(rows)`); (d) `mc_handoff_manifest.counts.<e>.<s>.n_records` (= n_tp + n_fp) | Four leaves, four reducers, **one identity**. Only (a)↔(d) is asserted (VF-9) and only (a)↔`len(rows)` is asserted (VF-4). (b) and (c) float free — and (b) is the basis VF-7 trusts for `n_tp_target`. |
| **CR-4** | the frozen §2 epoch boundaries | (a) `stability.EPOCHS` (int ranges, inclusive); (b) `dataset.STABILITY_EPOCHS` (string ranges, **half-open**); (c) `report._RECONCILE_EPOCH_RANGES` (deliberately duplicated as data, per its own comment); (d) `handoff._epoch_for_year` (reads `stability.EPOCHS`) | **Four** implementations of one frozen definition; (b) uses a different interval convention from (a)/(c). They agree today only because the boundaries are contiguous integer years. `structural.groups.stability_epochs` (b) and `stability_views…epochs` (a) are never cross-checked. |
| **CR-5** | P1/P5 percentile estimator | (a) `study.PERCENTILE_METHOD` + `study._percentile`; (b) `stability.PERCENTILE_METHOD` + `stability._percentile`; (c) `stats.PERCENTILE_METHOD` + `stats.percentile_ci` | Three separate `"linear"` constants and two identical `_percentile` bodies. `stability.py`'s docstring says it reuses study.py's "verbatim" — by copy, not by import. A DR-8 ruling applied to one is silently not applied to the others. |
| **CR-6** | the E2 worst-day P1/P5 values | (a) `executable[E2][scn]["worst_day_report"]["pooled"]` (L033); (b) `e2_worst_days.<t>.<scn>.pooled` (L043) — a dict spread of (a); (c) `executable[E2][scn]["pooled"]["worst_day_pnl_percentiles"]` (L029) — the source of (a) | The same two numbers appear at **three** payload paths. `validate_formal_payload` checks P1<=P5 at each independently and **never checks that the three agree**. A tamper on one path is invisible. |
| **CR-7** | the sealed trade-date universe | (a) `render_s0_report` computes `univ` from `formal["oracle_daily"][t]["day_universe"]`; (b) `validate_sealed_files` derives the identical set from `payload["oracle_daily"]` when `trade_date_universe is None` | The renderer passes `trade_date_universe=univ`, which **overrides** (b). The validator's own derivation path is dead in production, so what looks like two derivations is one. |
| **CR-8** | the grid per-seed selection | (a) `tp_dates` + `fp_dates`; (b) `day_markers` (a sorted re-encoding of the same selection); (c) `n_tp_actual`/`n_fp_actual`; (d) point-level `F_expected` vs per-seed `F_expected` | VF-7 checks (a)↔(c). Nothing checks (a)↔(b), and nothing checks the point-level vs seed-level `F_expected`. `day_markers` is the field MC actually consumes (frozen App A step 4). |
| **CR-9** | the RNG stream tags | (a) `stats.STATS_STREAM_TAG` / `gridmix.GRID_STREAM_TAG` (module constants); (b) `SEED_MANIFEST.stream_tags` (rebuilt from (a) and **verified** by VF-12); (c) `disclosures.method_conventions.stream_tags` — a **hand-written prose string** `"stats 9001 / gridmix 9002"` | (b) is verified; (c) is a hardcoded duplicate of the same numbers with no rebuild and no check. A tag change would update (a)/(b) and silently desynchronize the formal report's own disclosure. |
| **CR-10** | canonical JSON serialization | (a) `report.to_formal_json` (`_clean` walk + `_StrictEncoder`, `indent=1`); (b) `handoff.dumps_canonical` (`allow_nan=False, sort_keys=True`, no indent); (c) the inline `json.dumps(record_to_formal_dict(r), sort_keys=True, allow_nan=False)` in `render_s0_report` | Three serializers write into one sealed set. Only (a) rejects non-str dict keys and non-finite floats via an explicit pre-walk. `handoff.py`'s docstring acknowledges the duplication and defers unification to the main agent; it is still open. |
| **CR-11** | `theta_key` formatting | (a) `study.theta_key`; (b) `handoff._theta_key` (duplicated "by convention", per its own docstring) | A `:g` format drift between them was an actual live defect class in the M6.1.3 evidence matrix (D6a). |
| **CR-12** | `risk_usd_per_1_MNQ_planned` vs `minimum_1_contract_risk` | both are `float(rec.sizing_anchor_usd)` in `_sizing_row` | Two leaves, one value, **identity never asserted**. A tamper on either is invisible. |

## S5. What this matrix says about RC-1 and RC-2 (the M6.1.3 blockers)

**RC-1 guise checklist from `CODEX_REVIEW_PACKET_M6_1_3.md` §2 P-1 — every guise appears above with an honest status:**

| packet guise | matrix rows | status here |
|---|---|---|
| F2 / C4 / C5 — record values vs report | L026, L027, L132 | PARTIAL — VF-11 touches AF2 by **count only** (VF-11(c)); no record VALUE is ever read by any verifier |
| F1 — formal + `d_tp` fully synchronized | L025–L030, L071–L077 | PARTIAL — VF-11(a)/(b) anchor on `study[...]["d_tp"]`, which is itself producer output |
| B8 — JSONL + both hashes co-modified | L108, L109, L129–L138 | PARTIAL — VF-10 verifies bytes↔manifest, but nothing verifies bytes↔`d_tp`↔report values |
| A34 / A46-A51 — grid recompute anchored on its own dates and `n_tp_available` | L089, L092, L093, L098, L099 | PARTIAL — CR-3 names the unchecked cross-section identity |
| A54 / G6 — `F_expected` recompute reads the payload's own `p` | L068, L094 | PARTIAL — L068 is an unverified leaf acting as another leaf's verification anchor |
| A29 / C14 — bootstrap mean only peer-checked across seeds | L081 | DECISION_REQUIRED (DR-4) + CR-2 |
| G3 / G4 / G5 — `vol_terciles` / `theoretical_oracle` / `sizing_outputs` have no internal counterpart | L078–L080, L036–L040, L046–L061 | DECISION_REQUIRED / PARTIAL — VF-11's scope excludes all three by construction |

**RC-2:** `formal_seal_admission` recomputes **semantics** for exactly one field family (L139/L140 — seeds and stream tags, VF-12) and **schema only** for everything else. The day_strata and grid_samples content validators exist and are effective against fabricated artifacts, but they have no producer to guard (L144/L145 are NOT PRODUCED), so RC-2's live surface today is the SEED_MANIFEST path alone.

## S6. Architecturally impossible without a research ruling

Three items in the B0 mandate cannot be closed by engineering alone. They are recorded here so S1 is not graded against an impossible target:

1. **A2b `stability_views` cannot be made "correct" — only reproducible.** Its entire numeric content is conditional on DR-7's unruled population choice. An S1 reducer can make every cell re-derivable from atoms; it cannot make the cells *right* until DR-7 lands. Note also that DR-7 is the **only** DECISION_REQUIRED family that does not currently fail closed — A2b seals today with the D_TP-conditional reading silently adopted.
2. **A8's per-seed selection ledger cannot be made replayable while DR-2, DR-3 and DR-6 pend.** EV-5/EV-6 make the *capture* possible immediately, but the stratum key is `(year, volatility_regime, event_flag)`, and two of those three axes have no defined vocabulary. Capturing an UNRESOLVED-labelled stratum key does not yield a replayable pool — it yields a reproducible record of an undefined partition. S1 should capture it anyway (it is strictly better than today) but must not describe the result as closing RC-1 for A8.
3. **Every USD figure in the report is provisional until DR-1.** `_approved_injectables()` returns `None`, so no `StudyConfig` can be derived and the real chain is fail-closed pre-exposure. A canonical-evidence architecture can make P&L re-derivable from `TradePathRecord` + `CostScenarioSnapshot`; it cannot make the cost model final. Any S1 claim of the form "all report numbers rebuild from atoms" must carry this caveat explicitly, or it will read as a claim that the cost layer is settled.

One further honest note, outside the mandate's three families but load-bearing for the seal: **`governance.frozen_hashes`, `governance.trial_id` and `governance.engineering_seed` are compared against themselves at the seal boundary** (§Table 13, L124/L126/L127). The real byte-level check (`guards.verify_frozen_hashes()`) runs at the Stage-A gate and its *result* is never carried into the sealed governance block. EV-13 closes this and requires no ruling.
