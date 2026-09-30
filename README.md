# nq-letf-rebalancing-research (R2)

**What R2 asks.** Daily-reset leveraged and inverse ETFs promise a multiple of the *daily*
benchmark return, so each day they must re-strike their exposure. For fund *i* with leverage
*m* and prior-day assets *A*, the reset demand implied by the pre-close index return
*r_pre,t* is `dS_i,t = m_i,t (m_i,t − 1) A_i,t−1 r_pre,t`. Summed over the five
Nasdaq-100-benchmarked funds (QLD +2x, QID −2x, PSQ −1x, TQQQ +3x, SQQQ −3x), the aggregate
pressure is `F_t = K_t r_pre,t` with `K_t = Σ_i m_i,t (m_i,t − 1) A_i,t−1`. R2 asks whether
that demand leaves a mechanically predictable late-day footprint that transmits into
Nasdaq-100 index futures (NQ).

**The distinctness constraint.** For all five funds `m(m − 1) > 0`, so
`sign(F_t) = sign(r_pre,t)`: the sign of the pressure carries nothing that the day's own
return does not. Generic late-day momentum is therefore **forbidden** as a substitute for
R2. Any information R2 has must come from the magnitude and composition channel — `K_t`
(fund size × leverage mix) or an equivalent — beyond `sign(r_pre)`, `|r_pre|`, slow trend and
market state. If that cannot be established prospectively, R2 is parked.

**Current stage:** PRE-S1 / WAITING_FOR_EXTERNAL_EVIDENCE. No point-in-time source for
historical daily fund size (2010-2021) has been verified; six vendor enquiries are out and
unanswered on the evidence. There is no hypothesis, no preregistration and no result — see
[PROJECT_STATE.md](PROJECT_STATE.md).

## While R2 is pre-S1, none of the following happens without Aaron's explicit authorization

- decode the NQ archive, compute NQ returns or P&L, test any R2 signal, or look at outcome
  data to choose among point-in-time definitions or to reshape the sample;
- call current AUM historical point-in-time data; forward-fill, interpolate or impute
  historical AUM; infer publication timing from neighbouring dates; use a partial-universe
  `K_t` (OD-6);
- assume mutual-fund reset flow only attenuates the effect or only acts at the close;
- substitute generic late-day momentum for R2, broaden the ETF universe, or open an R3 here;
- buy data, start a paid trial, accept a licence, send further vendor messages, schedule
  follow-ups or sales meetings, reopen library access;
- consume an R2 trial, authorize S1, or label R2 `falsified` / `supported`.

Waiting for vendor evidence is not failure, and vendor silence is not a rejection.

## Reproduce

```bash
python tools/reproduce.py
```

Offline (no network, no NQ data). Runs the test suite, verifies every forward snapshot's
hashes, re-derives the forward-collection counts from `logs/` and the manifests, checks
every relative Markdown link, compares the counts with `PROJECT_STATE.md`, and exits
non-zero on any mismatch. Needs Python ≥ 3.10 with `pytest` and `tzdata` (Windows).
The live task keeps adding snapshots after a checkpoint; counts are taken as of the
snapshot named in `PROJECT_STATE.md`, and later ones are reported for information only.

## Where authority lives

| what | where |
|---|---|
| workflow (v2) | `../QUANT_WORKFLOW_VNEXT.md` in the author's workspace (not in this repository) |
| R2 Owner decisions OD-1, OD-2, OD-5, OD-6 | [R2_DELEGATED_OWNER_DECISIONS.md](R2_DELEGATED_OWNER_DECISIONS.md) |
| every grant and decision since, verbatim where it arrived by message | [DECISION_LOG.md](DECISION_LOG.md) |
| current state (not authority) | [PROJECT_STATE.md](PROJECT_STATE.md) |
| inputs to checkpoint CP-R2-V2-01 | [handoffs/](handoffs/) |

## Artifacts

| file | what it is |
|---|---|
| [R2_S0_PROVENANCE.md](R2_S0_PROVENANCE.md) | where R2 came from; what the feasibility stage is and is not |
| [R2_MINIMUM_DATA_CONTRACT.md](R2_MINIMUM_DATA_CONTRACT.md) | prospective data contract, written before availability was judged |
| [R2_DATA_SOURCE_AUDIT.md](R2_DATA_SOURCE_AUDIT.md) | local / public / paid source audit (+ 2026-09-19 amendment) |
| [R2_FEASIBILITY_REPORT.md](R2_FEASIBILITY_REPORT.md) | coverage matrix, identifiability finding, classification (+ amendment) |
| [R2_G3_ACCEPTANCE_CRITERIA.md](R2_G3_ACCEPTANCE_CRITERIA.md) | G-3 closure standard, written before its evidence existed |
| [R2_G3_PUBLICATION_TIMING_REPORT.md](R2_G3_PUBLICATION_TIMING_REPORT.md) | G-3 modern-endpoint evidence; its full-sample close was **not accepted** — see the amendment |
| [R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md](R2_G3_HISTORICAL_PUBLICATION_TIMELINE.md) | 2010-2019 evidence regimes R-1 … R-4 |
| [R2_G3_HISTORICAL_PIT_AMENDMENT.md](R2_G3_HISTORICAL_PIT_AMENDMENT.md) | G-3 status PARTIAL; AUM field observed from 2014-03-26; historical daily PIT-safe start NOT_ESTABLISHED (correction 2026-10-01) |
| [R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md](R2_SV1_SOURCE_ACCEPTANCE_CRITERIA.md) | SV-1 evidence standard, written before any candidate was judged; the standard for classifying vendor replies |
| [R2_SV1_SOURCE_MATRIX.md](R2_SV1_SOURCE_MATRIX.md) | 20 candidates across 9 classes, decisive evidence and missing facts |
| [R2_SV1_SOURCE_VERIFICATION_REPORT.md](R2_SV1_SOURCE_VERIFICATION_REPORT.md) | SV-1 result, 2016 acid test, acquisition readiness, forward option |
| [R2_SV1_VENDOR_ENQUIRY_PACKET.md](R2_SV1_VENDOR_ENQUIRY_PACKET.md) | the six prepared vendor enquiries |
| [R2_VENDOR_WAVE1_DISPATCH.md](R2_VENDOR_WAVE1_DISPATCH.md) | Wave-1 dispatch package as prepared 2026-09-20 (its header predates dispatch; all six were later sent) |
| [R2_VENDOR_RESPONSE_TRACKER.md](R2_VENDOR_RESPONSE_TRACKER.md) | one row per vendor; 6/6 sent; no evidentiary response yet |
| [vendor_outbound/](vendor_outbound/) | the six messages as sent: four by e-mail, two by official contact form |
| [R2_FORWARD_PIT_COLLECTION.md](R2_FORWARD_PIT_COLLECTION.md) | forward point-in-time collection: purpose, schema, schedule, capture ledger (2026-10-01 section is current) |
| [tools/collect_forward_pit.py](tools/collect_forward_pit.py) | collector + verifier, v1.1.0, manifest schema 2 |
| [tools/run_forward_pit_scheduled.py](tools/run_forward_pit_scheduled.py) | scheduled wrapper: lock, JSONL log, honest timing |
| [tools/task_action.py](tools/task_action.py) | canonical cmd.exe action-argument builder and validator |
| [tools/run_forward_pit_task.cmd](tools/run_forward_pit_task.cmd) | Task Scheduler entry point; captures stdout and stderr |
| [tools/install_forward_pit_task.ps1](tools/install_forward_pit_task.ps1) | resolves the interpreter, registers, verifies, exports the task XML |
| [tools/remove_forward_pit_task.ps1](tools/remove_forward_pit_task.ps1) | removes only `QuantTrade-R2-ForwardPIT` |
| `tools/test_*.py` | offline tests for the collector, the wrapper and the task action |
| [tools/reproduce.py](tools/reproduce.py) | the reproduce command |
| [ops/R2_FORWARD_PIT_TASK.xml](ops/R2_FORWARD_PIT_TASK.xml) | live task export: password-backed principal, canonical `/d /s /c` action, no secrets |
| [ops/R2_FORWARD_PIT_TASK.template.xml](ops/R2_FORWARD_PIT_TASK.template.xml) | sanitized declarative target definition, no secrets |
| [logs/](logs/) | append-only scheduler log (no fund values), task stdout log, console log |
| [data_forward_pit/](data_forward_pit/) | immutable, hashed forward snapshots (raw bytes + headers + manifest) |
| [data_probe/](data_probe/) | feasibility and G-3 timing probes, hashed; not research datasets |

No NQ data, no returns and no research results are in this repository.
