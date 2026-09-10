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
    for rel in profile["tree_payload"]:
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
        "framework_commit": b.commit,
        "repository_root_tree": git("rev-parse", "%s^{tree}" % b.commit),
        "itsf_src_tree": git("rev-parse", "%s:src/itsf" % b.commit),
        "mc_subtree_tree": git("rev-parse", "%s:src/itsf/mc" % b.commit),
        "tests_selected": profile["tests_selected"],
        "tests_deselected": profile["tests_deselected"],
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
    declared = {r["path"] for r in b.payload} | {"MANIFEST.json", "return/.keep"}
    actual = {p.relative_to(b.root).as_posix()
              for p in b.root.rglob("*") if p.is_file()}
    if declared != actual:
        refuse("inventory mismatch: undeclared=%s missing=%s"
               % (sorted(actual - declared)[:5], sorted(declared - actual)[:5]))
    if (b.root / "comparand").exists():
        refuse("comparand/ must be absent at initial cut")

    digest = sha256_bytes((b.root / "MANIFEST.json").read_bytes())
    print("bundle:          %s" % b.root)
    print("payload files:   %d" % len(b.payload))
    print("MANIFEST_SHA256: %s" % digest)
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
    return {"profile_version": profile["profile_version"], "obligations": rows}


def review_md(profile: dict) -> str:
    from build_review_md_lib import render              # noqa: E402
    return render(profile)


def runner_py(profile: dict) -> str:
    """The bundle-local runner. It arms the guard BEFORE importing pytest, so
    nothing the test session does happens outside the boundary."""
    roots = json.dumps(profile["bounded_admission"]["listing_only_roots"])
    return '''# -*- coding: utf-8 -*-
"""Run the selected tests inside the sealed bundle, under the execution guard.

The guard is armed before pytest is imported. There is no way to disarm an
audit hook, which is the property that makes this worth doing at all.
"""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import code_review_bundle_guard as G

G.block_colorama()
TMP = ROOT / "_tmp"
TMP.mkdir(exist_ok=True)
for var in ("TMP", "TEMP", "TMPDIR"):
    os.environ[var] = str(TMP)
import tempfile
tempfile.tempdir = str(TMP)

# BOUNDED ADMISSION, N14 profile only: directory-NAME enumeration under these
# two roots. File contents under them remain denied, which is the difference
# between the admission the Owner granted and a data read.
LISTING_ONLY = %s

guard = G.arm(ROOT, TMP, listing_only_roots=LISTING_ONLY)

TREE = ROOT / "tree"
sys.path.insert(0, str(TREE / "src"))
sys.path.insert(0, str(TREE / "tests"))
os.chdir(TREE)

import pytest
code = pytest.main(["-q", "tests", "-p", "no:cacheprovider", "--color=no"])

sys.stderr.write("\\n[guard] denials=%%d  in-bundle path ops=%%d  admitted listings=%%d\\n"
                 %% (len(guard.denials), guard.allowed_path_ops, guard.admitted_listings))
for ev, tgt in guard.denials[:20]:
    sys.stderr.write("[guard] DENIED %%s -> %%s\\n" %% (ev, tgt))
sys.exit(code)
''' % roots


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main(sys.argv)
