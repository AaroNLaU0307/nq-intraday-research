"""The P3-only append seam: one token, one run, once, and nothing else.

WHY IT EXISTS. `SUPPLEMENT_RUN_STARTED` is the ratified pre-start/post-start
boundary and §D.3.2 gives it to the runner. Until now no production code
could append anything, so the first real N09 would have written supplement
bytes with no P3 -- and the failure vocabulary cannot describe that: F2
requires P3 as predecessor, and the only reachable event, F1, asserts
"nothing consumed" about a run that had consumed everything.

WHY IT CANNOT BE APPENDED BY HAND BEFOREHAND, measured 2026-09-05:
`_walk_chain` marks the P2 `consumed_by_p3`, so a P3 already in the ledger
takes the live authorization to ZERO and five A_PRECHECK gates refuse. One
P2 authorizes one start; P3 spends it. So P3 has to land DURING the run --
after A_PRECHECK has read the live P2, before the first side effect.

THE SEAM IS NARROW ON PURPOSE. Aaron authorized a P3-only append, not a
registry writer. There is no event-type parameter, because a parameter is
how "P3-only" becomes "whatever the caller passes".

NO TEST HERE TOUCHES THE REAL REGISTRY: every case runs against a temporary
copy, and the one test that reads the real ledger only asserts a refusal
that happens before any write.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_registry as T           # noqa: E402
from itsf import contracts                        # noqa: E402
from itsf.mc import registry_boundary as rb       # noqa: E402
from itsf.mc import supplement_contract as sc     # noqa: E402
from itsf.mc import supplement_registry as sreg   # noqa: E402

REAL = rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH
SID = T.SID                                       # 'MC-DS-S001'
UTC = "2026-09-05T17:00:00+00:00"
COMMIT = "c" * 40


def _ledger(*rows, commit=COMMIT):
    """A CONTROLLED synthetic ledger, built one ratified row at a time.

    NOT a copy of the real one. The first version of this file took its
    commit from `resolve_supplement_chain(REAL).live_authorizations[0]`,
    which worked for exactly as long as the real ledger happened to carry a
    live P2. On 2026-09-05 MC-DS-S001 was sealed, refused by an independent
    verifier and retired, the live count went to zero, and every test here
    died on an IndexError -- a unit test of the seam brought down by the
    state of production.

    What the seam needs is a chain with exactly one live P2 at a known
    commit. That is constructed here, so it is true by definition rather
    than by luck.
    """
    T.ROOT = str(contracts.RULED_RUNS_ROOT)
    reg = T.Reg()
    reg.commit[SID] = commit
    for short in rows:
        reg.add(short, sid=SID)
    return reg.text()


class _Copy:
    """A temp ledger the seam may write to. Nothing here touches the real
    one; `REAL` is read only by the single test that says so."""

    def __init__(self, text=None, commit=COMMIT):
        self._text = _ledger("P1", "P2") if text is None else text
        self.commit = commit

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "TRIAL_REGISTRY.md"
        self.path.write_bytes(self._text.encode("utf-8"))
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def text(self):
        return self.path.read_text(encoding="utf-8")

    def chain(self):
        return sreg.resolve_supplement_chain(self.text(), SID)

    def append(self, **over):
        kw = dict(supplement_id=SID, head_commit=self.commit,
                  utc_stamp=UTC, path=self.path)
        kw.update(over)
        return rb.append_run_started(**kw)


class TestTheHappyPath(unittest.TestCase):

    def test_before_p3_there_is_exactly_one_live_p2(self):
        """The premise A_PRECHECK runs on."""
        with _Copy() as reg:
            self.assertEqual(1, len(reg.chain().live_authorizations))
            self.assertFalse(reg.chain().started)

    def test_p3_consumes_the_p2_and_starts_the_run(self):
        with _Copy() as reg:
            reg.append()
            after = reg.chain()
            self.assertEqual("", after.problem)
            self.assertTrue(after.started)
            self.assertIn("P3", after.short_ids)
            self.assertEqual(0, len(after.live_authorizations))

    def test_the_row_is_the_ratified_shape(self):
        with _Copy() as reg:
            row = reg.append()
            cells = [c.strip() for c in row.split("|")]
            self.assertEqual(sc.UNNUMBERED_SEQ_TOKEN, cells[1])
            self.assertEqual(UTC, cells[2])
            self.assertEqual(rb.RUN_STARTED_TOKEN, cells[3])
            self.assertEqual(reg.commit[:7], cells[4])   # 7-hex, not 40
            self.assertEqual(sc.ACTOR_RUNNER, cells[5])
            self.assertIn("atomic_start_marker: YES", cells[6])

    def test_it_is_a_pure_append(self):
        with _Copy() as reg:
            before = reg.path.read_bytes()
            row = reg.append()
            self.assertEqual(before + (row + "\n").encode("utf-8"),
                             reg.path.read_bytes())


class TestThePostP3PathNeedsNoLiveP2(unittest.TestCase):
    """The reason spending the P2 here is safe."""

    def test_every_gate_that_reads_the_chain_is_in_A_PRECHECK(self):
        import inspect

        from itsf.mc import supplement_runner as sr
        for stage in ("B_DERIVE", "C_BUILD"):
            for name in sc.GATE_TABLE[stage]:
                with self.subTest(stage=stage, gate=name):
                    body = inspect.getsource(sr.GATES[name])
                    for reader in ("_live_p2", "ctx.chain",
                                   "live_authorizations"):
                        self.assertNotIn(reader, body)

    def test_the_chain_module_never_re_reads_the_registry(self):
        import inspect

        from itsf.mc import supplement_chain as ch
        body = inspect.getsource(ch)
        self.assertNotIn("read_snapshot", body)
        self.assertNotIn("resolve_for_supplement", body)


class TestItRefusesEverythingElse(unittest.TestCase):

    def _refusal(self, reg, **over):
        with self.assertRaises(rb.AppendRefused) as caught:
            reg.append(**over)
        return caught.exception.code

    def test_a_duplicate_p3_is_refused(self):
        with _Copy() as reg:
            reg.append()
            frozen = reg.path.read_bytes()
            self.assertEqual("p3_already_present", self._refusal(reg))
            self.assertEqual(frozen, reg.path.read_bytes())   # and no write

    def test_a_wrong_commit_is_refused(self):
        with _Copy() as reg:
            frozen = reg.path.read_bytes()
            self.assertEqual("p3_commit_is_not_the_authorized_one",
                             self._refusal(reg, head_commit="a" * 40))
            self.assertEqual(frozen, reg.path.read_bytes())

    def test_a_malformed_commit_is_refused(self):
        with _Copy() as reg:
            self.assertEqual("p3_head_commit_not_40hex",
                             self._refusal(reg, head_commit=reg.commit[:7]))

    def test_a_foreign_supplement_id_is_refused(self):
        """A legal-looking id with no chain of its own cannot be started."""
        with _Copy() as reg:
            frozen = reg.path.read_bytes()
            code = self._refusal(reg, supplement_id="MC-DS-S002")
            self.assertIn(code, ("p3_without_exactly_one_live_p2",
                                 "p3_chain_does_not_resolve"))
            self.assertEqual(frozen, reg.path.read_bytes())

    def test_a_malformed_supplement_id_is_refused(self):
        with _Copy() as reg:
            self.assertEqual("p3_supplement_id_pattern",
                             self._refusal(reg, supplement_id="NOT-AN-ID"))

    def test_the_directory_stamp_format_is_refused(self):
        """The registry cell and the directory name are different formats;
        passing one where the other belongs must not be accepted."""
        with _Copy() as reg:
            self.assertEqual("p3_utc_stamp_malformed",
                             self._refusal(reg, utc_stamp="20260905T170000Z"))

    def test_there_is_no_event_type_parameter(self):
        """The narrowing that cannot be argued with: the token is not an
        input. A caller cannot ask this function for any other row."""
        import inspect
        params = inspect.signature(rb.append_run_started).parameters
        for forbidden in ("event", "token", "event_type", "note", "row"):
            self.assertNotIn(forbidden, params)
        self.assertEqual("SUPPLEMENT_RUN_STARTED", rb.RUN_STARTED_TOKEN)

    def test_the_seam_writes_no_other_token(self):
        import inspect
        body = inspect.getsource(rb.append_run_started)
        for other in ("SUPPLEMENT_EXECUTION_AUTHORIZED", "SUPPLEMENT_SEALED",
                      "SUPPLEMENT_ATTEMPT_FAILURE", "SUPPLEMENT_FAILED",
                      "SUPPLEMENT_PROPOSED", "SUPPLEMENT_SUPERSEDED"):
            self.assertNotIn(other, body)


class TestFailClosedLeavesNothingBehind(unittest.TestCase):
    """A refusal must leave no directory and no supplement byte -- which is
    a property of WHERE the call sits, so that is what is asserted."""

    def test_the_append_precedes_make_run_directory_with_nothing_between(self):
        import inspect

        from itsf.mc import supplement_chain as ch
        lines = inspect.getsource(ch.run_supplement_gate_first).splitlines()
        i_p3 = next(i for i, l in enumerate(lines)
                    if l.strip() == "append_run_started()")
        i_md = next(i for i, l in enumerate(lines)
                    if "make_run_directory(" in l)
        self.assertLess(i_p3, i_md)
        between = [l for l in lines[i_p3 + 1:i_md]
                   if l.strip() and not l.strip().startswith("#")]
        self.assertEqual([], between,
                         "something runs between the P3 append and the first "
                         "side effect: %r" % between)

    def test_a_refusing_append_stops_the_chain_before_any_directory(self):
        """Executed, not only read off the source: with every gate passing,
        a refusing P3 must still leave `make_run_directory` uncalled."""
        from unittest import mock

        from itsf.mc import supplement_authority as _sa
        from itsf.mc import supplement_chain as ch
        from itsf.mc import supplement_runner as sr

        made = []

        def _refuse():
            raise rb.AppendRefused("p3_refused_for_the_test")

        ctx = sr.GateContext(supplement_id=SID, head_commit="a" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        with mock.patch.object(sr, "GATES",
                               {k: (lambda c: None) for k in sr.GATES}),                 mock.patch.object(_sa, "derive_supplement_authority",
                                  return_value=object()):
            with self.assertRaises(rb.AppendRefused):
                ch.run_supplement_gate_first(
                    ctx, planned=mock.Mock(
                        runs_target=Path("no-such-dir"),
                        # Named because the chain now READS it before the
                        # P3 append: the pre-P3 residue check snapshots
                        # this run's two planned leaves. A `Mock` here made
                        # the stand-in kinder than production and the test
                        # died in `Path()` instead of at the refusal it is
                        # about. Both paths are absent, which snapshots as
                        # empty -- so the check passes and the refusal
                        # under test is still the P3 append's.
                        archive_target=Path("no-such-archive-dir")),
                    prepared=object(), universe=object(),
                    vol_method=object(), flag_by_date={},
                    event_na_mapping="none", incident_id="INC-0123456789ab",
                    archive_before=(), archive_after_reader=tuple,
                    make_run_directory=lambda t: made.append(t),
                    append_run_started=_refuse)
        self.assertEqual([], made, "a directory was created despite the "
                                   "P3 append refusing")

    def test_the_real_registry_is_refused_without_writing(self):
        """The one case against the REAL ledger, and the property is the
        BYTES, not the code.

        It used to pin `p3_commit_is_not_the_authorized_one`. Today the real
        MC-DS-S001 already carries a P3 -- the first authorized run appended
        one -- so the refusal now arrives as `p3_already_present`, from an
        earlier check. Both are pre-write refusals and both are correct; the
        specific one depends on ledger state, which is exactly why it is not
        pinned here. What is pinned is that the real file did not move."""
        frozen = REAL.read_bytes()
        with self.assertRaises(rb.AppendRefused) as caught:
            rb.append_run_started(SID, head_commit="0" * 40, utc_stamp=UTC)
        self.assertTrue(caught.exception.code.startswith("p3_"),
                        caught.exception.code)
        self.assertEqual(frozen, REAL.read_bytes())


if __name__ == "__main__":
    unittest.main()
