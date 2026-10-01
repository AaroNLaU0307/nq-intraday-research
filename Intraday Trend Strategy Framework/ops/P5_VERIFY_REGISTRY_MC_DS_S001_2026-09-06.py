"""P5 independent verifier -- REGISTRY phase (runs AFTER the blind phase).

Reads the real registry, compares the P4 claims against the blind results,
plans the post-P4 transition with the project's own planner, builds the
contract's failure-path candidate row (F2v), and preflights it in a
MEMORY-ONLY copy of the registry with the real parser. Appends nothing.
Asserts afterwards that registry, sealed and archive bytes are unchanged.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.mc import registry_boundary as rb                  # noqa: E402
from itsf.mc import supplement_contract as sc                # noqa: E402
from itsf.mc import supplement_registry as sr                # noqa: E402
from itsf.mc import supplement_runner as srun                # noqa: E402

SID = "MC-DS-S001"
OPS = REPO / "ops"
BLIND = OPS / "P5_VERIFY_BLIND_MC_DS_S001_2026-09-06.json"
DIAG = OPS / "P5_VERIFY_DIAG_MC_DS_S001_2026-09-06.json"
ATT = OPS / "P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md"
OUT = OPS / "P5_VERIFY_REGISTRY_MC_DS_S001_2026-09-06.json"
CAND = OPS / "F2V_CANDIDATE_MC_DS_S001_2026-09-06.md"
PROD = Path(r"C:\Users\Aaron\quant-data\itsf-runs\supplements"
            r"\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json")
ARCH = Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive\supplements"
            r"\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json")
ACTOR = "fresh fable verifier"   # fixture convention `fresh <family> verifier`
                                  # (tests/test_mc_supplement_registry.py:56),
                                  # rendered in the ruled governance shape


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


R: dict = {"phase": "REGISTRY", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                     time.gmtime()),
           "checks": {}, "problems": []}


def check(name, ok, detail=None):
    R["checks"][name] = {"ok": bool(ok), "detail": detail}
    if not ok:
        R["problems"].append(name)
    print(("PASS " if ok else "FAIL ") + name
          + ("" if detail is None else f"  {detail}"))


blind = json.loads(BLIND.read_bytes())
R["blind_results_sha256"] = sha(BLIND.read_bytes())
R["diag_results_sha256"] = sha(DIAG.read_bytes())
att_bytes = ATT.read_bytes()
R["attestation_path"] = str(ATT)
R["attestation_sha256"] = sha(att_bytes)
check("attestation_exists_nonempty", len(att_bytes) > 0,
      {"bytes": len(att_bytes), "sha256": R["attestation_sha256"]})

# ---------------------------------------------------------------- registry as it stands
snap = rb.read_snapshot()
text = snap.text
reg_path = Path(rb.REGISTRY_REPO_ROOT) / rb.REGISTRY_PATH
reg_bytes_before = reg_path.read_bytes()
R["registry"] = {"path": str(reg_path), "sha256": sha(reg_bytes_before),
                 "bytes": len(reg_bytes_before)}
res = sr.resolve_supplement_chain(text, SID)
check("registry_resolves_without_problem", res.problem == "", res.problem)
check("chain_ends_at_P4", res.short_ids[-1:] == ("P4",), res.short_ids)
check("chain_started_no_live_p2_not_retired",
      res.started and not res.live_authorizations and not res.retired)
p4 = [e for e in res.events if e.short_id == "P4"][0]
claims = dict(p4.fields)
R["p4_claims"] = claims

# ---------------------------------------------------------------- claim-by-claim comparison
cmp = {
    "sealed_sha256": (claims["sealed_sha256"], blind["production_sha256"]),
    "rows_digest": (claims["rows_digest"], blind["rows_digest_independent"]),
    "day_universe_digest": (claims["day_universe_digest"],
                            blind["day_universe_digest_independent"]),
    "source_input_sha256": (claims["source_input_sha256"],
                            blind["source_input_sha256_independent"]),
    "method_version": (claims["method_version"],
                       blind["authority"]["method_version"]),
    "n_rows": (int(claims["n_rows"]), int(blind["n_rows"])),
    "archive": (claims["archive"],
                "archive_ok" if blind["checks"][
                    "production_archive_byte_identity"]["ok"]
                else "archive_mismatch"),
}
R["p4_comparison"] = {k: {"claimed": a, "recomputed": b, "match": a == b}
                      for k, (a, b) in cmp.items()}
check("all_p4_claims_reproduced", all(a == b for a, b in cmp.values()),
      {k: v["match"] for k, v in R["p4_comparison"].items()})

# ---------------------------------------------------------------- verdict fields from the blind phase
R["rederivation_reproduced"] = blind["rederivation_reproduced"]
R["headline_replay_identity"] = blind["headline_replay_identity"]
R["n_cells"] = blind["n_cells"]
p5_possible = (blind["rederivation_reproduced"] == "YES"
               and blind["headline_replay_identity"] == "PASS"
               and blind["n_cells"] >= 1)
R["p5_pass_conditions_met"] = p5_possible
outcome = "verified" if p5_possible else "verification_failed"
nxt = srun.plan_next_short_id("P4", outcome=outcome)
R["planned_next_short_id"] = nxt
check("planner_routes_P4_to_contract_path",
      nxt == ("P5" if p5_possible else "F2v"), nxt)

# ---------------------------------------------------------------- candidate row (mechanical)
rows, _ = sr.parse_registry_rows(text)
highest = max(int(r.seq) for r in rows if r.numbered and r.seq.isdigit())
seq = highest + 1
spec = sc.EVENTS[nxt]
commit = "3df1656f105b9314235bd28957336a7dec4bde05"    # framework HEAD, verified clean
utc = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
check("actor_form_is_governance_and_permitted",
      sc.actor_form(ACTOR) == sc.ACTOR_FORM_GOVERNANCE
      and ACTOR != sc.ACTOR_AARON
      and not ACTOR.startswith(sc.ACTOR_MAIN_AGENT), ACTOR)
if nxt == "F2v":
    detail = (
        "8 of 2842 days carry a stratum label different from the one the "
        "S0-T001 run stratified on (vol T2 vs T3 on 2012-11-26 2012-11-27 "
        "2013-05-06 2014-10-20 2015-12-10 and event FOMC vs none on "
        "2019-10-11 2020-03-03 2020-03-23), headline draw reproduced in 0 of "
        "1008 cells as sealed and in 1008 of 1008 with those eight labels "
        "restored, verifier attestation "
        "ops/P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md sha256 "
        + R["attestation_sha256"])
    fields = [("supplement_id", SID),
              ("failure_code", "headline_replay_mismatch"),
              ("detail", detail),
              ("sealed_artifact_deleted", "NO"),
              ("supersession_required", "YES")]
else:
    fields = [("supplement_id", SID),
              ("rederivation_reproduced", "YES"),
              ("headline_replay_identity", "PASS"),
              ("n_cells", str(blind["n_cells"])),
              ("attestation_sha256", R["attestation_sha256"])]
assert all(";" not in v and "|" not in v for _, v in fields)
note = f"[{SID}] " + "; ".join(f"{k}: {v}" for k, v in fields)
row = f"| {seq} | {utc} | {spec.token} | {commit} | {ACTOR} | {note} |"
R["candidate_row"] = row
R["candidate_short_id"] = nxt
R["candidate_seq"] = seq

# ---------------------------------------------------------------- memory-only preflight
mem = text if text.endswith("\n") else text + "\n"
mem = mem + row + "\n"
events, refusal = sr.parse_supplement_events(mem)
check("candidate_row_parses_row_level", refusal is None,
      None if refusal is None else str(refusal))
res2 = sr.resolve_supplement_chain(mem, SID)
check("memory_chain_problem_empty", res2.problem == "", res2.problem)
check("memory_chain_predecessor_is_P4_then_candidate",
      res2.short_ids[-2:] == ("P4", nxt), res2.short_ids)
check("memory_chain_started_still_true", res2.started is True)
check("memory_chain_no_new_live_p2", len(res2.live_authorizations) == 0)
check("memory_chain_not_retired", res2.retired is False)
R["memory_chain"] = {
    "short_ids": list(res2.short_ids), "terminal": res2.terminal,
    "closed": res2.closed, "started": res2.started,
    "retired": res2.retired, "live": len(res2.live_authorizations),
    "state_after": sc.chain_state_refusal(nxt),
    "successors_of_candidate": list(spec.successors),
    "candidate_is_terminal": spec.terminal,
}
if nxt == "P5":
    check("memory_chain_terminal_P5_closed", res2.terminal == "P5"
          and res2.closed)
else:
    check("memory_chain_F2v_not_terminal_next_is_F3",
          res2.terminal == "" and not res2.closed
          and spec.successors == ("F3",)
          and sc.chain_state_refusal(nxt) == "AWAITING_RETIREMENT")
# sequence arithmetic re-checked by the parser (global namespace)
rows2, _ = sr.parse_registry_rows(mem)
ev2 = [e for e in events if e.short_id == nxt][-1]
check("candidate_consumes_next_global_sequence",
      int(ev2.seq) == highest + 1, {"highest_before": highest, "seq": seq})

# ---------------------------------------------------------------- nothing changed on disk
check("registry_bytes_unchanged",
      reg_path.read_bytes() == reg_bytes_before
      and sha(reg_bytes_before) == R["registry"]["sha256"])
check("sealed_bytes_unchanged",
      sha(PROD.read_bytes()) == blind["production_sha256"])
check("archive_bytes_unchanged",
      sha(ARCH.read_bytes()) == blind["archive_sha256"])

R["problems_total"] = len(R["problems"])
OUT.write_bytes(json.dumps(R, indent=1, sort_keys=True).encode("utf-8"))
CAND.write_text(
    "# CANDIDATE ROW FOR AARON — NOT APPENDED\n\n"
    f"```\nCANDIDATE_EVENT={nxt} {spec.token}\n"
    f"PREDECESSOR=P4 (chain {'/'.join(res.short_ids)})\n"
    f"GLOBAL_SEQUENCE={seq} (highest before: {highest})\n"
    f"ACTOR={ACTOR} (form: {sc.actor_form(ACTOR)})\n"
    f"COMMIT={commit} (framework HEAD at verification, worktree clean)\n"
    f"ATTESTATION={ATT.name} sha256 {R['attestation_sha256']}\n"
    f"PREFLIGHT_PROBLEMS={len(R['problems'])}\n"
    f"STATE_AFTER_APPEND={sc.chain_state_refusal(nxt)} ; successors {list(spec.successors)}\n"
    "```\n\nRow, verbatim (one line):\n\n```\n" + row + "\n```\n\n"
    "Memory-only preflight: see P5_VERIFY_REGISTRY_MC_DS_S001_2026-09-06.json.\n"
    "Registry, sealed artifact and archive copy were NOT modified.\n",
    encoding="utf-8")
print("\ncandidate:", nxt, "seq", seq)
print("problems:", R["problems"])
print("written", OUT.name, sha(OUT.read_bytes()))
print("written", CAND.name, sha(CAND.read_bytes()))
