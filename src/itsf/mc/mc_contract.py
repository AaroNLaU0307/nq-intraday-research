"""The MC run registry's vocabulary — G1..G8, as ratified and as modified.

PROVENANCE. G1-G8 of the N-D2/N-D3 ruling, 2026-08-24, delegated to Codex
GPT-5.6 Sol under Aaron's named batch delegation, over a Fable 5 proposal.
G2-G7 ratified unchanged; G1 and G8 ratified WITH MODIFICATIONS, and the
modification to G1 is load-bearing enough to state here rather than leave
in a decision record -- see AUTHORIZATION_SENTENCE below.

"FOLLOW THE SHAPE, DO NOT ASSUME IDENTITY." The ruling's words. This
vocabulary follows S0-T001's registry state machine and the ND1-R2
supplement grammar in FORM, and shares no namespace with either. Nothing
here imports `supplement_contract`, deliberately: the two lifecycles differ
(MC has branch sealing and a reveal; a supplement has neither), and an
import would make a later divergence silently impossible to see. A test
pins that the two token sets do not overlap.

WHY THIS IS NOT IN THE CONFIG DIGEST. `atoms.HARVESTED_CONSTANT_MODULES`
covers what decides a NUMBER the verdict rests on. This module decides
which run is AUTHORIZED, not what a run computes -- no constant here can
move a result. Adding it would tie every atom's identity to governance
wording, so that fixing a typo in an event name would invalidate a
production run.
"""
from __future__ import annotations

import dataclasses as _dc
import re
from types import MappingProxyType

__all__ = ["MCGrammarError", "EVENTS", "RUN_ID_RE", "COMMIT_RE",
           "INCIDENT_RE", "ROW_CELLS", "REQUIRED_FIELDS",
           "CONDITIONAL_FIELDS", "AARON_ONLY_EVENTS", "ACTOR_AARON",
           "LEGAL_TRANSITIONS", "BRANCHES", "AUTHORIZATION_SENTENCE",
           "BRANCH_POLICY_TOKEN", "MC_RULING", "FIRST_RUN_ID",
           "POSTSTART_FAILURE_REQUIRES_NEW_ID", "ID_REUSE_FORBIDDEN"]

MC_RULING = "G1_G8_RATIFIED_2026-08-24"
MC_RULING_DELEGATED = True


class MCGrammarError(ValueError):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


# --- identifiers ------------------------------------------------------------
#: `\Z`, not `$`. `$` also matches before a trailing newline, which is how a
#: value with a newline in it passes a pattern that looks strict -- the
#: defect a fresh review found in the supplement grammar (N06 round 1).
RUN_ID_RE = re.compile(r"^MC-R[0-9]{3}\Z")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}\Z")
INCIDENT_RE = re.compile(r"^INC-[0-9a-f]{12}\Z")
REASON_CODE_RE = re.compile(r"^[A-Z0-9_]+\Z")
SHA256_RE = re.compile(r"^[0-9a-f]{64}\Z")

FIRST_RUN_ID = "MC-R001"
BRANCHES = ("alpha", "beta")


# --- the closed event vocabulary (G1) --------------------------------------
@_dc.dataclass(frozen=True)
class EventSpec:
    name: str
    extra: tuple = ()          # fields required beyond REQUIRED_FIELDS
    note: str = ""


#: The six-cell registry row contract, shared with every other lifecycle
#: in `ops/TRIAL_REGISTRY.md`. The run id is NOT a cell -- it travels in the
#: note bracket, `[MC-R001] key: value; ...`, exactly as a supplement id
#: does. The sequence namespace is global across lifecycles.
ROW_CELLS = ("seq", "utc", "event", "commit", "actor", "note")
REQUIRED_FIELDS = ROW_CELLS

#: G1, from S0-T001's actual history: only Aaron authorizes a run. Every
#: other actor rule is UNRULED, and unruled is left unconstrained here
#: rather than invented -- a fabricated actor rule would refuse legal rows
#: and would look, in a year, exactly like a ratified one.
AARON_ONLY_EVENTS = ("MC_RUN_AUTHORIZED",)
ACTOR_AARON = "Aaron"

_SPECS = (
    EventSpec("MC_PACKET_DRAFTED"),
    EventSpec("MC_PACKET_APPROVED"),
    EventSpec("MC_RUNNER_READYCHECKED", ("smoke_ref",),
              "E3's smoke run is a READY prerequisite, so the reference "
              "is mandatory here rather than optional"),
    EventSpec("MC_READY_FOR_RUN_AUTHORIZATION"),
    EventSpec("MC_RUN_AUTHORIZED", ("smoke_ref", "authorization_sentence"),
              "G1: the row does not merely SAY authorized, it carries "
              "Aaron's sentence. The validator rebuilds the sentence from "
              "the run id, the commit cell and smoke_ref and requires an "
              "exact match, so the transported string is never trusted -- "
              "the N06 round-3 lesson, applied here"),
    EventSpec("MC_BRANCH_SEALED", ("branch", "payload_sha256",
                                   "byte_length"),
              "G7/G8: appended AFTER MC_RUN_COMPLETED and before any "
              "reveal. The hash exists only once the run produced it"),
    EventSpec("MC_RUN_STARTED", ("exposure_seq",),
              "G3: Stage-C entry consumes the pre-registered exposure "
              "slot, and the row carries which one"),
    EventSpec("MC_PRE_RUN_ATTEMPT_FAILURE", ("incident_id",),
              "G4: before STARTED. Exposure NOT consumed, run id NOT "
              "burned"),
    EventSpec("MC_RUN_AUTHORIZATION_SUPERSEDED",
              ("supersedes_event_sequence", "superseded_commit",
               "reason_code", "incident_id"),
              "G4: a code or config change invalidates the authorization; "
              "a new READY and a fresh sentence follow"),
    EventSpec("MC_RUN_FAILED_POSTSTART", ("incident_id",),
              "G4/G5: exposure already consumed and not rolled back; the "
              "re-run takes a NEW id"),
    EventSpec("MC_RUN_COMPLETED"),
    EventSpec("MC_PRIMARY_REVEALED"),
    EventSpec("MC_BRANCH_REVEALED", ("branch",),
              "M15: only the branch the primary verdict actually "
              "triggered"),
    EventSpec("MC_BRANCH_RETIRED_SEALED", ("branch",),
              "G7: the untriggered branch, sealed permanently. Without "
              "this row it dangles on the chain forever"),
    EventSpec("MC_RUN_CLOSED"),
    EventSpec("MC_ERRATUM", ("supersedes_event_sequence",),
              "append-only correction, citing the row it corrects"),
)

EVENTS: tuple = tuple(s.name for s in _SPECS)
SPEC_BY_NAME: dict = MappingProxyType({s.name: s for s in _SPECS})
CONDITIONAL_FIELDS: dict = MappingProxyType(
    {s.name: s.extra for s in _SPECS})


# --- legal transitions (G1) -------------------------------------------------
#: The main chain, plus the two loops S0-T001 actually exercised. Both were
#: reached in production -- two pre-run failures on the real S0 run -- so
#: they are recorded history rather than defensive speculation.
_MAIN = (
    "MC_PACKET_DRAFTED", "MC_PACKET_APPROVED", "MC_RUNNER_READYCHECKED",
    "MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED",
    "MC_RUN_STARTED", "MC_RUN_COMPLETED",
)

#: NOT a lifecycle step. An erratum corrects a row that already exists, so
#: it can follow anything, and putting it in the walk would make every
#: correction an illegal transition. It is validated like any other row and
#: excluded from the ordering -- see `mc_registry._walk`.
OUT_OF_CHAIN = ("MC_ERRATUM",)


def _transitions() -> frozenset:
    edges = set(zip(_MAIN, _MAIN[1:]))
    # G4's pre-start loop: AUTHORIZED -> failure -> supersede -> READY again
    edges |= {
        ("MC_RUN_AUTHORIZED", "MC_PRE_RUN_ATTEMPT_FAILURE"),
        ("MC_PRE_RUN_ATTEMPT_FAILURE", "MC_RUN_AUTHORIZED"),
        ("MC_PRE_RUN_ATTEMPT_FAILURE", "MC_RUN_AUTHORIZATION_SUPERSEDED"),
        ("MC_RUN_AUTHORIZATION_SUPERSEDED",
         "MC_READY_FOR_RUN_AUTHORIZATION"),
    }
    # G4/G5's post-start terminal: the id is spent, the chain closes
    edges |= {
        ("MC_RUN_STARTED", "MC_RUN_FAILED_POSTSTART"),
        ("MC_RUN_FAILED_POSTSTART", "MC_RUN_CLOSED"),
    }
    # G7/G8. THE ORDER IS THE POINT, and it is why COMPLETED does not reach
    # a reveal directly: both branch payloads are sealed while everyone is
    # still blind, and only then is anything revealed. An edge from
    # COMPLETED straight to MC_PRIMARY_REVEALED would let a run reveal its
    # primary with nothing sealed, which is the one ordering G7 exists to
    # forbid. For the same reason MC_PRIMARY_REVEALED does not reach
    # MC_RUN_CLOSED: the untriggered branch must be retired explicitly, or
    # it dangles on the chain forever.
    edges |= {
        ("MC_RUN_COMPLETED", "MC_BRANCH_SEALED"),
        ("MC_BRANCH_SEALED", "MC_BRANCH_SEALED"),
        ("MC_BRANCH_SEALED", "MC_PRIMARY_REVEALED"),
        ("MC_PRIMARY_REVEALED", "MC_BRANCH_REVEALED"),
        ("MC_PRIMARY_REVEALED", "MC_BRANCH_RETIRED_SEALED"),
        ("MC_BRANCH_REVEALED", "MC_BRANCH_RETIRED_SEALED"),
        ("MC_BRANCH_RETIRED_SEALED", "MC_BRANCH_RETIRED_SEALED"),
        ("MC_BRANCH_RETIRED_SEALED", "MC_RUN_CLOSED"),
    }
    return frozenset(edges)


LEGAL_TRANSITIONS = _transitions()


# --- the authorization sentence (G1, AS MODIFIED) ---------------------------
#: THE MODIFICATION, and why it matters. The proposal's sentence bound the
#: alpha and beta payload hashes. Those hashes do not exist when the
#: sentence is written -- the payloads are produced BY the authorized run --
#: so G1 as proposed could not be satisfied at the same time as M14 and G7.
#: Sol found the contradiction; the sentence now binds the branch POLICY,
#: and the hashes are bound after the fact by MC_BRANCH_SEALED.
BRANCH_POLICY_TOKEN = "PRECOMPUTE_BOTH_BLIND_SEAL_AFTER_COMPLETION"

AUTHORIZATION_SENTENCE = (
    "启动第一次真实MC，授权run_id: {run_id}，使用commit: {commit}，"
    "分支政策: {branch_policy}，smoke: {smoke_ref}=PASS")

#: G5. A post-start failure burns the id: it was bound to one decisive
#: execution by the authorization sentence and the exposure slot, so a
#: re-run under it would break the map from sealed bytes to execution.
POSTSTART_FAILURE_REQUIRES_NEW_ID = True
#: G6/R1. Once STARTED, a run id is spent for good.
ID_REUSE_FORBIDDEN = True


def authorization_sentence(run_id: str, commit: str,
                           smoke_ref: str) -> str:
    """The exact sentence Aaron must send, verbatim, for a real MC run.

    Refuses to render a malformed one. A sentence with a placeholder or a
    short commit is not a weaker authorization; it is not one at all, and
    producing it would put a string in front of a human that LOOKS like the
    thing that authorizes a run."""
    if not RUN_ID_RE.match(run_id or ""):
        raise MCGrammarError("mc_run_id_malformed",
                             f"{run_id!r} is not MC-R###")
    if not COMMIT_RE.match(commit or ""):
        raise MCGrammarError(
            "mc_commit_malformed",
            f"{commit!r} is not 40 lowercase hex; the sentence binds a "
            "full commit and an abbreviation authorizes nothing")
    if not smoke_ref or not re.match(r"^SMOKE-[0-9]{3}\Z", smoke_ref):
        raise MCGrammarError("mc_smoke_ref_malformed", f"{smoke_ref!r}")
    return AUTHORIZATION_SENTENCE.format(
        run_id=run_id, commit=commit,
        branch_policy=BRANCH_POLICY_TOKEN, smoke_ref=smoke_ref)
