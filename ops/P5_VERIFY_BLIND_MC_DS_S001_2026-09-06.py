"""P5 independent verifier -- BLIND phase (no registry read).

Fresh top-level session, 2026-09-06. Verifies the sealed MC-DS-S001 N09
supplement against the sealed S0-T001 bundle WITHOUT reading the registry
P4 claims. Every number below is computed here; nothing is copied from the
producing session. Development DBN payloads are NOT read (forbidden for this
seat); the vol column is verified through the sealed headline grid draws,
which are a pure function of (strata, TP/FP day sets, seeds, q, r, k, theta).

Exposure discipline: S0_REPORT.json is loaded for STRUCTURAL keys only
(oracle_daily.*.day_universe.tp_days/fp_days, feasibility_grid.cells.*.grid.*
per_seed dates/allocations/markers, repeats digests, fp_allocation block).
No P&L, precision, F_expected, verdict or exposure value is read, printed or
stored by this script.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf import contracts                                   # noqa: E402
from itsf.mc import atoms                                    # noqa: E402
from itsf.mc import consumer as mcc                          # noqa: E402
from itsf.mc import day_strata_supplement as ds              # noqa: E402
from itsf.mc import production_inputs as pi                  # noqa: E402
from itsf.mc import real_input                               # noqa: E402
from itsf.mc import supplement_authority as sa               # noqa: E402
from itsf.s0 import dataset as s0ds                          # noqa: E402
from itsf.s0 import gridmix as gm                            # noqa: E402
from itsf.s0 import study as s0study                         # noqa: E402

PROD = Path(r"C:\Users\Aaron\quant-data\itsf-runs\supplements"
            r"\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json")
ARCH = Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive\supplements"
            r"\MC-DS-S001_20260905T170810Z\DAY_STRATA_SUPPLEMENT.json")
S0_RUN = real_input.SEALED_RUN_DIR
S0_ARCH = Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive"
               r"\S0-T001_20260813T170432Z")
OUT = REPO / "ops" / "P5_VERIFY_BLIND_MC_DS_S001_2026-09-06.json"

R: dict = {"phase": "BLIND", "utc_started": time.strftime(
    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": {}, "problems": []}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check(name: str, ok: bool, detail=None):
    R["checks"][name] = {"ok": bool(ok), "detail": detail}
    if not ok:
        R["problems"].append(name)
    print(("PASS " if ok else "FAIL ") + name + ("" if detail is None
                                                 else f"  {detail}"))


# ---------------------------------------------------------------- 1-3 bytes
b_prod = PROD.read_bytes()
b_arch = ARCH.read_bytes()
R["production_sha256"] = sha(b_prod)
R["archive_sha256"] = sha(b_arch)
R["production_bytes"] = len(b_prod)
R["archive_bytes"] = len(b_arch)
check("production_archive_byte_identity", b_prod == b_arch,
      {"production": R["production_sha256"], "archive": R["archive_sha256"]})
sibling = [p.name for p in PROD.parent.iterdir()]
check("production_dir_contains_only_sealed_file", sibling == [PROD.name],
      sibling)
sibling_a = [p.name for p in ARCH.parent.iterdir()]
check("archive_dir_contains_only_sealed_file", sibling_a == [ARCH.name],
      sibling_a)

# ---------------------------------------------------------------- 4 schema
sup = json.loads(b_prod)
try:
    ds._validate_supplement_object(sup)
    check("supplement_object_schema_and_declared_digest", True)
except Exception as exc:                                   # noqa: BLE001
    check("supplement_object_schema_and_declared_digest", False, repr(exc))
check("sealed_bytes_are_canonical_serialisation",
      ds.canonical_supplement_bytes(sup) == b_prod)
rows = sup["rows"]
dates = [r["trade_date"] for r in rows]
check("rows_sorted_unique_by_trade_date", dates == sorted(set(dates)))
check("n_rows_equals_len_rows", sup["n_rows"] == len(rows), sup["n_rows"])
R["n_rows"] = len(rows)
R["first_trade_date"] = dates[0]
R["last_trade_date"] = dates[-1]

# ---------------------------------------------------------------- 5 rows digest (own implementation)
canon_rows = json.dumps([dict(r) for r in rows], sort_keys=True,
                        ensure_ascii=True, separators=(",", ":"),
                        allow_nan=False).encode("utf-8")
my_rows_digest = sha(canon_rows)
R["rows_digest_independent"] = my_rows_digest
R["rows_digest_declared_in_artifact"] = sup["rows_digest"]
check("rows_digest_reproduced_independently",
      my_rows_digest == sup["rows_digest"], my_rows_digest)
check("rows_digest_module_agrees", ds.canonical_rows_digest(rows)
      == my_rows_digest)

# ---------------------------------------------------------------- 6-9 source authority
t0 = time.time()
prepared = real_input.prepare_supplement_mc_input()     # gate-first
R["prepare_seconds"] = round(time.time() - t0, 1)
authority = sa.derive_supplement_authority(prepared)
expected_day_set, binding = sa.supplement_build_inputs(authority, prepared)
R["authority"] = {
    "trial_id": authority.trial_id,
    "authorized_commit": authority.authorized_commit,
    "method_version": authority.method_version,
    "method_digest": authority.method_digest,
    "source_artifact_id": authority.source_artifact_id,
    "source_artifact_sha256": authority.source_artifact_sha256,
    "test_only": authority.test_only,
    "bundle_table_digest": authority.bundle_table_digest,
    "theta_channels": list(authority.theta_channels),
    "n_days": authority.n_days,
    "day_universe_digest": authority.day_universe_digest,
    "source_input_sha256": authority.source_input_sha256,
    "authority_digest": authority.authority_digest,
}
check("binding_equals_rederived_binding", binding == sup["binding"],
      {"derived": binding, "sealed": sup["binding"]})
check("day_set_exactly_sealed_universe",
      frozenset(dates) == expected_day_set,
      {"missing": len(expected_day_set - frozenset(dates)),
       "extra": len(frozenset(dates) - expected_day_set)})
check("n_rows_equals_authority_n_days", len(rows) == authority.n_days)
# independent day-universe digest (own serialisation of the schema/value form)
my_du = sha(json.dumps({"schema": sa.DAY_UNIVERSE_DIGEST_SCHEMA,
                        "value": sorted(dates)}, sort_keys=True,
                       ensure_ascii=True, separators=(",", ":"),
                       allow_nan=False).encode("utf-8"))
R["day_universe_digest_independent"] = my_du
check("day_universe_digest_independent_matches_binding",
      my_du == sup["binding"]["day_universe_digest"], my_du)
# source input identity: hash of the pinned prepared identity bytes
my_sis = sha(mcc.prepared_identity_bytes(prepared))
R["source_input_sha256_independent"] = my_sis
check("source_input_sha256_matches_binding",
      my_sis == sup["binding"]["source_input_sha256"], my_sis)
check("method_version_is_frozen_atoms_method_version",
      sup["binding"]["method_version"] == atoms.METHOD_VERSION
      == sa.SUPPLEMENT_METHOD_VERSION, sup["binding"]["method_version"])
check("trial_id_S0_T001", sup["binding"]["trial_id"] == "S0-T001"
      == prepared.trial_id)
check("binding_commit_is_S0_authorized_commit",
      sup["binding"]["authorized_commit"] == prepared.authorized_commit,
      prepared.authorized_commit)
check("custody_source_is_pinned_attestation",
      prepared.source_artifact_id == mcc.ATTESTATION_PATH
      and prepared.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED
      and prepared.test_only is False)

# S0 sealed bytes still in place (both roots) and equal to the custody table
table = dict(prepared.file_sha256)
run_sha = {p.name: sha(p.read_bytes()) for p in S0_RUN.iterdir()
           if p.is_file()}
arch_sha = {p.name: sha(p.read_bytes()) for p in S0_ARCH.iterdir()
            if p.is_file()}
check("s0_run_dir_exact_set_and_digests_match_custody",
      run_sha == table, {"n_files": len(run_sha)})
check("s0_archive_dir_exact_set_and_digests_match_custody",
      arch_sha == table, {"n_files": len(arch_sha)})
my_btd = sha(json.dumps({"schema": sa.BUNDLE_TABLE_DIGEST_SCHEMA,
                         "value": {k: run_sha[k] for k in sorted(run_sha)}},
                        sort_keys=True, ensure_ascii=True,
                        separators=(",", ":")).encode("utf-8"))
check("bundle_table_digest_independent_matches_authority",
      my_btd == authority.bundle_table_digest, my_btd)

# ---------------------------------------------------------------- 10 event column (frozen F10 calendar, no bars)
ruled = contracts.aaron_ruled_methods()
cal = pi.build_event_calendar()
R["f10_events_csv_sha256"] = sha(pi.F10_EVENTS_CSV.read_bytes())
emap = s0ds.build_event_stratum_map({d: cal.encode_f10(d) for d in dates},
                                    ruled.event_na_mapping)
ev_mismatch = [r["trade_date"] for r in rows
               if emap["stratum_of"][r["trade_date"]] != r["event_stratum"]]
check("event_stratum_column_rederived_from_frozen_f10_calendar",
      not ev_mismatch, {"mismatches": len(ev_mismatch),
                        "event_na_mapping": ruled.event_na_mapping})
check("year_column_equals_trade_date_year",
      all(r["year"] == int(r["trade_date"][:4]) for r in rows))
check("vocabularies_within_ruled_sets",
      all(r["vol_stratum"] in ds.VOL_STRATA
          and r["event_stratum"] in ds.EVENT_STRATA for r in rows))

# ---------------------------------------------------------------- 11-12 headline replay identity
t0 = time.time()
rep = json.loads((S0_RUN / "S0_REPORT.json").read_bytes())
R["s0_report_load_seconds"] = round(time.time() - t0, 1)
cells = rep["feasibility_grid"]["cells"]
policy = ruled.grid_policy
fpm = ruled.fp_allocation
seeds = contracts.RESEARCH_BOOTSTRAP_SEEDS
strata_in = {r["trade_date"]: (str(r["year"]), r["vol_stratum"],
                               r["event_stratum"]) for r in rows}
theta_of = {s0study.theta_key(t): float(t) for t in s0study.FROZEN_THETAS}
n_cells_verified = 0
n_cells_failed = 0
n_infeasible_matched = 0
n_grids = 0
per_grid: dict = {}
headline_digests: dict = {}    # (tkey, q, r, seed) -> digest (for cross-cell identity)
for cell_key in sorted(cells):
    tkey, eng, scn = cell_key.split("|")
    theta = theta_of[tkey]
    du = rep["oracle_daily"][tkey]["day_universe"]
    tp_days = [str(d) for d in du["tp_days"]]
    fp_days = [str(d) for d in du["fp_days"]]
    all_dates = sorted(set(tp_days) | set(fp_days))
    stratum_of = gm._validated_strata(strata_in, all_dates)
    tp_pools = gm._pools({d: 0.0 for d in tp_days}, stratum_of)
    fp_pools = gm._pools({d: 0.0 for d in fp_days}, stratum_of)
    tp_avail = {k: len(v) for k, v in tp_pools.items()}
    fp_avail = {k: len(v) for k, v in fp_pools.items()}
    n_tp_av, n_fp_av = len(tp_days), len(fp_days)
    key_of_date = {d: k for k, dl in tp_pools.items() for d in dl}
    tp_keys = sorted(tp_pools)
    cell = cells[cell_key]
    g = {"points_ok": 0, "points_failed": 0, "infeasible_ok": 0,
         "avail_ok": (cell["n_tp_available"] == n_tp_av
                      and cell["n_fp_available"] == n_fp_av),
         "n_points": len(cell["grid"])}
    if not g["avail_ok"]:
        R["problems"].append(f"{cell_key}:availability_mismatch")
    expected_keys = {f"q{q / 1000:.2f}_r{r / 1000:.2f}"
                     for q in gm.Q_GRID_MILLIS for r in gm.R_GRID_MILLIS}
    if set(cell["grid"]) != expected_keys:
        R["problems"].append(f"{cell_key}:grid_key_set_mismatch")
    for q_mil in gm.Q_GRID_MILLIS:
        for r_mil in gm.R_GRID_MILLIS:
            pkey = f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"
            pt = cell["grid"][pkey]
            n_tp = gm.floor_n_tp(r_mil, n_tp_av)
            n_fp = gm.n_fp_for(n_tp, q_mil)
            ok = (pt["n_tp_target"] == n_tp and pt["n_fp_target"] == n_fp)
            if n_fp > n_fp_av:
                ok = ok and pt["infeasible_by_sample"] is True \
                    and not pt.get("per_seed")
                if ok:
                    g["infeasible_ok"] += 1
                    n_infeasible_matched += 1
                else:
                    g["points_failed"] += 1
                    n_cells_failed += 1
                    R["problems"].append(f"{cell_key}:{pkey}:infeasible")
                continue
            ok = ok and pt["infeasible_by_sample"] is False
            tp_alloc = gm.allocate(n_tp, tp_avail)
            headline_k = int(pt["repeats"]["headline_k"])
            ok = ok and headline_k == policy.k_start_index
            fp_block_ref = None
            for seed in seeds:
                rng = gm.repeat_rng(seed, theta, q_mil, r_mil, headline_k,
                                    policy)
                tp_dates = gm._select(tp_pools, tp_alloc, rng)
                sel = gm._selected_tp_composition(tp_dates, key_of_date,
                                                  tp_keys)
                fpb = gm.fp_allocation_from_selected_tp(n_fp, sel, fp_avail,
                                                        fpm)
                fp_dates = gm._select(fp_pools, fpb["fp_alloc"], rng)
                if fp_block_ref is None:
                    fp_block_ref = fpb
                row = pt["per_seed"][str(seed)]
                markers = sorted([[d, gm.MARK_TP] for d in tp_dates]
                                 + [[d, gm.MARK_FP] for d in fp_dates])
                digest = gm.repeat_draw_digest(tp_dates, fp_dates)
                sealed_digest = pt["repeats"]["per_seed"][str(seed)][
                    "digests_by_k"][str(headline_k)]
                same = (list(row["tp_dates"]) == tp_dates
                        and list(row["fp_dates"]) == fp_dates
                        and {k: int(v) for k, v in row["allocation_tp"].items()}
                        == tp_alloc
                        and {k: int(v) for k, v in row["allocation_fp"].items()}
                        == fpb["fp_alloc"]
                        and [list(m) for m in row["day_markers"]] == markers
                        and int(row["n_tp_actual"]) == len(tp_dates)
                        and int(row["n_fp_actual"]) == len(fp_dates)
                        and sealed_digest == digest)
                ok = ok and same
                headline_digests.setdefault((tkey, q_mil, r_mil, seed),
                                            set()).add(digest)
            fa = pt["fp_allocation"]
            ok = ok and ({k: int(v) for k, v in fa["fp_alloc"].items()}
                         == fp_block_ref["fp_alloc"]
                         and {k: int(v) for k, v in
                              fa["weights_selected_tp"].items()}
                         == fp_block_ref["weights_selected_tp"])
            if ok:
                g["points_ok"] += 1
                n_cells_verified += 1
            else:
                g["points_failed"] += 1
                n_cells_failed += 1
                R["problems"].append(f"{cell_key}:{pkey}:headline_mismatch")
    per_grid[cell_key] = g
    n_grids += 1
R["headline_replay"] = {
    "n_grids": n_grids,
    "n_cells_verified": n_cells_verified,
    "n_cells_failed": n_cells_failed,
    "n_infeasible_points_matched": n_infeasible_matched,
    "per_grid": per_grid,
    "cross_cell_draw_identity": all(len(v) == 1
                                    for v in headline_digests.values()),
    "seconds": round(time.time() - t0, 1),
}
check("headline_replay_identity_all_cells",
      n_cells_failed == 0 and n_cells_verified > 0
      and all(g["avail_ok"] for g in per_grid.values()),
      {"n_cells_verified": n_cells_verified,
       "n_cells_failed": n_cells_failed})
R["n_cells"] = n_cells_verified

# ---------------------------------------------------------------- 12b supplementary: full K=200 repeat-set digests
t0 = time.time()
full_k = {"grids_checked": 0, "seed_sets_ok": 0, "seed_sets_failed": 0}
cache: dict = {}
for cell_key in sorted(cells):
    tkey, eng, scn = cell_key.split("|")
    theta = theta_of[tkey]
    if tkey not in cache:
        du = rep["oracle_daily"][tkey]["day_universe"]
        tp_days = [str(d) for d in du["tp_days"]]
        fp_days = [str(d) for d in du["fp_days"]]
        stratum_of = gm._validated_strata(
            strata_in, sorted(set(tp_days) | set(fp_days)))
        tp_pools = gm._pools({d: 0.0 for d in tp_days}, stratum_of)
        fp_pools = gm._pools({d: 0.0 for d in fp_days}, stratum_of)
        tp_avail = {k: len(v) for k, v in tp_pools.items()}
        fp_avail = {k: len(v) for k, v in fp_pools.items()}
        key_of_date = {d: k for k, dl in tp_pools.items() for d in dl}
        tp_keys = sorted(tp_pools)
        n_tp_av, n_fp_av = len(tp_days), len(fp_days)
        digests_all: dict = {}
        for q_mil in gm.Q_GRID_MILLIS:
            for r_mil in gm.R_GRID_MILLIS:
                n_tp = gm.floor_n_tp(r_mil, n_tp_av)
                n_fp = gm.n_fp_for(n_tp, q_mil)
                if n_fp > n_fp_av:
                    continue
                tp_alloc = gm.allocate(n_tp, tp_avail)
                for seed in seeds:
                    dk: dict = {}
                    for k in gm.repeat_k_indices(policy, doublings=0):
                        rng = gm.repeat_rng(seed, theta, q_mil, r_mil, k,
                                            policy)
                        tp_dates = gm._select(tp_pools, tp_alloc, rng)
                        sel = gm._selected_tp_composition(
                            tp_dates, key_of_date, tp_keys)
                        fpb = gm.fp_allocation_from_selected_tp(
                            n_fp, sel, fp_avail, fpm)
                        fp_dates = gm._select(fp_pools, fpb["fp_alloc"], rng)
                        dk[k] = gm.repeat_draw_digest(tp_dates, fp_dates)
                    digests_all[(q_mil, r_mil, seed)] = (
                        dk, gm._digest_of_digests(dk))
        cache[tkey] = digests_all
    digests_all = cache[tkey]
    cell = cells[cell_key]
    for (q_mil, r_mil, seed), (dk, dod) in digests_all.items():
        pkey = f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"
        blk = cell["grid"][pkey]["repeats"]["per_seed"][str(seed)]
        sealed = {int(k): v for k, v in blk["digests_by_k"].items()}
        if sealed == dk and blk["digest_of_digests"] == dod:
            full_k["seed_sets_ok"] += 1
        else:
            full_k["seed_sets_failed"] += 1
            R["problems"].append(f"{cell_key}:{pkey}:{seed}:full_k_mismatch")
    full_k["grids_checked"] += 1
full_k["seconds"] = round(time.time() - t0, 1)
R["full_k_replay_supplementary"] = full_k
check("supplementary_full_k200_repeat_digests_all_cells",
      full_k["seed_sets_failed"] == 0 and full_k["seed_sets_ok"] > 0,
      full_k)

# ---------------------------------------------------------------- 13-14 verdict fields
R["rederivation_reproduced"] = "YES" if all(
    R["checks"][n]["ok"] for n in (
        "supplement_object_schema_and_declared_digest",
        "sealed_bytes_are_canonical_serialisation",
        "rows_digest_reproduced_independently",
        "binding_equals_rederived_binding",
        "day_set_exactly_sealed_universe",
        "day_universe_digest_independent_matches_binding",
        "source_input_sha256_matches_binding",
        "method_version_is_frozen_atoms_method_version",
        "s0_run_dir_exact_set_and_digests_match_custody",
        "s0_archive_dir_exact_set_and_digests_match_custody",
        "event_stratum_column_rederived_from_frozen_f10_calendar",
        "year_column_equals_trade_date_year")) else "NO"
R["headline_replay_identity"] = "PASS" if R["checks"][
    "headline_replay_identity_all_cells"]["ok"] else "FAIL"
R["utc_finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
OUT.write_bytes(json.dumps(R, indent=1, sort_keys=True).encode("utf-8"))
print("\nrederivation_reproduced =", R["rederivation_reproduced"])
print("headline_replay_identity =", R["headline_replay_identity"])
print("n_cells =", R["n_cells"])
print("problems =", R["problems"][:20], "(total", len(R["problems"]), ")")
print("written", OUT, sha(OUT.read_bytes()))
