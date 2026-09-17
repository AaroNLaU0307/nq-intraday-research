"""Current-stage state validator. UNSEALED, and deliberately so.

`psmv/validate_prereg.py` is inside the sealed digest set. It was written
before the seal and it asserts, among other things:

    check("state: S2 NOT AUTHORIZED", "S2  = NOT AUTHORIZED" in state)

That assertion was true at seal time and is now FALSE: Aaron authorized S2
BUILD on 2026-09-17. The sealed validator cannot be updated -- editing it would
break the seal it exists to protect -- and PROJECT_STATE.md must not be made to
lie in order to satisfy it. So the sealed validator now reports exactly one
expected failure, recorded in S2_BUILD_REPORT.md section 10, and THIS file
validates the current state instead.

It checks the two things that actually matter after a seal:

  1. the seal is intact -- every sealed digest still verifies;
  2. the current stage state is what it claims, and no authority has been
     silently granted.

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

    # ---- 5. the known, expected failure of the sealed validator ------
    sealed_validator = (ROOT / "psmv" / "validate_prereg.py").read_text(
        encoding="utf-8")
    check("the sealed validator's expired S2 assertion is still the ONLY one",
          len(re.findall(r'state: S2 NOT AUTHORIZED', sealed_validator)) == 1,
          "see S2_BUILD_REPORT.md section 10")

    for line in notes:
        print(line)
    print()
    for line in failures:
        print(line)
    print(f"\n{len(notes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
