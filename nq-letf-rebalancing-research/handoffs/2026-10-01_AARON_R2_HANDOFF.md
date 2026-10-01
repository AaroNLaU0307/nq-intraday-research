> **Published copy.** Byte-identical to the original in the author's unpublished workspace (`Workspace Docs/handoffs/r2-letf-inbox-2026-10-01/R2_HANDOFF_AARON_2026-10-01.md`)
> except three bracketed substitutions under D-R2-2026-10-01-02 / -03c: Morningstar employee first name, university name, Morningstar support-case number.

# FABLE HANDOFF — R2 NDX LEVERAGED-ETF RESET / REBALANCING RESEARCH

> Saved verbatim by the Fable delegate session on 2026-10-01 (03:30 +08:00) from Aaron's
> chat message of the same date. Source: Aaron (Owner). Nothing below was edited.

HANDOFF TYPE:
Complete project-state handoff / source-of-truth orientation

PROJECT:
nq-letf-rebalancing-research

ROOT:
C:\Users\Aaron\OneDrive\Desktop\Quant trade

PROJECT PATH:
C:\Users\Aaron\OneDrive\Desktop\Quant trade\nq-letf-rebalancing-research

HANDOFF OWNER:
Aaron

IMPORTANT:
This handoff does NOT itself authorize any new research stage, S1, data purchase,
paid trial, vendor follow-up, NQ decoding, outcome analysis, or R2 trial.

Aaron remains the final Owner.

Your first responsibility is to understand and preserve the existing research state,
not to restart or expand the project.

============================================================
0. CURRENT ONE-SENTENCE STATE
============================================================

R2 is a PRE-S1 research lineage whose scientific entry condition depends on
historical point-in-time (PIT) availability of daily fund-size / composition
information for the five NDX daily-reset leveraged ETFs.

Public-source investigation did NOT establish a verified full-sample PIT source.

A six-vendor Wave-1 enquiry was subsequently authorized and successfully
dispatched to all six vendors.

Current state:

    VENDOR_WAVE1_SENT_COUNT = 6
    VENDOR_WAVE1_TOTAL = 6
    VENDOR_WAVE1_STATUS = ALL_SENT

Current vendor evidence has not yet produced a VERIFIED_FULL or VERIFIED_PARTIAL
historical PIT source.

Therefore:

    R2_S1_AUTHORIZED = NO
    NQ_DATA_DECODED = NO
    NQ_RETURN_COMPUTED = NO
    R2_PNL_COMPUTED = NO
    TRIAL_CONSUMED = NO
    DATA_PURCHASE_AUTHORIZED = NO
    PAID_TRIAL_AUTHORIZED = NO

The project is currently waiting for external evidence.

Do NOT interpret the absence of vendor replies as evidence that the hypothesis
is false or that the data source does not exist.


============================================================
1. GOVERNANCE / AUTHORITY
============================================================

The project sits under:

C:\Users\Aaron\OneDrive\Desktop\Quant trade\QUANT_WORKFLOW_VNEXT.md

Authority precedence:

1. Aaron explicit Owner decisions / hard research invariants
2. Active sealed research contract / preregistration
3. QUANT_WORKFLOW_VNEXT.md
4. Generic project-local workflow
5. Model/global defaults

For this project specifically, several Owner decisions were delegated to Fable
and accepted by ChatGPT. Those decisions are persisted in:

    R2_DELEGATED_OWNER_DECISIONS.md

Do not silently replace those decisions.

If new information conflicts with an existing decision, surface the conflict
rather than silently changing the decision.

Fable is acting as scientific architect / delegated decision-maker where the
delegation explicitly permits it.

Fable is NOT a standing reviewer and must not invent additional governance.


============================================================
2. RELATIONSHIP TO R1
============================================================

R2 was created after the earlier R1 lineage.

R1 was:

    Scheduled-release information-diffusion continuation

R1 is already CLOSED.

R1 final formal state was:

    INSUFFICIENT_EVIDENCE

It was NOT formally falsified.

R1's existing NQ development data can be reused by R2 only under the explicit
new-lineage grant described below.

R2 is therefore NOT a fresh independent data sample.

This distinction is important.


============================================================
3. R2 SCIENTIFIC IDEA
============================================================

R2 studies whether leveraged-ETF daily reset / rebalancing mechanics can create
a predictable pressure transmitted into the NDX / NQ ecosystem.

The initial conceptual mechanism is:

    dS_i,t
      = m_i,t (m_i,t - 1) A_i,t-1 r_pre,t

and aggregate fund-side pressure:

    F_t = K_t r_pre,t

where:

    K_t = Σ_i [m_i,t (m_i,t - 1) A_i,t-1]

The intended universe is the five US-listed NDX-benchmarked daily-reset
leveraged ETFs:

    QLD   +2x
    QID   -2x
    PSQ   -1x
    TQQQ  +3x
    SQQQ  -3x

For these leverage values:

    m(m-1) > 0

for all five funds.

Therefore, in the single-NDX-universe formulation:

    sign(F_t) = sign(r_pre,t)

This is a critical scientific constraint.

It means R2 cannot simply rediscover:

    "the market went up before the close, therefore it continues"

or generic late-day momentum.

Generic momentum is explicitly FORBIDDEN as the R2 substitute.

The possible distinct information has to come from:

    K_t / L_t

or another equivalent measure of:

    magnitude
    composition
    fund-size exposure
    leverage mix
    reset/rebalancing pressure

that provides information beyond:

    sign(r_pre)
    |r_pre|
    slow trend
    generic market state

If prospective research cannot distinguish the proposed ETF-reset mechanism
from generic market momentum using the fund-size/composition information,
R2 must be PARKED.

This distinctness requirement is fundamental and must not be weakened later.


============================================================
4. S0 ORIGIN / STRATEGY SELECTION
============================================================

The broader S0 candidate families included:

    D1 = state-conditioned liquidity-pressure reversal
    D2 = event-anchored information-diffusion continuation
    D3 = overnight information-quality transfer / opening ratification
    D4 = predictable closing mechanical flow
    D5 = institutional execution footprint / metaorder
    D6 = crypto forced-flow / crowding reversal

Astra narrowing produced:

    R1 = D2 narrowed to scheduled-release information-diffusion continuation
    R2 = D4 narrowed to leveraged-ETF rebalancing/reset pressure transmitted
         to index futures

The third slot was intentionally left EMPTY.

Other candidates were PARKED/reserve:

    D3 = reserve / PARK
    D1 = PARK
    D5 = PARK
    D6 = PARK

D6 was also nested under D1.

Therefore there is currently no pre-existing R3 in this lineage.

Do not invent an R3 inside this project unless Aaron explicitly opens a new
selection process.


============================================================
5. R2 OWNER DECISIONS
============================================================

-------------------------
OD-1 — NEW LINEAGE GRANT
-------------------------

R2 is allowed to use the existing NQ DEVELOPMENT data under a new
lineage-specific grant.

This means:

    sample = NOT FRESH

but:

    prior exposure = explicitly disclosed

R2 gets separate trial accounting.

There is no mutation of the R1 registry.

There is no IV.

There is no Lockbox.

If R2 eventually reaches its first formal run:

    sample-level ordinal = 3
    R2 own lineage trial = 1

This must not be confused with R1's historical trial accounting.

-------------------------
OD-2 — UNIVERSE
-------------------------

First R2 lineage is strictly:

    NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY

Universe:

    QLD
    QID
    PSQ
    TQQQ
    SQQQ

Broader LETF flow research is NOT part of this lineage.

Generic momentum is forbidden as a substitute.

-------------------------
OD-5 — FUND SIZE PATH
-------------------------

Selected path:

    PATH_A_TRUE_PIT_DAILY

Meaning:

R2 requires actual historical point-in-time daily fund-size information
with evidence that the information was available at the relevant time.

The currently complete historical AUM files are NOT automatically considered
PIT-safe simply because the files exist today.

PATH_B was not selected as the primary route.

PATH_B could retain some slow composition information, but it materially
weakens the intended daily causal information and introduces stale/trend
confounding.

Do NOT overstate this as mathematically proving that PATH_B has zero
composition information.

PATH_C is:

    PARK

and is triggered if bounded source verification ultimately fails.

-------------------------
OD-6 — ZERO-CARRY PIT RULE
-------------------------

Selected rule:

    PROVEN_PUBLICATION_ONLY_ZERO_CARRY

Hard rules:

1. UNPROVEN availability = INELIGIBLE.
2. No forward-fill.
3. No interpolation.
4. No imputation.
5. No neighboring-date inference.
6. No partial-universe K_t.
7. All PIT universe members are required.
8. If a row was too late for time t, it cannot enter t.
9. A later backfill does not retroactively make t eligible.
10. Eligibility must be built and frozen BEFORE any NQ outcome decoding.

The known 2016 historical publication stall must therefore make affected
dates ineligible unless evidence proves the relevant data was actually
available by the required time.


============================================================
6. DATA FEASIBILITY — WHAT HAS ALREADY BEEN ESTABLISHED
============================================================

The project investigated public ProShares historical data.

Core ETFs:

    QLD
    QID
    PSQ
    TQQQ
    SQQQ

Public historical files contained approximately:

    20,616 rows

Observed public-file properties:

    zero missing NAV/shares/AUM in the available artifact
    zero duplicate dates

However:

IMPORTANT:

Published historical AUM completeness is NOT equivalent to historical PIT
availability.

The project therefore does NOT accept:

    "the historical file has the row"

as proof of:

    "the row was publicly available at the required historical time."

Also:

Published AUM should be used directly.

Do NOT reconstruct AUM as NAV × shares because historical split-adjustment
mismatches were observed.


============================================================
7. FUND-SIDE FEASIBILITY RESULTS
============================================================

Using the available historical fund-side data, the conceptual R2 fund-size
measure showed meaningful variation over:

    2010-06-07 through 2021-12-31

    n = 2915

Observed K_t-related scale:

    minimum ≈ $6.99B
    median  ≈ $17.75B
    maximum ≈ $161.69B

approximately a 23x range.

Inverse-share composition also varied substantially:

    approximately 10.7% to 81.6%

and composition shifted over time, including QID → TQQQ changes.

These observations establish DATA FEASIBILITY at the fund-side level.

They do NOT establish PIT eligibility.

No NQ outcomes were used to establish these feasibility facts.


============================================================
8. HISTORICAL PIT PROBLEM — G3
============================================================

This was the major blocker.

Initial assumptions that historical AUM was available by the next open were
rejected.

A historical repair investigation found:

- archived 2011/2012 ProShares files ending in shares outstanding did NOT have
  an AUM field.

- an AUM-bearing artifact was directly observed by approximately:
      2014-03-26 / 2014-03-27 era

- a TQQQ AUM capture was observed in 2018.

- historical normal evening batch behavior was observed.

- however, a critical counterexample occurred around:
      2016-04-01

  where the normal batch stalled and files remained at approximately the
  3/31 state for roughly 2.5 days before later backfill.

- the modern complete historical file does not preserve the original moment
  when each historical row was first available.

Therefore:

    G3_HISTORICAL_STATUS = PARTIAL

    AUM_FIELD_OBSERVED_START = 2014-03-26

but:

    HISTORICAL_DAILY_PIT_SAFE_START = UNKNOWN

and:

    FULL_SAMPLE_AUM_AVAILABLE_BY = UNKNOWN

and:

    G11_STALENESS_PROBLEM = MATERIAL

CRITICAL:
Do NOT rewrite "AUM field observed from 2014" into:
"2014 is the PIT-safe start."

That conclusion is not established.


============================================================
9. MUTUAL FUND / COVERAGE OMISSION
============================================================

Mutual-fund omission is a known measurement omission.

The magnitude is UNKNOWN.

Do NOT claim:

    "this only attenuates the effect"

and do NOT assume:

    "mutual funds affect only the close."

Those claims have not been established.

This should remain an explicit measurement limitation.


============================================================
10. SOURCE VERIFICATION — SV-1
============================================================

A public-source audit was performed.

Result:

    SV1_RESULT = NO_VERIFIED_SOURCE_PUBLICLY_ESTABLISHED

No public source was verified as satisfying the full historical PIT requirement.

Candidate source classes investigated included:

    ETF Global
    LSEG / Lipper
    Bloomberg
    Morningstar
    FactSet
    ProShares / ProFunds
    Ultumus / SIX
    other public / documented data-source routes

Important source conclusions:

ETF Global:
    strongest publicly documented PIT-metadata candidate

BUT:

    PLAUSIBLE_UNVERIFIED

It must NOT be called verified.

ETF Global's relevant documentation appeared to provide concepts such as
effective_date / processed_date, but the public evidence did not establish
the complete historical vintage/receipt semantics required for the entire
five-fund 2010–2021 sample.

LSEG / Lipper:
    daily TNA/AUM-type information and long US history were documented,
    but public evidence did not establish the required historical
    vintage/receipt semantics.

Bloomberg:
    history/revisions functionality exists,
    but public evidence did not establish field-level historical
    receipt/load timestamps required by this research.

Morningstar:
    historical daily net-assets-type data appears possible,
    but historical PIT vintage/timestamp semantics were not publicly verified.

FactSet:
    public evidence weaker for the exact PIT requirement.

ProShares:
    issuer-side information could potentially answer historical
    availability questions, but current public archives did not prove
    the full PIT chain.

Ultumus/SIX:
    point-in-time/version-control capabilities were documented,
    but the approximately five-year lookback was insufficient for the
    2010–2021 target.

2016 acid-test:

    verified public-source PASS count = 0

This was the reason the vendor enquiry wave was necessary.


============================================================
11. VENDOR ENQUIRY DESIGN
============================================================

The vendor enquiry requested historical evidence for sample dates around:

    2016-03-31
    2016-04-01
    2016-04-04
    2016-04-05

Requested evidence included:

    value date
    fund size OR NAV + unadjusted shares
    first receipt/load/publication timestamp
    timezone
    revision/vintage identifier

The point was NOT simply to ask:

    "Do you have historical AUM?"

The actual scientific question is:

    "Can you prove what information was available when, historically,
     for the required funds and fields?"

No NQ alpha/performance details were disclosed unnecessarily.


============================================================
12. FORWARD PIT COLLECTOR
============================================================

Because historical PIT could not be proven from existing archives, a
forward-PIT collection mechanism was built.

Collector:

    tools/collect_forward_pit.py

Version:

    1.1.0

It uses public HTTP and no credentials.

It captures:

    raw response bytes
    raw headers
    capture timestamp
    UTC timestamp
    ET timestamp
    HTTP Date
    Last-Modified
    ETag
    Content-Length
    latest row
    row count
    SHA256
    URL
    status
    schema
    failures

Failure states are preserved.

There is no silent retry fabrication.

Snapshots are stored under:

    data_forward_pit/

The snapshots are timestamped and hashed.

Important:
This is operational evidence, not cryptographic immutability.

Forward PIT collection does NOT repair historical 2010–2021 PIT uncertainty.

It also does NOT assign a post-2022 sample tier.

Current:

    POST_2022_SAMPLE_TIER = UNASSIGNED


============================================================
13. FORWARD PIT VALIDATION
============================================================

Synthetic/offline collector testing eventually reached:

    27/27 PASS

A genuine infrastructure validation captured:

    QLD
    QID
    PSQ
    TQQQ
    SQQQ

with:

    5/5 funds OK
    verified = true

A scheduler validation snapshot also succeeded.

One validation snapshot:

    2026-09-19/131606_ET

with:

    funds_ok = 5/5
    funds_failed = 0
    snapshot_verified = true
    collector_exit_code = 0

This proves the forward collector infrastructure works.

It does NOT prove historical PIT.


============================================================
14. WINDOWS SCHEDULER
============================================================

Task:

    QuantTrade-R2-ForwardPIT

The task was originally InteractiveToken.

That was corrected.

S4U was explicitly rejected because it does not provide the network credentials
needed by the HTTPS collector.

Persisted rule:

    S4U_UPGRADE_FOR_FORWARD_COLLECTOR = FORBIDDEN_WRONG_FIT
    S4U_USED = NO

The task was changed to a password-backed Microsoft Account principal.

Validated configuration:

    LogonType = Password
    RunLevel = Limited
    StartWhenAvailable = True
    MultipleInstances = IgnoreNew
    ExecutionTimeLimit = PT1H

The action uses canonical:

    /d /s /c

quoting.

The project working directory and Python interpreter are correct.

Python:

    3.14.2

The important acceptance test eventually passed:

    LastTaskResult = 0

and:

    PASSWORD_BACKED_TASK_CONTEXT_VALIDATED = YES

The task-context validation exercised:

    network access
    project-file access
    wrapper chain

under the registered principal.

The task's XML secret scan was clean.

No password, credential, token, cookie, or authentication material was
persisted in the repository/logs/XML.

Known scheduler artifact paths include:

    ops/R2_FORWARD_PIT_TASK.xml

    tools/install_forward_pit_task.ps1

    tools/remove_forward_pit_task.ps1

    tools/run_forward_pit_task.cmd

    tools/run_forward_pit_scheduled.py

    logs/forward_pit_scheduler.jsonl

    logs/forward_pit_task_stdout.log

A natural scheduled firing was originally scheduled for:

    2026-09-22 11:00 MYT

IMPORTANT:
The latest evidence explicitly validated the password-backed task context,
but the current handoff should NOT claim later natural scheduled-run success
unless such later evidence exists in the repository.

The manually triggered task validation and the natural wall-clock firing are
different observations.


============================================================
15. VENDOR WAVE-1 — FINAL DISPATCH STATE
============================================================

Wave-1 was authorized.

All six intended vendor enquiries were successfully dispatched.

Final:

    VENDOR_WAVE1_SENT_COUNT = 6
    VENDOR_WAVE1_TOTAL = 6
    VENDOR_WAVE1_STATUS = ALL_SENT

Exact known dispatch evidence:

ETF Global:
    SENT / awaiting response
    YAHOO_SENT/00_62116

Morningstar:
    SENT / awaiting response
    YAHOO_SENT/00_62118

ProShares / ProFunds:
    SENT / awaiting response
    YAHOO_SENT/00_62120

FactSet:
    SENT / awaiting response
    YAHOO_SENT/00_62121

LSEG / Lipper:
    submitted successfully
    2026-09-21T20:16:08+08:00
    confirmation page indicated the request was received

Bloomberg:
    submitted successfully
    2026-09-21T20:16:54+08:00
    confirmation page indicated the request was under review

No provider reference number was displayed for LSEG/Bloomberg.

All six were submitted exactly once.

No duplicate dispatch was detected.


============================================================
16. LSEG / BLOOMBERG FORM DETAILS
============================================================

LSEG required:

    First name
    Last name
    Email
    Phone
    Country
    Company
    Job title

City and area of interest were optional.

The submission included a mandatory communications notice.

Aaron explicitly authorized that mandatory communications notice before
submission.

No separate optional marketing checkbox existed.

Bloomberg required:

    business situation/problem
    Bloomberg Professional usage history
    first name
    last name
    business email
    phone
    job role
    company/company type
    city
    country

For Student role:

    University

appeared as a required field.

Company was hidden for Student.

The Bloomberg form also required a company type.

The chosen company type was:

    Other

Aaron explicitly authorized the mandatory Bloomberg communications notice.

Bloomberg usage status was:

    never used Bloomberg Professional / Bloomberg Terminal

No invented company or employment information was used.

The project did NOT persist the phone number or personal authentication
information.


============================================================
17. MORNINGSTAR — COMPLETE HISTORY OF THE CURRENT THREAD
============================================================

Morningstar is a particularly important case because the public trial/access
route did not resolve the research need.

Initial Morningstar response:

They said the enquiry came from an unregistered email address and asked for
the registered Morningstar Direct email.

A subsequent support case was opened:

    Case [Morningstar support case number — withheld by builder]

Morningstar stated that they could not associate the email with a registered
Morningstar Direct username and that licensed users were supported.

They indicated that non-registered users could request a trial.

The displayed trial route was:

    https://go.morningstar.com/TryMorningstarDirect

However, the user found that route unavailable / not usable in practice.

A subsequent interest response stated:

    Morningstar Cloud was not available on an individual license for students
    and suggested checking a university library.

The user did NOT want to pursue the university-library route further because
of uncertainty about [Aaron's university — name withheld by builder] internal access restrictions.

Morningstar then replied that:

    they could not find any account registered under
    [Aaron's university — name withheld by builder]

and looped in their Sales Team / [Morningstar sales contact — name withheld by builder] to assist with the next steps.

The user chose to wait rather than continue pursuing trial/library access.

Current Morningstar state should therefore be treated as:

    SALES_ROUTING_COMPLETE_AWAITING_RESPONSE

It is NOT:

    VERIFIED_FULL
    VERIFIED_PARTIAL
    REJECTED

Morningstar has not yet answered the core scientific question:

    historical PIT AUM / fund size
    vintage semantics
    first receipt/load/publication timestamp

Do not interpret "no [Aaron's university — name withheld by builder] account" as evidence that Morningstar cannot
provide the required historical data.

Do not buy a Morningstar license or trial without explicit Owner authorization.

Do not pursue further library-access steps unless Aaron explicitly reopens
that path.


============================================================
18. CURRENT VENDOR STATUS
============================================================

Current known state:

    ETF_GLOBAL =
        CLARIFICATION_ANSWERED_AWAITING_VENDOR_RESPONSE

    LSEG_LIPPER =
        SENT_AWAITING_RESPONSE

    BLOOMBERG =
        SENT_AWAITING_RESPONSE

    MORNINGSTAR =
        SALES_ROUTING_COMPLETE_AWAITING_RESPONSE

    PROSHARES_PROFUNDS =
        SENT_AWAITING_RESPONSE

    FACTSET =
        SENT_AWAITING_RESPONSE


No vendor has yet produced:

    VERIFIED_FULL

or:

    VERIFIED_PARTIAL

source evidence.


============================================================
19. WHAT COUNTS AS A USEFUL VENDOR RESPONSE
============================================================

Do NOT classify a vendor as VERIFIED simply because they say:

    "We have historical AUM."

That is insufficient.

A useful response must be evaluated against the actual research requirement.

VERIFIED_FULL would require enough evidence to establish:

    required fields
    required funds
    required historical period
    historical point-in-time availability
    receipt/load/publication timing or equivalent vintage semantics
    enough evidence to prevent look-ahead
    sufficient coverage for the intended R2 sample

VERIFIED_PARTIAL means:

    some historical period/funds/dates can be genuinely proven PIT-safe,
    but not the full requested universe/sample.

In that case:

    R2 remains pre-S1

and S1 must explicitly define:

    date-level eligibility
    fund-level eligibility
    coverage requirements
    zero-carry behavior
    sample boundary

Do NOT silently expand the eligible sample after seeing NQ outcomes.

PLAUSIBLE_UNVERIFIED means:

    vendor describes historical/revision/versioning capability,
    but cannot prove the required historical availability semantics.

That is useful evidence but NOT sufficient for S1.

REJECTED / NO_RELEVANT_EVIDENCE means:

    vendor cannot supply the required historical PIT information.

If all plausible routes ultimately fail after bounded verification:

    PATH_C = PARK

would become appropriate.

Do not turn lack of vendor response into REJECTED.


============================================================
20. CURRENT SCIENTIFIC GATE
============================================================

R2 has NOT reached S1.

The current gate is:

    Can we establish a defensible historical PIT fund-size/composition input?

Until that is answered:

    no preregistration
    no NQ decode
    no signal construction
    no return computation
    no P&L
    no alpha verdict
    no trial consumption


============================================================
21. S1 — WHAT WOULD HAVE TO HAPPEN IF A SOURCE IS VERIFIED
============================================================

If a vendor produces sufficiently strong evidence, the next stage is NOT
immediately backtesting.

The correct sequence is:

    1. classify the source evidence
    2. determine full vs partial coverage
    3. freeze sample eligibility
    4. design S1
    5. preregister the mechanism test
    6. define controls/baselines
    7. define outcome windows
    8. define costs / execution assumptions
    9. define how K_t / composition information is used
   10. explicitly prohibit generic momentum substitution
   11. validate the preregistration
   12. Aaron authorizes S1
   13. only then build/run

S1 must not be reverse-engineered from observed NQ outcomes.


============================================================
22. WHAT MUST NOT HAPPEN
============================================================

Do NOT:

- decode NQ data now
- calculate NQ returns now
- calculate P&L now
- test the R2 signal now
- inspect outcome data to choose among PIT definitions
- redefine the sample after seeing outcomes
- call current AUM historical PIT
- forward-fill missing historical AUM
- interpolate historical AUM
- infer publication timing from neighboring dates
- use a partial ETF universe for K_t
- silently assume mutual funds only affect the close
- silently claim mutual-fund omission only attenuates the effect
- substitute generic late-day momentum for R2
- buy data
- start a paid trial
- accept a paid license
- schedule vendor follow-ups
- send additional vendor messages
- book sales meetings
- reopen Morningstar library access
- broaden the LETF universe
- create R3 inside this lineage
- consume an R2 trial
- authorize S1

unless Aaron explicitly authorizes the relevant step.

Also do not call R2:

    FALSIFIED

or:

    SUPPORTED

because R2 has not yet produced outcome evidence.


============================================================
23. CURRENT FINAL STATE / "收工" STATE
============================================================

For the purpose of pausing active work:

    R2_ACTIVE_RESEARCH = NO
    R2_STAGE = PRE-S1
    R2_STATUS = WAITING_FOR_EXTERNAL_EVIDENCE

Vendor wave:

    ALL_SENT

Scientific source:

    NOT_VERIFIED

Research outcome:

    NONE

NQ outcome access:

    NOT_STARTED

S1:

    NOT_AUTHORIZED

Purchase:

    NOT_AUTHORIZED

Paid trial:

    NOT_AUTHORIZED

Follow-up:

    NOT_AUTHORIZED

Post-2022 tier:

    UNASSIGNED

This is an intentional pause, not a failed experiment.


============================================================
24. IMPORTANT DISTINCTION: WAITING IS NOT FAILURE
============================================================

The project currently has insufficient external evidence to enter S1.

That is a data-source / research-design gate.

It is NOT evidence that:

    ETF rebalancing has no effect
    the R2 mechanism is false
    NQ has no exploitable response
    the hypothesis is falsified

Likewise, a vendor not responding is not evidence against the mechanism.

Do not create a scientific verdict from administrative silence.


============================================================
25. RELEVANT PROJECT ARTIFACTS
============================================================

The local repository should be treated as the actual source of truth.

Important files/artifacts include:

    PROJECT_STATE.md

    R2_DELEGATED_OWNER_DECISIONS.md

    R2_VENDOR_WAVE1_DISPATCH.md

    R2_VENDOR_RESPONSE_TRACKER.md

    R2_FORWARD_PIT_COLLECTION.md

    ops/R2_FORWARD_PIT_TASK.xml

    tools/collect_forward_pit.py

    tools/install_forward_pit_task.ps1

    tools/remove_forward_pit_task.ps1

    tools/run_forward_pit_task.cmd

    tools/run_forward_pit_scheduled.py

    logs/forward_pit_scheduler.jsonl

    logs/forward_pit_task_stdout.log

    data_forward_pit/

    vendor_outbound/

and the broader workflow:

    C:\Users\Aaron\OneDrive\Desktop\Quant trade\QUANT_WORKFLOW_VNEXT.md


============================================================
26. SOURCE-OF-TRUTH RULE
============================================================

The repository and persisted project-state artifacts are the source of truth.

This chat handoff is a high-level reconstruction of the current state.

Before making any change, inspect:

    PROJECT_STATE.md
    R2_DELEGATED_OWNER_DECISIONS.md
    R2_VENDOR_RESPONSE_TRACKER.md
    R2_FORWARD_PIT_COLLECTION.md

and reconcile them with actual files/logs.

If chat state and repository state disagree:

    DO NOT silently choose one.

Report the discrepancy and identify which artifact is authoritative according
to the project's governance.

Do not invent commits, tags, hashes, timestamps, vendor replies, or scheduler
successes that are not actually present.


============================================================
27. IF A VENDOR REPLIES IN THE FUTURE
============================================================

The future workflow is:

    vendor reply
        ↓
    inspect exact evidence
        ↓
    determine whether it proves historical PIT semantics
        ↓
    classify:
        VERIFIED_FULL
        VERIFIED_PARTIAL
        PLAUSIBLE_UNVERIFIED
        REJECTED / NO_RELEVANT_EVIDENCE
        ↓
    update tracker/project state
        ↓
    determine whether R2 source gate is satisfied
        ↓
    ONLY IF satisfied:
        prepare S1
        ↓
    Aaron reviews/authorizes S1

Do NOT automatically purchase anything.

Do NOT automatically start a trial.

Do NOT automatically begin NQ research.

Do NOT treat a vendor sales statement as scientific verification.


============================================================
28. IF ALL VENDORS FAIL
============================================================

If the six-vendor wave and bounded source-verification process ultimately
produce no defensible historical PIT source:

    PATH_C = PARK

Then R2 can be parked as:

    unresolved data-feasibility / PIT-verification blocker

It should NOT be recorded as:

    FALSIFIED

unless a later scientific test actually falsifies the mechanism.


============================================================
29. IF A PARTIAL PIT SOURCE IS FOUND
============================================================

If a vendor proves only a subset:

    do not throw away the source automatically.

Instead determine:

    which dates
    which funds
    which fields
    which timestamps
    which publication semantics
    which sample periods

are actually proven.

Then construct a frozen eligibility table BEFORE touching NQ outcomes.

The S1 contract must state exactly which observations qualify.

No post-outcome expansion.


============================================================
30. FABLE'S ROLE FROM THIS HANDOFF
============================================================

Fable should NOT immediately start new work.

The project is intentionally paused.

The correct first response from Fable should be an acknowledgement that
the project state has been understood, including:

    - R2 is PRE-S1
    - vendor Wave-1 is 6/6 sent
    - no VERIFIED_FULL/PARTIAL source yet
    - no NQ outcome work has started
    - no purchase/trial is authorized
    - Morningstar is currently routed to Sales and awaiting response
    - R2 remains waiting for external evidence
    - existing Owner decisions remain binding

If no new vendor evidence is supplied, there is no need to manufacture work.

If new evidence appears, Fable should evaluate that evidence against the
existing R2 gate rather than redesigning the project.

If Aaron later explicitly asks to open a new R3/S0 selection, that should be
treated as a separate decision process and must not be mixed into R2.


============================================================
31. FINAL HANDOFF COMMAND
============================================================

Treat the entire preceding document as the current R2 project handoff.

Do not restart R2.

Do not broaden R2.

Do not consume a trial.

Do not purchase data.

Do not run NQ outcomes.

Do not authorize S1.

Do not classify the mechanism scientifically.

Preserve all existing Owner decisions.

The current correct state is:

    R2 = WAITING_FOR_EXTERNAL_EVIDENCE / PRE-S1
    VENDOR_WAVE1 = ALL_SENT
    VERIFIED_PIT_SOURCE = NONE
    S1 = NOT_AUTHORIZED
    NQ_OUTCOME_RESEARCH = NOT_STARTED

Wait for new evidence or explicit Owner instruction.
