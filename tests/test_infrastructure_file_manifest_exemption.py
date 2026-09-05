"""S0's infrastructure files are exempt from the SEALED manifest, not from
verification.

THE CONTRADICTION THIS CLOSES, measured 2026-09-05 on the first real N09
attempt. `s0/output_proof.py` classifies `manifest.jsonl` and
`REGISTRY_AFTER_RUN_STARTED.json` as `infrastructure_files` -- written by the
run infrastructure, not by the renderer, and therefore they "must not appear
in `sealed_files`". The MC consumer meanwhile required a sealed-manifest
digest for every bundle file except `manifest.jsonl`. So it demanded an entry
S0 was never going to write, and the real sealed bundle refused with
`bundle_manifest_coverage`.

WHY THE SUITE NEVER CAUGHT IT, and it is the more useful half of this record.
Every synthetic `_bundle()` in this suite calls a `_refresh_manifest` that
declares EVERY non-manifest file. The fixtures were more complete than what
S0 actually seals, so the check passed on synthetic bytes and failed on the
only bundle that matters. A fixture that is kinder than production hides
exactly the defect production will hit.

WHAT THIS FILE PROVES:

  1. the real S0 shape (manifest without the infrastructure files) prepares;
  2. NOTHING is lost -- absent, tampered, or malformed infrastructure files
     still refuse, through the external custody attestation and the content
     cross-checks;
  3. the exemption did NOT widen to renderer files;
  4. the exemption set still equals what S0 itself declares -- read out of
     the S0 call site, so the two cannot drift apart silently.

Synthetic bytes only. Nothing here reads the sealed run directory.
"""

import ast
import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_consumer as C                       # noqa: E402
from itsf.mc import consumer as mcc                # noqa: E402
from itsf.mc.atoms import MCInputError             # noqa: E402

S0_RUN_SCRIPT = REPO / "scripts" / "s0_real_run.py"


#: What the REAL S0 seal omits from its manifest, HARD-CODED. Deliberately
#: NOT `mcc.S0_INFRASTRUCTURE_FILES`: a fixture that derived its shape from
#: the constant under test would relax in step with a wrong constant, and
#: the tests below would pass while exercising nothing. Measured from the
#: sealed S0-T001 bundle (14 files on disk, 12 `file` records) and pinned to
#: S0's own declaration by the drift test at the bottom of this file.
REAL_S0_OMITS = frozenset({"manifest.jsonl", "REGISTRY_AFTER_RUN_STARTED.json"})


def _s0_shaped(bundle=None):
    """A bundle whose manifest covers only RENDERER files -- the real S0
    shape, which the suite's own `_refresh_manifest` does not produce."""
    b = dict(bundle if bundle is not None else C._bundle())
    names = sorted(set(b) - REAL_S0_OMITS)
    b["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(b[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")
    return b


class TestTheRealS0ShapePrepares(unittest.TestCase):

    def test_a_manifest_without_the_infrastructure_files_is_accepted(self):
        prepared = C._prepare(_s0_shaped())
        self.assertIsNotNone(prepared)

    def test_the_fixture_really_is_the_shape_that_used_to_refuse(self):
        """Guards the guard. If `_s0_shaped` ever started declaring the
        infrastructure files again, the test above would pass without
        exercising the exemption at all."""
        declared = {json.loads(l)["relative_path"]
                    for l in _s0_shaped()["manifest.jsonl"]
                    .decode("utf-8").splitlines() if l.strip()}
        self.assertEqual(frozenset(), declared & REAL_S0_OMITS)
        self.assertIn("S0_REPORT.json", declared)

    def test_the_fixture_does_not_track_the_constant_under_test(self):
        """MEASURED, and it caught a real defect in this file. The first
        draft built `_s0_shaped` from `mcc.S0_INFRASTRUCTURE_FILES`, so
        narrowing that constant back to `{manifest.jsonl}` ALSO relaxed the
        fixture -- the mutation produced a complete manifest and the test
        went on passing. A fixture derived from the thing under test cannot
        witness that thing being wrong."""
        import inspect
        body = inspect.getsource(_s0_shaped)
        self.assertNotIn("mcc.S0_INFRASTRUCTURE_FILES", body)
        self.assertIn("REAL_S0_OMITS", body)


class TestNothingIsLost(unittest.TestCase):
    """The exemption drops one redundant digest. Everything else that
    protected this file must still fire."""

    def test_an_absent_infrastructure_file_still_refuses(self):
        b = _s0_shaped()
        authority = mcc.CustodyAuthority.for_tests(b)     # before removal
        del b["REGISTRY_AFTER_RUN_STARTED.json"]
        with self.assertRaises(MCInputError) as caught:
            C._prepare(b, authority=authority)
        self.assertEqual("bundle_exact_set_violation", caught.exception.code)

    def test_tampered_bytes_still_refuse_on_the_external_digest(self):
        """The sealed manifest no longer covers it, so this is the check
        that has to bite -- and it is the stronger one, because the
        attestation lives OUTSIDE the bundle under review."""
        b = _s0_shaped()
        authority = mcc.CustodyAuthority.for_tests(b)     # pre-tamper
        payload = json.loads(b["REGISTRY_AFTER_RUN_STARTED.json"])
        payload["snapshot_before"]["trial_id"] = C.TRIAL
        payload["padding"] = "tampered"
        b["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps(
            payload).encode("utf-8")
        with self.assertRaises(MCInputError) as caught:
            C._prepare(b, authority=authority)
        self.assertEqual("bundle_hash_mismatch", caught.exception.code)

    def test_a_wrong_trial_binding_still_refuses_on_content(self):
        """Structure and meaning, not just bytes: the file's own snapshot
        must agree with the authorization it is presented under."""
        b = _s0_shaped()
        b["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps(
            {"snapshot_before": {"trial_id": "S0-WRONG",
                                 "authorized_commit": C.COMMIT}}
        ).encode("utf-8")
        with self.assertRaises(MCInputError) as caught:
            C._prepare(_s0_shaped(b))
        self.assertIn("binding_violation", caught.exception.code)

    def test_unparseable_content_still_refuses(self):
        b = _s0_shaped()
        b["REGISTRY_AFTER_RUN_STARTED.json"] = b"{ not json"
        with self.assertRaises(Exception):
            C._prepare(_s0_shaped(b))


class TestTheExemptionDidNotWiden(unittest.TestCase):

    def test_a_renderer_file_missing_from_the_manifest_still_refuses(self):
        b = _s0_shaped()
        kept = [l for l in b["manifest.jsonl"].decode("utf-8").splitlines()
                if l.strip()
                and json.loads(l)["relative_path"] != "S0_REPORT.json"]
        b["manifest.jsonl"] = "\n".join(kept).encode("utf-8")
        with self.assertRaises(MCInputError) as caught:
            C._prepare(b)
        self.assertEqual("bundle_manifest_coverage", caught.exception.code)

    def test_a_renderer_file_with_a_wrong_manifest_digest_still_refuses(self):
        b = _s0_shaped()
        rows = []
        for line in b["manifest.jsonl"].decode("utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["relative_path"] == "S0_REPORT.json":
                rec["file_sha256"] = "0" * 64
            rows.append(json.dumps(rec, sort_keys=True))
        b["manifest.jsonl"] = "\n".join(rows).encode("utf-8")
        with self.assertRaises(MCInputError) as caught:
            C._prepare(b)
        self.assertEqual("bundle_hash_mismatch", caught.exception.code)

    def test_the_exempt_set_is_exactly_two_and_both_are_still_required(self):
        self.assertEqual(2, len(mcc.S0_INFRASTRUCTURE_FILES))
        for name in mcc.S0_INFRASTRUCTURE_FILES:
            with self.subTest(name=name):
                self.assertIn(name, mcc.BUNDLE_EXACT_SET)


class TestItStillMatchesWhatS0Declares(unittest.TestCase):
    """A second hand-written list is a second thing to keep in agreement.
    This reads S0's own call site instead of trusting that they still
    match."""

    def test_the_exempt_set_equals_the_s0_call_sites_literal(self):
        tree = ast.parse(S0_RUN_SCRIPT.read_text(encoding="utf-8"))
        found = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "infrastructure_files":
                    found = {e.value for e in kw.value.elts}
        self.assertIsNotNone(
            found, "no infrastructure_files= call site in %s -- the exempt "
                   "set now has nothing to agree with" % S0_RUN_SCRIPT.name)
        self.assertEqual(set(mcc.S0_INFRASTRUCTURE_FILES), found)


if __name__ == "__main__":
    unittest.main()
