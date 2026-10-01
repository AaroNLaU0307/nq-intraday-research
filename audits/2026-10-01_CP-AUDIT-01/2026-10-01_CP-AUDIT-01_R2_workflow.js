export const meta = {
  name: 'cp-audit-01-r2',
  description: 'CP-AUDIT-01: read-only rigour audit of R2 nq-letf-rebalancing-research @7fc4e83 — 6 lens finders, 3-lens adversarial refutation per finding, completeness critic, synthesis',
  phases: [
    { title: 'Find', detail: 'six lens finders over the whole repository' },
    { title: 'Verify', detail: 'three refuters per finding: reproduce-from-bytes, rule-text, threat-path; survives if >=2 of 3 fail to refute' },
    { title: 'Critic', detail: 'completeness critic examines what no lens covered' },
    { title: 'Verify critic', detail: 'same three-refuter panel on critic findings' },
    { title: 'Synthesis', detail: 'one report in the CP-AUDIT-01 format' },
  ],
}

const SP = '/c/Users/Aaron/AppData/Local/Temp/claude/C--Users-Aaron-OneDrive-Desktop-Quant-trade/ba5d35b4-c6d4-480a-9d6c-eba4fdb6557a/scratchpad'
const REPO = SP + '/r2_clone'
const REPOW = 'C:/Users/Aaron/AppData/Local/Temp/claude/C--Users-Aaron-OneDrive-Desktop-Quant-trade/ba5d35b4-c6d4-480a-9d6c-eba4fdb6557a/scratchpad/r2_clone'

const PREAMBLE = `CP-AUDIT-01 — READ-ONLY RIGOUR AUDIT OF R2 (nq-letf-rebalancing-research) AT COMMIT 7fc4e83.
R2 is PRE-S1: no hypothesis, no preregistration, no outcome access (stated OUTCOME_EXPOSURE = NONE). A forward point-in-time (PIT) collector of ProShares/ProFunds fund NAV files (QLD QID PSQ TQQQ SQQQ) runs daily from Windows Task Scheduler (task QuantTrade-R2-ForwardPIT, 11:00 +08:00). Git history: bd66324 "R2 baseline as found 2026-10-01 (pre-v2-conformance)" then e1eb266, a6798b5, 33ee5cc (G-3 correction of record), b64d40f, fa01d04, e11a1c9 (tools/reproduce.py + README), 7fc4e83. Everything that happened before bd66324 was never in git: the baseline commit carries it all at once, so git cannot order events before it — only internal dates and captured bytes can.

WHERE TO WORK
- AUDIT COPY — read files, git history, run tests/tools here and only here: ${REPO}  (Windows form: ${REPOW}). A fresh clone, clean, checked out at 7fc4e8324c07c6ed2290584aa8650ca3ab87cd7e with full history. Do NOT modify it: other agents use it concurrently.
- PRIVATE COPY for ANY experiment that modifies bytes (mutation tests, tampered snapshots, altered PROJECT_STATE counts, scratch scripts): cp -r "${REPO}" "${SP}/mut/<LABEL>" with the LABEL given in your role line; work there; scratch scripts under ${SP}/mut/<LABEL>-scratch/.
- Workflow authority: C:/Users/Aaron/OneDrive/Desktop/Quant trade/QUANT_WORKFLOW_VNEXT.md (v2, activated 2026-09-26, no retroactivity; R2's records were rewritten for v2 conformance on 2026-10-01, so v2 governs the current records; acts before 2026-09-26 are judged under v1: C:/Users/Aaron/OneDrive/Desktop/Quant trade/Workspace Docs/workflow-evolution-2026-09-22/QUANT_WORKFLOW_VNEXT_v1_TEXT_2026-09-12.md).
- KB, read-only: C:/Users/Aaron/OneDrive/Desktop/Quant trade/quant-research-knowledge-base.
- The REAL project directory C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research is OFF LIMITS (its working tree has an uncommitted decision-log row that is out of scope; audit the committed tree only).

HARD RULES (breaking any invalidates the audit)
1. Read-only: create or modify nothing outside ${SP}/mut/. No state-changing git command outside your private copy.
2. Allowed to run in the audit copy: cd "${REPO}" && export PYTHONDONTWRITEBYTECODE=1 && python -m pytest tools -q -p no:cacheprovider ; python tools/reproduce.py ; python tools/collect_forward_pit.py --verify <snapshot_dir> .
3. NEVER run: tools/collect_forward_pit.py without --verify; tools/run_forward_pit_scheduled.py; tools/task_action.py (except as imported by pytest); tools/run_forward_pit_task.cmd; tools/install_forward_pit_task.ps1; tools/remove_forward_pit_task.ps1; schtasks or any Task Scheduler / registry command. No network access of any kind — the collector's tests mock HTTP; read a test before running it in a mutated copy and never let a mutation reach a real HTTP call. Never open, list or read C:/Users/Aaron/quant-data (the NQ archive).
4. Environment: Git Bash; python = Python 3.13.14. Cite lines at the target commit (nl -ba / grep -n).

EVIDENCE STANDARD
- A finding names a concrete THREAT to a research conclusion, a record's truth, or reproducibility, AND a concrete FAILURE PATH: which input or state leads to which wrong output, wrong claim or unverifiable record.
- NOT findings: style; "could be cleaner"; generic best practice; "another reviewer would add confidence"; hypotheticals that cannot reach a wrong conclusion or an unverifiable record given the actual data and state.
- Label: REPRODUCED = you ran or recomputed something and observed it (give the command and the observed output); REASONED = from reading (give file:line).
- Prose agreeing with code is not evidence for the code. A record disagreeing with the captured bytes IS a finding.
- Defects the project already records (e.g. backlog BL-R2-01, the G-1..G-10 list, MISSING_FORWARD_CAPTURE) are NOT new findings unless the record is inaccurate, incomplete, or understates the consequence — check them and say which.
- Severity: Critical = outcome exposure actually occurred, or a record falsely establishes PIT/source eligibility such that S1 could be built on non-PIT data; High = the collector/verification can accept altered or incomplete evidence undetected, or a load-bearing record (one the next decision relies on) is false; Medium = a check is weaker than claimed or a record is false but not load-bearing for the next decision; Low = a minor but real record inaccuracy. Do not inflate.
- Zero findings is a valid result.
- TWO HISTORIES: R2 is pre-seal, so findings may lead to ordinary fixes. BUT DECISION_LOG.md is append-only, captured evidence (data_forward_pit/, data_probe/, logs/) must never be rewritten, and committed dated amendment/correction files are immutable: state whether the smallest repair touches any of those (if so it must be a new dated correction or an appended row instead).
- Repair classes: IMPLEMENTATION_FIX | DATA_FIX | ANALYSIS_EXTENSION | METHODOLOGY_CHANGE | RECORD_CORRECTION.

BASELINE MACHINE CHECKS the orchestrator already ran in the audit copy (rerun if your lens needs it): pytest tools -> 40 passed, 12 subtests passed. tools/reproduce.py -> REPRODUCE PASS, exit 0, printing: tests PASS; counts as of 2026-09-30/144521_ET (later snapshots 0); snapshots 15 verified 15/15; jsonl rows 14; NATURAL 9 (catch-ups > 300s late: 2); MANUAL 6 (incl. no-log-row snapshots: 2026-09-19/125150_ET); trigger boundary 2026-09-21T11:00:00+08:00; collector 1.1.0, manifest schema {1: 1, 2: 14}; natural not clean: none; info only: raw 'task start' blocks = 14, captures with block = 14, without = 1; md links 33 relative links checked, 0 broken; per-capture slot -> snapshot: 2026-09-19T11:00 -> 2026-09-19/131606_ET late 51366.1s SCHEDULER_VALIDATION manual; 2026-09-21T11:00 -> 2026-09-21/063831_ET, 063916_ET, 064554_ET, 070042_ET (late ~27.5k-28.8k s, ROUTINE_FORWARD_COLLECTION, manual); 2026-09-22T11:00 -> 2026-09-21/230004_ET late 4.6s NATURAL; 2026-09-23 -> 2026-09-22/230004_ET NATURAL; 2026-09-24 -> 2026-09-23/230004_ET NATURAL; 2026-09-25 -> 2026-09-24/230004_ET NATURAL; 2026-09-26 -> 2026-09-25/230005_ET NATURAL; 2026-09-27 -> 2026-09-27/020143_ET late 10903.8s NATURAL catch-up; 2026-09-28 -> 2026-09-27/230001_ET NATURAL; 2026-09-29 -> 2026-09-28/230001_ET NATURAL; 2026-09-30 -> 2026-09-30/144521_ET late 56721.5s NATURAL catch-up; all COMPLETED 5/5 verified=True. python tools/collect_forward_pit.py --verify data_forward_pit/2026-09-30/144521_ET -> VERIFY PASS. The audit copy stays clean after these runs.`

const LENSES = [
  { key: 'blindness', title: 'Outcome blindness', body: `Establish from the bytes whether OUTCOME_EXPOSURE = NONE is true. Search every file at 7fc4e83 and every blob in history (git log -p --all; git grep over git rev-list --all) for: NQ or NDX-futures price/return/volatility/volume numbers or statistics (especially late-day window behaviour), references to reading the NQ archive (quant-data paths, databento, ohlcv, NQ.v.0, .dbn, .zst), any code or notebook that loads NQ data, results that could only come from outcome data, numbers imported from R1's revealed outcome or ITSF outcomes, and literature effect sizes presented as R2 measurements. Every feasibility figure (R2_FEASIBILITY_REPORT.md, R2_MINIMUM_DATA_CONTRACT.md, R2_DATA_SOURCE_AUDIT.md, R2_G3_*.md, handoffs/*) must be fund-side only (ETF NAV, shares outstanding, AUM, publication timing): trace each numeric table to its source in data_probe/ or data_forward_pit/ and say whether it is fund-side. Fund NAV data is not NQ outcome, but a computed fund-side quantity that is effectively a function of index returns in the future hypothesis's window could expose the target — assess whether any such computation exists and whether it matters for R2's question (a late-day rebalancing footprint in NQ futures). Check PROJECT_STATE flags NQ_DATA_DECODED NO, NQ_RETURN_COMPUTED NO, R2_PNL_COMPUTED NO, DATA_GRANT 'GRANTED, NOT EXERCISED', and the trial-accounting statement (sample ordinal 3, R2 trial 1) against the bytes.` },
  { key: 'collector', title: 'Forward PIT collector and wrapper', body: `Audit tools/collect_forward_pit.py, tools/run_forward_pit_scheduled.py, tools/task_action.py, tools/reproduce.py, tools/run_forward_pit_task.cmd, ops/R2_FORWARD_PIT_TASK.xml and ops/R2_FORWARD_PIT_TASK.template.xml, and the .ps1 installers (read only; never run). Check: timestamps and DST (ET folder names written from a +08:00 machine; the US DST change on 2026-11-01 and how slot/trigger times map; UTC vs local in manifests and the JSONL log; the slot/trigger computation in reproduce.py); hashing and --verify (exactly what is hashed — body bytes, headers, manifest; is MANIFEST.sha256 a hash of MANIFEST.json; could a snapshot's CSV and its manifest(s) be altered consistently without detection, i.e. is there any anchor outside the snapshot such as the JSONL log or a git commit that binds the hash; does --verify check file-set completeness, extra and missing files); failure preservation (on HTTP error or partial capture what is written, whether a failed capture is preserved or silently dropped, exit codes, what the wrapper logs); lock and duplicate handling (two concurrent runs, re-run in the same slot, same-second folder collisions); whether reproduce.py checks what it claims (list its claims from its docstring, README.md and PROJECT_STATE and verify each; prove by mutation in your private copy — e.g. tamper a CSV byte and its manifests consistently, delete a snapshot, add or drop a JSONL row, alter a PROJECT_STATE count — what it catches); the recorded BOM defect BL-R2-01 (find its record, reproduce it, assess whether its stated scope and impact are accurate and which snapshots are affected); whether the natural-vs-manual capture rule in DECISION_LOG.md (D-R2-2026-10-01-02: NATURAL = task-start block present AND capture_type = ROUTINE_FORWARD_COLLECTION AND scheduled_time >= StartBoundary 2026-09-21T11:00+08:00 AND sole recorded invocation for its slot; all else MANUAL) is applied by reproduce.py exactly as written — recompute the classification of each of the 15 snapshots by hand from logs/ and the manifests and compare, paying attention to the 'sole recorded invocation' clause and to catch-ups.` },
  { key: 'od6g3', title: 'OD-6 and the G-3 historical-PIT claims', body: `Read R2_DELEGATED_OWNER_DECISIONS.md (the exact OD-6 text and OD-1/2/5), R2_G3_ACCEPTANCE_CRITERIA.md, R2_G3_HISTORICAL_PIT_AMENDMENT.md, R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md, R2_G3_PUBLICATION_TIMING_REPORT.md, DECISION_LOG.md (D-R2-2026-10-01-01, the 2026-10-01 correction of record, commit 33ee5cc) and PROJECT_STATE's CAUSAL_TIMING block. Check every historical-PIT claim against the evidence in data_probe/: raw headers (Date, Last-Modified), archive-capture timestamps in capture filenames, body CSV contents; recompute every hash in data_probe/g3_historical_pit_2026-09-19/MANIFEST.sha256 and any other hash the documents quote. In particular: AUM_FIELD_OBSERVED_START = 2014-03-26 — does a capture actually show the field then, and is it stated as an observation rather than availability; HISTORICAL_DAILY_PIT_SAFE_START = NOT_ESTABLISHED — does any document still state or imply an established start; G-11 staleness (the 2016-04-01 missed day) — reproduce from captures; any neighbouring-date inference, forward-fill, or 'typical behaviour' reasoning that OD-6 forbids (inferring one date's publication time from other dates; assuming daily publication because most days were published; treating a capture at time T as proof of availability earlier than T). Check that the 2026-10-01 correction of record is complete: every document that carried the corrected label is corrected or explicitly superseded, and no live statement anywhere contradicts it (compare bd66324 vs 33ee5cc vs HEAD).` },
  { key: 'vendor', title: 'Vendor evidence handling', body: `R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md must have been fixed before any candidate was judged: establish what the bytes can prove about that order (internal dates, cross-references, the baseline handoff; git cannot order pre-bd66324 events) and flag any record that claims an order the bytes cannot support, or any sign the criteria were edited after judgments. The tracker (R2_VENDOR_RESPONSE_TRACKER.md) must never promote a candidate on sales language: check each status against the criteria's definitions. Every SV-1 matrix claim (R2_SV1_SOURCE_MATRIX.md, R2_SV1_SOURCE_VERIFICATION_REPORT.md) must be traceable to a cited source (URL, document, captured file): flag claims with no traceable source that the classification relies on. The dispatch record (R2_VENDOR_WAVE1_DISPATCH.md, vendor_outbound/*.md, R2_SV1_VENDOR_ENQUIRY_PACKET.md) must match the tracker and PROJECT_STATE (who, when, channel, content; 6/6 sent; 0 evidentiary responses; ETF Global clarification answered; Morningstar routed to Sales, SELF-REPORTED, in a6798b5). Find stale headers that state incompatible live facts (a header saying awaiting dispatch while dispatch is recorded, response counts that disagree, statuses superseded elsewhere). Reproduce the 2016 acid test 0/20 and check that R2_PATH_C_PARK_TRIGGER = NO follows from the criteria as defined.` },
  { key: 'records', title: 'Record consistency', body: `Check PROJECT_STATE.md (v2 section 6: one screen of about 60 lines, current state only, superseded facts deleted) against DECISION_LOG.md, R2_VENDOR_RESPONSE_TRACKER.md, R2_FORWARD_PIT_COLLECTION.md, README.md, logs/*, the snapshot manifests and handoffs/*. For every derived count PROJECT_STATE shows (snapshots, verified, JSONL rows, NATURAL, catch-ups, MANUAL, last snapshot, vendor counts), determine whether it is generated or compared by tools/reproduce.py or hand-copied, and whether it is true. Parse logs/forward_pit_scheduler.jsonl, logs/forward_pit_console.log and logs/forward_pit_task_stdout.log: UTC ordering of rows, timezone consistency, duplicates, rows without snapshots and snapshots without rows. The missing 2026-09-20 11:00 firing record: from ops/*.xml (StartBoundary), the logs, R2_FORWARD_PIT_COLLECTION.md, DECISION_LOG.md and PROJECT_STATE, determine what should exist for the 2026-09-20 and 2026-09-21 11:00 +08:00 slots, what does, and whether every record describes it the same way (MISSING_FORWARD_CAPTURE, not backfilled). Decision-log rows: each binding decision has id, UTC, decider, decision, evidence pointer; rows are written when the event happened (compare with commit times) and verbatim sections match rows; UNKNOWN where not establishable. Retired vocabulary (v2 section 12) used as live routing or gates in current records. README's artifact map vs the tree. Links: which links does reproduce.py check, and are links that leave the repository (e.g. to ../QUANT_WORKFLOW_VNEXT.md) checked or silently skipped?` },
  { key: 'tests', title: 'Test adequacy', body: `Run pytest in the audit copy. For each rule the collector, wrapper, task_action and reproduce.py enforce (hash verification, file-set completeness, manifest schema, lock/duplicate refusal, failure preservation, exit codes, NATURAL/MANUAL classification, PROJECT_STATE count comparison, BOM handling, timestamps and DST, link checking), identify the test that fails if the rule is removed and prove it by mutation in your private copy. Which enforced rules have no test? Can the synthetic fixtures produce the failure cases (HTTP error, partial capture, truncated body, BOM, DST boundary, duplicate slot, clock skew, missing log row, catch-up)? What would reproduce.py pass that it should fail: construct concrete cases in your private copy (a snapshot whose CSV, MANIFEST.json and MANIFEST.sha256 are all consistently altered; a deleted snapshot plus a consistently edited PROJECT_STATE; an extra file inside a snapshot; a JSONL row pointing to a nonexistent snapshot; a reordered log) and report which pass. Never let a mutated test reach the network.` },
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
    immutable_touch: { type: 'string', description: 'does the repair touch the append-only log, captured evidence or a committed dated amendment? yes/no + how it is done instead' },
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
  { key: 'rule', name: 'rule-text', text: `YOUR LENS: RULE-TEXT. Identify the binding text the finding relies on — the workflow version in force at the time (v1 before 2026-09-26, v2 after, no retroactivity), an OD decision in R2_DELEGATED_OWNER_DECISIONS.md, a DECISION_LOG row or verbatim section, an acceptance-criteria file, or a record's or tool's own explicit claim — and quote it briefly with file:line. Does the observed state actually violate it, read correctly and in scope? A record that states a false fact violates its own claim; prose that is merely incomplete or loosely worded without stating a false fact does not. If no binding text is violated, the finding misreads the text, or the rule did not apply at the time, refute.` },
  { key: 'threat', name: 'threat-path', text: `YOUR LENS: THREAT-PATH. Assume the finding's evidence is true. Walk the failure path concretely: which actual input or state leads to which wrong output, wrong claim in a record the next decision relies on, or unverifiable record? If the path needs inputs or states that cannot occur given the actual data, commits, schedule and records, or the consequence is immaterial (no conclusion or decision would change and no record becomes false or unverifiable), refute. Give your honest severity.` },
]

function refutePrompt(f, id, lensTitle, r) {
  return `${PREAMBLE}

YOUR ROLE: ADVERSARIAL REFUTER (${r.name}) of one finding. Private-copy LABEL: ref-${r.key}-${id}.
Your job is to REFUTE this finding. Default to refuted=true when the evidence does not hold, the threat is hypothetical, or the failure path does not reach a wrong conclusion, a wrong claim in a record, or an unverifiable record. refuted=false means you tried hard within your lens and could not refute it.
${r.text}

FINDING ${id} (raised by lens: ${lensTitle}):
${JSON.stringify(f, null, 1)}

Return: refuted; one_line (<=30 words, stands alone in a report); reasoning; evidence (commands + observed output, or quoted file:line); label (REPRODUCED only if you ran or recomputed something); severity_view (your honest severity if it stands, None if refuted); repair_view (is the proposed repair the smallest bounded one, correctly classified, and does it avoid rewriting the append-only log, captured evidence or a committed dated amendment?).`
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

Return: findings (each meeting the evidence standard, locations as path:lines at 7fc4e83); sound (what you examined and found sound, one line each with its evidence); coverage (what you examined and what you did not, honestly); commands (the key commands you ran). Before returning, re-check each finding once against the actual bytes and drop any you cannot support.`,
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
1. List what NO lens examined that could hold a threat to a record's truth, outcome blindness, PIT eligibility or reproducibility: every file in 'git ls-tree -r --name-only HEAD' that no coverage note covers (including handoffs/, vendor_outbound/, R2_S0_PROVENANCE.md, R2_MINIMUM_DATA_CONTRACT.md, R2_DATA_SOURCE_AUDIT.md, R2_FEASIBILITY_REPORT.md, the .ps1/.cmd tools, .gitattributes/.gitignore); every commit whose diff no lens discussed; every PROJECT_STATE claim no lens checked (e.g. the Task Scheduler facts: principal LogonType Password, RunLevel Limited, State Ready, next run — which the bytes may or may not support); every tool claim no lens tested.
2. Examine each of those now, as deeply as needed, under the same evidence standard.
3. Return: unexamined (what you identified); examined_now (what you examined and the result, one line each); unclosed_gaps (what you could not close and why — e.g. facts only the live Task Scheduler or the vendor could establish, bytes not in the repository); findings (NEW findings only, not duplicates of those below); sound.

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

YOUR ROLE: SYNTHESIS. Write the CP-AUDIT-01 report for R2 from the panel results below. You may re-check facts in the audit copy (private copy LABEL: synth). You MUST NOT change a panel outcome: survives=true (at least 2 of 3 refuters failed to refute) is CONFIRMED; survives=false is REFUTED. You MAY merge duplicates (a merged finding is confirmed if any instance survived; cite all instance ids and mention the refuted instances' reasons); set the final severity with a one-line reason from the finder's severity and the non-refuting refuters' severity_view (never higher than the highest non-refuting view); state the final label — REPRODUCED only if some agent (the finder, or a refuter that did not refute) actually ran or recomputed it and observed it; otherwise REASONED, written as "REASONED — not reproduced". If you believe a panel outcome is wrong, add a clearly marked "Synthesis note" under it without flipping it. Do not soften or inflate.

FORMAT — Markdown with exactly these sections:
# CP-AUDIT-01 — R2 rigour audit (nq-letf-rebalancing-research @ 7fc4e83)
## 1. Scope and method — target commit and the commits it covers; the six lenses; the three refuter lenses (reproduce-from-bytes, rule-text, threat-path) and the survival rule (a finding survives only if at least 2 of 3 fail to refute; a failed refuter agent counts as not confirming); the completeness critic and the same panel on its findings; the baseline machine checks and their results; the read-only, no-network, no-live-collector and no-outcome-data conditions (audit ran in a scratch clone, byte-identical at the target commit; the real working tree's uncommitted decision-log row was out of scope); include this line verbatim: "Workflow run ID: {{RUN_ID}} · script: {{SCRIPT}}".
## 2. Verdict — exactly two sentences: does the record support its stated state (PRE-S1, OUTCOME_EXPOSURE = NONE, the forward-collection counts, the G-3/OD-6 status, the vendor status) as reproducible and rule-computed — yes / no / with caveats.
## 3. Confirmed findings — ranked Critical -> High -> Medium -> Low. For each: "### <id(s)> — <title>" then bullets: Severity (+ reason) · Location (file:lines) · Evidence · Threat · Failure path · Label · Refuters — reproduce-from-bytes: <one line>; rule-text: <one line>; threat-path: <one line> · Smallest bounded repair — <text> [<CLASS>] · Touches append-only log / captured evidence / committed dated amendment: yes/no — <how it is done instead>.
## 4. Refuted findings — one line each: id — title — why refuted (from the refuters), so nobody re-raises them.
## 5. Examined and found sound — explicit, grouped by lens, deduplicated; include the critic's sound items.
## 6. Critic's unclosed gaps — each with why it could not be closed.
## 7. Recommended next actions — (a) needs the delegate's decision; (b) the builder may do alone once the delegate has accepted the findings. Nothing is repaired before acceptance.

Also return counts (after merging duplicates; critic_gaps = number of unclosed gaps) and top (up to 5 most severe confirmed findings, each with id, title, severity, label and a one-line summary).

PANEL RESULTS (all findings with their three votes):
${JSON.stringify(all, null, 1)}

LENS COVERAGE AND SOUND LISTS:
${JSON.stringify(lensSummary.map(s => ({ lens: s.lens, coverage: s.coverage, sound: s.sound })), null, 1)}

CRITIC:
${JSON.stringify(critic, null, 1)}`,
  { label: 'synthesis', phase: 'Synthesis', schema: SYNTH_SCHEMA, effort: 'max' })

return { synth, all, lensSummary, critic }
