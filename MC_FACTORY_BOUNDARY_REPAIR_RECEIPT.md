# MC FACTORY BOUNDARY REPAIR — engineering close-out receipt

BASELINE_HEAD=b3ac4534486f607242f5758cecbc918cbe2157be
SCOPE=engineering boundary only (no research definition touched)
ROLE=builder (Opus). NOT a verification. NOT a research authorization.

## 1. The finding

`PreparedMCInput` was a public frozen dataclass. Every field the
ten-check battery derives was a constructor parameter, so a caller could
obtain a seal-admissible object two ways that never ran the battery:

```
PreparedMCInput(...)                       # hand-assembled
dataclasses.replace(prepared, ...)         # mutate a genuine one
```

B-PROV (commit `b3ac453`) had already made the CUSTODY ROOT decisive:
`_assert_seal_provenance` re-derives the production attestation from
code pins and compares `test_only`, `source_artifact_id`,
`source_artifact_sha256`, trial/commit and the 14-file digest table.
Those five checks answer *which authority certified this input*. None of
them can answer *did the battery run* — and nothing downstream
re-derives `method_digest`, `seeds`, `k_per_seed`, `day_sequences`,
`traded_day_sets`, `calendar` or `authorization_snapshot`. Given a
bundle and an attestation that agree with each other (the production
case, and any production-LIKE case), a forged object satisfied all five
checks and was then stopped only by the UNRELATED feasibility gate.

Codex's synthetic reproduction, reproduced here exactly:

```
direct_constructed=True
battery_method_digest_changed=True
seal_provenance_accepted=True
full_seal_first_refusal=feasibility_gate_decision_required
```

Why the previous round's battery could not see it: its forgeries were
certified by a TEST_ONLY authority over a SYNTHETIC bundle and then
claimed the REAL attestation's source strings, so they died at
`seal_custody_table_mismatch` — a true refusal, but one that proves the
table check works rather than that the battery ran.

## 2. Pre-fix red proof (measured at `b3ac453`, production file untouched)

`tests/test_mc_battery_boundary.py` builds a PRODUCTION-LIKE custody
authority: a synthetic attestation document in the real grammar whose
trial/commit, source id, source digest and complete 14-file table are
internally consistent with the synthetic bundle, loaded through the same
`load_custody_authority_from_attestation` constructor the production
prepare entry and the seal both use. Under it the provenance layer is
GENUINELY satisfied, so only the battery question remains.

Measured at the baseline tree:

```
tests/test_mc_battery_boundary.py    28 failed, 16 passed
```

The three decisive observations, all from that run:

| observation | baseline result |
| --- | --- |
| `_assert_seal_provenance(prod_like)` on the genuine production-shaped product | ACCEPTED (test passed) |
| hand-built copy, nothing changed, full seal | `feasibility_gate_decision_required` |
| hand-built copy with `method_digest="f"*64`, full seal | `feasibility_gate_decision_required` |

Verbatim assertion diff for the first forgery:

```
>       assert _seal_code(forged) == "seal_prepared_not_battery_validated"
E       AssertionError: assert 'feasibility_...sion_required' == 'seal_prepare...ery_validated'
E         - seal_prepared_not_battery_validated
E         + feasibility_gate_decision_required
```

No real S0 bytes were read to build the fixture. The only real files it
reads are the two FROZEN METHOD documents (`MC_METHOD_SPEC.md`,
`gate1/platform_params.yaml`), copied into the fixture root so the
battery's method digest stays the production one.

## 3. The repair

### 3.1 Factory-only construction (E1)

`PreparedMCInput` gains ONE field:

```python
battery_receipt: "BatteryReceipt | None" = _dc.field(
    init=False, repr=False, compare=False, default_factory=lambda: None)
```

`init=False` is the boundary. The public constructor cannot be handed
one (`TypeError`), and `dataclasses.replace` skips `init=False` fields
entirely — so a replaced object is receipt-LESS by construction, a
no-op replace included. `default_factory` rather than a plain default is
required: with `slots=True` the dataclass machinery deletes class-level
defaults, and an `init=False` field with a plain default is read from
exactly that deleted attribute.

Construction itself stays public and unchanged. The ten-check battery's
own refusal codes remain reachable, and the cold replay still rebuilds a
prepared input from custody bytes. What is no longer reachable is SEAL
ADMISSIBILITY without the battery. The repair adds no caller-supplied
boolean or string of the `battery_validated=True` kind.

### 3.2 Typed battery receipt (E2)

`BatteryReceipt` is a frozen slots dataclass whose `__post_init__`
requires a module-private capability object and then DROPS it
(`object.__setattr__(self, "capability", None)`), so holding a genuine
receipt does not let a caller mint another; `dataclasses.replace` on a
receipt fails for the same reason. Refusal code:
`battery_receipt_capability_required`.

It binds:

| bound fact | where |
| --- | --- |
| external authority source id / source sha256 / test_only | receipt fields + `provenance` component |
| authority trial id / authorized commit | receipt fields + `trial_commit` component |
| complete 14-file digest table | `bundle_file_sha256` component |
| records content digest | `records_digest` component |
| complete engine/scenario/date key index | `record_keys` component |
| method digest | `method_digest` component |
| seeds, K, CRN scope | `seeds_k_crn` component |
| day sequences / traded day sets | `day_sequences`, `traded_day_sets` |
| calendar days + first-month offsets | `calendar` component |
| authorization snapshot | `authorization_snapshot` component |
| prepared identity, both forms | `prepared_digest`, `prepared_identity_sha256` |

Components are digested separately rather than folded into the single
prepared digest so a mismatch NAMES the component that moved instead of
reporting "identity changed". `_issue_battery_receipt` is called exactly
once, at the end of `_prepare_mc_input_impl`, on the far side of all ten
checks.

`verify_battery_receipt` recomputes every component from the LIVE object
and compares. Nothing in the receipt is ever read as a value or as
permission.

### 3.3 Cold replay (E3)

`replay_prepared_from_custody_bytes` still rebuilds a NEW prepared input
by re-parsing the retained custody bytes, still never reuses the forward
records mapping, and still requires the rebuild to reproduce the forward
prepared digest. It now CARRIES the forward receipt across — never mints
one:

* an input that had no receipt still has none after replay, so the
  replay cannot launder an un-battery-validated object;
* carrying is sound because every component the receipt binds is also
  bound into the prepared digest, and the two digests are proven equal
  immediately above the carry;
* without the carry, the seal's own replay product would arrive
  receipt-less and the seal would refuse itself.

### 3.4 Seal order (E4)

Unchanged and re-pinned:

```
verdict_and_seal_from_evidence
  1. cold_replay_evidence(...)        UNCONDITIONAL, first
  2. four-layer config digest equality
  3. _assert_seal_provenance(...)     checks (1)-(5) B-PROV, then (6) receipt
  4. _reduce_primary_from_base(...)   feasibility gate
  5. convergence_from_evidence(...)
```

Inside `_assert_seal_provenance` the five B-PROV checks stay FIRST so a
forged source string, a foreign trial or a substituted digest table each
keeps its own precise code; the receipt check is the catch-all beneath
them. Both new codes are machine-distinguishable and both fire ahead of
the feasibility gate:

```
seal_prepared_not_battery_validated   no receipt at all
seal_battery_receipt_mismatch         a receipt that does not describe THIS object
```

### 3.5 Production path (E5)

One production route, unchanged in shape:

```
real_input.prepare_real_mc_input
  -> guards (G9 + second copy)
  -> authorize_real_mc            (deterministic refusal today)
  -> load pinned attestation bytes
  -> mcc.prepare_mc_input
       -> load_custody_authority_from_attestation   (internal, code-pinned)
       -> _prepare_mc_input_impl                     (ten checks)
       -> PreparedMCInput(...)                       (sole production constructor)
       -> _issue_battery_receipt                     (sole receipt minter)
  -> evidence -> cold replay -> receipt verification -> seal
```

`PreparedMCInput(` appears at exactly two sites in production code: the
battery's own return and the cold-replay rebuild. There is no second
production constructor.

## 4. Disposition of the two forgery routes

| route | disposition |
| --- | --- |
| `PreparedMCInput(...)` | constructible; receipt is not an init parameter, so the object is never seal-admissible → `seal_prepared_not_battery_validated` |
| `dataclasses.replace(prepared, ...)` | `init=False` field is skipped → receipt lost → `seal_prepared_not_battery_validated` (no-op replace included) |
| replace + grafted genuine receipt (`object.__setattr__`) | receipt digests do not describe the mutated object → `seal_battery_receipt_mismatch` |
| forging a receipt (`BatteryReceipt(...)` or `replace`) | capability required and never retained on an instance → `battery_receipt_capability_required` |

## 5. Test evidence (OPUS_MEASURED — not independently reproduced)

| step | result |
| --- | --- |
| baseline full suite at `b3ac453` | 3336 passed |
| new module at `b3ac453` (red proof) | 28 failed, 16 passed |
| new module after repair | 44 passed |
| affected MC modules after repair (12 files) | 587 passed |
| fresh full suite after repair | 3380 passed, 0 failed (476s) |
| collection count | 3336 → 3380 |
| dual floor pin | `scripts/s0_real_run.py` and `tests/test_s0_runner.py` raised to 3380 |
| `scripts/final_candidate_scans.py` | exit 1, 3 findings — ALL pre-existing false positives in `src/itsf/mc/atoms.py` (`E2_UNRULED_TOKEN`, `NO_TRADE_TOKEN`, `E1_TRADED_TOKEN` read as credential assignments). That file is byte-identical to `b3ac453`; no finding comes from any file this round changed or added. |
| `git diff --check b3ac453..worktree` | clean |
| registry / exposure ledger / attestation sha256 | unchanged (`ee9da33f…`, `382182bf…`, `d839b965…`) |
| sealed S0 run directory | unchanged (14 files, identical names, sizes and mtimes; contents never read) |

The regression-sensitivity evidence is a real run of the identical test
file against the untouched baseline tree — not a source-string count and
not a mock's conclusion.

## 6. Residual and disclosed limits

1. **Module privates are not a security boundary in Python.** A caller
   who reaches into `itsf.mc.consumer._BATTERY_CAPABILITY` can mint a
   receipt, and one who monkeypatches `ATTESTATION_SHA256_PINNED` can
   redirect the custody root — the test fixture in this round does
   exactly the latter, deliberately. The boundary defends against normal
   external calls and against every accidental path, which is what the
   scope asked for. It does not defend against a caller editing module
   internals, and no in-process design can.
2. **The seal candidate schema moved** `mc_verdict_inputs.v4` →
   `mc_verdict_inputs.v5`: it now records the battery receipt it
   verified (digests only, no research value). The seal remains
   structurally unreachable — the reduction still refuses at
   `feasibility_gate_decision_required`.
3. **The production-like fixture patches `build_template_calendar`** to
   the small test calendar. The 24-month CME build is ~60x more
   lifecycle work per set and tests nothing about this boundary. The
   calendar is still exercised as a tampered field in the F4 matrix.
4. **Nothing was verified independently.** This document is the
   builder's own account. Stage I belongs to a fresh Sol session.

## 7. Not done in this round (explicitly)

No change to samples, labels, NA policy, costs, Primary definitions,
feasibility, convergence, exposure accounting or verdict semantics. No
registry or exposure-ledger edit. No S0 run/archive artifact touched. No
real data read. No MC, supplement or strategy execution. No READY event,
no authorization event, no run authorization. No amend, push or tag.
