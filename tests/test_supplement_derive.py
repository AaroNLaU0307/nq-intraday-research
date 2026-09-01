"""`supplement_derive` assembles, and it never produces the real input.

THE CLAIM THAT MATTERS. The module says it takes `prepared` as an argument
and never creates one -- that is the whole reason it can be reviewed and
tested while the step that spends something stays behind its gate. A
docstring saying so is a claim, so it is proved two ways below: the source
carries no call to the producer, and running the assembler changes no
governed byte.

THE FIXTURES ARE REUSED, NOT REBUILT. `test_mc_supplement_authority` already
constructs both a TEST_ONLY prepared input and a production-shaped one, and
building a second pair here would be a hand-written mirror of a hundred lines
of setup -- the shape that has gone stale repeatedly in this repository.
"""

import ast
import hashlib
import unittest
from pathlib import Path

import pytest

from itsf import contracts as _c
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_derive as sd
from itsf.mc import supplement_precheck as pc

import test_mc_supplement_authority as fx

# RE-EXPORT the fixture chain. pytest resolves fixtures by module namespace,
# not by import, so `import fx` alone leaves `test_prepared` unresolvable.
# Bound programmatically rather than listed by hand: a hand-written list of
# fixture names is a mirror of someone else's file, and mirrors go stale --
# which is the failure this repository keeps meeting.
# The marker attribute is version-specific: pytest 9 wraps fixtures in
# `FixtureFunctionDefinition` and drops `_pytestfixturefunction`, which is
# what the first version of this loop looked for -- it matched nothing and
# every fixture silently stayed unresolvable. Detected by type here, and
# asserted non-empty below so a future rename fails loudly instead of
# quietly re-exporting nothing.
from _pytest.fixtures import FixtureFunctionDefinition as _FixtureDef

_REEXPORTED = []
for _name in dir(fx):
    _obj = getattr(fx, _name)
    if isinstance(_obj, _FixtureDef):
        globals()[_name] = _obj
        _REEXPORTED.append(_name)
assert "test_prepared" in _REEXPORTED and "prod_like" in _REEXPORTED, (
    "the fixture re-export found %r; pytest's fixture marker changed shape "
    "again and this loop is matching nothing" % (_REEXPORTED,))

GOVERNED = (Path(_c.RULED_RUNS_ROOT), Path(_c.RULED_ARCHIVE_ROOT))
MODULE = Path(sd.__file__)


def _blobs():
    out = []
    for root in GOVERNED:
        if root.exists():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    out.append((str(path),
                                hashlib.sha256(path.read_bytes()).hexdigest()))
    return sorted(out)


class TestItNeverProducesTheRealInput(unittest.TestCase):
    """The safety claim, by source and by behaviour."""

    def test_the_source_carries_no_call_to_the_real_producer(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("prepare_real_mc_input", "prepare_mc_input",
                          "authorize_real_mc"):
            self.assertNotIn(
                forbidden, called,
                "%s calls %s; this module is supposed to RECEIVE a prepared "
                "input, never make one" % (MODULE.name, forbidden))

    def test_it_does_not_even_import_the_real_input_module(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertNotIn("real_input", source)

    def test_prepared_is_a_parameter_of_both_public_functions(self):
        """If either could default it, a caller could omit it and the module
        would have to find one -- which is the thing it must not do."""
        import inspect
        for fn in (sd.assemble_derive_context, sd.run_derive_gates):
            params = inspect.signature(fn).parameters
            self.assertIn("prepared", params, fn.__name__)
            self.assertIs(params["prepared"].default,
                          inspect.Parameter.empty,
                          "%s gives `prepared` a default" % fn.__name__)


class TestTheReportCoversEveryGate(unittest.TestCase):

    def test_it_reports_all_five_in_the_contracts_order(self):
        ctx, _gaps = pc.assemble_precheck_context()
        report = sd.run_derive_gates(ctx, object())
        self.assertEqual(list(sc.GATE_TABLE["B_DERIVE"]),
                         [name for name, _d in report.results])

    def test_a_nonsense_prepared_refuses_without_raising_out(self):
        """A caller error must arrive as a refusal REPORT, not an exception
        escaping the reporter -- otherwise 'how far did it get' has no
        answer at all."""
        ctx, _gaps = pc.assemble_precheck_context()
        report = sd.run_derive_gates(ctx, object())
        self.assertFalse(report.authority_minted)
        self.assertTrue(report.mint_refusal)
        self.assertFalse(report.passed)


def test_a_test_only_prepared_is_refused_by_the_production_gate(test_prepared):
    """THE PARTITION, and it is what makes this safe to point anywhere.

    `custody_authority_production` refuses a TEST_ONLY authority by design.
    If this ever passed, the rehearsal and this reporter would both be able
    to reach production behaviour with synthetic inputs."""
    ctx, _gaps = pc.assemble_precheck_context()
    report = sd.run_derive_gates(ctx, test_prepared)
    refusing = {n for n, d in report.results if d is not None}
    assert "custody_authority_production" in refusing, report.results
    assert not report.passed


def test_the_assembler_changes_no_governed_byte(test_prepared):
    before = _blobs()
    sd.run_derive_gates(pc.assemble_precheck_context()[0], test_prepared)
    assert _blobs() == before


def test_how_far_a_PRODUCTION_SHAPED_input_gets(prod_like, capsys):
    """THE MEASUREMENT this module was built to make.

    Not an assertion that it passes -- a record of where it stops, printed so
    the number in any report comes from a run rather than from me. `prod_like`
    is the genuine production-shaped battery product, so this is as close to
    the real question as anything can get without spending a degree of
    freedom."""
    ctx, gaps = pc.assemble_precheck_context()
    assert gaps == ()
    report = sd.run_derive_gates(ctx, prod_like)
    with capsys.disabled():
        print("\n  B_DERIVE against a production-shaped prepared input:")
        print("    authority minted:", report.authority_minted,
              report.mint_refusal[:90] if report.mint_refusal else "")
        for name, detail in report.results:
            print("    %-30s %s" % (name, "PASS" if detail is None
                                    else "REFUSE " + detail[:70]))
    assert len(report.results) == 5


if __name__ == "__main__":
    unittest.main()
