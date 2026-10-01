# -*- coding: utf-8 -*-
"""O9/O10 review probe, shipped as `probes/test_o9_production_entry_refusals.py`.

WHY THIS EXISTS. Five production entry points read the governed registry
through `registry_boundary.read_snapshot()` / `resolve_registry()`, both of
which default to `REGISTRY_REPO_ROOT / REGISTRY_PATH` -- an absolute path
that `src/itsf/mc/registry_boundary.py:75` freezes and that migration Route A
step S6 declares "FROZEN AND NOT OVERRIDABLE FROM THE ENVIRONMENT". Inside a
sealed bundle that path does not exist and the boundary denies reaching for
it, so the thirteen repository tests that exercise those entries cannot run.

WHAT THIS DOES INSTEAD, and why it is stronger rather than weaker. Both
boundary functions take an OPTIONAL PATH. The probe writes a SYNTHETIC
registry inside the bundle and points the boundary at it, so the boundary's
own read, digest and mediation code all still execute -- only the bytes are
synthetic. Then it calls each production entry and asserts it refuses.

That is a better test of the property than the repository version. Those
tests pass today partly because the real ledger happens to carry no MC
authorization; if it ever did, they would stop refusing for a reason that has
nothing to do with the gate. These refuse against a registry this probe
built, so the refusal is attributable to the gate and to nothing else.

WHAT IT DOES NOT ESTABLISH. Anything about the real ledger's contents. That
is an actual-artifact claim and belongs to the run-identity stage, which the
DAG places at N15 under REGISTRY_CHAIN_REVIEW_ON_SAME_REVIEWED_HEAD.
"""
TEMPLATE = '''# -*- coding: utf-8 -*-
"""O9/O10 -- every production entry refuses before it can act.

Generated into the bundle by scripts/o9_production_entry_probe_template.py.
It replaces execution of the repository tests that reach the same entries
through the real governed registry, which a sealed bundle cannot open.

Every registry byte below is synthetic and written inside the bundle.
"""
import pytest

from itsf.mc import registry_boundary as rb

HEADER = ("| # | utc | event | commit | actor | note |",
          "|---|---|---|---|---|---|")


@pytest.fixture
def synthetic_registry(tmp_path, monkeypatch):
    """A real file, inside the bundle, holding a registry that authorizes
    nothing. The boundary reads it with its OWN code -- read, digest,
    mediate -- because only the path is redirected, not the logic."""
    path = tmp_path / "SYNTHETIC_REGISTRY.md"
    path.write_text(
        "\\n".join(["# SYNTHETIC registry -- built here, NOT the governed ledger", "",
                    *HEADER, ""]),
        encoding="utf-8")
    real_read, real_resolve = rb.read_snapshot, rb.resolve_registry
    monkeypatch.setattr(rb, "read_snapshot",
                        lambda p=None: real_read(p if p is not None else path))
    monkeypatch.setattr(
        rb, "resolve_registry",
        lambda p=None: real_resolve(p if p is not None else path))
    return path


def _refuses(fn, *args):
    """Call it and return the exception. A production entry that RETURNS is
    the finding; so is one stopped by the bundle boundary before it ran,
    because then this probe measured the boundary and not the gate."""
    with pytest.raises(BaseException) as exc:
        fn(*args)
    name = type(exc.value).__name__
    assert name != "BundleEscapeDenied", (
        "the entry was stopped by the sealed boundary before reaching its "
        "gate, so this assertion is about the bundle and not about the code")
    assert name != "FileNotFoundError", (
        "the entry never reached its gate: it failed looking for a file")
    assert name != "TypeError", (
        "the call never entered the function -- a signature mismatch is "
        "this probe being wrong, not the implementation refusing")
    return exc.value


def _full_mc(mc_runner):
    """`execute_full_mc` is keyword-only past `prepared`. Calling it with one
    positional argument raises TypeError BEFORE the body, which would make
    this probe green while measuring nothing -- that happened once."""
    return lambda: mc_runner.execute_full_mc(
        None, run_id="SYNTHETIC-RUN", output_root="/synthetic/root",
        supplement={}, sealed_artifact_sha256="ab" * 32)


def test_o9_a_the_public_real_mc_entry_refuses(synthetic_registry):
    from itsf.mc import consumer
    exc = _refuses(consumer.run_real_mc)
    assert not isinstance(exc, AssertionError), (
        "run_real_mc reached its own 'unreachable' line, which means "
        "authorize_real_mc returned instead of raising")


def test_o9_b_the_real_input_preparation_refuses(synthetic_registry):
    from itsf.mc import real_input
    exc = _refuses(real_input.prepare_real_mc_input)
    assert not isinstance(exc, AssertionError)


def test_o9_c_the_full_mc_executor_refuses_before_it_runs(synthetic_registry):
    from itsf.mc import mc_runner
    exc = _refuses(_full_mc(mc_runner))
    assert not isinstance(exc, AssertionError)


def test_o9_d_the_day_strata_supplement_entry_refuses(synthetic_registry):
    from itsf.mc import day_strata_supplement
    exc = _refuses(day_strata_supplement.run_supplement_production)
    assert not isinstance(exc, AssertionError)


def test_o9_e_the_supplement_entry_is_launch_guarded_before_anything_else(
        synthetic_registry):
    """Nothing is patched out here. The FIRST refusal a caller meets is the
    trusted-launch guard, before the registry is read at all -- which is
    the ordering the entry claims for itself, measured rather than read."""
    from itsf.mc import supplement_runner
    exc = _refuses(supplement_runner.run_supplement_production, "MC-DS-S001")
    assert type(exc).__name__ == "RunBlockedError", type(exc).__name__


class _FakeChain:
    """The runner's test seam takes a RESOLVER, never a second read. This is
    what the seam is fed; the boundary still performs the one real read, of
    the synthetic file."""

    def __init__(self, problem="", live=()):
        self.problem = problem
        self.live_authorizations = tuple(live)
        self.retired = False


def _unguarded(monkeypatch):
    """Stand the launch guard down, exactly as the repository test does, so
    the refusal UNDER it can be reached. Everything else stays real."""
    monkeypatch.setattr("itsf.guards.assert_real_run_allowed",
                        lambda *a, **k: None)


def test_o9_f_a_defective_chain_is_refused_whole(synthetic_registry,
                                                 monkeypatch):
    from itsf.mc import supplement_runner as sr
    _unguarded(monkeypatch)
    with pytest.raises(sr.SupplementRunNotAuthorized) as ei:
        sr.run_supplement_production(
            resolver=lambda t, s: _FakeChain(problem="forward reference"))
    assert "REFUSE_WHOLE_RESOLUTION" in str(ei.value)


def test_o9_g_anything_but_exactly_one_live_authorization_is_refused(
        synthetic_registry, monkeypatch):
    """Zero and two are both refusals, and for the same reason: exactly one
    live P2 is the authorization, so a count is not a detail."""
    from itsf.mc import supplement_runner as sr
    _unguarded(monkeypatch)
    for live in ((), ("a", "b")):
        with pytest.raises(sr.SupplementRunNotAuthorized) as ei:
            sr.run_supplement_production(
                resolver=lambda t, s, _l=live: _FakeChain(live=_l))
        assert "exactly one is required" in str(ei.value)


def test_o9_h_the_seam_receives_the_boundarys_own_snapshot(
        synthetic_registry, monkeypatch):
    """The seam swaps the RESOLVER, never the read. If an injected resolver
    were ever handed text from somewhere else, the single-read property
    would be gone and this is where that shows."""
    from itsf.mc import supplement_runner as sr
    _unguarded(monkeypatch)
    seen = []

    def spy(text, sid):
        seen.append(text)
        return _FakeChain(problem="stop here")

    with pytest.raises(sr.SupplementRunNotAuthorized):
        sr.run_supplement_production(resolver=spy)
    assert len(seen) == 1, "the entry read more than once"
    assert "SYNTHETIC registry" in seen[0]


def test_o9_k_each_real_mc_entry_still_refuses_with_the_launch_guard_down(
        synthetic_registry, monkeypatch):
    """The three tests above measure the FIRST refusal, which is the launch
    guard. That is the right first question, but it leaves the gate beneath
    it unexercised -- and the gate is the thing O9 is about. So: guard
    down, registry synthetic, and every entry must still refuse."""
    from itsf.mc import consumer, mc_runner, real_input
    _unguarded(monkeypatch)
    for label, call in (("consumer.run_real_mc", consumer.run_real_mc),
                        ("real_input.prepare_real_mc_input",
                         real_input.prepare_real_mc_input),
                        ("mc_runner.execute_full_mc", _full_mc(mc_runner))):
        with pytest.raises(BaseException) as ei:
            call()
        name = type(ei.value).__name__
        assert name not in ("BundleEscapeDenied", "FileNotFoundError",
                            "RunBlockedError", "TypeError"), (label, name)
        assert not isinstance(ei.value, AssertionError), (
            "%s reached its own 'unreachable' line: the authorization gate "
            "returned instead of raising" % label)


def test_o9_l_a_prestart_reauthorization_supersedes_and_authorizes_nothing():
    """A P2S written before the run starts retires the P2 it names. The
    chain must still RESOLVE -- superseding is legal -- and must be left
    with ZERO live authorizations, because a supersede row is not itself
    an authorization. Both halves matter: a resolver that refused the
    whole chain would look safe while wedging a legal correction, and one
    that carried the authorization forward would let a withdrawn commit
    keep its permission."""
    import os
    from itsf.mc import supplement_registry as sreg
    from itsf.mc import supplement_contract as scon

    sid = "MC-DS-S001"
    c1 = "0123456789abcdef0123456789abcdef01234567"
    c2 = "fedcba9876543210fedcba9876543210fedcba98"
    utc = "2026-08-20T00:00:00+00:00"
    root = "C:" + os.sep + "synthetic" + os.sep + "never-created"

    def r(short, seq, fields, actor, head=False):
        body = "; ".join("%s: %s" % kv for kv in fields.items())
        lead = (sreg.execution_sentence_header(sid) + " ") if head else ""
        return ("| %s | %s | **%s** | %s | %s | [%s] %s%s |"
                % (seq, utc, scon.EVENTS[short].token, c1, actor, sid,
                   lead, body))

    text = "\\n".join([
        "# SYNTHETIC registry -- built here, NOT the governed ledger", "", *HEADER,
        r("P1", "1", {"ir_basis": "IR-29b Option B",
                      "schema": "mc_day_strata_supplement.v1",
                      "non_authorization_disclaimer":
                          "this row is not an authorization"}, "main agent"),
        r("P2", "2", {"supplement_id": sid, "authorized_commit": c1,
                      "output_root": root}, "Aaron", head=True),
        r("P2S", "3", {"supersedes_event_sequence": "2",
                       "superseded_authorized_commit": c1,
                       "reason_code": sreg.PRESTART_COMMIT_CHANGE,
                       "incident_id": "INC-0123456789ab",
                       "successor_authorized_commit": c2,
                       "same_id_reauthorization": "YES"}, "Aaron"),
        ""])

    events, refusal = sreg.parse_supplement_events(text)
    assert refusal is None, refusal
    chain = sreg.resolve_supplement_chain(text, sid)
    assert chain.problem == "", chain.problem
    assert len(chain.live_authorizations) == 0, (
        "the superseded P2 is still live: a withdrawn authorization kept "
        "its permission")


def test_o9_i_the_boundary_itself_refuses_an_absent_registry(tmp_path):
    """Absence must REFUSE, never read as an empty registry -- the exact
    defect the migration ruling names. Nothing is monkeypatched here."""
    missing = tmp_path / "no-such-registry.md"
    assert not missing.exists()
    with pytest.raises(BaseException) as exc:
        rb.read_snapshot(missing)
    assert type(exc.value).__name__ != "BundleEscapeDenied"
    text = str(exc.value).lower()
    assert "empty" not in text or "refus" in text


def test_o9_j_the_synthetic_registry_really_was_the_one_read(
        synthetic_registry):
    """Guards the fixture: if the redirect ever stopped working, every
    assertion above would be about the real ledger and this probe would be
    quietly measuring the wrong file."""
    snap = rb.read_snapshot()
    assert snap.source == str(synthetic_registry), snap.source
    assert "SYNTHETIC registry" in snap.text
    assert rb.REGISTRY_PATH not in snap.source.replace("\\\\", "/")
'''


def render() -> str:
    return TEMPLATE
