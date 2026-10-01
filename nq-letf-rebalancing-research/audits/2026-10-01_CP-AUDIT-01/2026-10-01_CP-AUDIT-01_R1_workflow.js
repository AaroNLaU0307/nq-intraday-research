export const meta = {
  name: 'cp-audit-01-r1',
  description: 'CP-AUDIT-01: read-only rigour audit of R1 nq-event-diffusion-research @18639ee — 6 lens finders, 3-lens adversarial refutation per finding, completeness critic, synthesis',
  phases: [
    { title: 'Find', detail: 'six lens finders over the whole repository' },
    { title: 'Verify', detail: 'three refuters per finding: reproduce-from-bytes, rule-text, threat-path; survives if >=2 of 3 fail to refute' },
    { title: 'Critic', detail: 'completeness critic examines what no lens covered' },
    { title: 'Verify critic', detail: 'same three-refuter panel on critic findings' },
    { title: 'Synthesis', detail: 'one report in the CP-AUDIT-01 format' },
  ],
}

const SP = '/c/Users/Aaron/AppData/Local/Temp/claude/C--Users-Aaron-OneDrive-Desktop-Quant-trade/ba5d35b4-c6d4-480a-9d6c-eba4fdb6557a/scratchpad'
const REPO = SP + '/ws/nq-event-diffusion-research'
const REPOW = 'C:/Users/Aaron/AppData/Local/Temp/claude/C--Users-Aaron-OneDrive-Desktop-Quant-trade/ba5d35b4-c6d4-480a-9d6c-eba4fdb6557a/scratchpad/ws/nq-event-diffusion-research'

const PREAMBLE = `CP-AUDIT-01 — READ-ONLY RIGOUR AUDIT OF R1 (nq-event-diffusion-research) AT COMMIT 18639ee.
R1 is a CLOSED lineage: sealed preregistration at CONTENT_COMMIT 46b8aef (seal attestation commit 595af1c, annotated tag r1-s1-sealed); S2 build (code 433e2cc, build attestation commit b99e10e, tag r1-s2-built); S3-A power gate (7426a2f); one governed Primary run R1-S3B-001 (28ed268); S4 verdict and lifecycle STOP (18639ee, tag r1-final). Pre-seal: 8656701, 66d9b43 (tag r1-pre-seal).

WHERE TO WORK
- AUDIT COPY — read files, git history and run tests/tools here and only here: ${REPO}  (Windows form: ${REPOW}). A fresh clone of the project, clean, checked out at 18639eea08ae89fa905866e8427caa48e4411d53, full history and all four annotated tags. Do NOT modify it: other agents use it concurrently.
- ITSF sibling so R1's own cross-check tests run: ${SP}/ws/Intraday Trend Strategy Framework — src/itsf exported from ITSF commit 11725fb (the three files pinned in r1/itsf_pin.py hash-MATCH) and gate1/f10_event_calendar/f10_events.csv (sha256 5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c = the OD-1 grant digest). The calendar holds release dates/times only, no market data; you may read it.
- PRIVATE COPY for ANY experiment that modifies bytes (mutation tests, patched validators, altered digests, scratch scripts): cp -r "${SP}/ws" "${SP}/mut/<LABEL>" with the LABEL given in your role line, then work in ${SP}/mut/<LABEL>/nq-event-diffusion-research. Put scratch scripts under ${SP}/mut/<LABEL>/.
- Workflow authority: C:/Users/Aaron/OneDrive/Desktop/Quant trade/QUANT_WORKFLOW_VNEXT.md (v2, activated 2026-09-26, NO retroactivity). R1 ran and closed 2026-09-17..18 under v1 (cutover 2026-09-12), text at C:/Users/Aaron/OneDrive/Desktop/Quant trade/Workspace Docs/workflow-evolution-2026-09-22/QUANT_WORKFLOW_VNEXT_v1_TEXT_2026-09-12.md. Judge an act by the rule in force when it happened; judge a record's present truth by what it says now.
- KB, read-only: C:/Users/Aaron/OneDrive/Desktop/Quant trade/quant-research-knowledge-base (README.md, schemas/).
- The REAL project directory C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-event-diffusion-research is OFF LIMITS (not even git status); the audit copy is byte-identical at the target commit.

HARD RULES (breaking any invalidates the audit)
1. Read-only: create or modify nothing outside ${SP}/mut/. No state-changing git command outside your private copy.
2. Tests: cd "${REPO}" && export PYTHONDONTWRITEBYTECODE=1 && python -m pytest tests -q -p no:cacheprovider . Tools you may run: tools/validate_state.py, tools/validate_seal_snapshot.py, psmv/validate_prereg.py. Anything else: read it first; run it only if it reads no market data.
3. NO OUTCOME DATA: never open, list, stat or run anything that reads C:/Users/Aaron/quant-data (NQ archive, databento archive, ITSF registry). psmv/psmv_structural.py (JOB_DIR points there) and r1/dev_adapter.py against real data must NOT be executed; read their code only. No network access of any kind.
4. The sealed outcome runs/R1-S3B-001/sealed_r1_outcome.json was revealed under Owner authorization on 2026-09-18; reading and recomputing from it is allowed.
5. Environment: Git Bash; python = Python 3.13.14 (numpy 2.5.0, pandas 2.3.3, pytest 9.1.1). Cite lines at the target commit (nl -ba / grep -n).

EVIDENCE STANDARD
- A finding names a concrete THREAT to a research conclusion, a record's truth, or reproducibility, AND a concrete FAILURE PATH: which input or state leads to which wrong output, wrong claim or unverifiable record.
- NOT findings: style; "could be cleaner"; generic best practice; "another reviewer would add confidence"; hypotheticals that cannot reach a wrong conclusion or an unverifiable record given the actual data and state.
- Label: REPRODUCED = you ran or recomputed something and observed it (give the command and the observed output); REASONED = from reading (give file:line).
- Prose agreeing with code is not evidence for the code. A sealed artifact disagreeing with prose IS a finding.
- Defects the project already discloses (PROJECT_STATE PERMANENT_RESIDUALS: OUTCOME_SCHEMA_LABEL_DEFECT and AXIS2_EVIDENCE_PROVENANCE_GAP; R1_SEALED_ERRATA.md E-1; the P-5 cost residual) are NOT new findings unless the disclosure is inaccurate, incomplete, or understates the consequence — check them and say which.
- Severity: Critical = the recorded verdict/conclusion is wrong or unsupported, or outcome contamination/leakage reached the result; High = a load-bearing rule or record is false or unenforced so that the conclusion or its reproducibility is materially uncertain; Medium = a record is false or a check is weaker than claimed but the conclusion stands; Low = a minor but real record inaccuracy. Do not inflate.
- Zero findings is a valid result.
- TWO HISTORIES: R1's sealed artifacts, runs/, ledgers, attestations and verdict are IMMUTABLE — a repair can only be a NEW dated correction file (or a change to unsealed tooling). For each finding state whether the smallest repair can be made without touching an immutable artifact.
- Repair classes: IMPLEMENTATION_FIX | DATA_FIX | ANALYSIS_EXTENSION | METHODOLOGY_CHANGE | RECORD_CORRECTION.

BASELINE MACHINE CHECKS the orchestrator already ran in the audit copy (rerun if your lens needs it): pytest tests -> 285 passed (no skips reported); tools/validate_state.py -> 60 passed, 0 failed; tools/validate_seal_snapshot.py -> PASS (161 checks at 46b8aef, 185 at 595af1c); psmv/validate_prereg.py -> 183 passed, 2 FAILED at HEAD ("state: S2 NOT AUTHORIZED", "state: outcome reveal not granted"); ITSF pins MATCH; the audit copy stays clean after the test run.`

const LENSES = [
  { key: 'lookahead', title: 'Look-ahead, leakage and point-in-time', body: `Trace the causal chain end to end in code AND against the sealed prereg: F10 event calendar (r1/events.py) -> bars (r1/bars.py; r1/dev_adapter.py read-only) -> decision delay O(08:33) -> signal (r1/signal.py, the two-bar reaction window) -> covariates (r1/covariates.py) -> controls C1/C2 (r1/controls.py) -> trade O(08:33)->O(09:29) (r1/trade.py) -> costs (r1/costs.py) -> r1/pipeline.py. At each step ask whether any value used at or before the decision timestamp can depend on information after it. Check in particular: timezone and DST handling around 08:30 ET releases (ET vs UTC conversion across March/November transitions, bar timestamp convention open-vs-close, what O(08:33) and the reaction window mean in bar indices and whether they can overlap the entry bar); release_time_status and non-standard release days in 2010-2021 (e.g. rescheduled releases such as the October 2013 shutdown); roll-window exclusions and roll-transition session mapping (any use of future roll information); warm-up/eligibility rules (complete_390, ADR14) and whether they use same-day minutes after the decision; C2 non-event day selection and C1 sign randomization; the cost table's provenance and period. For every invariant in prereg section N (LEAKAGE_AND_CAUSALITY_INVARIANTS) and every rule the prereg or S2_BUILD_REPORT.md says is enforced in code, find the enforcing code and determine by mutation in your private copy whether some test fails when the enforcement is removed. List anything the prereg says is enforced in code but is only prose.` },
  { key: 'seal', title: 'Seal integrity and commit order', body: `Recompute every digest in R1_S1_SEAL_ATTESTATION.json and R1_PREREG_MANIFEST.json from git objects at CONTENT_COMMIT 46b8aef and at HEAD 18639ee (git show <commit>:<path> | sha256sum); mind .gitattributes (eol/text) and state which byte form each digest is defined over and whether both forms agree. Confirm the attestation and annotated tag r1-s1-sealed bind to 595af1c, whose parent is 46b8aef, and that 595af1c changes no sealed file. List every sealed file changed after 46b8aef by any commit (git diff --name-status 46b8aef 18639ee and per-commit) and whether each change is permitted and classified (R1_SEALED_ERRATA.md, ledger). Verify that the build attestation (R1_S2_BUILD_ATTESTATION.json, tag r1-s2-built) and the run identity (artifacts/R1_S3B_RUN_IDENTITY.json) match the tree at the run commit: recompute the executable-identity rollup exactly as r1/build_identity.py and r1/run_identity.py define it at 433e2cc, at 28ed268 and at HEAD. Check the order prereg (46b8aef) -> build (433e2cc/b99e10e) -> power gate (7426a2f) -> run (28ed268) -> verdict (18639ee) in commit topology, commit/author dates, tag dates, ledger timestamps, and timestamps inside the artifact JSONs. Check that tools/validate_seal_snapshot.py, tools/validate_state.py and psmv/validate_prereg.py actually check what they claim: read their check lists, and for load-bearing claims prove detection by mutation in your private copy (e.g. flip a byte in a sealed file, change a recorded digest, edit an r1/*.py file) and see whether the validator fails. Explain the two FAILs of psmv/validate_prereg.py at HEAD and whether any record claims that validator passes at HEAD.` },
  { key: 'verdict', title: 'Verdict-rule mechanics', body: `Independently recompute the verdict. Read the sealed decision rule in R1_S1_PREREGISTRATION_SEALED.md (at least C.2, C.3, G.3, G.5, I.1, I.3, I.5, K.2, L, M.1-M.4) and R1_PREREG_MANIFEST.json. In your private scratch dir write your own short Python that reads runs/R1-S3B-001/sealed_r1_outcome.json and applies the sealed decision table as written in the prereg (NOT by importing r1/verdict.py): Base mean Y_net, the interval if persisted or recomputable, half-width, M, each axis, the resulting status. Compare with artifacts/R1_S4_VERDICT.json, PROJECT_STATE.md, the ledger rows, artifacts/R1_S4_KB_FINDING_PROPOSAL.yaml and r1/verdict.py. Check: implemented rule equals sealed rule (thresholds, SESOI M, direction, strict vs non-strict inequalities, ties, which cost scenario is Primary, unresolved conditions); the validity checks ran and passed before the primary result was read, and whether that order is provable from bytes (ledger sequence, commit order, receipt); outcome sealed unread and reveal authorized before reading (ledger seq 8-11, artifacts/R1_S3B_OUTCOME_RECEIPT.json, content of 28ed268 vs 18639ee); no post-outcome relabelling (compare verdict vocabulary and failure labels in the prereg with those in the verdict record — was any label, e.g. INSUFFICIENT_EVIDENCE_LOW_POWER, introduced only after the outcome?); the KB finding proposal claims nothing stronger than the verdict; the status vocabulary is the KB set (read the KB schemas). Verify the disclosed OUTCOME_SCHEMA_LABEL_DEFECT arithmetic (-10.268455 vs -8.768455, the $1.50 gap) from the Base records and whether any reading of the rule could change the verdict; verify the AXIS2 disclosure.` },
  { key: 'stats', title: 'Statistical validity and resolvability', body: `Examine r1/bootstrap.py: resampling unit (events vs bars vs days), dependence across overlapping or clustered event windows (e.g. CPI and NFP close together, same-day events), seed and determinism, interval type and number of resamples — and whether the recorded interval can be recomputed from the bundle. Check that n = 246 counts events (not bars or days) consistently across the prereg, the power gate, the outcome and the verdict. The power gate (r1/power_gate.py, artifacts/R1_S3A_POWER_GATE.json, prereg I.3, I.4, J): what it estimates (C2 dispersion over 2331 non-event days), whether that is a valid proxy for event-day dispersion, whether the gate could actually return a stop/redesign, whether MDE was computed after any real statistic was seen; compare its predicted SE 1.7985 with the realized half-width 4.9066 (implied SE about 2.50) and decide whether the sealed design could, in practice, only return unresolved. SESOI M = $3.99 and the costs: are they tied to pre-committed sources (prereg G.*, cost-table digest)? Trial accounting: consistent across R1_TRIAL_REGISTRY.md, prereg B.3 and I.2, PROJECT_STATE and the ledger (SAMPLE_FORMAL_TRIAL_ORDINAL = 2, N_trials, sample-reuse disclosures, prior ITSF exposure). Multiple-comparison exposure from auxiliary analyses (r1/auxiliary.py, prereg L, I.2, M): is any auxiliary or Axis-2 result reported so as to imply confirmatory evidence? Recompute what you can from the sealed outcome bundle in your private scratch dir.` },
  { key: 'records', title: 'Record consistency and governance evidence', body: `Cross-check PROJECT_STATE.md, R1_EXECUTION_LEDGER.md, R1_TRIAL_REGISTRY.md, R1_DELEGATED_OWNER_DECISIONS.md, R1_S0_PROVENANCE.md, R1_FINAL_CONTROLLER_SNAPSHOT.json, S2_BUILD_REPORT.md, R1_SEALED_ERRATA.md and every artifacts/*.json against each other and against git: recompute every sha256 quoted anywhere; resolve every commit hash quoted; compare every timestamp with commit and tag dates; check every tag. Every grant, consumption, reveal and verdict must have a ledger row and a commit — enumerate each event with its row and commit; flag any missing row or any row reconstructed after the fact (compare the row's own timestamp with the commit that introduced it); verify the ledger's hash chain if it has one. Find hand-copied derived facts that disagree with their source (e.g. PROJECT_STATE says 264 tests while pytest collects 285 at HEAD — find why, and whether any record is now false). Find stale lines stating incompatible live facts (e.g. REAL_DATA_ADAPTER = NOT EXECUTED on R1 beside a real power gate and a real run; the sealed prereg header 'S2 NOT AUTHORIZED'). Retired vocabulary: judge by the rule in force when written (v1 until 2026-09-26; v2 has no retroactivity), but say whether a CURRENT-state claim read today under v2 would mislead. PSMV record-repair scope (prereg S.6, registry section 4, PROJECT_STATE PSMV block): did it stay 'output surface only'; did anything sealed or outcome-relevant change? Check the decider/seat attribution of every binding decision (Aaron, Fable, ChatGPT, Opus) against the decision records.` },
  { key: 'tests', title: 'Test adequacy and runtime identity', body: `Run pytest in the audit copy and record the result and any skips (and why). For each rule the prereg, S2_BUILD_REPORT.md, PROJECT_STATE or r1/invariants.py says is ENFORCED in code, find the test that fails if the rule is removed and prove it by mutation in your private copy (remove or weaken the rule, rerun the relevant tests, record pass/fail). Prioritize rules that bear on the verdict: decision delay, signal window, trade-window endpoints, cost-scenario application, n counting, bootstrap unit and seed, verdict thresholds and ties, outcome sealed before read, consumption row before outcome access, executable identity. Can the synthetic generator tests/synth.py produce the failure cases (DST days, missing bars, roll days, early closes, delayed releases, overlapping events, ties at a threshold)? Does the attested runtime identity (R1_S2_BUILD_ATTESTATION.json, artifacts/R1_S3B_RUN_IDENTITY.json — interpreter, numpy/pandas versions, platform) reproduce here (Python 3.13.14, numpy 2.5.0, pandas 2.3.3), and would any difference change an outcome-bearing computation (e.g. the bootstrap RNG stream)? Is the sealed run re-executable from the repository alone, excluding the licensed archive: is there a documented command, and do all inputs other than the archive live in the repository or in digest-pinned sources? Never execute a path that reads real data.` },
]

const FINDING = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    severity: { type: 'string', enum: ['Critical', 'High', 'Medium', 'Low'] },
    locations: { type: 'array', items: { type: 'string' }, description: 'path:line-range at the target commit' },
    evidence: { type: 'string', description: 'what was observed; commands and outputs for REPRODUCED' },
    label: { type: 'string', enum: ['REPRODUCED', 'REASONED'] },
    threat: { type: 'string' },
    failure_path: { type: 'string' },
    repair: { type: 'string', description: 'smallest bounded repair' },
    repair_class: { type: 'string', enum: ['IMPLEMENTATION_FIX', 'DATA_FIX', 'ANALYSIS_EXTENSION', 'METHODOLOGY_CHANGE', 'RECORD_CORRECTION'] },
    immutable_touch: { type: 'string', description: 'can the repair be done without touching an immutable artifact? yes/no + how' },
  },
  required: ['title', 'severity', 'locations', 'evidence', 'label', 'threat', 'failure_path', 'repair', 'repair_class', 'immutable_touch'],
}
const FIND_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: FINDING },
    sound: { type: 'array', items: { type: 'string' }, description: 'examined and found sound, one line each with the evidence' },
    coverage: { type: 'string', description: 'what was examined and what was not' },
    commands: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'sound', 'coverage', 'commands'],
}
const VOTE_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    one_line: { type: 'string', description: 'at most 30 words, stands alone in the report' },
    reasoning: { type: 'string' },
    evidence: { type: 'string', description: 'commands and observed output, or quoted file:line' },
    label: { type: 'string', enum: ['REPRODUCED', 'REASONED'] },
    severity_view: { type: 'string', enum: ['None', 'Low', 'Medium', 'High', 'Critical'] },
    repair_view: { type: 'string' },
  },
  required: ['refuted', 'one_line', 'reasoning', 'evidence', 'label', 'severity_view', 'repair_view'],
}
const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    unexamined: { type: 'array', items: { type: 'string' } },
    examined_now: { type: 'array', items: { type: 'string' } },
    unclosed_gaps: { type: 'array', items: { type: 'string' } },
    findings: { type: 'array', items: FINDING },
    sound: { type: 'array', items: { type: 'string' } },
  },
  required: ['unexamined', 'examined_now', 'unclosed_gaps', 'findings', 'sound'],
}
const SYNTH_SCHEMA = {
  type: 'object',
  properties: {
    markdown: { type: 'string' },
    counts: {
      type: 'object',
      properties: {
        confirmed: { type: 'integer' }, critical: { type: 'integer' }, high: { type: 'integer' },
        medium: { type: 'integer' }, low: { type: 'integer' }, refuted: { type: 'integer' }, critic_gaps: { type: 'integer' },
      },
      required: ['confirmed', 'critical', 'high', 'medium', 'low', 'refuted', 'critic_gaps'],
    },
    top: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, title: { type: 'string' }, severity: { type: 'string' }, label: { type: 'string' }, line: { type: 'string' } },
        required: ['id', 'title', 'severity', 'label', 'line'],
      },
    },
  },
  required: ['markdown', 'counts', 'top'],
}

const REFUTERS = [
  { key: 'reproduce', name: 'reproduce-from-bytes', text: `YOUR LENS: REPRODUCE-FROM-BYTES. Re-run or recompute the finding's evidence yourself from the files and git objects in the audit copy (experiments only in your private copy). If the observation does not reproduce exactly, or the cited file:lines do not say what the finding says, refute it. If the finding is REASONED but mechanically checkable, check it mechanically. If you cannot establish the evidence, refute.` },
  { key: 'rule', name: 'rule-text', text: `YOUR LENS: RULE-TEXT. Identify the binding text the finding relies on — a sealed prereg section, the workflow version in force at the time (v1 before 2026-09-26, v2 after, no retroactivity), a decision record, an attestation, or a record's own explicit claim — and quote it briefly with file:line. Does the observed state actually violate it, read correctly and in scope? A record that states a false fact violates its own claim; prose that is merely incomplete or loosely worded without stating a false fact does not. If no binding text is violated, the finding misreads the text, or the rule did not apply at the time, refute.` },
  { key: 'threat', name: 'threat-path', text: `YOUR LENS: THREAT-PATH. Assume the finding's evidence is true. Walk the failure path concretely: which actual input or state leads to which wrong output, wrong claim in a record someone relies on, or unverifiable record? If the path needs inputs or states that cannot occur given the actual data, commits and records, or the consequence is immaterial (no conclusion or decision would change and no record becomes false or unverifiable), refute. Give your honest severity.` },
]

function refutePrompt(f, id, lensTitle, r) {
  return `${PREAMBLE}

YOUR ROLE: ADVERSARIAL REFUTER (${r.name}) of one finding. Private-copy LABEL: ref-${r.key}-${id}.
Your job is to REFUTE this finding. Default to refuted=true when the evidence does not hold, the threat is hypothetical, or the failure path does not reach a wrong conclusion, a wrong claim in a record, or an unverifiable record. refuted=false means you tried hard within your lens and could not refute it.
${r.text}

FINDING ${id} (raised by lens: ${lensTitle}):
${JSON.stringify(f, null, 1)}

Return: refuted; one_line (<=30 words, stands alone in a report); reasoning; evidence (commands + observed output, or quoted file:line); label (REPRODUCED only if you ran or recomputed something); severity_view (your honest severity if it stands, None if refuted); repair_view (is the proposed repair the smallest bounded one, correctly classified, and doable without touching an immutable artifact?).`
}

function verifyFinding(f, id, lensTitle, phaseName) {
  return parallel(REFUTERS.map(r => () => agent(refutePrompt(f, id, lensTitle, r), {
    label: `refute:${r.key}:${id}`, phase: phaseName, schema: VOTE_SCHEMA, effort: 'max',
  }))).then(votes => {
    let incomplete = false
    const vs = votes.map((v, i) => {
      if (v) return { lens: REFUTERS[i].name, ...v }
      incomplete = true
      return { lens: REFUTERS[i].name, refuted: true, one_line: 'REFUTER AGENT FAILED — counted as not confirming', reasoning: '', evidence: '', label: 'REASONED', severity_view: 'None', repair_view: '' }
    })
    const notRefuted = vs.filter(v => !v.refuted).length
    if (incomplete) log(`panel incomplete for ${id}`)
    return { id, lens: lensTitle, ...f, votes: vs, not_refuted: notRefuted, survives: notRefuted >= 2, panel_incomplete: incomplete }
  })
}

phase('Find')
const lensResults = await pipeline(
  LENSES,
  lens => agent(`${PREAMBLE}

YOUR ROLE: FINDER for the lens "${lens.title}". Private-copy LABEL: find-${lens.key}.
Examine the WHOLE repository through this lens, not only the files named below.
${lens.body}

Return: findings (each meeting the evidence standard, locations as path:lines at 18639ee); sound (what you examined and found sound, one line each with its evidence, e.g. "prereg sha256 reproduces at 46b8aef and HEAD: <digest>"); coverage (what you examined and what you did not, honestly); commands (the key commands you ran). Before returning, re-check each finding once against the actual bytes and drop any you cannot support.`,
    { label: `find:${lens.key}`, phase: 'Find', schema: FIND_SCHEMA, effort: 'high' }),
  (res, lens) => {
    if (!res) { log(`finder ${lens.key} returned nothing`); return { lens: lens.title, key: lens.key, res: null, verified: [] } }
    log(`${lens.key}: ${res.findings.length} finding(s) -> 3-refuter panels`)
    return parallel(res.findings.map((f, i) => () => verifyFinding(f, `${lens.key}-${i + 1}`, lens.title, 'Verify')))
      .then(v => ({ lens: lens.title, key: lens.key, res, verified: v.filter(Boolean) }))
  },
)

const lensSummary = lensResults.filter(Boolean).map(r => ({
  lens: r.lens,
  coverage: r.res ? r.res.coverage : 'FINDER FAILED — no coverage',
  sound: r.res ? r.res.sound : [],
  commands: r.res ? r.res.commands : [],
  findings: r.verified.map(v => ({ id: v.id, title: v.title, locations: v.locations, survives: v.survives })),
}))
const lensVerified = lensResults.filter(Boolean).flatMap(r => r.verified)
log(`lens findings: ${lensVerified.length}, surviving: ${lensVerified.filter(v => v.survives).length}`)

phase('Critic')
const critic = await agent(`${PREAMBLE}

YOUR ROLE: COMPLETENESS CRITIC. Private-copy LABEL: critic.
Six lens finders examined the repository. Their coverage notes, what they found sound, their commands and their findings (with panel survival) are below. Your task:
1. List what NO lens examined that could hold a threat to the verdict, a record's truth or reproducibility: every file in 'git ls-tree -r --name-only HEAD' that no coverage note covers; every commit whose diff no lens discussed; every PROJECT_STATE claim no lens checked; every sealed rule no lens traced to code; every tool or validator claim no lens tested; every artifact JSON field no lens reconciled.
2. Examine each of those now, as deeply as needed, under the same evidence standard.
3. Return: unexamined (what you identified); examined_now (what you examined and the result, one line each); unclosed_gaps (what you could not close and why — e.g. forbidden data, bytes not in the repository); findings (NEW findings only, not duplicates of those below); sound.

LENS REPORTS:
${JSON.stringify(lensSummary, null, 1)}`,
  { label: 'critic', phase: 'Critic', schema: CRITIC_SCHEMA, effort: 'high' })

phase('Verify critic')
const criticVerified = critic && critic.findings.length
  ? (await parallel(critic.findings.map((f, i) => () => verifyFinding(f, `critic-${i + 1}`, 'Completeness critic', 'Verify critic')))).filter(Boolean)
  : []
log(`critic findings: ${criticVerified.length}, surviving: ${criticVerified.filter(v => v.survives).length}; unclosed gaps: ${critic ? critic.unclosed_gaps.length : 'CRITIC FAILED'}`)

phase('Synthesis')
const all = [...lensVerified, ...criticVerified]
const synth = await agent(`${PREAMBLE}

YOUR ROLE: SYNTHESIS. Write the CP-AUDIT-01 report for R1 from the panel results below. You may re-check facts in the audit copy (private copy LABEL: synth). You MUST NOT change a panel outcome: survives=true (at least 2 of 3 refuters failed to refute) is CONFIRMED; survives=false is REFUTED. You MAY merge duplicates (a merged finding is confirmed if any instance survived; cite all instance ids and mention the refuted instances' reasons); set the final severity with a one-line reason from the finder's severity and the non-refuting refuters' severity_view (never higher than the highest non-refuting view); state the final label — REPRODUCED only if some agent (the finder, or a refuter that did not refute) actually ran or recomputed it and observed it; otherwise REASONED, written as "REASONED — not reproduced". If you believe a panel outcome is wrong, add a clearly marked "Synthesis note" under it without flipping it. Do not soften or inflate.

FORMAT — Markdown with exactly these sections:
# CP-AUDIT-01 — R1 rigour audit (nq-event-diffusion-research @ 18639ee)
## 1. Scope and method — target commit and the commits it covers; the six lenses; the three refuter lenses (reproduce-from-bytes, rule-text, threat-path) and the survival rule (a finding survives only if at least 2 of 3 fail to refute; a failed refuter agent counts as not confirming); the completeness critic and the same panel on its findings; the baseline machine checks and their results; the read-only and no-outcome-data conditions (audit ran in a scratch clone, byte-identical at the target commit); include this line verbatim: "Workflow run ID: {{RUN_ID}} · script: {{SCRIPT}}".
## 2. Verdict — exactly two sentences: does the record support its stated conclusion and state as reproducible and rule-computed — yes / no / with caveats.
## 3. Confirmed findings — ranked Critical -> High -> Medium -> Low. For each: "### <id(s)> — <title>" then bullets: Severity (+ reason) · Location (file:lines) · Evidence · Threat · Failure path · Label · Refuters — reproduce-from-bytes: <one line>; rule-text: <one line>; threat-path: <one line> · Smallest bounded repair — <text> [<CLASS>] · Without touching an immutable artifact: yes/no — <how>.
## 4. Refuted findings — one line each: id — title — why refuted (from the refuters), so nobody re-raises them.
## 5. Examined and found sound — explicit, grouped by lens, deduplicated; include the critic's sound items.
## 6. Critic's unclosed gaps — each with why it could not be closed.
## 7. Recommended next actions — (a) needs the delegate's decision; (b) the builder may do alone once the delegate has accepted the findings. Nothing is repaired before acceptance; R1 corrections are new dated files only.

Also return counts (after merging duplicates; critic_gaps = number of unclosed gaps) and top (up to 5 most severe confirmed findings, each with id, title, severity, label and a one-line summary).

PANEL RESULTS (all findings with their three votes):
${JSON.stringify(all, null, 1)}

LENS COVERAGE AND SOUND LISTS:
${JSON.stringify(lensSummary.map(s => ({ lens: s.lens, coverage: s.coverage, sound: s.sound })), null, 1)}

CRITIC:
${JSON.stringify(critic, null, 1)}`,
  { label: 'synthesis', phase: 'Synthesis', schema: SYNTH_SCHEMA, effort: 'max' })

return { synth, all, lensSummary, critic }
