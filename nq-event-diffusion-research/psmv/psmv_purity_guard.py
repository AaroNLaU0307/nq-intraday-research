"""L-13 PSMV OUTPUT PURITY GUARD — and the proof that it can fail.

A guard that has never been shown to fail is not a guard. This module applies
three mechanical rules to the PSMV artifact and its producing source, then
re-applies each rule to a deliberately POISONED copy (written to the scratchpad,
never to the project) and asserts that the rule REFUSES it.

RULES
  R1  NO_FLOAT_LEAF        Every numeric leaf in the artifact is an `int`.
                           Counts, ordinals and minute indices are integers;
                           a price, a return, a mean, a standard deviation, a
                           dispersion or an MDE is not. A single float leaf is
                           therefore sufficient evidence of contamination.
  R2  NO_FORBIDDEN_KEY     No object key matches an outcome-bearing token.
  R3  SOURCE_FIELD_SCAN    The producing module contains no string literal
                           equal to a price/volume record field, so it cannot
                           have dereferenced one.

The poisoned fixtures use fabricated sentinel constants (1.2345 / "close").
No market value is read, written or inspected anywhere in this file.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
ARTIFACT = PROJECT / "artifacts" / "PSMV_STRUCTURAL_REPORT.json"
SOURCE = PROJECT / "psmv" / "psmv_structural.py"
ATTESTATION = PROJECT / "artifacts" / "PSMV_PURITY_ATTESTATION.json"

FORBIDDEN_RECORD_FIELDS = {"open", "high", "low", "close", "volume",
                           "price", "px", "bid_px", "ask_px"}

# Keys are split on every non-alphanumeric character and matched TOKEN-WISE.
# A word-boundary regex is not enough: `\bmean\b` does not match inside
# `mean_return_per_event`, because `_` is a word character. The first version
# of this guard made exactly that mistake and its own mutation fixture caught
# it -- which is the reason the mutation demonstration exists.
FORBIDDEN_KEY_TOKENS = {
    "price", "prices", "px", "open", "high", "low", "close", "volume",
    "return", "returns", "pnl", "sharpe", "mean", "median", "stdev",
    "stddev", "variance", "sigma", "dispersion", "mde", "sign", "signs",
    "direction", "spread", "mae", "mfe", "excursion", "init", "ynet",
    "ygross", "devent", "quantile", "percentile", "moment",
}

# Keys that trip token matching for a declared, audited reason. Each entry is
# a deliberate exception, not a pattern loosening: the token set stays strict
# and every future collision must be justified here or fixed at the source.
KEY_ALLOWLIST = {
    "E4_r_init_zero_no_direction":
        "names the DEFERRED test PSMV did not perform; the node records only "
        "status and rationale, and carries no value",
    "L1_minus_early_close_equals_L2":
        "'early close' is the scheduled half-day session structure (ITSF "
        "frozen L44), never a closing price",
    "minus_scheduled_early_close_days":
        "same: scheduled half-day count",
}

_TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
def rule_no_float_leaf(obj, path="$") -> list[str]:
    bad: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            bad += rule_no_float_leaf(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += rule_no_float_leaf(v, f"{path}[{i}]")
    elif isinstance(obj, bool) or obj is None:
        pass
    elif isinstance(obj, int):
        pass
    elif isinstance(obj, float):
        bad.append(f"{path}: float leaf")
    elif isinstance(obj, str):
        if re.fullmatch(r"[+-]?\d+\.\d+", obj.strip()):
            bad.append(f"{path}: decimal-shaped string leaf")
    else:
        bad.append(f"{path}: unexpected leaf type {type(obj).__name__}")
    return bad


def rule_no_forbidden_key(obj, path="$") -> list[str]:
    bad: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k)
            tokens = {t.lower() for t in _TOKEN_SPLIT.split(key) if t}
            hit = tokens & FORBIDDEN_KEY_TOKENS
            if hit and key not in KEY_ALLOWLIST:
                bad.append(f"{path}.{key}: forbidden key token(s) "
                           f"{sorted(hit)}")
            bad += rule_no_forbidden_key(v, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += rule_no_forbidden_key(v, f"{path}[{i}]")
    return bad


def rule_source_field_scan(source_path: Path) -> list[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.strip().lower() in FORBIDDEN_RECORD_FIELDS:
                bad.append(f"line {node.lineno}: string literal "
                           f"{node.value!r} could name a price/volume field")
    return bad


# --------------------------------------------------------------------------
def main() -> int:
    if not ARTIFACT.exists():
        print("PURITY: artifact missing -- fail closed")
        return 1
    art = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    live = {
        "R1_NO_FLOAT_LEAF": rule_no_float_leaf(art),
        "R2_NO_FORBIDDEN_KEY": rule_no_forbidden_key(art),
        "R3_SOURCE_FIELD_SCAN": rule_source_field_scan(SOURCE),
    }

    # ---- the must-fail demonstration ------------------------------------
    scratch = Path(os.environ.get("TMPDIR") or tempfile.gettempdir()) / "r1_psmv_mutation"
    scratch.mkdir(parents=True, exist_ok=True)

    poisoned = copy.deepcopy(art)
    poisoned["__MUTATION_FIXTURE_NOT_A_RESULT__"] = {
        "fabricated_sentinel_float": 1.2345}
    mutation_r1 = rule_no_float_leaf(poisoned)

    poisoned2 = copy.deepcopy(art)
    poisoned2["mean_return_per_event"] = 0
    mutation_r2 = rule_no_forbidden_key(poisoned2)

    src = SOURCE.read_text(encoding="utf-8")
    poisoned_src = scratch / "poisoned_psmv_structural.py"
    poisoned_src.write_text(
        src + '\n\ndef _mutation_fixture(arr):\n    return arr["close"]\n',
        encoding="utf-8")
    mutation_r3 = rule_source_field_scan(poisoned_src)

    (scratch / "poisoned_artifact_float.json").write_text(
        json.dumps(poisoned, indent=1), encoding="utf-8")
    (scratch / "poisoned_artifact_key.json").write_text(
        json.dumps(poisoned2, indent=1), encoding="utf-8")

    demos = {
        "R1_NO_FLOAT_LEAF": {"injected": "fabricated sentinel float 1.2345",
                             "refused": bool(mutation_r1),
                             "findings": len(mutation_r1)},
        "R2_NO_FORBIDDEN_KEY": {"injected": "key 'mean_return_per_event'",
                                "refused": bool(mutation_r2),
                                "findings": len(mutation_r2)},
        "R3_SOURCE_FIELD_SCAN": {"injected": 'literal "close" in a subscript',
                                 "refused": bool(mutation_r3),
                                 "findings": len(mutation_r3)},
    }

    live_pass = all(not v for v in live.values())
    demo_pass = all(d["refused"] for d in demos.values())

    attestation = {
        "artifact": "R1_PSMV_PURITY_ATTESTATION",
        "schema": "r1_psmv_purity.v1",
        "invariant": "L-13 PSMV output purity",
        "target_artifact": ARTIFACT.name,
        "target_artifact_sha256": sha256_file(ARTIFACT),
        "producing_source": SOURCE.name,
        "producing_source_sha256": sha256_file(SOURCE),
        "rules": {
            "R1_NO_FLOAT_LEAF": "every numeric leaf is an int",
            "R2_NO_FORBIDDEN_KEY": "no object key contains an outcome token, "
                                   "matched token-wise after splitting on "
                                   "every non-alphanumeric character",
            "R3_SOURCE_FIELD_SCAN": "the producing module holds no string "
                                    "literal naming a price/volume field",
        },
        "live_result": {k: {"pass": not v, "findings": v} for k, v in live.items()},
        "live_pass": live_pass,
        "mutation_demonstration": demos,
        "mutation_demonstration_pass": demo_pass,
        "mutation_fixture_location": str(scratch),
        "mutation_fixture_note": "fabricated sentinels only; no market value "
                                 "was read, written or inspected",
        "key_allowlist": KEY_ALLOWLIST,
        "verdict": "PASS" if (live_pass and demo_pass) else "FAIL",
    }
    ATTESTATION.write_text(json.dumps(attestation, indent=2) + "\n",
                           encoding="utf-8")

    for k, v in live.items():
        print(f"PURITY {k}: {'PASS' if not v else 'FAIL ' + str(v[:3])}")
    for k, d in demos.items():
        print(f"MUTATION {k}: guard refused the poisoned fixture = {d['refused']}")
    print(f"PURITY VERDICT: {attestation['verdict']}")
    print(f"PURITY: wrote {ATTESTATION}")
    return 0 if attestation["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
