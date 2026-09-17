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

    # ---- 2. current stage state --------------------------------------
    for phrase, why in (
            ("STAGE                = S2 BUILD (COMPLETE)", "stage"),
            ("S1                   = SEALED", "S1 sealed"),
            ("S3_RUN               = NOT AUTHORIZED", "S3 not authorized"),
            ("OD3_POWER_GATE       = NOT RUN", "gate not run"),
            ("R1_OUTCOME           = NOT COMPUTED", "no outcome"),
            ("TRIAL_CONSUMED       = NO", "trial not consumed"),
            ("INTERNAL_VALIDATION  = NOT GRANTED", "IV not granted"),
            ("LOCKBOX              = NOT GRANTED", "Lockbox not granted"),
            ("OUTCOME_REVEAL       = NOT GRANTED", "reveal not granted"),
            ("R1_OUTCOME_EXPOSURE  = NONE", "no exposure")):
        check(f"state: {why}", phrase in state, phrase.split("=")[0].strip())

    # ---- 3. no real outcome exists anywhere in the repository --------
    run_dirs = [p for p in ROOT.rglob("sealed_r1_outcome.json")]
    check("no sealed R1 outcome file exists in the repository",
          not run_dirs, "; ".join(str(p) for p in run_dirs[:3]))

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
    from r1.ledger import (LEDGER_FILE, assert_sealed_registry_unchanged,
                           current_digest, verify_chain)
    assert_sealed_registry_unchanged(contract)
    check("sealed trial registry is byte-identical", True,
          contract.trial_registry_sha256[:16])
    check("operational ledger is OUTSIDE the sealed digest set",
          LEDGER_FILE not in seal["sealed_digests"])
    entries = verify_chain(ROOT / LEDGER_FILE)
    check("operational ledger chain verifies",
          entries[0].event == "GENESIS" and len(entries) >= 2,
          f"{len(entries)} entries, head {current_digest(ROOT / LEDGER_FILE)[:12]}")
    check("RUN_STARTED has NOT been appended -- the trial is not consumed",
          not any(e.event == "RUN_STARTED" for e in entries))

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
