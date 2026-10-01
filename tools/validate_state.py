"""Current-stage state validator. UNSEALED, and deliberately so.

Validation after a seal is TWO questions, and conflating them is how a stale
assertion gets reported as a normal failure:

    SEAL_SNAPSHOT_VALIDATION   does the sealed validator pass against the state
                               it was sealed with?   -> tools/validate_seal_snapshot.py
    CURRENT_STATE_VALIDATION   is the CURRENT stage state what it claims?
                               -> this file

`psmv/validate_prereg.py` is sealed and asserts seal-time state, including
`state: S2 NOT AUTHORIZED`, which was true when Aaron sealed S1 and is false now
that he has authorized S2. It is neither edited (that would break the seal it
protects) nor satisfied by making PROJECT_STATE.md lie. It is run in its own
context, where it passes cleanly.

This file checks what matters now:

  1. the seal is intact -- every sealed digest still verifies;
  2. the current stage state is what it claims, and no authority has been
     silently granted;
  3. the sealed trial registry is immutable while the operational ledger is
     append-safe;
  4. the post-seal artifacts, the Development adapter and A1 are in place.

**LIFECYCLE AWARENESS.** The stage-dependent assertions used to be hard-coded to
S2-era truths -- "no outcome exists", "the trial is not consumed", "the reveal is
not granted". Those were correct at S2 and became FALSE the moment Aaron
authorized S3-B and then the S4 reveal, so the tool reported legitimate progress
as failure. The stage is now DERIVED FROM THE OPERATIONAL LEDGER -- the
append-only hash chain, which is the authoritative record of what actually
happened -- and each stage asserts its own invariants:

    S2            no RUN_STARTED        -> trial NOT consumed, NO outcome file
    S3A           POWER_GATE_EXECUTED,  -> the same pre-run invariants as S2
                  no RUN_STARTED           (the power gate reads no outcome)
    S3B_CONSUMED  RUN_STARTED           -> trial consumed, EXACTLY ONE run and
                                           EXACTLY ONE outcome bundle
    S4_REVEALED   REVEALED              -> reveal granted and recorded
    S4_CLOSED     VERDICT_CLOSED        -> verdict recorded, lifecycle STOP

Nothing is weakened to get green. The post-run stages assert STRICTLY MORE than
the pre-run stage did: "no outcome exists" is replaced by "exactly one outcome
exists, and its bytes still hash to the digest the receipt recorded", which is
the invariant that actually protects an immutable result.

This tool reads NO outcome value. It hashes the bundle and reads counts and
identity fields; it never opens the payload records.

CORRECTION 2026-10-02 (R1_RECORD_CORRECTIONS_2026-10-02.md, CP-AUDIT-01 R1-critic-1,
delegate decision D-R2-2026-10-02-01 R1-f): the closeout version derived S3A but
routed it to the post-run branches, so "each stage asserts its own invariants" did
not hold for S3A (5 false FAILs replaying 7426a2f). S3A now takes the pre-run
branches. The digest ec52a9f1... pinned at ledger seq 13 and in the final
controller snapshot refers to the CLOSEOUT bytes of this file, not to this version.

Run:  python tools/validate_state.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from r1.contract import load_sealed_contract, sha256_file   # noqa: E402
from r1.invariants import (scan_no_duplicated_constants,     # noqa: E402
                           scan_no_parameter_scan,
                           scan_no_raw_decoder_import,
                           scan_no_release_time_inference,
                           verify_l13_still_holds)
from r1.power_gate import prove_gate_independence            # noqa: E402

#: Sealed verdict enums, mirrored here for validation only. This tool asserts
#: that a recorded verdict is one of the legal values; it never decides one.
LEGAL_AXIS1 = ("PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE",
               "PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M",
               "PREDICTIVE_EFFECT_UNRESOLVED", "PARKED")
LEGAL_AXIS2 = ("MECHANISM_SPECIFICITY_ESTABLISHED",
               "MECHANISM_SPECIFICITY_NOT_ESTABLISHED")
LEGAL_VERDICTS = ("SUPPORTED", "FALSIFIED", "INSUFFICIENT_EVIDENCE", "PARKED")


PRE_RUN_STAGES = ("S2", "S3A")  # no RUN_STARTED yet: no trial consumed, no outcome

def lifecycle_stage(entries) -> str:
    """Derive the stage from the append-only ledger, never from prose.

    The ledger is the authoritative record of what happened. PROJECT_STATE.md is
    a description of it, and a description can drift; the chain cannot, because
    every entry commits to its parent.
    """
    events = {e.event for e in entries}
    if "VERDICT_CLOSED" in events:
        return "S4_CLOSED"
    if "REVEALED" in events:
        return "S4_REVEALED"
    if "RUN_STARTED" in events:
        return "S3B_CONSUMED"
    if "POWER_GATE_EXECUTED" in events:
        return "S3A"
    return "S2"


def parse_state_block(text: str) -> dict[str, str]:
    """Read PROJECT_STATE.md's fenced state block into {KEY: value}.

    Continuation lines are folded into the value they belong to, so a wrapped
    field is read as one value rather than silently truncated.
    """
    m = re.search(r"^```\n(.*?)^```", text, re.S | re.M)
    body = m.group(1) if m else text
    fields: dict[str, str] = {}
    key: str | None = None
    for line in body.splitlines():
        head = re.match(r"^([A-Z][A-Z0-9_]*(?:\s*\u00b7\s*[A-Z]+)?)\s*=\s*(.*)$", line)
        if head:
            key = head.group(1).split("\u00b7")[0].strip()
            fields[key] = head.group(2).strip()
        elif key and line.strip():
            fields[key] += " " + line.strip()
    return fields


failures: list[str] = []
notes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (notes if ok else failures).append(
        f"{'PASS' if ok else 'FAIL'}  {name}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    seal = json.loads((ROOT / "R1_S1_SEAL_ATTESTATION.json").read_text(
        encoding="utf-8"))

    # ---- 1. the seal is intact ---------------------------------------
    for rel, digest in seal["sealed_digests"].items():
        check(f"sealed digest holds: {rel}",
              sha256_file(ROOT / rel) == digest)
    contract = load_sealed_contract()
    check("contract binds the sealed commit",
          contract.content_commit == seal["CONTENT_COMMIT"])
    check("sealed n is 252", contract.pre_seal_structural_n == 252)
    check("sealed k is 1", contract.k == 1)

    # ---- 2. current stage state, ASSERTED AGAINST THE LEDGER ----------
    from r1.ledger import LEDGER_FILE                        # noqa: PLC0415
    from r1.ledger import verify_chain as _verify_chain      # noqa: PLC0415
    entries = _verify_chain(ROOT / LEDGER_FILE)
    stage = lifecycle_stage(entries)
    fields = parse_state_block(state)
    check("lifecycle stage derived from the operational ledger", True,
          f"{stage} ({len(entries)} ledger entries)")

    # Invariant at EVERY stage: the seal stands and no authority was widened.
    for key, want, why in (
            ("S1", "SEALED", "S1 sealed"),
            ("INTERNAL_VALIDATION", "NOT GRANTED", "IV not granted"),
            ("LOCKBOX", "NOT GRANTED", "Lockbox not granted"),
            ("PROTECTED_ITSF_OUTCOMES", "NOT GRANTED", "ITSF outcomes not granted")):
        check(f"state: {why}", fields.get(key, "").startswith(want),
              f"{key} = {fields.get(key, '<missing>')[:48]}")

    # Stage-dependent. Each stage asserts ITS OWN truth, never a stale one.
    if stage in PRE_RUN_STAGES:
        for key, want, why in (
                ("TRIAL_CONSUMED", "NO", "trial not consumed"),
                ("OUTCOME_REVEAL", "NOT GRANTED", "reveal not granted"),
                ("R1_OUTCOME_EXPOSURE", "NONE", "no exposure")):
            check(f"state[S2]: {why}", fields.get(key, "").startswith(want),
                  f"{key} = {fields.get(key, '<missing>')[:48]}")
    else:
        check("state[post-run]: trial consumed",
              fields.get("TRIAL_CONSUMED", "").startswith("YES"),
              fields.get("TRIAL_CONSUMED", "<missing>")[:48])

    if stage in ("S4_REVEALED", "S4_CLOSED"):
        check("state[revealed]: reveal granted",
              fields.get("OUTCOME_REVEAL", "").startswith("GRANTED"),
              fields.get("OUTCOME_REVEAL", "<missing>")[:48])
        check("state[revealed]: exposure records the reveal",
              "REVEALED" in fields.get("R1_OUTCOME_EXPOSURE", "").upper(),
              fields.get("R1_OUTCOME_EXPOSURE", "<missing>")[:48])

    if stage == "S4_CLOSED":
        verdict_file = ROOT / "artifacts" / "R1_S4_VERDICT.json"
        check("state[closed]: the S4 verdict artifact exists", verdict_file.exists())
        if verdict_file.exists():
            v = json.loads(verdict_file.read_text(encoding="utf-8"))
            # Final-state ENUMS only -- no outcome value is read here.
            check("state[closed]: Axis-1 verdict is a legal sealed enum",
                  v.get("axis_1", {}).get("verdict") in LEGAL_AXIS1,
                  str(v.get("axis_1", {}).get("verdict")))
            check("state[closed]: Axis-2 verdict is a legal sealed enum",
                  v.get("axis_2", {}).get("verdict") in LEGAL_AXIS2,
                  str(v.get("axis_2", {}).get("verdict")))
            check("state[closed]: final verdict is a legal research verdict",
                  v.get("final_research_verdict") in LEGAL_VERDICTS,
                  str(v.get("final_research_verdict")))
            # PROJECT_STATE must AGREE with the durable artifact, not drift.
            check("state[closed]: PROJECT_STATE Axis-1 agrees with the artifact",
                  fields.get("AXIS_1", "").startswith(
                      str(v.get("axis_1", {}).get("verdict"))),
                  fields.get("AXIS_1", "<missing>")[:48])
            check("state[closed]: PROJECT_STATE final verdict agrees with the artifact",
                  fields.get("R1_FINAL_VERDICT", "").startswith(
                      str(v.get("final_research_verdict"))),
                  fields.get("R1_FINAL_VERDICT", "<missing>")[:48])
        check("state[closed]: lifecycle is STOP",
              "STOP" in fields.get("R1_LIFECYCLE", "").upper()
              or "STOP" in fields.get("STAGE", "").upper(),
              fields.get("R1_LIFECYCLE", fields.get("STAGE", "<missing>"))[:48])

    # ---- 3. outcome existence, stage-appropriate ----------------------
    # Pre-run: none may exist. Post-run: EXACTLY ONE must exist and its bytes
    # must still hash to the digest the receipt recorded. The second assertion
    # is strictly stronger than the first -- it is what protects immutability.
    bundles = sorted(ROOT.rglob("sealed_r1_outcome.json"))
    if stage in PRE_RUN_STAGES:
        check("no sealed R1 outcome file exists in the repository",
              not bundles, "; ".join(str(p) for p in bundles[:3]))
    else:
        check("exactly one sealed R1 outcome file exists",
              len(bundles) == 1, "; ".join(str(p) for p in bundles[:3]))
        run_dirs = [p for p in (ROOT / "runs").iterdir() if p.is_dir()] \
            if (ROOT / "runs").exists() else []
        check("exactly one real run directory exists",
              len(run_dirs) == 1, "; ".join(p.name for p in run_dirs))
        receipt = ROOT / "artifacts" / "R1_S3B_OUTCOME_RECEIPT.json"
        check("the outcome receipt exists", receipt.exists())
        if receipt.exists() and len(bundles) == 1:
            r = json.loads(receipt.read_text(encoding="utf-8"))
            check("outcome bundle bytes still match the recorded file digest",
                  sha256_file(bundles[0]) == r["outcome_file_sha256"],
                  r["outcome_file_sha256"][:16])
            check("outcome bundle identity bindings match the seal",
                  r["identity_bindings"]["CONTENT_COMMIT"] == seal["CONTENT_COMMIT"])
            check("exactly one run was executed",
                  r["execution"]["runs_executed"] == 1,
                  str(r["execution"]["runs_executed"]))

    # ---- 4. the engine's own guards ----------------------------------
    check("L-3 scan clean", scan_no_release_time_inference() == ())
    check("L-8 constants scan clean", scan_no_duplicated_constants() == ())
    check("L-8 parameter scan clean", scan_no_parameter_scan() == ())
    check("L-10 scan clean", scan_no_raw_decoder_import() == ())
    check("L-13 PSMV purity still holds", verify_l13_still_holds() == ())
    proof = prove_gate_independence()
    check("OD-3 gate is independent of the primary path",
          proof["independent"] is True, str(proof["findings"]))

    # ---- 5. validation is SEPARATED, not excused ---------------------
    # The sealed validator asserts SEAL-TIME state and is run against the
    # seal-time content by tools/validate_seal_snapshot.py, where it passes
    # cleanly. It is deliberately NOT run against HEAD here: that would report
    # a validator failure as a normal state.
    check("seal-snapshot validation is a separate tool",
          (ROOT / "tools" / "validate_seal_snapshot.py").exists())
    sealed_validator = (ROOT / "psmv" / "validate_prereg.py").read_text(
        encoding="utf-8")
    check("the sealed validator itself is untouched",
          len(re.findall(r"state: S2 NOT AUTHORIZED", sealed_validator)) == 1)

    # ---- 6. registry immutability and the operational ledger ---------
    from r1.ledger import (assert_sealed_registry_unchanged,  # noqa: PLC0415
                           current_digest)
    assert_sealed_registry_unchanged(contract)
    check("sealed trial registry is byte-identical", True,
          contract.trial_registry_sha256[:16])
    check("operational ledger is OUTSIDE the sealed digest set",
          LEDGER_FILE not in seal["sealed_digests"])
    check("operational ledger chain verifies",
          entries[0].event == "GENESIS" and len(entries) >= 2,
          f"{len(entries)} entries, head {current_digest(ROOT / LEDGER_FILE)[:12]}")
    n_started = sum(1 for e in entries if e.event == "RUN_STARTED")
    if stage in PRE_RUN_STAGES:
        check("RUN_STARTED has NOT been appended -- the trial is not consumed",
              n_started == 0)
    else:
        # Stronger than the pre-run assertion: one run, and never a second.
        check("RUN_STARTED appears EXACTLY ONCE -- one trial, never a second",
              n_started == 1, f"{n_started} occurrence(s)")

    # ---- 7. post-seal interpretation artifacts -----------------------
    errata = ROOT / "R1_SEALED_ERRATA.md"
    check("sealed errata record exists", errata.exists())
    check("errata is NOT in the sealed digest set",
          "R1_SEALED_ERRATA.md" not in seal["sealed_digests"])
    check("errata records the descriptive-only materiality",
          "MATERIALITY                    = DESCRIPTIVE_ONLY"
          in errata.read_text(encoding="utf-8"))

    # ---- 8. the Development adapter is implemented, not deferred -----
    adapter_src = (ROOT / "r1" / "dev_adapter.py").read_text(encoding="utf-8")
    check("Development adapter is implemented",
          "NotImplementedError" not in adapter_src)
    check("Development adapter imports its decoder lazily",
          not any(ln.startswith("import databento")
                  for ln in adapter_src.splitlines()))

    # ---- 8b. S2 implementation identity ------------------------------
    from r1.build_identity import (ATTESTATION_FILE, assert_executable_identity,
                                   runtime_source_map, runtime_source_rollup)
    rollup = runtime_source_rollup()
    check("runtime source rollup computed",
          len(rollup) == 64, f"{len(runtime_source_map())} files, {rollup[:12]}")
    check("no runtime module hard-codes a build commit",
          not any("0bc815dc22863e50777311a9c2c25922ecfeb4fd"
                  in (ROOT / rel).read_text(encoding="utf-8")
                  for rel in runtime_source_map()))
    if (ROOT / ATTESTATION_FILE).exists():
        ident = assert_executable_identity()
        check("executable identity matches the attested S2_CODE_COMMIT",
              True, ident.s2_code_commit[:12])
        check("S2 build attestation is NOT in the sealed digest set",
              ATTESTATION_FILE not in seal["sealed_digests"])
    else:
        notes.append("SKIP  S2 build attestation not present yet "
                     "(expected inside the S2_CODE_COMMIT itself)")

    # ---- 9. A1 is wired into the production path ---------------------
    import inspect

    from r1.pipeline import run_study
    params = inspect.signature(run_study).parameters
    check("run_study takes no caller-supplied A1 boolean",
          "a1_sign_holds" not in params)
    check("run_study takes no n-shrinkage judgement",
          "n_shrunk_materially" not in params)
    check("A1 is computed in the pipeline",
          "evaluate_a1" in inspect.getsource(run_study))

    for line in notes:
        print(line)
    print()
    for line in failures:
        print(line)
    print(f"\n{len(notes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
