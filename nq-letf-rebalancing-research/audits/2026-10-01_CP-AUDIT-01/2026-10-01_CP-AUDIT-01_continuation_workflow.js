export const meta = {
  name: 'cp-audit-01-continuation',
  description: 'CP-AUDIT-01 continuation (R1 + R2) under delegate token-economy decision: dedup groups, one threat-path refuter for Medium/Low (3 for Critical/High), critics, syntheses — at most 10 agents in flight',
  phases: [
    { title: 'Verify', detail: 'remaining refuter votes on deduplicated groups, batches of 10' },
    { title: 'Critic', detail: 'one completeness critic per project' },
    { title: 'Verify critic', detail: 'critic findings: 3 refuters if Critical/High, 1 sole threat-path refuter otherwise; batches of 10' },
    { title: 'Synthesis', detail: 'one report per project' },
  ],
}

const SP = '/c/Users/Aaron/AppData/Local/Temp/claude/C--Users-Aaron-OneDrive-Desktop-Quant-trade/ba5d35b4-c6d4-480a-9d6c-eba4fdb6557a/scratchpad'
const STATE = { r1: SP + '/state/r1_state.json', r2: SP + '/state/r2_state.json' }

const R1REPO = SP + '/ws/nq-event-diffusion-research'
const R2REPO = SP + '/r2_clone'

const PRE = {}
PRE.r1 = `CP-AUDIT-01 — READ-ONLY RIGOUR AUDIT OF R1 (nq-event-diffusion-research) AT COMMIT 18639ee.
R1 is a CLOSED lineage: sealed preregistration at CONTENT_COMMIT 46b8aef (seal attestation commit 595af1c, annotated tag r1-s1-sealed); S2 build (code 433e2cc, build attestation commit b99e10e, tag r1-s2-built); S3-A power gate (7426a2f); one governed Primary run R1-S3B-001 (28ed268); S4 verdict and lifecycle STOP (18639ee, tag r1-final). Pre-seal: 8656701, 66d9b43 (tag r1-pre-seal).

WHERE TO WORK
- AUDIT COPY — read files, git history and run tests/tools here and only here: ${R1REPO}. A fresh clone of the project, clean, checked out at 18639eea08ae89fa905866e8427caa48e4411d53, full history and all four annotated tags. Do NOT modify it: other agents use it concurrently.
- ITSF sibling so R1's own cross-check tests run: ${SP}/ws/Intraday Trend Strategy Framework — src/itsf exported from ITSF commit 11725fb (pins MATCH) and gate1/f10_event_calendar/f10_events.csv (sha256 5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c = the OD-1 grant digest; release dates/times only, no market data; you may read it).
- PRIVATE COPY for ANY experiment that modifies bytes: cp -r "${SP}/ws" "${SP}/mut/<LABEL>" with the LABEL given in your role line, then work in ${SP}/mut/<LABEL>/nq-event-diffusion-research. Put scratch scripts under ${SP}/mut/<LABEL>/.
- Workflow authority: C:/Users/Aaron/OneDrive/Desktop/Quant trade/QUANT_WORKFLOW_VNEXT.md (v2, activated 2026-09-26, NO retroactivity). R1 ran and closed 2026-09-17..18 under v1 (cutover 2026-09-12), text at C:/Users/Aaron/OneDrive/Desktop/Quant trade/Workspace Docs/workflow-evolution-2026-09-22/QUANT_WORKFLOW_VNEXT_v1_TEXT_2026-09-12.md. Judge an act by the rule in force when it happened; judge a record's present truth by what it says now.
- KB, read-only: C:/Users/Aaron/OneDrive/Desktop/Quant trade/quant-research-knowledge-base.
- The REAL project directory C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-event-diffusion-research is OFF LIMITS (not even git status).

HARD RULES (breaking any invalidates the audit)
1. Read-only: create or modify nothing outside ${SP}/mut/. No state-changing git command outside your private copy.
2. Tests: cd "${R1REPO}" && export PYTHONDONTWRITEBYTECODE=1 && python -m pytest tests -q -p no:cacheprovider . Tools you may run: tools/validate_state.py, tools/validate_seal_snapshot.py, psmv/validate_prereg.py. Anything else: read it first; run it only if it reads no market data.
3. NO OUTCOME DATA: never open, list, stat or run anything that reads C:/Users/Aaron/quant-data. psmv/psmv_structural.py and r1/dev_adapter.py against real data must NOT be executed. No network access of any kind.
4. The sealed outcome runs/R1-S3B-001/sealed_r1_outcome.json was revealed under Owner authorization on 2026-09-18; reading and recomputing from it is allowed.
5. Environment: Git Bash; python = Python 3.13.14 (numpy 2.5.0, pandas 2.3.3, pytest 9.1.1). Cite lines at the target commit.

EVIDENCE STANDARD
- A finding names a concrete THREAT to a research conclusion, a record's truth, or reproducibility, AND a concrete FAILURE PATH: which input or state leads to which wrong output, wrong claim or unverifiable record.
- NOT findings: style; "could be cleaner"; generic best practice; "another reviewer would add confidence"; hypotheticals that cannot reach a wrong conclusion or an unverifiable record given the actual data and state.
- Label: REPRODUCED = you ran or recomputed something and observed it; REASONED = from reading (file:line).
- Prose agreeing with code is not evidence for the code. A sealed artifact disagreeing with prose IS a finding.
- Already-disclosed defects (PROJECT_STATE PERMANENT_RESIDUALS OUTCOME_SCHEMA_LABEL_DEFECT and AXIS2_EVIDENCE_PROVENANCE_GAP; R1_SEALED_ERRATA.md E-1; P-5) are not new findings unless the disclosure is inaccurate, incomplete, or understates the consequence.
- Severity: Critical = the recorded verdict/conclusion is wrong or unsupported, or outcome contamination reached the result; High = a load-bearing rule or record is false or unenforced so the conclusion or its reproducibility is materially uncertain; Medium = a record is false or a check is weaker than claimed but the conclusion stands; Low = a minor but real record inaccuracy. Do not inflate. Zero findings is valid.
- TWO HISTORIES: R1's sealed artifacts, runs/, ledgers, attestations and verdict are IMMUTABLE — a repair can only be a NEW dated correction file (or a change to unsealed tooling).
- Repair classes: IMPLEMENTATION_FIX | DATA_FIX | ANALYSIS_EXTENSION | METHODOLOGY_CHANGE | RECORD_CORRECTION.

BASELINE MACHINE CHECKS (orchestrator, audit copy): pytest tests -> 285 passed; tools/validate_state.py -> 60 passed, 0 failed; tools/validate_seal_snapshot.py -> PASS (161 at 46b8aef, 185 at 595af1c); psmv/validate_prereg.py -> 183 passed, 2 FAILED at HEAD ("state: S2 NOT AUTHORIZED", "state: outcome reveal not granted"); ITSF pins MATCH.`

PRE.r2 = `CP-AUDIT-01 — READ-ONLY RIGOUR AUDIT OF R2 (nq-letf-rebalancing-research) AT COMMIT 7fc4e83.
R2 is PRE-S1: no hypothesis, no preregistration, no outcome access (stated OUTCOME_EXPOSURE = NONE). A forward point-in-time (PIT) collector of ProShares/ProFunds fund NAV files (QLD QID PSQ TQQQ SQQQ) runs daily from Windows Task Scheduler (task QuantTrade-R2-ForwardPIT, 11:00 +08:00). Git history: bd66324 "R2 baseline as found 2026-10-01 (pre-v2-conformance)" then e1eb266, a6798b5, 33ee5cc (G-3 correction of record), b64d40f, fa01d04, e11a1c9 (tools/reproduce.py + README), 7fc4e83. Everything before bd66324 was never in git, so git cannot order events before it — only internal dates and captured bytes can.

WHERE TO WORK
- AUDIT COPY — read files, git history, run tests/tools here and only here: ${R2REPO}. A fresh clone, clean, checked out at 7fc4e8324c07c6ed2290584aa8650ca3ab87cd7e with full history. Do NOT modify it.
- PRIVATE COPY for ANY experiment that modifies bytes: cp -r "${R2REPO}" "${SP}/mut/<LABEL>" with the LABEL given in your role line; scratch scripts under ${SP}/mut/<LABEL>-scratch/.
- Workflow authority: C:/Users/Aaron/OneDrive/Desktop/Quant trade/QUANT_WORKFLOW_VNEXT.md (v2, activated 2026-09-26, no retroactivity; v2 governs R2's current records; acts before 2026-09-26 are judged under v1: C:/Users/Aaron/OneDrive/Desktop/Quant trade/Workspace Docs/workflow-evolution-2026-09-22/QUANT_WORKFLOW_VNEXT_v1_TEXT_2026-09-12.md).
- KB, read-only: C:/Users/Aaron/OneDrive/Desktop/Quant trade/quant-research-knowledge-base.
- The REAL project directory C:/Users/Aaron/OneDrive/Desktop/Quant trade/nq-letf-rebalancing-research is OFF LIMITS (its uncommitted decision-log row is out of scope; audit the committed tree only).

HARD RULES (breaking any invalidates the audit)
1. Read-only: create or modify nothing outside ${SP}/mut/. No state-changing git command outside your private copy.
2. Allowed in the audit copy: cd "${R2REPO}" && export PYTHONDONTWRITEBYTECODE=1 && python -m pytest tools -q -p no:cacheprovider ; python tools/reproduce.py ; python tools/collect_forward_pit.py --verify <snapshot_dir> .
3. NEVER run: tools/collect_forward_pit.py without --verify; tools/run_forward_pit_scheduled.py; tools/task_action.py (except as imported by pytest); tools/run_forward_pit_task.cmd; tools/install_forward_pit_task.ps1; tools/remove_forward_pit_task.ps1; schtasks or any Task Scheduler / registry command. No network access of any kind; never let a mutated test reach a real HTTP call. Never open, list or read C:/Users/Aaron/quant-data.
4. Environment: Git Bash; python = Python 3.13.14. Cite lines at the target commit.

EVIDENCE STANDARD
- A finding names a concrete THREAT to a research conclusion, a record's truth, or reproducibility, AND a concrete FAILURE PATH: which input or state leads to which wrong output, wrong claim or unverifiable record.
- NOT findings: style; "could be cleaner"; generic best practice; "another reviewer would add confidence"; hypotheticals that cannot reach a wrong conclusion or an unverifiable record given the actual data and state.
- Label: REPRODUCED = you ran or recomputed something and observed it; REASONED = from reading (file:line).
- Prose agreeing with code is not evidence for the code. A record disagreeing with the captured bytes IS a finding.
- Already-recorded defects (BL-R2-01, the G-1..G-10 list, MISSING_FORWARD_CAPTURE) are not new findings unless the record is inaccurate, incomplete, or understates the consequence.
- Severity: Critical = outcome exposure actually occurred, or a record falsely establishes PIT/source eligibility such that S1 could be built on non-PIT data; High = the collector/verification can accept altered or incomplete evidence undetected, or a load-bearing record (one the next decision relies on) is false; Medium = a check weaker than claimed or a record false but not load-bearing for the next decision; Low = a minor but real record inaccuracy. Do not inflate. Zero findings is valid.
- TWO HISTORIES: R2 is pre-seal, so findings may lead to ordinary fixes, BUT DECISION_LOG.md is append-only, captured evidence (data_forward_pit/, data_probe/, logs/) must never be rewritten, and committed dated amendment/correction files are immutable.
- Repair classes: IMPLEMENTATION_FIX | DATA_FIX | ANALYSIS_EXTENSION | METHODOLOGY_CHANGE | RECORD_CORRECTION.

BASELINE MACHINE CHECKS (orchestrator, audit copy): pytest tools -> 40 passed, 12 subtests passed. tools/reproduce.py -> REPRODUCE PASS, exit 0: snapshots 15 verified 15/15; jsonl rows 14; NATURAL 9 (catch-ups 2); MANUAL 6 (incl. no-log-row snapshot 2026-09-19/125150_ET); trigger boundary 2026-09-21T11:00:00+08:00; collector 1.1.0; manifest schema {1: 1, 2: 14}; md links 33 checked, 0 broken. collect_forward_pit.py --verify data_forward_pit/2026-09-30/144521_ET -> VERIFY PASS.`

const DELEGATE_DECISIONS = `DELEGATE DECISION 1 (verbatim, from the Fable delegate session "NDX leveraged-ETF rebalancing research handoff", received 2026-10-02 by this session):
"Delegate decision on token economy for CP-AUDIT-01 (workflow §7): the usage limit has cut both runs twice and Aaron is sensitive to token spend, so reduce the remaining verification cost without lowering the bar on what matters. Keep every cached result. For the remaining unverified findings: (1) first collapse duplicates across lenses in plain code (same file and same threat) so each distinct finding is verified once; (2) run three refuters only for Critical and High; run one refuter with the threat-path lens for Medium and Low, surviving if not refuted; (3) keep the critic and the synthesis. Record in each report's method section exactly which findings had three votes and which had one, so I can weigh them. If editing the script would invalidate the cache for already-completed votes, keep the old script for those and apply the reduction only to calls that have not run. Do not restart from scratch."
DELEGATE MESSAGE 2 (verbatim, same session, relaying Aaron):
"Execution instruction from Aaron (his words: "让opus每十个开agent"): run the remaining agents in batches of ten — at most ten agents in flight at a time, the next ten only after the batch finishes. Apply it to the refuter votes, the critic and the synthesis for both runs; keep all cached results and the reduced-refuter rule from my last message. This is an execution choice, not a change to the audit's content."`

const THREAT_STANDARD = `YOUR LENS: THREAT-PATH. Assume the finding's evidence is true. Walk the failure path concretely: which actual input or state leads to which wrong output, wrong claim in a record someone relies on, or unverifiable record? If the path needs inputs or states that cannot occur given the actual data, commits and records, or the consequence is immaterial (no conclusion or decision would change and no record becomes false or unverifiable), refute. Give your honest severity.`
const THREAT_SOLE = `YOUR LENS: THREAT-PATH, AS THE SOLE REFUTER. Under the delegate's token-economy decision, Medium and Low findings get ONE refuter — you — and the finding survives only if you do not refute it. So do both: (1) first check the cited evidence against the bytes (open the cited file:lines; re-run the key command where cheap); if the evidence does not hold, refute; (2) then, assuming the evidence holds, walk the failure path concretely: which actual input or state leads to which wrong output, wrong claim in a record someone relies on, or unverifiable record? If the path needs inputs or states that cannot occur given the actual data, commits and records, or the consequence is immaterial (no conclusion or decision would change and no record becomes false or unverifiable), refute. The group may merge several instances that raise the same threat on the same files: judge them together; if only part stands, do not refute — say exactly which part stands in one_line and reasoning, and set severity for that part. Give your honest severity.`
const RULE_TEXT = `YOUR LENS: RULE-TEXT. Identify the binding text the finding relies on — a sealed prereg section, the workflow version in force at the time (v1 before 2026-09-26, v2 after, no retroactivity), a decision record, an attestation, or a record's own explicit claim — and quote it briefly with file:line. Does the observed state actually violate it, read correctly and in scope? A record that states a false fact violates its own claim; prose that is merely incomplete or loosely worded without stating a false fact does not. If no binding text is violated, the finding misreads the text, or the rule did not apply at the time, refute.`
const REPRO_TEXT = `YOUR LENS: REPRODUCE-FROM-BYTES. Re-run or recompute the finding's evidence yourself from the files and git objects in the audit copy (experiments only in your private copy). If the observation does not reproduce exactly, or the cited file:lines do not say what the finding says, refute it. If the finding is REASONED but mechanically checkable, check it mechanically. If you cannot establish the evidence, refute.`

const FINDING = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    severity: { type: 'string', enum: ['Critical', 'High', 'Medium', 'Low'] },
    locations: { type: 'array', items: { type: 'string' } },
    evidence: { type: 'string' },
    label: { type: 'string', enum: ['REPRODUCED', 'REASONED'] },
    threat: { type: 'string' },
    failure_path: { type: 'string' },
    repair: { type: 'string' },
    repair_class: { type: 'string', enum: ['IMPLEMENTATION_FIX', 'DATA_FIX', 'ANALYSIS_EXTENSION', 'METHODOLOGY_CHANGE', 'RECORD_CORRECTION'] },
    immutable_touch: { type: 'string' },
  },
  required: ['title', 'severity', 'locations', 'evidence', 'label', 'threat', 'failure_path', 'repair', 'repair_class', 'immutable_touch'],
}
const VOTE_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    one_line: { type: 'string', description: 'at most 30 words, stands alone in the report' },
    reasoning: { type: 'string' },
    evidence: { type: 'string' },
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
        three_vote: { type: 'integer' }, one_vote: { type: 'integer' },
      },
      required: ['confirmed', 'critical', 'high', 'medium', 'low', 'refuted', 'critic_gaps', 'three_vote', 'one_vote'],
    },
    top: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, title: { type: 'string' }, severity: { type: 'string' }, label: { type: 'string' }, votes: { type: 'string' }, line: { type: 'string' } },
        required: ['id', 'title', 'severity', 'label', 'votes', 'line'],
      },
    },
  },
  required: ['markdown', 'counts', 'top'],
}

async function inBatches(thunks, label) {
  const out = []
  for (let i = 0; i < thunks.length; i += 10) {
    const chunk = thunks.slice(i, i + 10)
    log(`${label}: batch ${Math.floor(i / 10) + 1} of ${Math.ceil(thunks.length / 10)} (${chunk.length} agent(s))`)
    out.push(...(await parallel(chunk)))
  }
  return out
}

function groupVotePrompt(t) {
  const lensName = t.lens === 'threat-path-sole' ? 'threat-path, sole refuter' : 'threat-path'
  const others = t.members.filter(m => m !== t.rep)
  return `${PRE[t.project]}

YOUR ROLE: ADVERSARIAL REFUTER (${lensName}) of one deduplicated finding group, ${t.gid}. Private-copy LABEL: c-ref-${t.gid}.
The finding text is in the state file ${STATE[t.project]} (JSON). Print the representative finding with:
  python -c "import json,sys; d=json.load(open(r'${STATE[t.project]}',encoding='utf-8')); print(json.dumps(d['findings']['${t.rep}'],indent=1,ensure_ascii=False))"
${others.length ? `and the merged duplicate instances ${others.join(', ')} the same way (same key 'findings'). They were collapsed into this group because they raise the same threat on the same files.` : ''}
Do NOT read the 'votes' or 'groups' keys: judge independently of any earlier refuter.
Your job is to REFUTE the group. Default to refuted=true when the evidence does not hold, the threat is hypothetical, or the failure path does not reach a wrong conclusion, a wrong claim in a record, or an unverifiable record. refuted=false means you tried hard within your lens and could not refute it.
${t.lens === 'threat-path-sole' ? THREAT_SOLE : THREAT_STANDARD}

Return: refuted; one_line (<=30 words, stands alone in a report); reasoning; evidence (commands + observed output, or quoted file:line); label (REPRODUCED only if you ran or recomputed something); severity_view (your honest severity if it stands, None if refuted); repair_view (is the proposed repair the smallest bounded one, correctly classified, and does it avoid touching an immutable artifact / append-only log / captured evidence?).`
}

function criticVotePrompt(project, f, id, lensKey) {
  const text = lensKey === 'sole' ? THREAT_SOLE : lensKey === 'threat' ? THREAT_STANDARD : lensKey === 'rule' ? RULE_TEXT : REPRO_TEXT
  const name = lensKey === 'sole' ? 'threat-path, sole refuter' : lensKey === 'threat' ? 'threat-path' : lensKey === 'rule' ? 'rule-text' : 'reproduce-from-bytes'
  return `${PRE[project]}

YOUR ROLE: ADVERSARIAL REFUTER (${name}) of one finding raised by the completeness critic, ${id}. Private-copy LABEL: c-ref-${id}-${lensKey}.
Your job is to REFUTE it. Default to refuted=true when the evidence does not hold, the threat is hypothetical, or the failure path does not reach a wrong conclusion, a wrong claim in a record, or an unverifiable record. refuted=false means you tried hard within your lens and could not refute it.
${text}

FINDING ${id}:
${JSON.stringify(f, null, 1)}

Return: refuted; one_line (<=30 words); reasoning; evidence; label; severity_view; repair_view.`
}

const tasks = args.tasks

phase('Verify')
const voteRes = await inBatches(tasks.map(t => () => agent(groupVotePrompt(t), {
  label: `c-refute:${t.gid}`, phase: 'Verify', schema: VOTE_SCHEMA, effort: 'max',
})), 'group votes')
const newVotes = tasks.map((t, i) => {
  const v = voteRes[i]
  if (!v) return { ...t, failed: true }
  const survives = t.lens === 'threat-path-sole' ? !v.refuted : ((t.cachedStands || 0) + (v.refuted ? 0 : 1)) >= 2
  return { ...t, vote: { lens: t.lens === 'threat-path-sole' ? 'threat-path (sole refuter, with evidence check)' : 'threat-path', ...v }, survives }
})
const failedVotes = newVotes.filter(v => v.failed).map(v => v.gid)
if (failedVotes.length) {
  log(`STOPPING before critic/synthesis: ${failedVotes.length} vote(s) failed: ${failedVotes.join(', ')}`)
  return { incomplete: true, stage: 'votes', failedVotes, newVotes }
}
log(`group votes done: ${newVotes.filter(v => v.survives).length}/${newVotes.length} pending groups survive`)

const votesFor = p => newVotes.filter(v => v.project === p).map(v => ({ gid: v.gid, rep: v.rep, members: v.members, rule: v.lens, survives: v.survives, vote: v.vote }))

const CRITIC_EXTRA = {
  r1: `every file in 'git ls-tree -r --name-only HEAD' that no coverage note covers; every commit whose diff no lens discussed; every PROJECT_STATE claim no lens checked; every sealed rule no lens traced to code; every tool or validator claim no lens tested; every artifact JSON field no lens reconciled`,
  r2: `every file in 'git ls-tree -r --name-only HEAD' that no coverage note covers (including handoffs/, vendor_outbound/, R2_S0_PROVENANCE.md, R2_MINIMUM_DATA_CONTRACT.md, R2_DATA_SOURCE_AUDIT.md, R2_FEASIBILITY_REPORT.md, the .ps1/.cmd tools, .gitattributes/.gitignore); every commit whose diff no lens discussed; every PROJECT_STATE claim no lens checked (e.g. the Task Scheduler facts: principal LogonType Password, RunLevel Limited, State Ready, next run); every tool claim no lens tested`,
}

phase('Critic')
const criticRes = await inBatches(['r1', 'r2'].map(p => () => agent(`${PRE[p]}

YOUR ROLE: COMPLETENESS CRITIC for ${p.toUpperCase()}. Private-copy LABEL: critic-${p}.
Six lens finders examined the repository; their results and the verification so far are in the state file ${STATE[p]} (JSON keys: lens_summary = each finder's coverage note, sound list and commands; findings = every finding raised, by id; groups = the deduplicated finding groups with members, rule and status). Read lens_summary and groups first (python -c "import json; d=json.load(open(r'${STATE[p]}',encoding='utf-8')); ..."). The PENDING groups were verified in this continuation; their votes are below.
Your task:
1. List what NO lens examined that could hold a threat to a conclusion, a record's truth or reproducibility: ${CRITIC_EXTRA[p]}.
2. Examine each of those now, as deeply as needed, under the same evidence standard.
3. Return: unexamined (what you identified); examined_now (what you examined and the result, one line each); unclosed_gaps (what you could not close and why — e.g. forbidden data, facts only the live system or a vendor could establish, bytes not in the repository); findings (NEW findings only — not duplicates of any finding id in the state file); sound.

CONTINUATION VOTES ON PENDING GROUPS:
${JSON.stringify(votesFor(p), null, 1)}`,
  { label: `critic:${p}`, phase: 'Critic', schema: CRITIC_SCHEMA, effort: 'high' })), 'critics')
const critic = { r1: criticRes[0], r2: criticRes[1] }
if (!critic.r1 || !critic.r2) {
  log('STOPPING before synthesis: a critic failed')
  return { incomplete: true, stage: 'critic', newVotes, critic }
}

phase('Verify critic')
const cTasks = []
for (const p of ['r1', 'r2']) {
  critic[p].findings.forEach((f, i) => {
    const id = `${p.toUpperCase()}-critic-${i + 1}`
    const lenses = (f.severity === 'Critical' || f.severity === 'High') ? ['reproduce', 'rule', 'threat'] : ['sole']
    lenses.forEach(l => cTasks.push({ p, id, f, l }))
  })
}
log(`critic findings: r1 ${critic.r1.findings.length}, r2 ${critic.r2.findings.length}; ${cTasks.length} vote(s)`)
const cRes = await inBatches(cTasks.map(t => () => agent(criticVotePrompt(t.p, t.f, t.id, t.l), {
  label: `c-refute:${t.id}:${t.l}`, phase: 'Verify critic', schema: VOTE_SCHEMA, effort: 'max',
})), 'critic votes')
if (cRes.some(v => !v)) {
  log('STOPPING before synthesis: a critic-finding vote failed')
  return { incomplete: true, stage: 'critic-votes', newVotes, critic, cTasks: cTasks.map((t, i) => ({ id: t.id, l: t.l, ok: !!cRes[i] })) }
}
const criticVerified = { r1: [], r2: [] }
for (const p of ['r1', 'r2']) {
  critic[p].findings.forEach((f, i) => {
    const id = `${p.toUpperCase()}-critic-${i + 1}`
    const vs = cTasks.map((t, j) => ({ t, v: cRes[j] })).filter(x => x.t.id === id)
      .map(x => ({ lens: x.t.l === 'sole' ? 'threat-path (sole refuter, with evidence check)' : ({ reproduce: 'reproduce-from-bytes', rule: 'rule-text', threat: 'threat-path' })[x.t.l], ...x.v }))
    const nr = vs.filter(v => !v.refuted).length
    const survives = vs.length === 1 ? nr === 1 : nr >= 2
    criticVerified[p].push({ id, ...f, votes: vs, vote_count: vs.length, survives })
  })
}

const ORCH_NOTES = {
  r1: `ORCHESTRATOR REPRODUCTIONS (this session, inline, before the workflow): bundle runs/R1-S3B-001/sealed_r1_outcome.json sha256 f6ca60e2dee7bb3c3c810fc8fe459d42449008ee12c9e331aefea75a16e5dd6e (= PROJECT_STATE); 246 records; Base mean of y_net_usd -8.768455; stored base_interval [-13.920945, -4.107835], half-width 4.906555 > M 3.99; stored mean_y_net_usd -10.268455 = Base - 1.50 exactly. The sealed M.1 UNRESOLVED list does not literally cover "interval entirely below M with half-width >= M", but sealed C.2 ("INSUFFICIENT_EVIDENCE is everything in between") and I.5 ("If it fails, the record is INSUFFICIENT_EVIDENCE, whatever the point estimate") do, so the recorded verdict follows the sealed rule. ITSF pinned files and the F10 calendar digest reproduce.`,
  r2: `ORCHESTRATOR REPRODUCTIONS (this session, inline, before the workflow): pytest tools 40 passed + 12 subtests; tools/reproduce.py REPRODUCE PASS with the counts quoted in the preamble; --verify PASS on 2026-09-30/144521_ET; the audit clone stays clean after these runs.`,
}
const RUNS = `Original runs: R1 wf_33f700d0-516 (script cp-audit-01-r1), R2 wf_fa4eb879-a84 (script cp-audit-01-r2). Both were interrupted twice by account usage limits and resumed from cache (completed agents replayed, failed ones re-run); the R1 run was then stopped on the delegate's decision. All cached finder results and refuter votes were kept. Deduplication into groups was done by the orchestrator by hand (same file and same threat), recorded in the state file's 'groups' key, before this continuation run ({{CONT_RUN_ID}}, script cp-audit-01-continuation) verified the remaining groups, ran the critics and wrote this synthesis, at most ten agents in flight.`

phase('Synthesis')
const synthRes = await inBatches(['r1', 'r2'].map(p => () => agent(`${PRE[p]}

YOUR ROLE: SYNTHESIS — write the CP-AUDIT-01 report for ${p.toUpperCase()}. Private-copy LABEL: synth-${p}. You may re-check facts in the audit copy.

INPUTS
1. State file ${STATE[p]} (read it fully with python): findings (every finding raised, by id, with evidence, threat, failure path, repair, class, immutable_touch), finding_lens (the lens that raised each), votes (every earlier refuter vote, by finding id and lens), groups (the deduplicated groups: gid, title, members, rep = representative, rule, status), lens_summary (coverage notes and sound lists per lens).
2. Continuation votes on the groups that were PENDING (below).
3. The critic's result and its verified findings (below).

OUTCOME RULES — apply exactly, never change an outcome:
- rule decided-3: three cached votes on the representative decide (CONFIRMED iff at least 2 of 3 did not refute). 3 votes.
- rule complete-3: two cached votes + the continuation threat-path vote; CONFIRMED iff at least 2 of 3 did not refute. 3 votes.
- rule single-1-cached: the one cached threat-path vote (pure threat-path lens, evidence assumed true) decides. 1 vote.
- rule single-1: the one continuation sole threat-path vote (which also checked the evidence against the bytes) decides: CONFIRMED iff not refuted. 1 vote.
- critic findings: Critical/High had three votes (2 of 3 rule); Medium/Low had one sole threat-path vote.
A group whose vote narrowed it ("stands, narrowed") is confirmed as narrowed: report only the part that stands. Merged members' extra sub-claims that no vote examined must be listed as "raised, not separately verified". Final severity: at most the highest non-refuting severity_view among the deciding votes; give a one-line reason. Final label: REPRODUCED only if the finder or a non-refuting deciding vote actually ran or recomputed it and observed it; otherwise "REASONED — not reproduced". If you believe an outcome is wrong, add a marked "Synthesis note" without flipping it. Do not soften or inflate.

FORMAT — Markdown, exactly these sections:
# CP-AUDIT-01 — ${p === 'r1' ? 'R1 rigour audit (nq-event-diffusion-research @ 18639ee)' : 'R2 rigour audit (nq-letf-rebalancing-research @ 7fc4e83)'}
## 1. Scope and method — target commit and covered commits; the six lenses; the refuter lenses and survival rules; the run history (${RUNS}); the two delegate messages quoted verbatim (below); a table of every group: gid · title · member finding ids · rule · number of deciding votes (3 or 1) · outcome — so the delegate can weigh three-vote against one-vote findings; a sentence that one-vote outcomes carry less verification weight; that the continuation's sole refuter used the threat-path lens extended with an evidence check (stricter than pure threat-path) while cached single votes used the pure lens; the baseline machine checks; read-only, no-network${p === 'r2' ? ', no-live-collector' : ''} and no-outcome-data conditions (scratch clone, byte-identical at the target commit); this line verbatim: "Workflow run IDs: {{RUN_IDS}} · scripts: {{SCRIPTS}}".
## 2. Verdict — exactly two sentences: ${p === 'r1' ? 'does the record support its stated conclusion and state as reproducible and rule-computed' : 'does the record support its stated state (PRE-S1, OUTCOME_EXPOSURE = NONE, the forward-collection counts, the G-3/OD-6 status, the vendor status) as reproducible and rule-computed'} — yes / no / with caveats.
## 3. Confirmed findings — ranked Critical -> High -> Medium -> Low; within a severity, three-vote before one-vote. For each: "### <gid> (<member ids>) — <title>" then bullets: Severity (+ reason) · Votes (3 or 1, and the rule) · Location (file:lines) · Evidence · Threat · Failure path · Label · Refuters — one line from each deciding vote, named by lens · Smallest bounded repair — <text> [<CLASS>] · ${p === 'r1' ? 'Without touching an immutable artifact: yes/no — <how>' : 'Touches append-only log / captured evidence / committed dated amendment: yes/no — <how it is done instead>'}.
## 4. Refuted findings — one line each: gid (member ids) — title — votes — why refuted, so nobody re-raises them.
## 5. Examined and found sound — explicit, grouped by lens, deduplicated; include the critic's sound items and the orchestrator reproductions below.
## 6. Critic's unclosed gaps — each with why it could not be closed.
## 7. Recommended next actions — (a) needs the delegate's decision; (b) the builder may do alone once the delegate has accepted the findings. Nothing is repaired before acceptance.${p === 'r1' ? ' R1 corrections are new dated files only.' : ''}

Also return counts (by group after merging: confirmed and by severity, refuted, critic_gaps = number of unclosed gaps, three_vote / one_vote = how many CONFIRMED items were decided by three votes vs one) and top (up to 5 most severe confirmed items with id, title, severity, label, votes, one-line summary).

${DELEGATE_DECISIONS}

${ORCH_NOTES[p]}

CONTINUATION VOTES ON PENDING GROUPS:
${JSON.stringify(votesFor(p), null, 1)}

CRITIC RESULT:
${JSON.stringify({ unexamined: critic[p].unexamined, examined_now: critic[p].examined_now, unclosed_gaps: critic[p].unclosed_gaps, sound: critic[p].sound }, null, 1)}

CRITIC FINDINGS WITH THEIR VOTES:
${JSON.stringify(criticVerified[p], null, 1)}`,
  { label: `synthesis:${p}`, phase: 'Synthesis', schema: SYNTH_SCHEMA, effort: 'max' })), 'syntheses')

return { incomplete: !synthRes[0] || !synthRes[1], synth: { r1: synthRes[0], r2: synthRes[1] }, newVotes, critic, criticVerified }
