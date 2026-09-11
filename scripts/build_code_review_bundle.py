# -*- coding: utf-8 -*-
"""Build a sealed code-review bundle. CODE_REVIEW_BUNDLE_CONTRACT v1.

SEPARATE FROM `scripts/build_verifier_dir.py` ON PURPOSE. That builder carries
the ratified run-verification / Stage-I refusals and is not touched here: for
v1 a little duplication is cheaper than weakening a boundary that is already
verified. Only behaviour-invariant helpers are shared in spirit (sha256, git
export, canonical serialization) and each is re-implemented in a few lines
rather than imported, so nothing there can change under it.

POSITIVE ADMISSION. Nothing is copied because it happens to be in the
repository. Every payload byte must be one of four things, declared per file
and recorded in the manifest:

    GIT_EXPORT        exact bytes of a blob at the target commit
    GENERATED         produced here, with generator + source provenance
    TEMPLATE          fixed REVIEW/return scaffolding authored for the contract
    ENVIRONMENT       explicitly permitted environment identity

Anything else refuses the cut. So does a link, an unexpected file, a refused
content class, or a payload whose provenance cannot be established.

IMPORT CLOSURE IS NOT EVIDENCE COMPLETENESS -- measured, 2026-09-10. The
selected N14 surface imports 108 project-local modules and OPENS 270. A payload
built from the import graph is missing data files, fixtures and configuration
that execution actually reads, and the gap stays invisible until the guard
denies something mid-run: the first cut refused on `gate1/platform_params.yaml`,
a data file no import reveals. So the payload set for this contract must be
derived from the FILE-OPEN / RESOURCE-ACCESS closure under the guarded runner,
and validation must measure that closure rather than the AST import graph.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT_VERSION = "CODE_REVIEW_BUNDLE_CONTRACT v1"
TRANSPORT_VERSION = "BUNDLE-v1"

#: Refused content classes (Layer 2). Checked by path, before any read.
REFUSED_PATTERNS = (
    re.compile(r"(^|/)qros-state\.yaml$"),
    re.compile(r"(^|/)ops/outcome_quarantine/"),
    re.compile(r"(^|/)EXPOSURE_LEDGER\.md$"),
    re.compile(r"(^|/)ops/DECISIONS\.md$"),
    re.compile(r"(^|/)ops/RESEARCH_STATE\.md$"),
    re.compile(r"(^|/)ops/BACKLOG\.md$"),
    re.compile(r"(^|/)ops/ARTIFACTS_UNDER_REVIEW\.json$"),
    re.compile(r"(^|/)ops/REVIEWER_EXPOSURE_LOG\.md$"),
    re.compile(r"(^|/)ops/OFF_LIMITS_"),
    re.compile(r"(^|/)ops/N14_(NORMATIVE|CLAIM_BLIND)_AUTHORITIES"),
    re.compile(r"S0_T001_RESULT"),
    # attestation RECORDS carry prior verdicts; the fixed template under
    # ops/templates/ is scaffolding the reviewer needs and is not a record.
    re.compile(r"(^|/)ops/(?!templates/).*ATTESTATION"),
    re.compile(r"(^|/)ops/RULING_"),
    re.compile(r"(^|/)ops/SEAT_RESULT"),
    re.compile(r"(^|/)ops/REVIEW_PACKET"),
)

#: CLAIM_BLIND, layer 2. REFUSED_PATTERNS judges a file by its PATH; these
#: judge admitted PROSE by what it says. The distinction that matters, and
#: that the N14-EXACT-TREE-004 stop turned on: a normative Owner ruling is
#: admissible even though the Owner issued it -- what is not is a judgment
#: about the CORRECTNESS OR ACCEPTANCE OF THE IMPLEMENTATION UNDER REVIEW,
#: including a prior reviewer's verdict, findings and measured test results.
#: Design vocabulary that merely contains the same words (FAIL_CLOSED, a
#: PASS|FAIL field enumeration, an APPROVED_PROFILE_ID key) is NOT caught,
#: and that separation was verified against the seven candidate documents
#: before this shipped.
CLAIM_BLIND_PATTERNS = (
    ("PRIOR_REVIEW_VERDICT", re.compile(r"判\s*(HOLD|PASS)")),
    ("PRIOR_REVIEW_ROUND",
     re.compile(r"第[一二三四五六七八九十]+次\s*(HOLD|PASS)")),
    ("PRIOR_REVIEW_FINDING",
     re.compile(r"(HOLD|PASS)\s*的\s*Finding|Finding\s*[0-9]+")),
    ("PRIOR_VERDICT_FIELD",
     re.compile(r"(PRIOR_)?VERDICT\s*[:=]\s*(PASS|HOLD|FAIL)")),
    ("PRIOR_TEST_RESULT",
     re.compile(r"已实测全红|全部通过|测试全绿")),
    ("PRIOR_REVIEW_SEAT",
     re.compile(r"(fresh\s+Sol|独立复核).{0,24}(HOLD|PASS|判)")),
)


#: THE PRINCIPAL THE REVIEW SEAT RUNS AS, and why this exists at all.
#:
#: A delivery declared `return/` writable in three places -- the manifest, the
#: guard and REVIEW.md -- and materialised that permission nowhere. The builder
#: runs as the repository owner, who holds FullControl by inheritance, so every
#: builder-side check passed. The review seat runs as a DIFFERENT account that
#: inherits ReadAndExecute only, and its launcher died creating the scratch
#: directory with WinError 5 before the guard ever armed.
#:
#: Resolved BY NAME at cut time rather than by a hardcoded SID, and never the
#: owner's own account: the grant belongs to the review seat, not to whoever
#: happened to build the bundle.
REVIEW_PRINCIPAL = "CodexSandboxUsers"
#: `icacls` right set: Modify, inherited by files and subdirectories, so the
#: scratch directory the runner creates under `return/` inherits it. This is
#: the exact shape of the grant on the one delivery a seat demonstrably wrote
#: into -- replicated rather than invented.
REVIEW_SURFACE_RIGHTS = "(OI)(CI)(M)"
#: Rights letters that confer any mutation. Anything else on a sealed surface
#: is fine; any of these is the defect this check exists to catch.
_WRITE_RIGHT_TOKENS = ("(F)", "(M)", "(W)", "(WD)", "(AD)", "(WA)", "(WEA)",
                       "(D)", "(DE)", "(DC)")


def _icacls(*args) -> tuple:
    r = subprocess.run(["icacls", *args], capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _principal_rights(path: Path) -> list:
    """Every rights string `icacls` reports for the review principal."""
    code, out = _icacls(str(path))
    if code != 0:
        refuse("icacls could not read the ACL of %s: %s" % (path, out.strip()))
    found = []
    for line in out.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        who, _, rights = line.rpartition(":")
        if who.split(chr(92))[-1].strip() == REVIEW_PRINCIPAL:
            found.append(rights.strip())
    return found


def materialise_write_surfaces(root: Path) -> dict:
    """Make the DECLARED writable surface actually writable for the seat.

    Only `return/`. Nothing else is touched, so every sealed surface keeps the
    read-only inheritance the principal already has -- which is why this is a
    grant and not a matching set of denials.
    """
    code, out = _icacls(str(root / "return"), "/grant",
                        "%s:%s" % (REVIEW_PRINCIPAL, REVIEW_SURFACE_RIGHTS))
    if code != 0:
        refuse("could not grant the review principal %r write access to "
               "return/: %s" % (REVIEW_PRINCIPAL, out.strip()))
    return {"principal": REVIEW_PRINCIPAL, "rights": REVIEW_SURFACE_RIGHTS,
            "surface": "return/"}


def verify_write_surfaces(root: Path, profile: dict) -> dict:
    """DECLARED write surfaces == MEASURED effective write surfaces.

    Generic, not attempt-specific: it reads what is DECLARED writable and
    checks the filesystem agrees, for the principal that will actually run the
    review. Two halves, and both are needed --

      * the declared surface must carry an explicit INHERITABLE grant, and a
        real create/write/rename/delete must succeed there;
      * every sealed surface must give that principal NO mutation right.

    The builder cannot impersonate the review principal, so the seat-side half
    is established structurally -- the grant and its inheritance flags -- not
    by performing a write as that user. The probes are real filesystem
    operations under the builder's own token, which is what proves the surface
    exists and is usable at all.
    """
    writable = ["return"]
    sealed = ["", "tree", "authority", "probes", "environment",
              "MANIFEST.json", "REVIEW.md", "run_review.cmd",
              "run_bundle_tests.py", "code_review_bundle_guard.py"]
    report = {"principal": REVIEW_PRINCIPAL, "declared_writable": writable,
              "sealed_checked": sealed, "probes": [], "grants": {}}

    for rel in writable:
        rights = _principal_rights(root / rel)
        explicit = [r for r in rights if "(I)" not in r]
        report["grants"][rel] = explicit
        if not explicit:
            refuse("declared writable surface %r carries NO explicit grant for "
                   "%r -- the declaration would be a comment, not a permission"
                   % (rel, REVIEW_PRINCIPAL))
        if not any(t in r for r in explicit for t in ("(M)", "(F)", "(W)")):
            refuse("declared writable surface %r grants %r no write right: %s"
                   % (rel, REVIEW_PRINCIPAL, explicit))
        if not all("(OI)" in r and "(CI)" in r for r in explicit):
            refuse("the grant on %r is not inheritable (%s); the scratch "
                   "directory the runner creates under it would not inherit it"
                   % (rel, explicit))

    for rel in sealed:
        target = root / rel if rel else root
        for r in _principal_rights(target):
            if any(t in r for t in _WRITE_RIGHT_TOKENS):
                refuse("sealed surface %r grants %r a mutation right (%s); the "
                       "payload must be read-only to review execution"
                       % (rel or "<bundle root>", REVIEW_PRINCIPAL, r))

    # Real filesystem operations, not ACL text. Create, write, rename, delete,
    # and a NESTED directory, because the runner makes `return/.scratch`.
    probe = root / "return" / ".write_surface_probe"
    try:
        probe.mkdir()
        first = probe / "a.txt"
        first.write_text("probe", encoding="utf-8")
        first.replace(probe / "b.txt")
        (probe / "b.txt").unlink()
        probe.rmdir()
        report["probes"].append("return/: mkdir, write, rename, delete OK")
    except OSError as exc:
        refuse("the declared writable surface is not writable even to the "
               "builder: %s" % exc)
    if probe.exists():
        refuse("the write-surface probe left residue in return/")
    return report


def claim_blind_hits(text: str) -> dict:
    return {name: len(pat.findall(text))
            for name, pat in CLAIM_BLIND_PATTERNS if pat.search(text)}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def git_blob(commit: str, path: str) -> bytes:
    r = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob",
                        "%s:%s" % (commit, path)], capture_output=True)
    if r.returncode:
        raise SystemExit("not a blob at %s: %s" % (commit, path))
    return r.stdout


def canonical(obj) -> bytes:
    """One serialization, everywhere, so a digest means the same thing twice."""
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
            .replace("\r\n", "\n") + "\n").encode("utf-8")


class Refused(SystemExit):
    pass


def refuse(why: str):
    raise Refused("BUNDLE CUT REFUSED: " + why)


class Bundle:
    def __init__(self, out_dir: Path, review_id: str, profile: dict):
        self.root = out_dir / review_id
        self.review_id = review_id
        self.profile = profile
        self.commit = profile["framework_commit"]
        self.payload = []          # manifest rows, in insertion order

    # -- the only way bytes ever enter the bundle -----------------------
    def _write(self, rel: str, data: bytes, provenance: dict):
        for pat in REFUSED_PATTERNS:
            if pat.search(provenance.get("source_path", "")) or pat.search(rel):
                refuse("refused content class: %s (%s)"
                       % (rel, provenance.get("source_path", "")))
        cls = provenance["class"]
        if cls not in ("GIT_EXPORT", "GENERATED", "TEMPLATE", "ENVIRONMENT"):
            refuse("unknown admission class %r for %s" % (cls, rel))
        # ADDED 2026-09-11 after a shipped runner failed to parse: RUNNER_BODY
        # is a non-raw triple-quoted string, so an unescaped newline escape in
        # it became a real newline and split a string literal in the file. A
        # template that does not compile is a bundle that cannot be reviewed,
        # and the cut is where that has to be caught -- not the reviewer's
        # first command.
        if rel.endswith(".py"):
            try:
                compile(data.decode("utf-8"), rel, "exec")
            except (SyntaxError, UnicodeDecodeError) as exc:
                refuse("emitted Python does not parse: %s -- %s" % (rel, exc))
        else:
            # CLAIM_BLIND on PROSE. Source and tests are exempt because they
            # ARE the object of review -- REVIEW.md already tells the reviewer
            # that an implementation comment is SELF_REPORTED and never the
            # rule the implementation is judged against. A governance document
            # carries no such warning and would read as authority, which is
            # exactly how the N14-EXACT-TREE-004 leak happened.
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = ""
            hits = claim_blind_hits(text)
            if hits:
                refuse("CLAIM_BLIND: %s carries prior judgement of the "
                       "implementation under review -- %s" % (rel, hits))
        dest = self.root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        self.payload.append({
            "path": rel.replace("\\", "/"),
            "provenance": provenance,
            "byte_count": len(data),
            "sha256": sha256_bytes(data),
        })

    def git_export(self, rel_in_bundle: str, repo_path: str):
        data = git_blob(self.commit, repo_path)
        self._write(rel_in_bundle, data, {
            "class": "GIT_EXPORT", "source_path": repo_path,
            "commit": self.commit,
            "blob": git("rev-parse", "%s:%s" % (self.commit, repo_path)),
        })

    def generated(self, rel: str, data: bytes, generator: str, sources: list):
        self._write(rel, data, {"class": "GENERATED", "source_path": rel,
                                "generator": generator, "sources": sources})

    def template(self, rel: str, text: str):
        self._write(rel, text.encode("utf-8"), {"class": "TEMPLATE",
                                                "source_path": rel})

    def environment(self, rel: str, data: bytes, detail: str):
        self._write(rel, data, {"class": "ENVIRONMENT", "source_path": rel,
                                "detail": detail})


# ---------------------------------------------------------------- checks
def no_links_anywhere(root: Path):
    bad = [p for p in root.rglob("*") if p.is_symlink()]
    if bad:
        refuse("symlink or junction inside the bundle: %s" % bad[:3])
    if os.name == "nt":
        for p in root.rglob("*"):
            try:
                attrs = os.stat(p, follow_symlinks=False).st_file_attributes
            except (OSError, AttributeError):
                continue
            if attrs & 0x400:                       # REPARSE_POINT
                refuse("reparse point (junction) inside the bundle: %s" % p)


def outcome_scan(root: Path) -> list:
    """Layer 4. SECONDARY defense: a clean scan is not proof of blindness."""
    sys.path.insert(0, str(REPO))
    from tests.test_review_artifacts_are_outcome_clean import OUTCOME_RESTATEMENTS
    hits = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        for label, pat, _ in OUTCOME_RESTATEMENTS:
            if pat.search(rel):
                hits.append("%s (NAME) -> %s" % (rel, label))
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pat, _ in OUTCOME_RESTATEMENTS:
            if pat.search(text):
                hits.append("%s -> %s" % (rel, label))
    return hits


def main(argv):
    profile_path = Path(argv[1])
    out_dir = Path(argv[2])
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    review_id = profile["review_id"]
    b = Bundle(out_dir, review_id, profile)
    if b.root.exists():
        refuse("%s already exists; a cut never overwrites" % b.root)
    b.root.mkdir(parents=True)

    # ---- tree/: exact Git exports at the target commit ----------------
    # One exception, and it is declared rather than quiet: the grant record is
    # FIELD-SELECTED (see scripts/build_grant_extract_lib.py) because its
    # correction sections state prior measured results about the code under
    # review. It enters as GENERATED with its generator recorded, so the
    # manifest distinguishes it from every Git export around it.
    from build_grant_extract_lib import render as _grant, SOURCE as _GRANT_SRC
    for rel in profile["tree_payload"]:
        if rel == _GRANT_SRC:
            b.generated("tree/" + rel, _grant(REPO),
                        generator="scripts/build_grant_extract_lib.py:render",
                        sources=[rel + " (field-selected; retrospective "
                                       "sections excluded and counted)"])
            continue
        b.git_export("tree/" + rel, rel)

    # ---- authority/: exact Git exports, kept apart from the tree ------
    for rel in profile["authority_payload"]:
        b.git_export("authority/" + Path(rel).name, rel)

    # ---- RULES_EXTRACT: generated, with generator + source provenance -
    extract = build_rules_extract(profile)
    b.generated("authority/RULES_EXTRACT.md", extract,
                generator="scripts/build_code_review_bundle.py:build_rules_extract",
                sources=profile["rules_extract_sources"])

    # ---- environment/ -------------------------------------------------
    env = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "pytest_version": _pytest_version(),
        "lockfile": "tree/ops/requirements.lock.txt"
        if "ops/requirements.lock.txt" in profile["tree_payload"] else None,
        # PORTABLE RUNTIME IDENTITY. Recorded here because a version+package
        # lock identifies an interpreter on ONE machine and says nothing about
        # whether a review seat can reach it -- which is how two seats stopped.
        "review_runtime": profile["review_runtime"],
        "note": ("Third-party packages are RUNTIME DEPENDENCIES, not project code "
                 "under review. ops/REVIEWER_CONTRACT.md section 4.2 already makes "
                 "executing an allowlisted module's dependencies EXECUTION rather "
                 "than inspection, declared in the attestation. No third-party "
                 "source is admitted and none is required."),
    }
    b.environment("environment/ENVIRONMENT.json", canonical(env),
                  detail="interpreter and test-runner identity")

    # ---- the guard and the bundle-local runner ------------------------
    b.template("code_review_bundle_guard.py",
               (REPO / "scripts" / "code_review_bundle_guard.py").read_text(encoding="utf-8"))
    b.template("run_bundle_tests.py", runner_py(profile))
    # The reviewer's entrypoint. It is a TEMPLATE like the runner: authored for
    # the contract, not exported from the tree.
    from build_review_launcher_lib import render as _launcher      # noqa: E402
    b.template("run_review.cmd", _launcher(profile))
    from o4d_probe_template import render as _probe          # noqa: E402
    b.template("probes/test_o4d_write_boundary.py", _probe())
    from o13_path_refusal_probe_template import render as _probe13   # noqa: E402
    b.template("probes/test_o13_path_refusals.py", _probe13())
    from o9_production_entry_probe_template import render as _probe9  # noqa: E402
    b.template("probes/test_o9_production_entry_refusals.py", _probe9())

    # ---- return/: empty at dispatch, with its scaffolding -------------
    (b.root / "return").mkdir()
    (b.root / "return" / ".keep").write_bytes(b"")

    # ---- OBLIGATION_MAP + REVIEW ---------------------------------------
    omap = build_obligation_map(profile, b)
    b.generated("OBLIGATION_MAP.json", canonical(omap),
                generator="scripts/build_code_review_bundle.py:build_obligation_map",
                sources=[str(profile_path.name)])
    b.template("REVIEW.md", review_md(profile))

    # ---- MANIFEST last: it binds everything above ----------------------
    manifest = {
        "review_id": review_id,
        "lineage": profile["lineage"],
        "substantive_round": profile["substantive_round"],
        "round_consumed": False,
        "transport_version": TRANSPORT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "profile_version": profile["profile_version"],
        # DELIVERY IDENTITY. Added 2026-09-11: one identity had come to name two
        # different manifests, which the contract forbids because a citation then
        # points at two different packages. The retired identity is recorded here
        # WITHOUT any verdict -- there is none to record; neither cut was ever
        # dispatched -- so the property can be checked rather than trusted.
        "review_runtime": profile["review_runtime"],
        # WRITE SURFACES. v1 declared what may be READ and said nothing about
        # where the run may WRITE, so the runner helped itself to the sealed
        # payload root and a seat without that permission stopped on it.
        "write_surfaces": profile["write_surfaces"],
        "delivery_identity": {
            "id": review_id,
            "lineage": profile["lineage"],
            "maps_to_manifests": 1,
            "retired_identities": profile.get("retired_delivery_identities", {}),
        },
        "framework_commit": b.commit,
        "repository_root_tree": git("rev-parse", "%s^{tree}" % b.commit),
        "itsf_src_tree": git("rev-parse", "%s:src/itsf" % b.commit),
        "mc_subtree_tree": git("rev-parse", "%s:src/itsf/mc" % b.commit),
        "tests_selected": profile["tests_selected"],
        "tests_deselected": profile["tests_deselected"],
        "tests_not_collected": profile["tests_not_collected"],
        "execution_selection_equivalence": profile["execution_selection_equivalence"],
        "authority_set": sorted(profile["authority_payload"]) + ["authority/RULES_EXTRACT.md"],
        "evidence_set": sorted(profile["tree_payload"]),
        "environment": env,
        "generated_artifact_provenance": [
            r for r in b.payload if r["provenance"]["class"] == "GENERATED"],
        "builder_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "payload": b.payload,
        "manifest_self_hash": "NOT SELF-HASHED BY CONSTRUCTION -- "
                              "MANIFEST_SHA256 is emitted out of band",
    }
    (b.root / "MANIFEST.json").write_bytes(canonical(manifest))

    # ---- refusal gates -------------------------------------------------
    no_links_anywhere(b.root)
    # Every admitted document that is neither code nor test must be named in
    # the profile with a reason. Silence is how a governance record slips in
    # beside the source it passes judgement on.
    gov = profile["governance_admissions"]
    needs = [rel for rel in profile["tree_payload"]
             if not rel.startswith(("src/", "tests/"))
             and rel not in ("ops/requirements.lock.txt", ".python-version",
                             "pytest.ini", "pyproject.toml", "setup.cfg",
                             "tox.ini")]
    undeclared = [r for r in needs if not gov.get(r)]
    if undeclared:
        refuse("governance document admitted with no recorded reason: %s"
               % undeclared)
    stale = [r for r in gov if r not in profile["tree_payload"]]
    if stale:
        refuse("governance_admissions names a file that is not admitted: %s"
               % stale)
    hits = outcome_scan(b.root)
    if hits:
        refuse("outcome restatement inside the bundle:"
               + "".join(
                   [chr(10) + "  " + h for h in hits[:10]]))
    declared = {r["path"] for r in b.payload} | {"MANIFEST.json", "return/.keep"}
    actual = {p.relative_to(b.root).as_posix()
              for p in b.root.rglob("*") if p.is_file()}
    if declared != actual:
        refuse("inventory mismatch: undeclared=%s missing=%s"
               % (sorted(actual - declared)[:5], sorted(declared - actual)[:5]))
    if (b.root / "comparand").exists():
        refuse("comparand/ must be absent at initial cut")

    # WRITE SURFACES LAST, and VERIFIED rather than declared. The ACL is
    # delivery STATE, not manifest bytes, so this disturbs neither the
    # digest nor determinism -- and it is exactly the state a reviewer
    # receives.
    granted = materialise_write_surfaces(b.root)
    surfaces = verify_write_surfaces(b.root, profile)

    digest = sha256_bytes((b.root / "MANIFEST.json").read_bytes())
    print("bundle:          %s" % b.root)
    print("payload files:   %d" % len(b.payload))
    print("MANIFEST_SHA256: %s" % digest)
    print("write surface:   %s granted %s on %s; %d sealed surfaces "
          "verified non-writable for that principal"
          % (granted["principal"], granted["rights"],
             granted["surface"], len(surfaces["sealed_checked"])))
    for line in surfaces["probes"]:
        print("                 %s" % line)
    return digest


def _pytest_version() -> str:
    try:
        import pytest
        return pytest.__version__
    except Exception:
        return "unknown"


def build_rules_extract(profile: dict) -> bytes:
    """Field-selected normative rules. Prospective rules only: no verdict, no
    acceptance judgement, no closure claim, no test outcome. The exclusions are
    COUNTED, never restated -- that distinction is why the previous authority
    artifact had to be retired."""
    from build_rules_extract_lib import render          # noqa: E402
    return render(REPO, profile)


def build_obligation_map(profile: dict, b: Bundle) -> dict:
    rows, unresolved = {}, []
    inb = {r["path"] for r in b.payload}
    for oid, cell in profile["obligations"].items():
        resolved = {}
        for key in ("authority", "implementation_locus", "test_or_probe",
                    "non_imported_evidence", "environment_input_identity"):
            val = cell.get(key)
            if val in (None, "NONE"):
                reason = cell.get("%s_none_reason" % key)
                if not reason:
                    unresolved.append("%s.%s is NONE with no authoritative reason"
                                      % (oid, key))
                resolved[key] = {"value": "NONE", "reason": reason}
                continue
            items = val if isinstance(val, list) else [val]
            missing = [i for i in items if i not in inb]
            if missing:
                unresolved.append("%s.%s not in the bundle: %s" % (oid, key, missing))
            resolved[key] = {"value": items}
        auth = resolved["authority"].get("value") or []
        if auth != "NONE" and all(str(a).startswith(("tree/src/", "tree/tests/"))
                                  for a in auth):
            unresolved.append("%s.authority points only at implementation/test code" % oid)
        rows[oid] = resolved
    if unresolved:
        refuse("obligation map incomplete:\n  " + "\n  ".join(unresolved))
    # Every withheld execution, with its reason, in the one file the reviewer
    # is told to read alongside REVIEW.md. A withholding whose reason lives
    # only in the builder's head is indistinguishable from a quiet omission,
    # which is the failure this node has already hit four times.
    withheld = {
        "deselected_node_ids": {k: profile["tests_deselected_reasons"].get(k)
                                for k in profile["tests_deselected"]},
        "not_collected_files": {k: profile["tests_not_collected_reasons"].get(k)
                                for k in profile["tests_not_collected"]},
        "measured_consequence": profile["execution_selection_equivalence"],
    }
    blank = [k for d in ("deselected_node_ids", "not_collected_files")
             for k, v in withheld[d].items() if not v]
    if blank:
        refuse("execution withheld with no recorded reason: %s" % blank)
    return {"profile_version": profile["profile_version"], "obligations": rows,
            "withheld_execution": withheld}


def review_md(profile: dict) -> str:
    from build_review_md_lib import render              # noqa: E402
    return render(profile)


def runner_py(profile: dict) -> str:
    """The bundle-local runner. It arms the guard BEFORE importing pytest, so
    nothing the test session does happens outside the boundary.

    Built by substitution rather than %-formatting: the body is full of %
    signs from its own logging, and doubling them was a source of noise.
    """
    body = RUNNER_BODY
    body = body.replace("@@LISTING_ONLY@@",
                        json.dumps(profile["bounded_admission"]["listing_only_roots"]))
    body = body.replace("@@DESELECT@@", json.dumps(profile["tests_deselected"], indent=4))
    body = body.replace("@@NOT_COLLECTED@@",
                        json.dumps(profile["tests_not_collected"], indent=4))
    assert "@@" not in body
    return body


RUNNER_BODY = """# -*- coding: utf-8 -*-
\"\"\"Run the selected tests and review probes inside the sealed bundle.

The guard is armed before pytest is imported, so nothing the session does --
collection included -- happens outside the boundary. An audit hook cannot be
removed once installed, which is the property that makes this worth doing.
\"\"\"
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import code_review_bundle_guard as G

G.block_colorama()

# CTYPES IS IMPORTED HERE, BEFORE THE BOUNDARY GOES UP, AND THE REASON IS A
# CORRECTION WORTH READING.
#
# The guard denies the whole `ctypes.*` audit family. On the builder's host that
# looked survivable, and it was -- by accident. An unpinned `.pth` in that
# machine's USER site-packages (`pip_system_certs`, reaching
# `pip._vendor.truststore._windows`) imported `ctypes` during interpreter
# startup, before any project code ran, so `windll.kernel32` was already bound
# and nothing tripped the denial. On a clean interpreter -- which is exactly
# what the portable review runtime is -- `numpy._core._internal` imports
# `ctypes`, `ctypes/__init__.py` binds `windll.kernel32.GetLastError`, the
# denial fires, and pandas cannot be imported at all. Measured: 3 denials, 2
# collection errors, nothing ran.
#
# WHAT THIS DOES AND DOES NOT PERMIT. Importing the stdlib module binds
# kernel32 at import time. Every LATER `ctypes.dlopen` -- loading any other
# native library, which is the escape the reservation names -- is still denied
# in full, and the guard report counts the refusals. So the family denial is
# unchanged for everything the review does; what changed is that a stdlib
# import numpy requires no longer depends on an accident of the builder's
# machine. That accident was masking the dependency, not satisfying it.
import ctypes                                             # noqa: E402,F401

# EPHEMERAL SCRATCH LIVES UNDER THE REVIEWER SURFACE, NOT AT THE BUNDLE ROOT.
# The previous runner created `<bundle_root>/_tmp`, and the review seat got
# WinError 5 there before the guard was even armed -- which was correct of the
# seat: a sealed input directory has no business being writable. `return/` is
# where the review contract already sends INITIAL_FINDINGS, FREEZE and
# ATTESTATION, and it is the only surface the seat has demonstrably been able to
# write. Scratch is a DOT directory inside it so it can never be mistaken for a
# reviewer artefact.
RETURN = ROOT / "return"
SCRATCH = RETURN / ".scratch"
if not RETURN.is_dir():
    sys.stderr.write(
        "DELIVERY FAILURE: the reviewer surface " + str(RETURN)
        + " is missing. Report this and stop.\\n")
    raise SystemExit(94)

# LIFECYCLE, step 1: absent or empty before execution. Done BEFORE the guard is
# armed, because `shutil.rmtree` is one of the escape classes the guard denies
# outright and this must not become a reason to carve a hole in that.
import shutil
if SCRATCH.exists():
    shutil.rmtree(SCRATCH, ignore_errors=True)
try:
    SCRATCH.mkdir(parents=True)
except OSError as exc:
    sys.stderr.write(
        "DELIVERY FAILURE: cannot create the review scratch directory "
        + str(SCRATCH) + " (" + type(exc).__name__ + ": " + str(exc) + ")."
        "\\nThe reviewer surface return/ must be writable. Report this and "
        "stop; do not make the sealed payload writable.\\n")
    raise SystemExit(95)

for var in ("TMP", "TEMP", "TMPDIR"):
    os.environ[var] = str(SCRATCH)
import tempfile
tempfile.tempdir = str(SCRATCH)

# The payload stays read-only even if this runner is started WITHOUT -B. The
# launcher passes -B; setting the flag here means a reviewer who invokes the
# runner directly still writes no bytecode into the sealed tree.
sys.dont_write_bytecode = True

os.environ["N14_BUNDLE_ROOT"] = str(ROOT)

# BOUNDED ADMISSION, this profile only: directory-NAME enumeration under these
# roots. File CONTENTS under them stay denied, which is the whole difference
# between the admission the Owner granted and a data read.
LISTING_ONLY = @@LISTING_ONLY@@

# Deselected by node id, with the reason recorded in OBLIGATION_MAP.json. Their
# SOURCE stays in the bundle and you are expected to read it -- what is withheld
# is their execution, not their text.
DESELECT = @@DESELECT@@

# NOT COLLECTED, which is not the same as deselected: pytest never imports
# these at all, because importing them is what fails. The reason for each is
# in OBLIGATION_MAP.json and the SOURCE is in tree/ for you to read.
NOT_COLLECTED = @@NOT_COLLECTED@@

guard = G.arm(ROOT, SCRATCH, listing_only_roots=LISTING_ONLY,
              writable_root=RETURN)

TREE = ROOT / "tree"
sys.path.insert(0, str(TREE / "src"))
sys.path.insert(0, str(TREE / "tests"))
os.chdir(TREE)

import pytest

# TWO INVOCATIONS, NOT ONE, and the reason is mechanical rather than tidy:
# passing probes/ (which is outside tree/) alongside tests moves pytest's
# rootdir up to the bundle root, after which every --deselect node id silently
# stops matching. The first sealed run lost all eleven deselections that way
# and the only symptom was eleven tests failing that were meant to be skipped.
# Running the two trees separately keeps rootdir at tree/, where the ids are
# written, and separates the repository suite from the review probes in the
# output -- which is worth having on its own.
# `--basetemp` pins pytest's own tmp tree into the scratch surface. Without it
# pytest derives one from TMP/TEMP, which works but is implicit -- and implicit
# is what put a scratch directory in the sealed payload in the first place.
BASE = ["-q", "-p", "no:cacheprovider", "--color=no"]
targs = BASE + ["tests", "--basetemp", str(SCRATCH / "pytest-tests")]
for node in DESELECT:
    targs += ["--deselect", node]
for path in NOT_COLLECTED:
    targs += ["--ignore", str(TREE / path)]
sys.stderr.write("\\n[bundle] repository tests\\n")
code = pytest.main(targs)
sys.stderr.write("\\n[bundle] review probes\\n")
pcode = pytest.main(BASE + [str(ROOT / "probes"),
                            "--basetemp", str(SCRATCH / "pytest-probes")])
code = code or pcode

report = {
    "denials": len(guard.denials),
    "in_bundle_path_ops": guard.allowed_path_ops,
    "admitted_listings": guard.admitted_listings,
    "denied": [[e, t] for e, t in guard.denials[:50]],
    "scratch_root": str(SCRATCH.relative_to(ROOT)).replace(chr(92), "/"),
    "writable_root": str(RETURN.relative_to(ROOT)).replace(chr(92), "/"),
    "sealed_payload_writable": False,
}
(ROOT / "return" / "GUARD_REPORT.json").write_text(
    json.dumps(report, indent=2) + "\\n", encoding="utf-8")
sys.stderr.write("\\n[guard] denials=" + str(len(guard.denials))
                 + "  in-bundle path ops=" + str(guard.allowed_path_ops)
                 + "  admitted listings=" + str(guard.admitted_listings) + "\\n")
# LIFECYCLE, steps 3 and 4. On success the scratch is REMOVED, so nothing
# ephemeral survives to be mistaken for evidence. On failure it is kept for
# diagnosis and labelled, because a stopped review is exactly when the
# temporary state is worth having -- and the label is what keeps it from
# reading as a reviewer artefact. `shutil.rmtree` is denied by the armed
# guard, so this walks and unlinks, which is permitted under return/.
def _wipe(root):
    removed = 0
    for base, dirs, names in os.walk(root, topdown=False):
        for name in names:
            try:
                os.remove(os.path.join(base, name))
                removed += 1
            except OSError:
                pass
        for name in dirs:
            try:
                os.rmdir(os.path.join(base, name))
            except OSError:
                pass
    try:
        os.rmdir(root)
    except OSError:
        pass
    return removed


if code == 0 and pcode == 0:
    n_removed = _wipe(str(SCRATCH))
    sys.stderr.write("\\n[scratch] removed after a clean run ("
                     + str(n_removed) + " files)\\n")
else:
    try:
        with open(str(SCRATCH / "EPHEMERAL_DO_NOT_READ_AS_EVIDENCE.txt"),
                  "w", encoding="utf-8") as fh:
            fh.write(
                "This directory is EPHEMERAL EXECUTION STATE from a review run"
                " that did not exit clean.\\n\\nIt is NOT a reviewer"
                " artefact and is NOT evidence for O1-O13. The reviewer's"
                " returns are INITIAL_FINDINGS.md, FREEZE.json and"
                " ATTESTATION.md, which live in return/ itself and never"
                " here.\\n\\nIt is kept only because the run failed and"
                " the temporary state may help diagnose why. Delete it"
                " freely.\\n")
    except OSError:
        pass
    sys.stderr.write("\\n[scratch] kept for diagnosis at "
                     + str(SCRATCH) + " -- labelled ephemeral, not"
                     " evidence\\n")

sys.exit(code)
"""


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main(sys.argv)
