# DECISION_LOG — nq-letf-rebalancing-research (R2)

Append-only (workflow v2 §6). One row per grant, consumption, seal, reveal, verdict,
disposition, methodology change or delegate/Owner decision. Rows are added when the event
happens and never reconstructed from a later state: an instant that cannot be established
is `UNKNOWN`. Rows are never edited; a correction is a new row citing the one it corrects.
Anything binding that arrives by message is copied verbatim into §2 before it is acted on.

Started 2026-10-01 at checkpoint CP-R2-V2-01. Rows 1–7 record events that happened before
this log existed; their evidence is the file named, as preserved in the baseline commit
`bd66324`.

## 1. Log

| id | UTC | decider | decision | evidence pointer |
|---|---|---|---|---|
| OD-1 | UNKNOWN (record created 2026-09-20) | Aaron (delegated) / Fable (decided) / ChatGPT (accepted) | `GRANT_EXISTING_NQ_DEVELOPMENT` — new R2 lineage-specific grant over the local NQ Development archive, 2010-06-06 → 2022-01-01 exclusive; granted, not exercised | `R2_DELEGATED_OWNER_DECISIONS.md` §1 |
| OD-2 | UNKNOWN (record created 2026-09-20) | Aaron (delegated) / Fable (decided) / ChatGPT (accepted) | `NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY` — QLD, QID, PSQ, TQQQ, SQQQ; generic momentum substitute FORBIDDEN | `R2_DELEGATED_OWNER_DECISIONS.md` §2 |
| OD-5 | UNKNOWN (record created 2026-09-20) | Aaron (delegated) / Fable (decided) / ChatGPT (accepted) | `PATH_A_TRUE_PIT_DAILY`; PATH_C = PARK fallback, evidentiary trigger | `R2_DELEGATED_OWNER_DECISIONS.md` §3, §5 |
| OD-6 | UNKNOWN (record created 2026-09-20) | Aaron (delegated) / Fable (decided) / ChatGPT (accepted) | `PROVEN_PUBLICATION_ONLY_ZERO_CARRY` — ten binding rules | `R2_DELEGATED_OWNER_DECISIONS.md` §4 |
| VW1 | authorization: UNKNOWN · dispatch: 2026-09-21T11:25Z (ETF Global), 11:26Z (Morningstar), 11:27Z (ProShares / ProFunds, FactSet), 12:16:08Z (LSEG / Lipper form), 12:16:54Z (Bloomberg form) | Aaron | Vendor Wave-1 authorized and dispatched: 6/6 sent, each exactly once; no purchase, trial, contract or follow-up authorized | `R2_VENDOR_RESPONSE_TRACKER.md` §1, §6; `vendor_outbound/`. Note: `R2_VENDOR_WAVE1_DISPATCH.md` header still reads `NOT SENT. NOT AUTHORIZED TO SEND.` as of its 2026-09-20 creation; not edited |
| FPC | authorization: UNKNOWN · scheduling: UNKNOWN (task first installed 2026-09-20 +08:00; re-registered password-backed 2026-09-21, live export file time 2026-09-21T11:00:42Z) | Aaron | Forward PIT collection authorized, built and scheduled (`QuantTrade-R2-ForwardPIT`, daily 11:00 +08:00); standing; collects forward dates only, assigns no sample tier | `R2_FORWARD_PIT_COLLECTION.md` header, §6, §2026-10-01 section; `ops/R2_FORWARD_PIT_TASK.xml` |
| WF-V2 | UNKNOWN (activated 2026-09-26) | Aaron | Workflow v2 (`QUANT_WORKFLOW_VNEXT.md`) applies to R2 from 2026-09-26; no retroactivity | `../QUANT_WORKFLOW_VNEXT.md` header |
| D-R2-2026-10-01-01 | 2026-09-30T19:30Z | Fable 5.1 delegate session, 2026-10-01 | Label correction under OD-6: `HISTORICAL_DAILY_PIT_SAFE_START = NOT_ESTABLISHED`; "safe period" lines withdrawn from `PROJECT_STATE.md` — verbatim in §2.1 | `handoffs/2026-10-01_FABLE_DELEGATE_RECONCILIATION.md` §3; `R2_G3_HISTORICAL_PIT_AMENDMENT.md` (correction 2026-10-01) |
| G-R2-2026-10-01-PUSH | received ≈2026-09-30T19:35Z (builder clock read 19:35:08Z at the tool result it arrived with) | Fable 5.1 delegate session (message) — push itself is Owner-retained | `G-R2-2026-10-01-PUSH = NOT_YET_GRANTED (repository not created)`. The builder prompt's Owner grant block reached this session with `VISIBILITY` and condition (3) unfilled; the delegate's amendment defers the remote and push. No remote, no push — verbatim in §2.2 | this file §2.2 |
| D-R2-2026-10-01-02 | stated by sender: 2026-09-30T19:50Z · received before 2026-09-30T19:41:42Z (builder clock) | Fable 5.1 delegate session, 2026-10-01 | One-shot for CP-R2-V2-01: X1 scan result accepted as expected (with name-withholding additions); X2 capture-origin rule adopted; X3 recorded as BL-R2-01 — verbatim in §2.3 | this file §2.3 |
| BL-R2-01 | 2026-10-01 (recorded; builder clock 2026-09-30T19:41Z) | builder (backlog row, under D-R2-2026-10-01-02) | Installer one-shot marker written with a UTF-8 BOM (Windows PowerShell 5.1 `Set-Content -Encoding utf8`) → wrapper `json.loads` fails → marker deleted → default label. Effect limited to the `capture_type` label of a re-install validation run; `2026-09-21/070042_ET` manifest immutable and not relabelled; no research impact. Fix (read with `utf-8-sig`, with a test) is an `IMPLEMENTATION_FIX` for a later separate commit after CP-R2-V2-01 is accepted | `R2_FORWARD_PIT_COLLECTION.md` §2026-10-01; `tools/run_forward_pit_scheduled.py` `consume_capture_type_once`; `tools/install_forward_pit_task.ps1` marker block |
| OWNER-R2-2026-10-01 | ≈2026-09-30T19:50Z (received in the builder session; builder clock read 19:50:01Z immediately after) | Aaron, directly in the builder session | Publication scope is decided by the Fable delegate; Aaron confirms: all of R2's `data_forward_pit/` and `data_probe/` committed; ITSF, R1 and R2 merged through a publication mirror into Aaron's existing public repository `AaroNLaU0307/Intraday-Trend-Strategy-Framework`; repository stays PUBLIC; university name and Morningstar case number removed from builder-authored files; the push is performed by Aaron himself — verbatim in §2.5 | this file §2.5 |
| D-R2-2026-10-01-02-S | stated by sender: 2026-09-30T19:55Z · received before 2026-09-30T19:45:25Z (builder clock) | Fable 5.1 delegate session, 2026-10-01 | Supplement to D-R2-2026-10-01-02, "Option 1": the reconciliation copy in `handoffs/` gets the same substitution treatment and note as the handoff copy — verbatim in §2.6 | this file §2.6 |
| D-R2-2026-10-01-03a | stated by sender: 2026-09-30T20:20Z · received before 2026-09-30T19:50:01Z (builder clock) | Fable 5.1 delegate (session 'NDX leveraged-ETF rebalancing research handoff'), under OWNER-R2-2026-10-01 | `DATA_IN_REPO = ALL` — verbatim in §2.6 | this file §2.6 |
| D-R2-2026-10-01-03b | as 03a | as 03a | `PUBLICATION_TARGET` = public mirror of ITSF, R1 and R2 via git subtree; no remote, no push by the builder — verbatim in §2.6 | this file §2.6 |
| D-R2-2026-10-01-03c | as 03a | as 03a | `VISIBILITY = PUBLIC`; university name and case number withheld from builder-authored files; three bracketed substitutions in the `handoffs/` copies; hostname and Windows username remain — verbatim in §2.6. Applied: the tracker commit was rebuilt before any publication, so no reachable commit carries the two tokens | this file §2.6; `R2_VENDOR_RESPONSE_TRACKER.md`; `handoffs/` |
| D-R2-2026-10-01-03d | as 03a | as 03a | Sequence: CP-R2-V2-01 → delegate PASS → CP-MONO-01 → Aaron pushes → post-push reproduce recorded — verbatim in §2.6 | this file §2.6 |
| D-R2-2026-10-01-03e | as 03a | as 03a | Rigour audit after CP-MONO-01 is run by the delegate, read-only; the builder is the repair seat and does not start or pre-empt it — verbatim in §2.6 | this file §2.6 |
| G-R2-2026-10-01-PUSH-OWNER | ≈2026-09-30T19:50Z | Aaron, directly (OWNER-R2-2026-10-01) | The push to `https://github.com/AaroNLaU0307/Intraday-Trend-Strategy-Framework.git` is performed by Aaron himself. The builder holds no push grant; the earlier `G-R2-2026-10-01-PUSH = NOT_YET_GRANTED` row stays true for the builder | this file §2.5 |
| D-R2-2026-10-01-03d-A | received before 2026-09-30T19:53:16Z (builder clock); no UTC stated by sender | Fable 5.1 delegate session, 2026-10-01 (states: on Aaron's instruction that the audit may precede the upload) | Amends D-R2-2026-10-01-03d: the read-only rigour audit runs after CP-R2-V2-01 is accepted and BEFORE the mirror and the push; confirmed findings are repaired and accepted before CP-MONO-01 starts — verbatim in §2.7. The R1 record-correction lease it mentions is not taken up by this row | this file §2.7 |
| ACC-CP-R2-V2-01 | stated by sender: 2026-09-30T20:45Z (sender: stated UTCs are composed times; receipt bounds govern) · received after 2026-09-30T19:53:16Z (builder clock) | Fable 5.1 delegate session, 2026-10-01 | CP-R2-V2-01 **PASS** at `e11a1c9266a53b8c0c021b5081745941f098b4a2`. REPRODUCED by the delegate: clean tree; reproduce exit 0 (40 tests, 15/15 verified, NATURAL 9 incl. 2 catch-ups, MANUAL 6, 33 links); no change under data_forward_pit/, data_probe/, logs/, ops/ or collector/wrapper vs `bd66324`; university name and case number in 0 files over all revisions; PROJECT_STATE, G-3 correction, DECISION_LOG rows and handoffs/ notes present. Stale dispatch / collection headers and the missing 2026-09-20 firing record passed to the rigour audit (running against `e11a1c9`). No further R2 commits until findings arrive | delegate message (this row); commit `e11a1c9` |
| ACC-CP-AUDIT-01 / D-R2-2026-10-02-01 | stated by sender: 2026-10-01T18:30Z · received before 2026-10-01T17:51:53Z (builder clock) | Fable 5.1 delegate session, 2026-10-02 | CP-AUDIT-01 ACCEPTED (PASS); all 11 R1 and 14 R2 confirmed findings accepted at the reported severities; repair decisions R1-a…g and R2-a…i — verbatim in §2.8. The audit was run by a separate Claude Code session ("R1/R2 rigour audit checkpoint"), run IDs in `audits/2026-10-01_CP-AUDIT-01/2026-10-01_CP-AUDIT-01_RUN_IDS.md` | this file §2.8; `audits/2026-10-01_CP-AUDIT-01/` |
| AUD-PERSIST-01 | 2026-10-01T17:51Z (builder clock) | builder, under D-R2-2026-10-02-01 Step 0 | Reports, run-ID index and the three workflow scripts persisted byte-identical in `audits/2026-10-01_CP-AUDIT-01/` (sha256 table in its README; R2 report `7cc924d7…`, R1 report `d617e1da…`); panel JSON pinned by hash, not copied | `audits/2026-10-01_CP-AUDIT-01/README.md` |
| AUD-PROC-01 | as D-R2-2026-10-02-01 | Fable 5.1 delegate (in D-R2-2026-10-02-01) | Procedural: the OD-6 finder's `/tmp/x` write was outside the workspace; accepted with disclosure; nothing is invalidated | R2 report §1 Conditions, §7(a)1 |
| EXP-DISC-R2-01 | as D-R2-2026-10-02-01 | Fable 5.1 delegate (in D-R2-2026-10-02-01) | Exposure disclosure: during CP-AUDIT-01 an ITSF post-reveal summary value (ITSF S0-T001 exposure-ledger row, already revealed) entered one finder's context. It is ITSF's, unrelated to R2's target, and was not used. R2 `OUTCOME_EXPOSURE = NONE` is unchanged; no other action | R2 report §1 Conditions, §7(a)11 |
| FIX-R2-2026-10-02-01 | 2026-10-02 (commit time) | builder, IMPLEMENTATION_FIX under D-R2-2026-10-02-01 R2-a | One tools commit, in the decided order: (1) BL-R2-01 fixed — the wrapper reads the one-shot marker with `utf-8-sig`; new test writes the exact Windows PowerShell 5.1 bytes (BOM + JSON + CRLF) and fails without the fix; (2) then the NATURAL boundary is pinned in `tools/reproduce.py` to the literal 2026-09-21T11:00:00+08:00 of D-R2-2026-10-01-02; the task export is read only for a labelled WARN; regression tests show the counts do not depend on the export (R2-G06); (3) `reproduce.py` tolerates non-COMPLETED rows (counted as rows and per slot, never NATURAL) (R2-G05); (4) `tools/task_action.py:75` no longer needs Python 3.12; README states only the interpreters actually run (R2-critic-1). Counts unchanged: NATURAL 9, MANUAL 6. No methodology change; no installer re-run | the tools commit; `tools/test_reproduce.py`; `tools/test_run_forward_pit_scheduled.py` |
| COR-R2-BL01 | 2026-10-02 | builder, RECORD_CORRECTION under D-R2-2026-10-02-01 (R2-G07) | Restates BL-R2-01's impact (BL-R2-01 row unchanged): `capture_type` is a predicate of the D-R2-2026-10-01-02 NATURAL rule. `2026-09-21/070042_ET` is MANUAL only through the sole-invocation-per-slot clause. Until the fix, an installer validation run alone in its slot would have been counted NATURAL. Fixed in FIX-R2-2026-10-02-01 before any installer re-run | BL-R2-01; R2 report R2-G07 |
| BL-R2-02 | 2026-10-02 | builder, NON-BLOCKING BACKLOG under D-R2-2026-10-02-01 R2-a | R2-G04 (refuted): `--verify` and `reproduce.py` accept a snapshot whose files and both integrity files were rewritten consistently; only the git byte-diff catches it. Candidate: add-only history check and JSONL-anchor check in reproduce.py | R2 report §4 R2-G04, §7(a)9 |
| BL-R2-03 | 2026-10-02 | builder, NON-BLOCKING BACKLOG under D-R2-2026-10-02-01 R2-a | R2-G08 (refuted): one per-fund exception (e.g. CSV drift: bare-CR line endings, a stray quote) aborts the whole capture via the exit-4 COLLECTOR_ERROR path. Candidate: per-fund isolation in `collect()` | R2 report §4 R2-G08 |
| BL-R2-04 | 2026-10-02 | builder, NON-BLOCKING BACKLOG under D-R2-2026-10-02-01 R2-a | R2-G24 (refuted): 37 of 66 single-rule mutations survive the suite; every untested rule holds on all captured data. Candidate: targeted tests | R2 report §4 R2-G24 |
| BL-R2-05 | 2026-10-02 | builder, NON-BLOCKING BACKLOG under D-R2-2026-10-02-01 R2-a | Side observation (ii): `parse_csv_body`'s docstring "Never raises on malformed input" (`tools/collect_forward_pit.py:229`) is false for bare-CR line endings and fields over 131,072 characters; no captured body comes near either | R2 report §7(a)10(ii) |
| COR-R2-G14 | 2026-10-02 | Fable 5.1 delegate (D-R2-2026-10-02-01 R2-b); recorded by builder | Nasdaq Fund Network (SV-1 matrix row 18) is **REJECTED under R3**: its only documented Total Net Assets message is "As of TBD 2027", so history begins after the sample; the NFN spec bytes were never captured; no enquiry (no vendor contact is authorized, and NFN cannot cover 2010-2021). The hand-copied "six" plausible vendors were seven as of 2026-09-19 (NFN unasked; ProShares issuer archive omitted from SV-1 report §8); with NFN rejected, six remain, all enquired. `R2_PATH_C_PARK_TRIGGER = NO` unchanged | `R2_SV1_SOURCE_MATRIX.md` and `R2_SV1_SOURCE_VERIFICATION_REPORT.md`, corrections of record 2026-10-02 |
| COR-R2-G15 | 2026-10-02 | Fable 5.1 delegate (D-R2-2026-10-02-01 R2-c); recorded by builder | `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md` §2 governs VERIFIED_PARTIAL: R6 is assessed for every VERIFIED candidate; `2016_ACID_TEST = PASS` is required only for VERIFIED_FULL, or where the claimed PIT scope covers 2016-03-31 to 2016-04-05. Tracker §5 item 4 and the §2 legend corrected by dated note; dispatch §4 superseded by that note. RECORD_CORRECTION, not a methodology change | `R2_VENDOR_RESPONSE_TRACKER.md` §5 note 2026-10-02 |
| COR-R2-G02 | 2026-10-02 | Fable 5.1 delegate (D-R2-2026-10-02-01 R2-d); recorded by builder | Corrects the OD-1 narrative ("No file in that archive has been decoded or inspected by R2", `R2_DELEGATED_OWNER_DECISIONS.md` §1, not edited): R2's pre-grant reads of the NQ Development archive were **metadata only** — file listing and counts, job metadata, `condition.json` availability flags, manifest hashes (`R2_FEASIBILITY_REPORT.md` §14); no bar was decoded and no outcome touched. Ruled: disclosed metadata access, not outcome access and not a widening of the grant. `OUTCOME_EXPOSURE = NONE`, `NQ_DATA_DECODED = NO` and OD-1 "not exercised" stand. The data-source audit's "condition.json marks each date available" is withdrawn (ITSF `qa_addendum_a1.json`, same job: 3,604 available, 20 degraded) | `R2_DATA_SOURCE_AUDIT.md` correction of record 2026-10-02 C-2; `PROJECT_STATE.md` DATA_GRANT |
| COR-R2-G18 | 2026-10-02 | Fable 5.1 delegate (D-R2-2026-10-02-01 R2-f); recorded by builder | OD §5's "several PLAUSIBLE_UNVERIFIED candidates remain and none has been asked" (`R2_DELEGATED_OWNER_DECISIONS.md`, not edited) was true as of 2026-09-20 and is superseded by the Wave-1 dispatch (row VW1). `vendor_outbound/` holds the pre-send texts as prepared 2026-09-20, not the sent messages; the dispatch evidence is SELF-REPORTED in tracker §1. VW1's evidence pointer is read accordingly | tracker §1 note 2026-10-02; `README.md` artifact table |
| COR-R2-G13 | 2026-10-02 | builder, RECORD_CORRECTION under D-R2-2026-10-02-01 R2-h | The "≥ ~2.5 days" back-fill bound (OD-6 notes, SV-1 criteria R6, matrix, SV-1 report, timeline, G-3 amendment) overstates the captured evidence. Latest proven absence of the 04/01/2016 row: SSO retrieval 2016-04-04 00:19:39 ET (newest row 03/31; Last-Modified 2016-03-31 18:25:30 ET) — REPRODUCED from `data_probe/g3_historical_pit_2026-09-19/captures/20160404041939_headers.txt`. Proven lateness ≥ 2.25 days after the usual 18:25 ET batch clock (≥ 2.35 days after the close). Availability by the 09:30 ET open on 2016-04-04 is UNKNOWN. The 2011 writes were at 19:44:26-27 ET. TQQQ: one captured CSV (2018-09-29); the 2016-03-10 302 is uncaptured. The 15 / 13 / 2 tally stands. No eligibility or OD-5/OD-6 consequence; no level-1 record is edited | this row; R2 report §3 R2-G13 |
| COR-R2-G16 | 2026-10-02 | builder, RECORD_CORRECTION under D-R2-2026-10-02-01 R2-h | Cites VW1 (not edited). The Morningstar routing reply (2026-09-22T06:30:19Z) and free-trial application (06:37:41Z) were carried out under an authorization recorded only at `bd66324` (`PROJECT_STATE.md` FREE_TRIAL_AUTHORIZED / FOLLOWUP_AUTHORIZED lines; tracker §6) — decider, instant and scope UNKNOWN. VW1's "trial" and "follow-up" mean "paid trial" and "additional follow-up". No trial step is authorized now: `TRIAL_ACTIVATION_AUTHORIZED = NO` (tracker §6, PROJECT_STATE FLAGS) | tracker §6; `PROJECT_STATE.md` FLAGS |
| COR-R2-RECORDS | 2026-10-02 | builder, RECORD_CORRECTION under D-R2-2026-10-02-01 R2-e/g/h | Appended dated corrections, earlier text unedited: G-3 full-sample claims withdrawn in the feasibility report (AM-2, AM-6) and the data-source audit (A-1, B-1 body) (R2-G11); row-count erratum 20,616 → 23,616 with pointers (R2-G03); SV-1 count errors (R2-G20); 2026-09-20 slot labelled NO_FIRING_RECORD and two false collection-record sentences superseded (R2-G10, side observations i, iii); README caveats | the correction sections dated 2026-10-02 in `R2_FEASIBILITY_REPORT.md`, `R2_DATA_SOURCE_AUDIT.md`, `R2_G3_PUBLICATION_TIMING_REPORT.md`, `R2_SV1_SOURCE_MATRIX.md`, `R2_FORWARD_PIT_COLLECTION.md` |

## 2. Binding messages, verbatim

### 2.1 D-R2-2026-10-01-01 (copied verbatim from the reconciliation §3)

Sender: Fable 5.1 delegate session, 2026-10-01. UTC: 2026-09-30T19:30Z.

````
## 3. Delegate decision D-R2-2026-10-01-01 — label correction under OD-6

```
DECISION_ID  = D-R2-2026-10-01-01
DECIDER      = Fable 5.1 delegate (session named by Aaron for R2, 2026-10-01)
UTC          = 2026-09-30T19:30Z
SCOPE        = labels / causal-timing record only (delegated: scope and methodology
               changes, labels). Not a sample, universe, cost or hypothesis change.
ONE_SHOT     = yes (a record correction)
```

**Decision.** The causal-timing record in `PROJECT_STATE.md` is corrected to:

```
G3_HISTORICAL_STATUS             = PARTIAL                       (unchanged)
AUM_FIELD_OBSERVED_START         = 2014-03-26                    (fact; unchanged)
HISTORICAL_DAILY_PIT_SAFE_START  = NOT_ESTABLISHED
PRE_2014-03-26_PERIOD            = UNRESOLVED                    (unchanged)
FULL_SAMPLE_AUM_AVAILABLE_BY     = UNKNOWN                       (unchanged)
G11_STALENESS_PROBLEM            = MATERIAL                      (unchanged)
S1_TAU_CONSTRAINT                = tau > 09:30 ET on trading day t, applicable only to
                                   dates a verified source proves eligible under OD-6
                                   (mechanical constraint; tau is not chosen)
```

The lines `HISTORICAL_PIT_SAFE_START = 2014-03-26`, `SAFE_PERIOD_AUM_AVAILABLE_BY =
NEXT_TRADING_DAY_OPEN … TYPICAL, NOT GUARANTEED` and `EVIDENCE_LEVEL = B` are removed
from `PROJECT_STATE.md` as a "safe period" concept.

**Why.** OD-6 (`PROVEN_PUBLICATION_ONLY_ZERO_CARRY`, precedence level 1) makes
eligibility a per-date, per-fund, proven property: rule 1 "unproven availability =
ineligible", rule 5 "no neighbouring-date inference". A "safe start date" derived from the
first observed AUM-bearing artifact plus typical batch behaviour is exactly a
neighbouring-date inference, and the 2016-04-01 stall shows the typical behaviour fails
inside that period. The observation that the field exists from 2014-03-26 is a fact and is
kept; the label "PIT-safe" is not a fact OD-6 allows the project to assert without a
source. This agrees with Aaron's handoff §8 and does not reopen OD-5 or OD-6.

**What it does not do.** It does not delete or rewrite `R2_G3_HISTORICAL_PIT_AMENDMENT.md`
or any report; the builder appends a dated correction section there citing this decision.
It does not narrow or widen the sample window (unchanged: 2010-06-06 → 2022-01-01
exclusive). It creates no eligibility table (OD-6: the table needs a verified source).
````

### 2.2 Delegate amendment to CP-R2-V2-01 — push deferred (verbatim)

Sender: Fable 5.1 delegate session for R2 ("NDX leveraged-ETF rebalancing research
handoff"), cross-session message. Received ≈2026-09-30T19:35Z.

```
Delegate amendment to CP-R2-V2-01: the GitHub repository does not exist yet, so do NOT run `gh repo create`, add a remote, or push in this checkpoint. Everything else in the prompt stands.

From: Fable 5.1 delegate session for R2 (ListAgents name: "NDX leveraged-ETF rebalancing research handoff"). Aaron has asked builder and delegate to message each other directly from now on; he acts as Owner only for the Owner-retained gates.

Scope of this message (decision, standing for CP-R2-V2-01):
1. Tasks A–H of the prompt (baseline commit, decision log, forward-collection evidence, tracker, G-3 correction, PROJECT_STATE rewrite, tools/reproduce.py, README) — proceed to completion, commit locally.
2. Task §10 (remote + push) — DEFERRED. Aaron will create the repository himself and give the URL later. The push is Owner-retained: it happens only when Aaron runs the git commands himself or types the grant into your session in his own words. Nothing I relay counts as that grant. Record in DECISION_LOG.md: `G-R2-2026-10-01-PUSH = NOT_YET_GRANTED (repository not created)`.
3. README.md is a first-class deliverable because it is what the public repository shows first: mechanism in one paragraph, the distinctness constraint (sign(F_t) = sign(r_pre), generic momentum forbidden), current stage line, pre-S1 prohibitions condensed, the reproduce command, the corrected artifact table, and where authority lives. No results, no hypothesis.
4. Prepare the repository so that the push is one command for Aaron: branch `main`, clean tree, `tools/reproduce.py` exit 0 on HEAD, `.gitignore` as specified. Put the exact two commands (`git remote add origin <URL>` / `git push -u origin main`) in your checkpoint message with `<URL>` left as a placeholder.
5. The amended prompt file is at `..\Workspace Docs\handoffs\r2-letf-inbox-2026-10-01\OPUS_BUILDER_PROMPT_CP-R2-V2-01.md` (§10 rewritten to match this message). Copy the handoff and reconciliation files from that folder into the project's `handoffs/` as instructed in Task B.

When done, send the checkpoint message (format in prompt §11) to me by name at this session. I will reproduce from the repository at your HEAD commit and return PASS or HOLD with a named blocker. If any discrepancy beyond D1–D7 appears, or anything is ambiguous about write permission, stop at that point and message me rather than choosing.
```

### 2.3 D-R2-2026-10-01-02 (verbatim)

Sender: Fable 5.1 delegate session for R2, cross-session message. Stated UTC
2026-09-30T19:50Z; received before 2026-09-30T19:41:42Z by the builder clock (the stated
instant is later than receipt; recorded as sent).
Verbatim except one token: the university name is replaced by a bracketed placeholder under
OWNER-R2-2026-10-01 and D-R2-2026-10-01-03c (§2.5, §2.6).

```
Decisions on X1/X2/X3 — proceed with commit 1 unchanged; details below. Delegate D-R2-2026-10-01-02, one-shot for CP-R2-V2-01, UTC 2026-09-30T19:50Z. Log verbatim.

X1 — scan result accepted as expected. (a) The Owner-seat label "Aaron" is binding record text; untouched. (b) Windows profile path, local account name and hostname are machine identifiers, not credentials; they stay as they are in logs, XML and tools. Commit 1 proceeds byte-identical. Two additions for what Tasks B and D bring in:
  1. Task D (tracker): write "Morningstar Sales team" — do not write the Morningstar employee's first name anywhere you author.
  2. Task B (handoff copy in handoffs/): replace the employee's first name with "[Morningstar sales contact — name withheld by builder]" and state that single substitution in a two-line note at the top of the copy. That is the only departure from byte-identity; the untouched original stays in Workspace Docs, which is not published. The case number and "[Aaron's university — name withheld under D-R2-2026-10-01-03c]" stay: they are Aaron's own facts and Aaron will decide visibility knowing they are there.
  3. In the checkpoint message, list for Aaron exactly what a public repository would expose: hostname, Windows username, university affiliation, Morningstar case number. I will put that in front of him before any push.

X2 — your mechanical rule is adopted as the definition. NATURAL = block present AND capture_type = ROUTINE_FORWARD_COLLECTION AND scheduled_time ≥ StartBoundary 2026-09-21T11:00+08:00 AND sole recorded invocation for its slot. PROJECT_STATE carries the rule-based counts (NATURAL 9 incl. 2 StartWhenAvailable catch-ups; MANUAL 6; snapshots 15; JSONL rows 14) with the one-line rule beside them. reproduce.py computes the rule-based counts and fails on mismatch with PROJECT_STATE; it may also print the literal block count as an informational line, clearly labelled, but that number goes nowhere else. Replace the prompt's Task C wording with this rule in R2_FORWARD_PIT_COLLECTION.md's new section, and note the 2026-09-21 11:00:01 trigger failure (no log line) there as MISSING_FORWARD_CAPTURE, not backfilled.

X3 — agreed: backlog row, no tools change in this checkpoint. Record it as BL-R2-01: installer marker written with BOM (PowerShell 5.1 Set-Content -Encoding utf8) → wrapper json.loads fails → marker deleted → default label; effect limited to the capture_type label of a re-install validation run; 070042_ET manifest immutable and not relabelled; no research impact; fix (read with utf-8-sig, with a test) is an IMPLEMENTATION_FIX you may make in a later separate commit under builder autonomy, after this checkpoint is accepted.

Nothing here reopens OD-1/2/5/6, the sample window, exposure or trial accounting. Continue through Task H, then send the checkpoint message to me by name.
```

### 2.4 Note on a refused recording

The builder session's permission layer refused to record, as Owner decisions, Owner
instructions that reached the builder only by relay through the delegate session (message
received before 2026-09-30T19:45:25Z, proposing rows OWNER-R2-2026-10-01-A/B/C and an earlier
D-R2-2026-10-01-03). Those rows were never written. They are superseded by Aaron's own
statement (§2.5) and by D-R2-2026-10-01-03a–e (§2.6). The one delegate answer in that
message that stands on the delegate's own authority, "Option 1" for the reconciliation copy,
is carried as D-R2-2026-10-01-02-S.

### 2.5 OWNER-R2-2026-10-01 (verbatim, typed by Aaron in the builder session)

Received ≈2026-09-30T19:50Z.

```
我是 Aaron。发布范围由 Fable delegate 决定，我确认以下内容：R2 的 data_forward_pit 和 data_probe 全部提交；ITSF、nq-event-diffusion-research、nq-letf-rebalancing-research 三个项目通过发布镜像合并进我已建好的公开仓库 AaroNLaU0307/Intraday-Trend-Strategy-Framework；仓库保持 PUBLIC，但你写的文件里去掉学校名和 Morningstar 案例号。推送由我本人执行。
```

### 2.6 D-R2-2026-10-01-02-S and D-R2-2026-10-01-03a–e (verbatim decision text)

Sender: Fable 5.1 delegate session 'NDX leveraged-ETF rebalancing research handoff'.

D-R2-2026-10-01-02-S (from the message received before 2026-09-30T19:45:25Z):

```
Answer to your question: Option 1 — apply the same substitution and note to the reconciliation copy.
```

D-R2-2026-10-01-03a–e (stated UTC 2026-09-30T20:20Z; received before 2026-09-30T19:50:01Z by
the builder clock; recorded as sent):

```
D-R2-2026-10-01-03a  DATA_IN_REPO = ALL. data_forward_pit/ and data_probe/ are committed in full. Later LFS/manifest-only is a separate decision.
D-R2-2026-10-01-03b  PUBLICATION_TARGET = one public GitHub repository, AaroNLaU0307/Intraday-Trend-Strategy-Framework (empty, created by Aaron), holding ITSF, nq-event-diffusion-research (R1) and nq-letf-rebalancing-research (R2) as three subfolders of a publication mirror built with git subtree, histories preserved; local project folders never move; records are written only in the local projects; mirror path C:\Users\Aaron\OneDrive\Desktop\Quant trade\_publish\Intraday-Trend-Strategy-Framework, branch main; root README, root byte-copy of QUANT_WORKFLOW_VNEXT.md with WORKFLOW_COPY_NOTE.md, tools/sync_mirror script. No remote, no push by the builder.
D-R2-2026-10-01-03c  VISIBILITY = PUBLIC; university name and Morningstar case number withheld from every builder-authored file; the two handoffs/ copies carry three bracketed substitutions (employee first name, university, case number) with a header note; hostname and Windows username remain.
D-R2-2026-10-01-03d  Sequence: finish CP-R2-V2-01 (commit PROJECT_STATE, DECISION_LOG, README, tools/reproduce.py, handoffs/) → checkpoint message to me → on PASS, CP-MONO-01 as specified in my earlier message → checkpoint message → Aaron pushes → post-push reproduce run recorded.
D-R2-2026-10-01-03e  Rigour audit: after CP-MONO-01 is accepted, the delegate runs a read-only multi-agent audit (ultracode workflow) of R1 and R2 from this session against the mirror's HEAD commit, reporting findings to you; you are the repair seat for anything confirmed. Do not start an audit yourself; do not pre-empt it.
```

### 2.7 D-R2-2026-10-01-03d-A (verbatim)

Sender: Fable 5.1 delegate session 'NDX leveraged-ETF rebalancing research handoff'.
Received before 2026-09-30T19:53:16Z, after the CP-R2-V2-01 checkpoint message (commit
`e11a1c9`) was sent.

```
Sequence change (delegate D-R2-2026-10-01-03d amended, on Aaron's instruction that the rigour audit may precede the upload): the audit runs BEFORE the mirror and the push.

New order:
1. You finish CP-R2-V2-01 and send me the checkpoint (unchanged).
2. I accept (PASS/HOLD). On PASS, I run the read-only R2 rigour audit from my session against your HEAD commit. The R1 audit is already running against 18639ee.
3. I send you the confirmed findings for each project. You repair: R2 under builder autonomy (pre-seal, IMPLEMENTATION_FIX / RECORD_CORRECTION as classified); R1 only as new dated correction files — R1 is closed and its sealed artifacts, runs/ and ledgers are immutable; nothing there is rewritten. For R1 you hold a declared record-correction lease as the only writer; state it in R1's records when you first write there.
4. Repairs committed locally → checkpoint → my acceptance.
5. Then CP-MONO-01 (mirror, as specified) → checkpoint → Aaron pushes.

Nothing else changes. Do not start the mirror until step 4 is accepted.
```

### 2.8 D-R2-2026-10-02-01 — CP-AUDIT-01 acceptance and repair decisions (verbatim)

Sender: Fable 5.1 delegate session 'NDX leveraged-ETF rebalancing research handoff'. Stated
UTC 2026-10-01T18:30Z; received before 2026-10-01T17:51:53Z by the builder clock (recorded as
sent).

```
CP-AUDIT-01 is ACCEPTED (PASS) and here are the repair decisions. Delegate decision D-R2-2026-10-02-01, Fable 5.1 delegate, UTC 2026-10-01T18:30Z; log verbatim, then repair. Reports and panel data: Workspace Docs\handoffs\r2-letf-inbox-2026-10-01\audits\ (R1 report sha256 d617e1da…, R2 report 7cc924d7…; verify before copying).

ACCEPTANCE. REPRODUCED by me from the repositories: R1-G01 (all 13 ledger utc stamps end :00 and contradict commit times and the bundle's written_utc 2026-09-17T16:46:12Z), R2-G11 (CLOSED_PASS at FEASIBILITY:771 and AUDIT:579, READY_FOR_S1_DESIGN=YES at :830), R2-G03 (probe CSVs hold 23,616 data rows, records say 20,616), R2-G23 (`git log -1 -- PROJECT_STATE.md` = fa01d04). REASONED: the rest, on the reports' file:line evidence. All 11 R1 and 14 R2 confirmed findings are accepted at the severities given; one-vote items are accepted as record corrections, which is all any of them asks for. Procedural: the OD-6 finder's /tmp/x write was outside the workspace and is accepted with disclosure; nothing is invalidated. The ITSF post-reveal value that entered one finder's context is logged as an exposure disclosure in R2's DECISION_LOG (ITSF's, already revealed, unrelated to R2's target, unused); no other action.

STEP 0 — persist. Copy the two reports, RUN_IDS.md and the three workflow scripts into nq-letf-rebalancing-research/audits/2026-10-01_CP-AUDIT-01/ as immutable files (hashes in README of that folder). For R1: do your lease check; if no other writer, create nq-event-diffusion-research/audits/ with the R1 report. Commit the ACC-CP-R2-V2-01 row with this.

R1 DECISIONS (closed lineage: new dated files only; no edit to any sealed, digest-bound or attested file; no ledger row; no tag):
R1-a. One new file R1_RECORD_CORRECTIONS_2026-10-02.md carrying every accepted finding with exactly the narrowed content of report §3 (G01, G12, G14, G04, G06, G15, critic-4, G17, critic-1, G05, critic-3), file:line at 18639ee, pinned digests, and the refuted sub-claims named so nobody re-raises them.
R1-b. PROJECT_STATE.md keeps its r1-final bytes (option one). The correction file is the pointer readers need; add nothing to PROJECT_STATE.
R1-c. ANALYSIS_EXTENSION authorized, bounded and descriptive: the sealed H.2/I.2/D.3/J era, micro-era and event-type splits (G14) and the C1 replay values with seed disclosure (G12), computed only from the sealed bundle, date_et and the L-11-pinned calendar, recorded in the correction file with D.2 (no CPI/NFP promotion) and D.3 (micro-era on its own axis) kept, no verdict change, no trial consumed, no re-bootstrap of the Primary, and NOT the block-10 interval. Log it as ANALYSIS_EXTENSION with my decision id.
R1-d. Critic gaps 3 and 6 (who gave the S4 final verdict; who authorized KB ingestion cdc99e1): record as UNKNOWN in the correction file. Do not reconstruct.
R1-e. Refuted-but-factual items G02/G03 (uncommitted drivers, unrecorded run_study args), G07, G10, G13, G18, G08 become NON-BLOCKING BACKLOG rows in a backlog section of the correction file.
R1-f. R1-critic-1 IMPLEMENTATION_FIX in the unsealed tools/validate_state.py is allowed, plus the note that the ec52a9f1… pin refers to the closeout bytes. Expected after: pytest 285 passed, validate_state 60/0, validate_seal_snapshot PASS, validate_prereg 183/2 (same two standing FAILs), `git diff r1-final` = the new files + that tool.
R1-g. KB card corrections (card :46/:94, :93-96, :143-145, note at :77-78): prepare the exact annotation text in the correction file. Then, as a separate commit in quant-research-knowledge-base (local, no history rewrite, run `python -m quant_kb.validate`), apply them as dated annotations citing the correction file. This is a local merge-class act within delegated scope; log it in R1's correction file and in R2's DECISION_LOG by commit hash.

R2 DECISIONS:
R2-a. Tools commit (IMPLEMENTATION_FIX): BL-R2-01 utf-8-sig fix with a test on the exact PowerShell 5.1 bytes (G07); then the NATURAL boundary pinned to the literal 2026-09-21T11:00:00+08:00 with labelled WARN and regression test (G06) — confirmed: this implements X2 as written and changes no methodology; a per-registration boundary history or counting prose-only failed firings would be METHODOLOGY_CHANGE and is out of scope; order is fix before pin, both before any installer re-run. Also: task_action.py:75 made 3.10-compatible and README:48 states only the interpreters actually run (critic-1); reproduce.py tolerates non-COMPLETED rows instead of crashing (G05, accepted as part of this commit). G04, G08, G24 and side observation (ii) become NON-BLOCKING BACKLOG rows.
R2-b. G14 NFN: REJECTED under R3 — its only documented TNA message is "As of TBD 2027", history begins after the sample; disclose that the NFN spec bytes were never captured; no enquiry (no vendor contact is authorized and NFN cannot cover 2010-2021). Correct every hand-copied "six" (report :219, :231 adding the ProShares issuer archive, :273, :376-377) as a dated correction. One DECISION_LOG row.
R2-c. G15: criteria §2 governs. R6 must be assessed for every VERIFIED candidate; 2016_ACID_TEST = PASS is required only for VERIFIED_FULL, or where the claimed PIT scope covers 2016-03-31 to 2016-04-05. RECORD_CORRECTION: dated note in the tracker correcting §5 item 4 and the PASS legend, superseding dispatch §4:325-329 by note. One DECISION_LOG row. Not a methodology change.
R2-d. G02: accept the DECISION_LOG row correcting the OD-1 narrative: pre-grant reads were metadata (file listing / condition.json) only, no bar decoded, no outcome touched; ruled as disclosed metadata access, not outcome access and not a widening of the grant. Fix the A-1 condition.json statement and the PROJECT_STATE wording.
R2-e. G10/G09: label the 2026-09-20 11:00 +08:00 slot "NO_FIRING_RECORD — task registration instant not established in any committed byte; not counted as a missed firing and not backfilled". Do not assert the slot was in force.
R2-f. G18: one DECISION_LOG row marking OD §5 "none has been asked" as true as of 2026-09-20 and superseded by the Wave-1 dispatch; no edit to R2_DELEGATED_OWNER_DECISIONS.md. README:80 and tracker §1 corrected as the report says (templates vs sent messages, channel changes, ETF Global clarification marked SELF-REPORTED).
R2-g. G11: append the two dated correction sections (after AM-6 and after A-6) withdrawing AM-2/A-1 as full-sample claims and AM-6 outright, folding in the B-1 body claims at AUDIT:138 and :160 (side observation iv), and the README:68-69 caveat. The 2026-09-19 bytes stay identical.
R2-h. G03, G13, G16, G20, G23, side observations (i) and (iii): the appended dated corrections exactly as report §7(b)2 lists them; (i) and (iii) go into a dated section of R2_FORWARD_PIT_COLLECTION.md and (iii) into its supersession list.
R2-i. PROJECT_STATE rewrite at the repair checkpoint: LAST_CHECKPOINT as an explicit hash; trial flags per G16; archive-access wording per G02; NEXT_DECISION = acceptance of the repair checkpoint, then CP-MONO-01, then Aaron's push.

CHECKPOINT CP-REPAIR-01 to me when done: commit range per repository (R2, R1, KB), pytest + reproduce output for R2, the four R1 check results, `git diff --stat r1-final`, and anything you could not do and why. Nothing else starts before my acceptance.
```
