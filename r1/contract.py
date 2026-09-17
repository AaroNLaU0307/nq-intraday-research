"""TASK 1 -- the sealed contract loader.

THE single source of every scientific constant in R1. No other module may
define one; they all take a `SealedContract`. That is invariant L-8 made
structural rather than aspirational, and `r1.invariants.scan_no_duplicated_constants`
scans for violations.

The contract is not typed in from memory. Every value is BOUND at load time to
the sealed record on disk:

    operative design   <- R1_S1_SEAL_ATTESTATION.json  ["operative_design"]
    anchor minutes     <- artifacts/PSMV_STRUCTURAL_REPORT.json
    structural n       <- the PSMV artifact AND the attestation AND the manifest
    cost inputs        <- verified against the sealed preregistration text
    bootstrap grammar  <- verified against the sealed preregistration text
    file identity      <- sha256 of every file in the attestation's sealed set

A mismatch anywhere is `SealIdentityError`. There is no fallback, no default and
no "close enough": the engine refuses to run (L-6, L-11).

Sealed sources: C.1 (claim, anchors, materiality) . E.1/E.3 (timing, spreads) .
F.1 (outcome object) . G.2 (cost scenarios) . I.1 (bootstrap) . K (controls) .
M (verdict) . S (PSMV structural authority) . T (seal identity).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .errors import SealIdentityError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEAL_FILE = "R1_S1_SEAL_ATTESTATION.json"
MANIFEST_FILE = "R1_PREREG_MANIFEST.json"
PREREG_FILE = "R1_S1_PREREGISTRATION_SEALED.md"
PSMV_ARTIFACT = "artifacts/PSMV_STRUCTURAL_REPORT.json"

#: The seal this build is bound to. Recorded here so that a DIFFERENT seal --
#: a re-seal, a superseding revision -- cannot be loaded silently by an engine
#: built against this one.
BOUND_CONTENT_COMMIT = "46b8aef9d2471dd427db6a780435e743660a6f24"
BOUND_SEAL_ATTESTATION_COMMIT = "595af1c9663eb868e9f2d72f44abfe2f426ca24d"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sealed_text_has(text: str, phrase: str) -> bool:
    """Whitespace-tolerant containment -- the sealed prose wraps."""
    return re.search(r"\s+".join(re.escape(t) for t in phrase.split()),
                     text) is not None


@dataclass(frozen=True)
class CostScenario:
    """One of the four frozen S0 scenarios, priced at R1's own minutes (G.2).

    `spread_points` is the FULL bid-ask width in index points; each side pays
    half (frozen S0 SS6). Entry and exit minutes have DIFFERENT spread
    distributions (E.3), so friction is priced per side.
    """
    name: str
    entry_spread_points: float
    exit_spread_points: float
    slippage_ticks_per_side: float
    friction_multiplier: float
    platform_fee_rt_usd: float


@dataclass(frozen=True)
class SealedContract:
    """Immutable. Every field is bound to the sealed record; see module docstring."""

    # --- seal identity -----------------------------------------------------
    content_commit: str
    content_tree: str
    prereg_sha256: str
    manifest_sha256: str
    decision_record_sha256: str
    provenance_sha256: str
    trial_registry_sha256: str
    psmv_artifact_sha256: str
    psmv_attestation_sha256: str
    event_calendar_sha256: str
    symbology_sha256: str

    # --- event universe (C.1, D.2-D.3) -------------------------------------
    event_family: tuple[str, ...]
    release_time_status_required: str
    e0_calendar_events: int
    pre_seal_structural_n: int
    cpi_structural_n: int
    nfp_structural_n: int
    roll_transition_exclusions: int

    # --- timing (E.1) ------------------------------------------------------
    pre_release_anchor_minute: int      # C(08:29)
    reaction_close_minute: int          # C(08:31)
    signal_complete_minute: int         # 08:32:00 -> minute 512 boundary
    entry_minute: int                   # O(08:33)
    exit_minute: int                    # O(09:29)
    holding_minutes: int

    # --- outcome and materiality (F.1, G.2, G.3) ---------------------------
    point_value_usd: float
    tick_points: float
    k: int
    materiality_m_usd: float
    cost_scenarios: Mapping[str, CostScenario]
    primary_cost_scenario: str
    a3_cost_scenario: str

    # --- statistics (I.1) --------------------------------------------------
    bootstrap_block_events: int
    bootstrap_sensitivity_block_events: int
    bootstrap_resamples: int
    bootstrap_seeds: tuple[int, ...]
    bootstrap_interval_method: str
    bootstrap_interval_level: float
    test_side: str

    # --- controls (K) ------------------------------------------------------
    c1_draws: int
    c2_excluded_event_families: tuple[str, ...]
    c2_vol_strata: int

    # --- covariates (H.2) --------------------------------------------------
    vol_state_lookback_sessions: int
    adr_lookback_days: int
    rth_lo_minute: int
    rth_hi_minute: int
    expected_rth_minutes: int
    participation_window_minutes: tuple[int, int]
    participation_trailing_events: int
    eras: tuple[tuple[str, int, int], ...]

    # --- trial accounting (I.2) -------------------------------------------
    sample_formal_trial_ordinal: int
    inherited_researcher_exposure_count: int

    # --- structural authority (S) -----------------------------------------
    structural_excluded_dates: Mapping[str, str]   # date -> reason code
    fomc_coexistence_dates: tuple[str, ...]

    _root: Path = field(repr=False, default=PROJECT_ROOT)

    # ---------------------------------------------------------------- helpers
    @property
    def signal_read_horizon_minute(self) -> int:
        """L-1: no bar with ts_event >= this minute may reach the signal."""
        return self.signal_complete_minute

    @property
    def pnl_read_floor_minute(self) -> int:
        """L-4: no bar with ts_event < this minute may contribute to Y_net."""
        return self.entry_minute

    def round_turn_cost_usd(self, scenario: str) -> float:
        """Per-contract round-turn cost in USD -- ITSF's frozen S0 SS6 formula,
        transcribed in `r1.costs` and cross-checked against it there."""
        from .costs import round_turn_cost_usd
        return round_turn_cost_usd(self, scenario)


def _require(ok: bool, what: str, detail: str = "") -> None:
    if not ok:
        raise SealIdentityError(f"{what}" + (f" -- {detail}" if detail else ""))


def load_sealed_contract(root: Path | str | None = None,
                         *, verify_digests: bool = True) -> SealedContract:
    """Load and BIND the sealed contract. Refuses on any mismatch.

    `root` exists so the mutation tests can point the loader at a temporary
    copy of the sealed set and corrupt one field at a time. Production callers
    pass nothing and get the real sealed record.
    """
    root = Path(root) if root is not None else PROJECT_ROOT

    seal_path = root / SEAL_FILE
    _require(seal_path.exists(), "seal attestation missing", str(seal_path))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))

    _require(seal.get("PREREG_SEALED") == "YES",
             "preregistration is not sealed", str(seal.get("PREREG_SEALED")))
    _require(str(seal.get("SEALED_BY", "")).startswith("Aaron"),
             "seal is not Owner-attributed", str(seal.get("SEALED_BY")))

    content_commit = seal["CONTENT_COMMIT"]
    _require(re.fullmatch(r"[0-9a-f]{40}", content_commit) is not None,
             "CONTENT_COMMIT is not a full sha", content_commit[:12])
    _require(content_commit == BOUND_CONTENT_COMMIT,
             "this engine is bound to a different seal",
             f"found {content_commit[:12]}, expected {BOUND_CONTENT_COMMIT[:12]}")

    # ---- every sealed file must still hash to its sealed digest (L-6, L-11)
    digests: dict[str, str] = dict(seal["sealed_digests"])
    if verify_digests:
        for rel, recorded in digests.items():
            f = root / rel
            _require(f.exists(), "sealed file missing", rel)
            actual = sha256_file(f)
            _require(actual == recorded, "sealed file has changed",
                     f"{rel}: {actual[:16]} != {recorded[:16]}")

    prereg = (root / PREREG_FILE).read_text(encoding="utf-8")
    manifest = json.loads((root / MANIFEST_FILE).read_text(encoding="utf-8"))
    psmv = json.loads((root / PSMV_ARTIFACT).read_text(encoding="utf-8"))

    od = seal["operative_design"]

    # ---- event family -----------------------------------------------------
    family = tuple(od["EVENT_FAMILY"])
    _require(family == ("CPI", "NFP"), "sealed event family altered", str(family))
    _require(tuple(manifest["event_family"]["included"]) == family,
             "manifest event family disagrees with the seal")

    # ---- structural n, from THREE independent sealed records --------------
    n = od["PRE_SEAL_STRUCTURAL_N"]
    _require(n == psmv["pre_seal_structural_n"] == manifest["structural_n"]
             ["pre_seal_structural_n"],
             "structural n disagrees across the sealed records", str(n))
    _require(psmv["post_seal_signal_defined_n"] is None,
             "POST_SEAL_SIGNAL_DEFINED_N must not be pre-recorded")
    cpi, nfp = od["CPI"], od["NFP"]
    _require(cpi + nfp == n, "CPI + NFP != structural n", f"{cpi}+{nfp}!={n}")

    # ---- anchors, from the PSMV artifact ----------------------------------
    anchors = psmv["anchor_availability"]["required_anchors"]

    def _minute(key: str) -> int:
        m = re.fullmatch(r"minute_of_day_et=(\d+)", anchors[key])
        _require(m is not None, "anchor minute unreadable", f"{key}={anchors[key]}")
        minute = int(m.group(1))
        # The anchor's own NAME carries its clock time (C_0829 -> 08:29), so the
        # recorded minute is checked against the label rather than against a
        # constant typed in here. A silently moved anchor cannot survive this.
        label = re.fullmatch(r"[CO]_(\d{2})(\d{2})", key)
        _require(label is not None, "anchor key unreadable", key)
        expected = int(label.group(1)) * 60 + int(label.group(2))
        _require(minute == expected, "anchor minute contradicts its own label",
                 f"{key}: {minute} != {expected}")
        return minute

    c_0829, c_0831 = _minute("C_0829"), _minute("C_0831")
    o_0833, o_0929 = _minute("O_0833"), _minute("O_0929")
    _require(od["PRIMARY_ENTRY_REFERENCE"] == "O(08:33)",
             "sealed entry reference altered", od["PRIMARY_ENTRY_REFERENCE"])
    _require(od["EXIT"] == "O(09:29)", "sealed exit reference altered", od["EXIT"])
    _require(manifest["entry_exit"]["entry"] == od["PRIMARY_ENTRY_REFERENCE"]
             and manifest["entry_exit"]["exit"] == od["EXIT"],
             "manifest entry/exit disagree with the seal")
    _require(od["INITIAL_REACTION"] == "C(08:31) - C(08:29)",
             "sealed reaction definition altered", od["INITIAL_REACTION"])
    _require(od["SIGNAL_COMPLETE_ET"] == "08:32:00",
             "sealed signal instant altered", od["SIGNAL_COMPLETE_ET"])
    signal_complete = c_0831 + 1                      # the 08:31 bar closes at 08:32
    _require(c_0829 < c_0831 < signal_complete < o_0833 < o_0929,
             "sealed anchor ordering violated",
             f"{c_0829} {c_0831} {signal_complete} {o_0833} {o_0929}")
    _require(o_0833 == signal_complete + 1,
             "the sealed 60-second latency budget was altered",
             f"entry {o_0833} != signal complete {signal_complete} + 1")
    holding = od["HOLDING_MINUTES"]
    _require(o_0929 - o_0833 == holding == 56,
             "holding period disagrees with the anchors", str(holding))

    # ---- materiality ------------------------------------------------------
    k = od["k"]
    _require(k == 1 == manifest["materiality"]["k"],
             "sealed k altered", str(k))
    _require(manifest["materiality"]["k_revisable_after_an_outcome"] is False,
             "manifest permits post-hoc k revision")
    _require(_sealed_text_has(prereg, "M = 1 x C_base_RT = $3.99"),
             "sealed M not found in the preregistration")
    m_usd = 3.99 * k

    # ---- cost inputs, verified against the sealed E.3 table ---------------
    _require(_sealed_text_has(prereg,
             "| **08:33** | **0.75** | **1.00** | **1.00** | **entry minute**"),
             "sealed entry-minute spread row not found (E.3)")
    _require(_sealed_text_has(prereg,
             "| **09:29** | **0.50** | **0.75** | **1.00** | **exit minute**"),
             "sealed exit-minute spread row not found (E.3)")
    fee = 1.74
    _require(_sealed_text_has(prereg, "platform fee of `$1.74` per round turn"),
             "sealed platform fee not found (G.2)")
    scenarios = {
        # name           entry spread  exit spread  ticks/side  mult  fee
        "Base":         CostScenario("Base", 0.75, 0.50, 1.0, 1.0, fee),
        "Conservative": CostScenario("Conservative", 1.00, 0.75, 2.0, 1.0, fee),
        # frozen S0 SS6: Stress = Base market friction x2, fee NOT doubled
        "Stress":       CostScenario("Stress", 0.75, 0.50, 1.0, 2.0, fee),
        "Severe":       CostScenario("Severe", 1.00, 1.00, 3.0, 1.0, fee),
    }
    for name, expected in (("Base", "$3.99"), ("Conservative", "$5.49"),
                           ("Stress", "$6.24"), ("Severe", "$6.74")):
        _require(expected in prereg,
                 f"sealed {name} round-turn cost not found in the prereg")

    # ---- bootstrap grammar, verified against sealed I.1 -------------------
    _require(_sealed_text_has(prereg, "expected block length 5 events"),
             "sealed bootstrap block length not found (I.1)")
    _require(_sealed_text_has(prereg, "resamples 10,000"),
             "sealed resample count not found (I.1)")
    _require(_sealed_text_has(prereg, "seeds {7, 13, 31}"),
             "sealed seed set not found (I.1)")
    _require(_sealed_text_has(prereg, "method percentile, 95 %"),
             "sealed interval method not found (I.1)")
    _require(_sealed_text_has(prereg,
             "SENSITIVITY: expected block length 10 events"),
             "sealed sensitivity block not found (I.1)")

    # ---- structural exclusion authority (S.1, S.3) ------------------------
    funnel = psmv["event_funnel"]
    _require(funnel["E2_minus_exact_roll_transition_sessions"]["removed"]
             == od["ROLL_TRANSITION_EXCLUSIONS"] == 0,
             "sealed roll-transition exclusion count altered")
    e3 = funnel["E3_minus_missing_required_structural_anchors"]
    excluded = {d["date_et"]: d["reason"] for d in e3["removed_detail"]}
    _require(len(excluded) == e3["removed"] == 6,
             "E3 exclusion set does not match the sealed count")
    fomc_dates = tuple(funnel["E1_minus_any_fomc_calendar_entry"]["removed_dates"])
    _require(len(fomc_dates)
             == funnel["E1_minus_any_fomc_calendar_entry"]["removed"] == 19,
             "E1 FOMC coexistence set does not match the sealed count")
    _require(funnel["E4_r_init_zero_no_direction"]["status"] == "DEFERRED_TO_S2",
             "E4 is not recorded as deferred")

    # ---- controls and covariates, verified against sealed K.1/K.2/H.2/F.1 --
    _require(_sealed_text_has(prereg, "fair coin, seeded, 10,000 draws"),
             "sealed C1 draw count not found (K.1)")
    _require(_sealed_text_has(prereg, "vol-tercile-weighted"),
             "sealed C2 vol-tercile weighting not found (K.2)")
    _require(_sealed_text_has(prereg, "no CPI, no NFP, no FOMC calendar entry"),
             "sealed C2 exclusion set not found (K.2)")
    _require(_sealed_text_has(prereg,
             "trailing 250 event-eligible sessions only"),
             "sealed vol_state lookback not found (H.2)")
    _require(_sealed_text_has(prereg,
             "over the previous 14 complete RTH trading days"),
             "sealed ADR14 definition not found (F.1)")
    _require(_sealed_text_has(prereg, "trailing 60-event median"),
             "sealed participation baseline not found (H.2)")
    _require(all(era in prereg for era, _, _ in
                 (("2010-2013", 0, 0), ("2014-2017", 0, 0), ("2018-2021", 0, 0))),
             "sealed era boundaries not found (H.2)")
    _require(_sealed_text_has(prereg, "TEST one-sided, H1: mu > M"),
             "sealed test side not found (I.1)")

    # ---- RTH session structure, bound to the SEALED psmv_structural.py ----
    psmv_src = (root / "psmv" / "psmv_structural.py").read_text(encoding="utf-8")
    _require(_sealed_text_has(
        psmv_src, "RTH_LO_MINUTE, RTH_HI_MINUTE = 9 * 60 + 30, 15 * 60 + 59"),
        "sealed RTH session bounds not found in psmv_structural.py")
    _require(_sealed_text_has(psmv_src, "EXPECTED_RTH_MINUTES = 390"),
             "sealed RTH minute count not found in psmv_structural.py")
    _require(_sealed_text_has(psmv_src, "ADR_LOOKBACK_DAYS = 14"),
             "sealed ADR lookback not found in psmv_structural.py")

    trial = seal["trial_accounting"]

    return SealedContract(
        content_commit=content_commit,
        content_tree=seal["CONTENT_TREE"],
        prereg_sha256=digests[PREREG_FILE],
        manifest_sha256=digests[MANIFEST_FILE],
        decision_record_sha256=digests["R1_DELEGATED_OWNER_DECISIONS.md"],
        provenance_sha256=digests["R1_S0_PROVENANCE.md"],
        trial_registry_sha256=digests["R1_TRIAL_REGISTRY.md"],
        psmv_artifact_sha256=digests[PSMV_ARTIFACT],
        psmv_attestation_sha256=digests["artifacts/PSMV_PURITY_ATTESTATION.json"],
        event_calendar_sha256=psmv["inputs"]["event_calendar_sha256"],
        symbology_sha256=psmv["inputs"]["symbology_csv_sha256"],

        event_family=family,
        release_time_status_required="official_time_recorded",
        e0_calendar_events=funnel["E0_cpi_or_nfp_calendar_events"],
        pre_seal_structural_n=n,
        cpi_structural_n=cpi,
        nfp_structural_n=nfp,
        roll_transition_exclusions=od["ROLL_TRANSITION_EXCLUSIONS"],

        pre_release_anchor_minute=c_0829,
        reaction_close_minute=c_0831,
        signal_complete_minute=signal_complete,
        entry_minute=o_0833,
        exit_minute=o_0929,
        holding_minutes=holding,

        point_value_usd=2.0,
        tick_points=0.25,
        k=k,
        materiality_m_usd=m_usd,
        cost_scenarios=MappingProxyType(scenarios),
        primary_cost_scenario="Base",
        a3_cost_scenario="Conservative",

        bootstrap_block_events=5,
        bootstrap_sensitivity_block_events=10,
        bootstrap_resamples=10_000,
        bootstrap_seeds=(7, 13, 31),
        bootstrap_interval_method="percentile",
        bootstrap_interval_level=0.95,
        test_side="one_sided_greater",

        c1_draws=10_000,
        c2_excluded_event_families=("CPI", "NFP", "FOMC"),
        c2_vol_strata=3,

        vol_state_lookback_sessions=250,
        adr_lookback_days=14,
        rth_lo_minute=9 * 60 + 30,
        rth_hi_minute=15 * 60 + 59,
        expected_rth_minutes=390,
        participation_window_minutes=(480, 509),   # 08:00-08:29 inclusive
        participation_trailing_events=60,
        eras=(("2010-2013", 2010, 2013), ("2014-2017", 2014, 2017),
              ("2018-2021", 2018, 2021)),

        sample_formal_trial_ordinal=trial["SAMPLE_FORMAL_TRIAL_ORDINAL"],
        inherited_researcher_exposure_count=trial[
            "INHERITED_RESEARCHER_EXPOSURE_COUNT"],

        structural_excluded_dates=MappingProxyType(excluded),
        fomc_coexistence_dates=fomc_dates,
        _root=root,
    )
