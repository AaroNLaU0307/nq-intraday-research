# -*- coding: utf-8 -*-
"""Reproduction harness for the two N14 Round-1 blocking findings.

WHY THIS EXISTS. The bounded repair authorised on 2026-09-11 required each
finding to be mechanically reproduced BEFORE its implementation was touched,
and to STOP rather than repair a path that could not be reproduced. One
reproduced and one did not, so this harness is the evidence for both answers
and the way to re-check them without taking my word for it.

    python scripts/n14_round1_repro.py

It reads only frozen synthetic objects and a throwaway registry in the system
temp directory. It NEVER touches the real registry, never runs MC, and writes
nothing into the repository.

RUN IT AGAINST THE REVIEWED TARGET. The findings are against commit
b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d; `src/` was byte-identical to that
commit when these results were taken.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import grid_replay as gr                       # noqa: E402
from itsf.mc import mc_contract as mcc                      # noqa: E402
from itsf.mc import mc_registry as mr                       # noqa: E402
from itsf.mc import registry_boundary as rb                 # noqa: E402

COMBO = "lucid|E1|P2"
C40 = "a" * 40
UTC = "2026-08-25T00:00:00Z"
RID = "MC-R001"
HEADER = ("| # | utc | event | commit | actor | note |\n"
          "|---|-----|-------|--------|-------|------|\n")


# ---------------------------------------------------------------- finding A
def _cell(p5: float, median: float) -> gr.CellStatistics:
    return gr.CellStatistics(conservative_p5={COMBO: p5},
                             stress_median={COMBO: median},
                             feasible={COMBO: True},
                             identity={"n_tp": 10, "n_fp": 5})


def _marked(key) -> gr.InfeasibleCell:
    return gr.InfeasibleCell(reason=gr.INFEASIBLE_BY_SAMPLE, q_mil=int(key[0]),
                             r_mil=int(key[1]), master_seed=1, doublings=0,
                             n_tp=10, n_fp=999, fp_available=5,
                             detail="synthetic")


def finding_a() -> bool:
    """O7/O12: can a MIXED K/2K class pair vanish and leave converged=True?

    Every mixed arrangement, both region kinds, with an ordinary sampleable
    cell and a genuine boundary-band cell alongside so the mixed cell is the
    only thing under test.
    """
    mixed, band = gr.GRID_CELL_KEYS[0], gr.GRID_CELL_KEYS[1]
    cases = (
        ("K marked / 2K out", _marked(mixed), _cell(-10.0, -10.0)),
        ("K marked / 2K in ", _marked(mixed), _cell(100.0, 50.0)),
        ("K out    / 2K marked", _cell(-10.0, -10.0), _marked(mixed)),
        ("K in     / 2K marked", _cell(100.0, 50.0), _marked(mixed)),
    )
    print("FINDING A -- O7/O12 mixed-class K/2K comparison")
    print("  %-18s %-22s %-10s %s"
          % ("kind", "arrangement", "converged", "mixed cell surfaced"))
    false_convergence = False
    for kind in gr.REGION_KINDS:
        for name, cell_k, cell_2k in cases:
            at_k = {k: _cell(100.0, 50.0) for k in gr.GRID_CELL_KEYS}
            at_2k = {k: _cell(100.0, 50.0) for k in gr.GRID_CELL_KEYS}
            at_k[mixed], at_2k[mixed] = cell_k, cell_2k
            at_k[band], at_2k[band] = _cell(1.0, 1.0), _cell(-1.0, -1.0)
            cmp = gr.compare_region_maps(kind, at_k, at_2k, k=64, k_doubled=128)
            surfaced = mixed in cmp.flipped_cells
            if cmp.converged:
                false_convergence = True
            print("  %-18s %-22s %-10s %s"
                  % (kind[:17], name, cmp.converged, surfaced))

    # The same-class control, which existing authority makes legal.
    at_k = {k: _cell(100.0, 50.0) for k in gr.GRID_CELL_KEYS}
    at_2k = {k: _cell(100.0, 50.0) for k in gr.GRID_CELL_KEYS}
    at_k[mixed] = at_2k[mixed] = _marked(mixed)
    control = gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                                     k=64, k_doubled=128)
    print("  control: both marked (legal, same class) -> converged=%s"
          % control.converged)

    # The one branch that IS silent: the public drift function on its own.
    at_k[mixed], at_2k[mixed] = _marked(mixed), _cell(-10.0, -10.0)
    drift = gr.cell_drift_violations(gr.POSITIVE_EV_REGION, at_k, at_2k)
    print("  cell_drift_violations() standalone on the mixed grid -> %r"
          % (drift,))
    print("  PRE_REPAIR_COUNTEREXAMPLE_REPRODUCED = %s"
          % ("YES" if false_convergence else "NO"))
    print()
    return false_convergence


# ---------------------------------------------------------------- finding B
def _mc_row(token: str, seq: int, fields=None, actor: str = "Aaron") -> str:
    fields = dict(fields or {})
    if token == "MC_RUN_AUTHORIZED":
        fields.setdefault("smoke_ref", "SMOKE-001")
        fields.setdefault("authorization_sentence",
                          mcc.authorization_sentence(RID, C40,
                                                     fields["smoke_ref"]))
    parts = "; ".join("%s: %s" % kv for kv in fields.items())
    note = "[%s]%s" % (RID, (" " + parts) if parts else "")
    return ("| %d | %s | **%s** | %s | %s | %s |"
            % (seq, UTC, token, C40, actor, note))


def finding_b() -> bool:
    """O9: can the generic append boundary create MC permission state?

    A throwaway ledger already carrying the lawful prerequisites, so the
    permission row under test is the only thing in question.
    """
    tmp = Path(tempfile.mkdtemp(prefix="n14_round1_repro_"))
    print("FINDING B -- O9 generic serialized_append permission boundary")
    print("  scratch ledger: %s" % tmp)
    every = True
    for token in ("MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED"):
        target = tmp / ("SCRATCH_%s.md" % token)
        base = HEADER + "\n".join([
            _mc_row("MC_PACKET_DRAFTED", 1),
            _mc_row("MC_PACKET_APPROVED", 2),
            _mc_row("MC_RUNNER_READYCHECKED", 3, {"smoke_ref": "SMOKE-001"}),
        ]) + "\n"
        target.write_bytes(base.encode("utf-8"))
        before = target.read_bytes()

        addition = ("\n" + _mc_row(token, 4) + "\n").encode("utf-8")
        accepted, why = True, ""
        try:
            rb.serialized_append(target, addition)
        except Exception as exc:                              # noqa: BLE001
            accepted, why = False, "%s: %s" % (type(exc).__name__, exc)
        after = target.read_bytes()
        appended = after != before and addition.strip() in after

        events, refusal = mr.parse_mc_events(after.decode("utf-8"))
        parsed = refusal is None and any(e.token == token for e in events)

        every = every and accepted and appended and parsed
        print("  %s" % token)
        print("     accepted by generic append : %s%s"
              % (accepted, "" if accepted else "  (%s)" % why))
        print("     bytes physically appended  : %s" % appended)
        print("     downstream parser sees it  : %s" % parsed)
    print("  AARON_ONLY_EVENTS = %r  (the contract's only actor rule)"
          % (mcc.AARON_ONLY_EVENTS,))
    print("  PRE_REPAIR_PERMISSION_APPEND_REPRODUCED = %s"
          % ("YES" if every else "NO"))
    print()
    return every


if __name__ == "__main__":
    a = finding_a()
    b = finding_b()
    print("=" * 70)
    print("FINDING A (O7/O12) reproduced : %s" % ("YES" if a else "NO"))
    print("FINDING B (O9)     reproduced : %s" % ("YES" if b else "NO"))
