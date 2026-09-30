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
