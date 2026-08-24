"""Coercion of caller data inside the digest / identity derivations.

WHY. Four N06 review rounds found four Highs and all four had one shape:
a caller-supplied value took part in a comparison that decided whether to
write. The repairs applied one rule at three sites -- exact built-in
scalars, refuse subclasses, NEVER coerce (`freeze_payload`, the builder's
rows, the authority's day universe). `str(v)` is the opposite of that
rule: it runs the attacker's own `__str__` and keeps the result.

Two of those four defects were coercion sites, and BOTH surfaced after
the review that should have caught them. The failure mode is not that
coercion is always wrong -- it is that a new site appears and nobody
notices it is the fifth instance of a pattern with four Highs behind it.

SCOPE. Only the functions that DERIVE A DIGEST OR AN IDENTITY, because
those are the values later comparisons are made against. Error-message
formatting, path normalisation and registry integer parsing are out of
scope on purpose: cataloguing them would bury the signal.

THIS FILE DOES NOT CLAIM THE REGISTERED SITES ARE SAFE. It pins them, so
adding one more fails a test instead of passing unnoticed.

MEASURED 2026-08-24, probe on the live tree:
    day_universe_digest   real 9ccceef7... vs __str__-liar 747bf557...
    bundle_table_digest   real f50c424d... vs __str__-liar 2ed483e2...
both DIVERGE while the poisoned elements still compare EQUAL. The
half-forged route (poisoned prepared, genuine authority) is refused with
`supplement_authority_bundle_table_mismatch`. The fully-forged pair was
NOT tested and is NOT claimed safe.
"""
from __future__ import annotations

import ast
from pathlib import Path

from itsf.mc import supplement_authority as sa
from itsf.mc import day_strata_supplement as dss

#: (module, function) whose body feeds a digest or an identity comparison.
WATCHED = {
    (sa, "day_universe_digest"),
    (sa, "bundle_table_digest"),
    (sa, "enforce_day_universe_identity"),
    (sa, "_mint_authority"),
    (dss, "_validate_row"),
    (dss, "canonical_rows_digest"),
}

#: Coercion sites currently tolerated, each with WHY. A site absent from
#: here is a finding; an entry with no matching site is stale.
KNOWN = {
    ("day_universe_digest", "str"): (
        "Probed: the digest DOES diverge under a __str__ liar. Callers are "
        "type-checked upstream (verify_supplement_authority, N06 round 4), "
        "so this is defence BY ORDERING, not by construction."),
    ("bundle_table_digest", "str"): (
        "Same shape over prepared.file_sha256. The half-forged route is "
        "refused by the bundle-table comparison; the fully-forged pair was "
        "not tested."),
    ("enforce_day_universe_identity", "str"): (
        "Derives ref_dates / channel sequences / tp sets from the sealed "
        "records. Reachable only through a prepared input, which is "
        "capability-guarded -- and that capability is the disclosed F1/F2 "
        "residual, so this is ordering again."),
    ("_mint_authority", "str"): (
        "Stamps the authority's own fields from prepared. The minted "
        "object is later re-verified field by field against prepared, so a "
        "coerced value cannot disagree with its source undetected."),
    ("_validate_row", "str"): (
        "Hermetic row validation. Production callers normalise first "
        "(build_supplement_from_authority, _rebuild_from_rows, N06 rounds "
        "3-4), so ordering again, not construction."),
    ("_validate_row", "int"): ("same row, same reason."),
}

_COERCERS = {"str", "int", "float"}


def _sites():
    """(function, coercer) pairs actually present in the watched bodies."""
    found = set()
    for module, fname in WATCHED:
        src = Path(module.__file__).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.FunctionDef) or node.name != fname:
                continue
            for call in ast.walk(node):
                if not isinstance(call, ast.Call):
                    continue
                fn = call.func
                if not (isinstance(fn, ast.Name) and fn.id in _COERCERS):
                    continue
                # coercing a literal or a slice of one is not caller data
                arg = call.args[0] if call.args else None
                if isinstance(arg, (ast.Constant, ast.JoinedStr)):
                    continue
                found.add((fname, fn.id))
    return found


def test_no_unregistered_coercion_in_a_digest_derivation():
    """A new coercion inside a digest/identity derivation must be
    registered with a reason. This does NOT bless the registered ones."""
    unknown = sorted(_sites() - set(KNOWN))
    assert not unknown, (
        "coercion of caller-reachable data inside a digest or identity "
        "derivation, not registered:\n  "
        + "\n  ".join(f"{f}() -> {c}()" for f, c in unknown)
        + "\n\nFour N06 Highs came from this shape. Either type-check "
          "exactly (see supplement_production._freeze_value) or add it to "
          "KNOWN with the reason it is tolerated.")


def test_the_register_has_no_stale_entries():
    """A stale entry hides that a site was fixed, which is how a register
    quietly stops meaning anything."""
    stale = sorted(set(KNOWN) - _sites())
    assert not stale, (
        "KNOWN lists sites that no longer exist -- remove them:\n  "
        + "\n  ".join(f"{f}() -> {c}()" for f, c in stale))


def test_the_divergence_measurement_is_pinned_not_folklore():
    """The docstring's measurement, kept executable. If a repair removes
    the coercion this fails, and both this test and the KNOWN entry go."""
    class _StrLiar(str):
        def __str__(self):
            return "0" * 64

        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        __hash__ = str.__hash__

    days = ("2026-08-03", "2026-08-04")
    poisoned = (_StrLiar(days[0]), days[1])
    assert sa.day_universe_digest(days) != sa.day_universe_digest(poisoned)
    assert poisoned[0] == days[0]      # ...yet still compares equal
