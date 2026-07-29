# S0 INPUT PREFLIGHT REPORT

- stage: `INPUT_PREFLIGHT_ONLY`
- real_s0: `NOT_RUN`
- approval: `AWAITING_AARON_APPROVAL`
- input_commit: `d09ce4e4f0653a191ba035d5f90a7ec3316c864f`
- integration_commit: `null` (filled by the main agent at integration)
- generated_at_utc: `2026-07-29T07:30:52.620675+00:00`

Input-eligibility verification only. This document contains counts, booleans, reason classifications and status fields exclusively. No feature value, no distribution, no label value, no cost figure, no simulation output and no judgment appears anywhere in it, by construction and by machine-checked guard (tests/test_preflight.py).

Read path: `DevelopmentSignalLoader.load_real` over 139 archived A1 files. Development window [2010-06-06, 2022-01-01). Loader QA events: none.

## 0. Startup preconditions

- Development end-exclusive boundary is 2022-01-01: **True**
- frozen event table sha256 matches the IR-17 approved bytes: **True** (`5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c`, 468 rows)
- naming note: ROLE_WINDOWS[DataRole.DEVELOPMENT_SIGNAL] — the task spec called it DEV_END_EXCLUSIVE; that name lives in dbn_loader.py which derives it from this map

## 1. Date eligibility funnel

Order per the 2026-07-29 errata. Each level is conserved (parent = child + removed) and all removed sets are mutually disjoint, so no date can vanish unaccounted for.

| stage | operation | count |
|---|---|---|
| L0 | scheduled trading days | 2989 |
| -- | minus zero-bar days | 20 |
| L1 | observed RTH days | 2969 |
| -- | minus scheduled early-close days | 85 |
| L2 | regular full-session candidates | 2884 |
| -- | minus RTH missing > 10% days | 2 |
| L3 | structurally eligible days | 2882 |
| -- | minus ADR14 warm-up | 14 |
| **L4** | **final feature-construction dates** | **2868** |

Final range: 2010-06-25 .. 2021-12-31.

Side diagnostic (NOT a funnel deduction stage; also the lookback basis for the ADR14 warm-up test): complete 390-bar RTH days = 2870.

Conservation checks:

- `L0_minus_zero_bar_equals_L1`: **True**
- `L1_minus_early_close_equals_L2`: **True**
- `L2_minus_missing_gt_10pct_equals_L3`: **True**
- `L3_minus_adr14_warmup_equals_L4`: **True**
- `removed_sets_mutually_disjoint`: **True**
- `no_date_vanishes_unaccounted`: **True**
- `no_rth_bars_on_unscheduled_days`: **True**

Removed — RTH missing > 10%: 2020-02-28, 2020-06-30.
Removed — ADR14 warm-up: 2010-06-07 .. 2010-06-24 (14 days).

## 2. Exact anchors

Population = L3 structurally eligible days. No forward fill, no next-bar substitution, no interpolation, no last-trade substitution, no implicit completion of any kind was applied (IR-15).

| anchor | available | missing | missing reasons | downstream |
|---|---|---|---|---|
| O0930 | 2882 | 0 | - | `field_na_day_retained` |
| C0959 | 2882 | 0 | - | `field_na_day_retained` |
| O1000 | 2882 | 0 | - | `field_na_day_retained` |
| C1544 | 2882 | 0 | - | `field_na_day_retained` |
| prev_rth_close | 2809 | 73 | no_prior_rth_day_in_sample=1, prev_day_scheduled_early_close_no_1559_bar=70, prev_day_1559_bar_absent=2 | `field_na_day_retained_pending_D7` |

- prev_rth_close missing on: 2010-06-07, 2010-07-06, 2010-09-07, 2010-11-29, 2011-01-18, 2011-02-22, 2011-05-31, 2011-07-05, 2011-09-06, 2011-11-28, 2012-01-17, 2012-02-21, 2012-05-29, 2012-07-05, 2012-09-04, 2012-11-26, 2012-12-26, 2013-07-05, 2013-12-02, 2013-12-26, 2014-05-27, 2014-07-07, 2014-09-02, 2014-12-01, 2014-12-26, 2015-01-20, 2015-02-17, 2015-05-26, 2015-07-06, 2015-09-08, 2015-11-30, 2015-12-28, 2016-01-19, 2016-02-16, 2016-05-31, 2016-07-05, 2016-09-06, 2016-11-28, 2017-01-17, 2017-02-21, 2017-05-30, 2017-07-05, 2017-09-05, 2017-11-27, 2018-01-16, 2018-02-20, 2018-05-29, 2018-07-05, 2018-09-04, 2018-11-26, 2018-12-26, 2019-01-22, 2019-02-19, 2019-05-28, 2019-07-05, 2019-09-03, 2019-12-02, 2019-12-26, 2020-01-21, 2020-02-18, 2020-03-02, 2020-05-26, 2020-07-01, 2020-07-06, 2020-09-08, 2020-11-30, 2020-12-28, 2021-01-19, 2021-02-16, 2021-06-01, 2021-07-06, 2021-09-07, 2021-11-29

Downstream handling follows frozen L44-L45 only: a missing exact anchor makes the dependent field NA and the day is retained. The prior-day close anchor is flagged `pending_D7` because L45 does not sub-classify anchor-NA days; no substitute bar was selected and no degradation rule was invented. See DECISION_PACKET_PREFLIGHT_D7_PREV_RTH_CLOSE.md.

### Frozen L82 no-direction days: 26

ret_open30 == 0 exactly: frozen L82 requires these be counted and reported separately as no-direction, non-tradeable days. The day is NOT deleted.

Dates: 2011-02-18, 2011-05-16, 2011-05-19, 2011-06-16, 2011-07-05, 2012-02-24, 2012-03-09, 2012-04-02, 2012-09-21, 2012-10-05, 2012-10-08, 2012-12-26, 2013-04-12, 2013-06-26, 2013-09-11, 2013-11-01, 2014-01-03, 2014-04-28, 2014-06-23, 2014-07-23, 2015-02-23, 2015-11-03, 2016-03-31, 2017-05-12, 2020-10-06, 2021-07-15

NA reason precedence:

- reasons are assigned by FIRST match in the documented order per feature; a day can satisfy several (e.g. an ADR14 warm-up day that is also a roll transition is counted once, under the earlier test), so reason counts sum to the NA total exactly
- F5 order: roll_transition_day_na, anchor_missing, prev_rth_close_anchor_missing, adr14_warmup

## 3. Non-critical missing minutes (IR-15)

- days excluded BEFORE this layer by the frozen > 10% rule: 2020-02-28, 2020-06-30 (not counted as retained path-feature days)
- opening path (09:30-10:00) affected days: 3 — 2020-03-09, 2020-03-12, 2020-03-16
- PM path (10:00-15:44) affected days: 9 — 2010-09-10, 2010-12-23, 2010-12-28, 2010-12-29, 2010-12-30, 2012-03-09, 2012-03-12, 2013-12-13, 2020-03-18

## 4. F1-F11 constructibility

Features were computed in memory solely to classify constructibility, NA status, NA reason and constancy. No value is reported.

| feature | constructible days | NA days | is_constant | NA reasons |
|---|---|---|---|---|
| F1 | 2868 | 14 | False | adr14_warmup=14 |
| F2 | 2868 | 14 | False | adr14_warmup=14 |
| F3 | 2882 | 0 | False | - |
| F4 | 2823 | 59 | False | f4_lookback_warmup=59 |
| F5 | 2750 | 132 | False | prev_rth_close_anchor_missing=73, adr14_warmup=12, roll_transition_day_na=47 |
| F6 | 2881 | 1 | False | overnight_window_empty=1 |
| F7 | 2868 | 14 | False | overnight_window_empty=1, adr14_warmup=13 |
| F8 | 2856 | 26 | False | zero_denominator_no_direction=26 |
| F9 | 2882 | 0 | False | - |
| F10 | 2873 | 9 | False | multi_event_day_single_category_undetermined=9 |
| F11 | 2882 | 0 | False | - |

### F4 lookback basis (disclosed rule)

- rule used: prior 60 OBSERVED RTH trading days that have a complete 30-bar 09:30-10:00 window, strictly preceding the day, scheduled early-close days included (their morning window is a normal one)
- the frozen text fixes: the LENGTH (60 trading days) and the window
- the frozen text does NOT fix: which day-set counts as the 60
- NA days under this rule: 59
- **OPEN ITEM**: affects only the F4 NA count at the start of the sample; no day is deleted. See DECISION_PACKET_PREFLIGHT_F4_LOOKBACK_BASIS.md

### F10 event coverage

- encoding: IR-13 category membership, then IR-12 multi-event -> NA
- category day counts: {'CPI': 139, 'NFP': 138, 'FOMC_scheduled_statement_days': 92}
- intersection with eligible days: {'CPI': 137, 'NFP': 134, 'FOMC': 92, 'none': 2528}
- FOMC statement rows in the frozen table: 96; minus the four IR-13 `unscheduled_fomc_action` diagnostic dates (2019-10-11, 2020-03-03, 2020-03-15, 2020-03-23) = 92 scheduled statement days
- multi-event NA days after IR-13: 9 — 2013-10-30, 2014-09-17, 2014-12-17, 2016-03-16, 2017-03-15, 2017-06-14, 2017-12-13, 2019-12-11, 2020-06-10
- diagnostic sidecar, raw multi-event days before IR-13: 19 — 2010-10-15, 2013-06-18, 2013-09-17, 2013-10-30, 2013-12-17, 2014-03-18, 2014-06-17, 2014-09-17, 2014-12-17, 2015-09-16, 2015-12-15, 2016-03-16, 2017-03-15, 2017-06-14, 2017-12-13, 2018-06-12, 2019-10-04, 2019-12-11, 2020-06-10
- **OPEN ITEM**: IR-12 cites 19 multi-event days (raw table); after IR-13 narrows FOMC to scheduled statement days only 9 remain multi-category. See DECISION_PACKET_PREFLIGHT_F10_MULTIEVENT_SCOPE.md
- IR-17 rows carrying no official release time: 45 (date-level encoding unaffected; no day deleted, F10 not made NA by this)
- years with no matching event in the Development window: none

| year | CPI | NFP | FOMC rows (all calendar entries) | FOMC scheduled statement days (F10) |
|---|---|---|---|---|
| 2010 | 7 | 6 | 8 | 5 |
| 2011 | 12 | 12 | 15 | 8 |
| 2012 | 12 | 12 | 15 | 8 |
| 2013 | 12 | 12 | 17 | 8 |
| 2014 | 12 | 12 | 17 | 8 |
| 2015 | 12 | 12 | 16 | 8 |
| 2016 | 12 | 12 | 16 | 8 |
| 2017 | 12 | 12 | 16 | 8 |
| 2018 | 12 | 12 | 16 | 8 |
| 2019 | 12 | 12 | 18 | 8 |
| 2020 | 12 | 12 | 21 | 7 |
| 2021 | 12 | 12 | 16 | 8 |

The `FOMC rows` column counts every official calendar entry (a two-day meeting contributes 2 rows, conference calls and notation votes are included as archived); only the last column feeds F10 under IR-13.

### F11 / F5 roll session-date semantics

- source: gate1/symbology/nq_v0_mapping.csv (IR-16, 48 intervals)
- semantics: transition instant 00:00 UTC = prior-evening ET pre-open; mapped to the first valid RTH session date on/after the official interval start
- transitions: 47 (DATA_QA_ADDENDUM section 8 cross-check 47: True)
- `n_transitions_is_47`: **True**
- `all_map_to_valid_rth_trading_day`: **True**
- `no_weekend_transition`: **True**
- `all_inside_official_interval`: **True**
- `distinct_transition_dates`: **True**
- is_roll_transition days inside the eligible set: 47
- is_roll_window days: 235 (inside eligible set: 235)

## 5. Label anchors (existence only)

| label | required anchors | days with all anchors | days missing >=1 |
|---|---|---|---|
| Y_cont | O1000, C1544, ADR14, d_open(O0930,C0959) | 2842 | 40 |
| Y1 | O1000, C1544, ADR14 | 2868 | 14 |
| Y2 | O1000, C1544, PM close path | 2882 | 0 |
| Y3 | C1544, PM high, PM low | 2882 | 0 |
| Y4 | O1000, PM high, PM low, ADR14, d_open(O0930,C0959) | 2842 | 40 |
| Y5 | O1000, PM high, PM low, ADR14, d_open(O0930,C0959) | 2842 | 40 |

No label value, distribution, mean, frequency or any forward-looking statistic was computed.

## 6. Cross-check vs DATA_QA_ADDENDUM.md

| item | preflight | addendum | match |
|---|---|---|---|
| scheduled trading days | 2989 | 2989 | True |
| scheduled early closes | 97 | 97 | True |
| observed RTH days | 2969 | 2969 | True |
| zero-bar scheduled days | 20 | 20 | True |
| 0930-1000 complete days | 2960 | 2960 | True |
| 1000-1544 complete days | 2873 | 2873 | True |
| 1000-1544 early-close excluded | 85 | 85 | True |
| complete 390-bar RTH days | 2870 | 2870 | True |
| ADR14 warm-up days | 14 | 14 | True |
| roll transitions | 47 | 47 | True |

**All items match: True**

## 7. Status

- `INPUT_PREFLIGHT_ONLY`
- `REAL_S0_NOT_RUN`
- `AWAITING_AARON_APPROVAL`

Real S0 was not run. No strategy figure of any kind was produced.
