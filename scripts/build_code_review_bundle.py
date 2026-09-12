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


#: NO GRANT IS APPLIED ANY MORE, and that is the correction. The review seat
#: runs under a RESTRICTED token and proved that the sealed-bundle path stays
#: unwritable to it even with an ordinary Modify ACE present -- so three
#: attempts to make a bundle-local directory writable were answering the wrong
#: question. The bundle is now immutable to review execution and the reviewer
#: writes to a seat-native root outside it. What remains here is the CHECK.


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
    writable = list(profile["write_surfaces"].get("in_bundle_writable") or [])
    sealed = ["", "tree", "authority", "probes", "environment",
              "MANIFEST.json", "run_review.cmd",
              "run_bundle_tests.py", "code_review_bundle_guard.py",
              "review_output.py"]
    sealed.append("VERIFY.md" if _mode(profile) == "POSTHOLD_VERIFICATION"
                  else "REVIEW.md")
    if _mode(profile) == "POSTHOLD_VERIFICATION":
        sealed.append("frozen")
    report = {"principal": REVIEW_PRINCIPAL, "declared_writable": writable,
              "sealed_checked": sealed, "probes": [], "grants": {}}

    if writable:
        refuse("the contract declares %s writable inside the bundle, but the "
               "bundle is immutable to review execution under this contract; "
               "reviewer output belongs in the external output root" % writable)

    for rel in sealed:
        target = root / rel if rel else root
        for r in _principal_rights(target):
            if any(t in r for t in _WRITE_RIGHT_TOKENS):
                refuse("sealed surface %r grants %r a mutation right (%s); the "
                       "payload must be read-only to review execution"
                       % (rel or "<bundle root>", REVIEW_PRINCIPAL, r))

    # The reviewer's own surface is EXTERNAL and seat-native, so the capability
    # that matters is proved there rather than here -- by `review_output.py`,
    # at launch, in the seat, by doing it. What this function still owns is the
    # other half: that nothing in the delivery is writable at all.
    report["probes"].append(
        "no in-bundle writable surface is declared; %d sealed surfaces carry "
        "no mutation right for %s" % (len(sealed), REVIEW_PRINCIPAL))
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
        #: bundle-relative path -> the REASON it may carry prior judgement.
        #: Empty for an ordinary review; a remediation verification declares
        #: exactly the files whose content IS the prior judgement.
        self.claim_blind_exempt = dict(
            profile.get("claim_blind_exempt") or {})
        #: which of them a file actually needed. An exemption nothing used is
        #: a dead allowlist entry, and the cut refuses one: it implies a live
        #: exception where there is none.
        self.claim_blind_exempt_used = set()

    # -- the only way bytes ever enter the bundle -----------------------
    def _write(self, rel: str, data: bytes, provenance: dict):
        for pat in REFUSED_PATTERNS:
            if pat.search(provenance.get("source_path", "")) or pat.search(rel):
                refuse("refused content class: %s (%s)"
                       % (rel, provenance.get("source_path", "")))
        cls = provenance["class"]
        if cls not in ("GIT_EXPORT", "GENERATED", "TEMPLATE", "ENVIRONMENT",
                       "FROZEN_REVIEW_RETURN"):
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
            reason = self.claim_blind_exempt.get(rel.replace("\\", "/"))
            if hits and not reason:
                refuse("CLAIM_BLIND: %s carries prior judgement of the "
                       "implementation under review -- %s" % (rel, hits))
            if hits:
                # DECLARED, NOT WAIVED. An exemption exists only where the
                # prior judgement IS the object the delivery hands over -- a
                # remediation verification cannot withhold the findings it
                # asks the verifier to check closure of. The reason rides
                # into the manifest beside the file, so the exemption is
                # readable rather than implicit.
                provenance = dict(provenance)
                provenance["claim_blind_exempt"] = reason
                provenance["claim_blind_hits"] = sorted(hits)
                self.claim_blind_exempt_used.add(rel.replace("\\", "/"))
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

    def frozen_return(self, rel: str, data: bytes, *, source: str,
                      produced_by: str, review_id: str):
        """BYTES A PRIOR INDEPENDENT REVIEWER RETURNED, carried unmodified.

        The fifth positive admission class, and it exists for exactly one
        situation: a delivery whose purpose is to verify that a named set of
        frozen findings is closed cannot withhold those findings from the
        verifier. Nothing here is edited, excerpted or reformatted -- the
        digest in the manifest is the digest of the bytes that seat wrote, so
        a restatement anywhere else in the package can be checked against
        them rather than trusted.
        """
        self._write(rel, data, {"class": "FROZEN_REVIEW_RETURN",
                                "source_path": source,
                                "produced_by": produced_by,
                                "returned_against_review_id": review_id})


# ---------------------------------------------------------------- checks
def frozen_returns(profile: dict) -> list:
    """THE frozen returns this delivery carries, normalised to a list.

    A first-generation post-HOLD verification carries ONE return: the review
    whose findings are being closed. A RESIDUAL verification carries two --
    the original findings AND the verification that judged them -- because the
    residual targets are defined by the second document and the findings they
    refer to live in the first. Withholding either would ask the verifier to
    adjudicate against a baseline it cannot read, which is the one thing the
    FROZEN_REVIEW_RETURN class exists to prevent.

    Each return keeps its own subdirectory. Two independent seats returned a
    `GUARD_REPORT.json`; flattening them would silently drop one.
    """
    frozen = profile["frozen_baseline"]
    rows = frozen if isinstance(frozen, list) else [frozen]
    out, seen = [], set()
    for row in rows:
        prefix = row.get("prefix", "frozen/")
        if not prefix.startswith("frozen/") or not prefix.endswith("/"):
            refuse("frozen return prefix %r must live under frozen/" % prefix)
        for art in row["artifacts"]:
            rel = prefix + art["name"]
            if rel in seen:
                refuse("two frozen returns both claim %s" % rel)
            seen.add(rel)
        out.append(row)
    return out


def _mode(profile: dict) -> str:
    """REVIEW (the O1-O13 adjudication) or POSTHOLD_VERIFICATION.

    One builder, because the parts that must not differ -- positive
    admission, the link and outcome refusals, the inventory closure, the
    write-surface verification, the guard, the runner, the launcher and the
    explicit workspace -- are the parts that took five deliveries to get
    right. What the mode switches is the DOCUMENT and the target map.
    """
    mode = profile.get("mode", "REVIEW")
    if mode not in ("REVIEW", "POSTHOLD_VERIFICATION"):
        refuse("unknown delivery mode %r" % mode)
    return mode


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
    mode = _mode(profile)
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
    # The output-root resolver travels WITH the delivery: the launcher runs it
    # before the guard exists, and the runner re-derives the same path from it,
    # so a mismatch is detectable instead of assumed.
    b.template("review_output.py",
               (REPO / "scripts" / "review_output.py").read_text(encoding="utf-8"))
    b.template("run_bundle_tests.py", runner_py(profile))
    # The reviewer's entrypoint. It is a TEMPLATE like the runner: authored for
    # the contract, not exported from the tree.
    from build_review_launcher_lib import render as _launcher      # noqa: E402
    b.template("run_review.cmd", _launcher(profile))
    # THE PROBE SET IS DECLARED, not fixed. An ordinary review ships all four;
    # a bounded remediation verification ships only the two EXECUTION-BOUNDARY
    # controls, because the other two adjudicate O1-O13 obligations and that
    # is not what a closure verification is for. Both surviving probes
    # prescribe their own denial, so the runner's admission rule still has
    # something to reconcile.
    _PROBES = {
        "probes/test_o4d_write_boundary.py":
            ("o4d_probe_template", "render"),
        "probes/test_o13_path_refusals.py":
            ("o13_path_refusal_probe_template", "render"),
        "probes/test_o9_production_entry_refusals.py":
            ("o9_production_entry_probe_template", "render"),
        "probes/test_runtime_init_boundary.py":
            ("runtime_init_probe_template", "render"),
    }
    wanted = profile.get("probes") or sorted(_PROBES)
    unknown = [p for p in wanted if p not in _PROBES]
    if unknown:
        refuse("profile names probes this builder cannot emit: %s" % unknown)
    for rel in wanted:
        module_name, entry = _PROBES[rel]
        module = __import__(module_name)
        b.template(rel, getattr(module, entry)())

    # NO `return/` ANY MORE. The bundle is immutable to review execution, so a
    # directory that exists only to be written into would be a promise the
    # delivery cannot keep -- which is exactly the promise that stopped three
    # seats. Reviewer returns live in the external output root.

    # ---- the delivery's own document and target map ---------------------
    if mode == "POSTHOLD_VERIFICATION":
        # THE FROZEN RETURNS, byte-exact. Carried because a closure
        # verification cannot be performed against a baseline the verifier is
        # not allowed to read, and digest-pinned so a restatement anywhere
        # else in this package can be checked against them.
        for frozen in frozen_returns(profile):
            source_root = Path(frozen["source_root"])
            prefix = frozen.get("prefix", "frozen/")
            for row in frozen["artifacts"]:
                data = (source_root / row["name"]).read_bytes()
                got = sha256_bytes(data)
                if got != row["sha256"] or len(data) != row["byte_count"]:
                    refuse("frozen return %s is not the declared bytes "
                           "(%s/%d declared, %s/%d found)"
                           % (row["name"], row["sha256"][:12],
                              row["byte_count"], got[:12], len(data)))
                b.frozen_return(prefix + row["name"], data,
                                source=str(source_root / row["name"]),
                                produced_by=frozen["produced_by"],
                                review_id=frozen["review_id"])
        targets = build_verification_targets(profile, b)
        b.generated("VERIFICATION_TARGETS.json", canonical(targets),
                    generator="scripts/build_code_review_bundle.py"
                              ":build_verification_targets",
                    sources=[str(profile_path.name),
                             "frozen/INITIAL_FINDINGS.md"])
        from build_verification_md_lib import render as _verify   # noqa: E402
        b.template("VERIFY.md", _verify(profile))
    else:
        omap = build_obligation_map(profile, b)
        b.generated("OBLIGATION_MAP.json", canonical(omap),
                    generator="scripts/build_code_review_bundle.py:build_obligation_map",
                    sources=[str(profile_path.name)])
        b.template("REVIEW.md", review_md(profile))

    # ---- MANIFEST last: it binds everything above ----------------------
    manifest = {
        "review_id": review_id,
        "mode": mode,
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
        # GUARD ADMISSION. v1 shipped a flat denial list, and a reviewer who
        # could not attribute one entry in it stopped before reading any code
        # -- correctly. What the run may refuse, what a refusal means, and
        # which refusals are PRESCRIBED are declared here and reconciled
        # mechanically in GUARD_REPORT.json.
        "guard_admission": profile["guard_admission"],
        "delivery_identity": {
            "id": review_id,
            "lineage": profile["lineage"],
            "maps_to_manifests": 1,
            "retired_identities": profile.get("retired_delivery_identities", {}),
        },
        # WHAT THIS DELIVERY IS FOR. Present only in verification mode, and it
        # names the frozen baseline and the repaired target by digest so the
        # package cannot be mistaken for a substantive round.
        "verification_of": (profile["repaired_target"]
                            if mode == "POSTHOLD_VERIFICATION" else None),
        "frozen_baseline": ([{k: v for k, v in row.items()
                              if k != "source_root"}
                             for row in frozen_returns(profile)]
                            if mode == "POSTHOLD_VERIFICATION" else None),
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
    unused = sorted(set(b.claim_blind_exempt) - b.claim_blind_exempt_used)
    if unused:
        refuse("declared claim-blind exemptions that nothing used: %s. A dead "
               "allowlist entry implies a live exception where there is none "
               "-- remove them, or find out why the scan stopped matching"
               % unused)
    hits = outcome_scan(b.root)
    if hits:
        refuse("outcome restatement inside the bundle:"
               + "".join(
                   [chr(10) + "  " + h for h in hits[:10]]))
    declared = {r["path"] for r in b.payload} | {"MANIFEST.json"}
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
    surfaces = verify_write_surfaces(b.root, profile)

    digest = sha256_bytes((b.root / "MANIFEST.json").read_bytes())
    print("bundle:          %s" % b.root)
    print("payload files:   %d" % len(b.payload))
    print("MANIFEST_SHA256: %s" % digest)
    print("write surface:   NONE in the bundle; %d sealed surfaces verified "
          "non-writable for %s"
          % (len(surfaces["sealed_checked"]), surfaces["principal"]))
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


def build_verification_targets(profile: dict, b: Bundle) -> dict:
    """F01-F07 as a MAP, with every locus resolved to a pinned payload file.

    The same discipline as the obligation map, for the same reason: a target
    that names a file the delivery does not carry is a target the verifier
    cannot adjudicate, and it must break the CUT rather than surface as a
    missing-file error on the reviewer's first command.
    """
    inb = {r["path"] for r in b.payload}
    digests = {r["path"]: r["sha256"] for r in b.payload}
    unresolved = []

    def resolve(entry, required_prose):
        loci = {}
        for locus in entry["loci"]:
            path = locus.split("::", 1)[0]
            if path not in inb:
                unresolved.append("%s names %s, which this delivery does not "
                                  "carry" % (entry["id"], path))
                continue
            loci[locus] = digests[path]
        for name in required_prose:
            if not (entry.get(name) or "").strip():
                unresolved.append("%s.%s is empty" % (entry["id"], name))
        return loci

    rows = {}
    for target in profile["verification_targets"]:
        loci = resolve(target, ("frozen_finding", "closure_requires",
                                "builder_claim"))
        rows[target["id"]] = {
            "title": target["title"],
            "frozen_finding": target["frozen_finding"],
            "closure_requires": target["closure_requires"],
            "builder_claim_SELF_REPORTED": target["builder_claim"],
            "loci_sha256": loci,
            "frozen_probe_refs": target.get("frozen_probe_refs", []),
            "focused_tests": target.get("focused_tests", []),
            "builder_declared_incompleteness":
                target.get("builder_declared_incompleteness"),
        }
    # NON-REGRESSION CONTROLS are a DIFFERENT question and must never be
    # mistaken for a target. A target asks "is this finding now closed?"; a
    # control asks "did closing something else break this one?" -- and the
    # answer to a control can only ever be NO_REGRESSION or REGRESSED. Keeping
    # them in separate maps is what stops a control from being read as a
    # re-adjudication of an independently closed finding.
    controls = {}
    for control in profile.get("non_regression_controls", []):
        loci = resolve(control, ("title", "previously_closed_as",
                                 "control_question"))
        controls[control["id"]] = {
            "title": control["title"],
            "previously_closed_as": control["previously_closed_as"],
            "control_question": control["control_question"],
            "loci_sha256": loci,
            "control_tests": control.get("control_tests", []),
            "may_not_be_reopened": True,
        }
    if unresolved:
        refuse("verification targets do not resolve:"
               + "".join(chr(10) + "  " + u for u in unresolved))
    required = set(profile.get("required_target_ids")
                   or ["F01", "F02", "F03", "F04", "F05", "F06", "F07"])
    missing = required - set(rows)
    if missing:
        refuse("the frozen finding set is incomplete: %s" % sorted(missing))
    overlap = set(rows) & set(controls)
    if overlap:
        refuse("%s is both a verification target and a non-regression "
               "control; it cannot be both" % sorted(overlap))
    required_controls = set(profile.get("required_control_ids") or [])
    missing = required_controls - set(controls)
    if missing:
        refuse("the non-regression control set is incomplete: %s"
               % sorted(missing))
    return {
        "schema": "n14_posthold_verification_targets.v1",
        "verification_id": profile["review_id"],
        "not_a_substantive_round": True,
        "round_accounting_unchanged": profile["round_accounting"],
        "frozen_baseline_sha256": {
            row["review_id"]: row["initial_findings_sha256"]
            for row in frozen_returns(profile)},
        "repaired_target": profile["repaired_target"],
        "targets": rows,
        "non_regression_controls": controls,
    }


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

# THERE IS NO PRE-BOOTSTRAP HERE, AND THAT IS THE POINT.
#
# An earlier runner imported `ctypes` before arming, because the family denial
# otherwise fired while `ctypes/__init__.py` bound `windll.kernel32` and pandas
# could not be imported at all. That worked, and it hid a second case it did
# not cover: during pandas' own initialisation, dateutil's Windows timezone
# backend loads `user32` to resolve localized names. That denial was NOT hidden
# -- it was SWALLOWED. `BundleEscapeDenied` is a `PermissionError` is an
# `OSError` is a `WindowsError`, dateutil catches exactly that, and the review
# silently ran against a different timezone backend while every test passed.
#
# So nothing is pre-imported now. No pandas, no dateutil, no timezone module,
# no lockfile, no arbitrary package -- not even the stdlib `ctypes` this file
# used to reach for. The entry point keeps its normal lazy initialisation
# order, and the guard instead recognises WHEN a pinned runtime module is
# running its first normal initialisation, permitting a native resolution only
# inside that extent, only with runtime code on the stack, and only to a
# library that resolves into the runtime tree or a protected system location.
# Everything else in the `ctypes.*` family is denied exactly as before.

# THE WORKSPACE IS SUPPLIED, NOT DISCOVERED, AND IT IS FROZEN BEFORE THE GUARD.
#
# The bundle is immutable to review execution: the seat runs under a restricted
# token that cannot write inside it whatever its ACL says. Four earlier attempts
# went looking for a writable directory instead -- one inside the bundle, then
# `tempfile.gettempdir()`, then a known-folder lookup -- and each was the same
# mistake wearing a different API: a sealed object guessing at something only
# the dispatcher knows. So the base arrives as ONE explicit launch argument,
# and nothing here reads TMP, TEMP, TMPDIR, a known folder or a profile to
# obtain it.
import review_output as RO

try:
    SUPPLIED = RO.parse_workspace_base(sys.argv[1:])
except RO.OutputRootRefused as exc:
    sys.stderr.write(
        "DELIVERY FAILURE: " + str(exc) + "\\nLaunch through "
        "run_review.cmd, which passes it. Report this and stop.\\n")
    raise SystemExit(94)

# CANONICALISE, PROVE DISJOINT IN BOTH DIRECTIONS, TAKE ONE FRESH CHILD,
# EXERCISE IT, BIND IT -- all before the guard arms. Every refusal here is a
# delivery failure rather than something to work around: the authority for this
# path is the dispatch, not this runner and not the seat.
try:
    RETURN = RO.prepare(ROOT, SUPPLIED).resolve()
    BINDING = RO.binding_for(RO._manifest_with_digest(ROOT))
    RO.check_binding(RETURN, BINDING)
    SUPPLIED_CANON = str(RO.canonical(SUPPLIED))
except Exception as exc:
    sys.stderr.write(
        "DELIVERY FAILURE: the supplied review workspace could not be "
        "established.\\n  " + str(exc) + "\\nReport this and stop. Do "
        "NOT try to write inside the sealed bundle and do NOT change its "
        "permissions.\\n")
    raise SystemExit(96)
sys.stderr.write("\\n[workspace] review workspace: " + str(RETURN) + "\\n")

# `prepare` created the scratch directory inside the fresh child, so there is
# nothing to clear here. A pre-existing child is refused rather than emptied,
# which is also why `shutil.rmtree` -- an escape class the guard denies
# outright -- is no longer needed at all.
SCRATCH = RETURN / RO.SCRATCH_NAME

# OUTPUT ROUTING, NOT AUTHORITY DISCOVERY, and the distinction is the whole
# architecture. These three are SET, after the workspace has been validated and
# frozen, so that pytest's temporary tree and anything else that asks the
# platform for a temp directory lands inside the one writable surface rather
# than somewhere the guard will deny. They are never READ to choose that
# surface: that is what the explicit parameter above is for.
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

# The ONLY writable region is the frozen child. The bundle, the runtime, the
# repository, quant-data -- and the supplied workspace BASE itself, with
# everything else under it -- are all outside it and stay read-only or denied.
# The base is deliberately not admitted: it was authority to create one
# directory, not a licence to read the seat's other work.
guard = G.arm(ROOT, RETURN, listing_only_roots=LISTING_ONLY,
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

# EVERY REFUSAL IS ATTRIBUTED, OR THE RUN FAILS.
#
# A sealed negative control DECLARES the refusal it is about to cause, so a
# reviewer can tell a prescribed control from an accident without taking anyone
# 's word for it. Two things then fail the run: a refusal no control declared,
# and a declared refusal that never happened -- the second means the control
# stopped controlling, which is the quieter of the two failures.
#
# This is also the answer to a third-party library swallowing an exception. The
# pytest session can report success while the guard has recorded an
# unattributed refusal; the exit code below does not.
code, reconciled = G.admission_exit_code(guard, code)
unexpected = reconciled["unexpected_denials"]
missing = reconciled["missing_prescribed_denials"]

report = {
    "denials": len(guard.denials),
    "in_bundle_path_ops": guard.allowed_path_ops,
    "admitted_listings": guard.admitted_listings,
    "denied": [[e, t] for e, t in guard.denials[:50]],
    "expected_denials": reconciled["expected_denials"],
    "unexpected_denials": unexpected,
    "missing_prescribed_denials": missing,
    "prescribed_negative_controls": reconciled["prescribed"],
    "runtime_initialization_events":
        reconciled["runtime_initialization_events"],
    "workspace_authority": "EXPLICIT_DISPATCH_PARAMETER",
    "supplied_workspace_base": SUPPLIED_CANON,
    "review_output_root": str(RETURN),
    "scratch_root": str(SCRATCH),
    "sealed_payload_writable": False,
    "output_binding": BINDING,
}
(RETURN / "GUARD_REPORT.json").write_text(
    json.dumps(report, indent=2) + "\\n", encoding="utf-8")
sys.stderr.write("\\n[guard] denials=" + str(len(guard.denials))
                 + " (expected " + str(len(reconciled["expected_denials"]))
                 + ", UNEXPECTED " + str(len(unexpected)) + ")"
                 + "  runtime-init native resolutions="
                 + str(len(reconciled["runtime_initialization_events"]))
                 + "  in-bundle path ops=" + str(guard.allowed_path_ops)
                 + "  admitted listings=" + str(guard.admitted_listings) + "\\n")
if unexpected or missing:
    for row in unexpected:
        sys.stderr.write("[guard] UNEXPECTED REFUSAL: " + str(row) + "\\n")
    for row in missing:
        sys.stderr.write("[guard] PRESCRIBED REFUSAL DID NOT HAPPEN: "
                         + str(row) + "\\n")
    sys.stderr.write(
        "\\nDELIVERY FAILURE: the guard recorded a refusal no sealed "
        "negative control prescribes, or a prescribed one that never "
        "happened. A library can swallow a refusal and let the session report "
        "success, so this is checked here rather than inferred from the test "
        "result. Report the lines above and stop.\\n")
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
                " ATTESTATION.md, which live in the output root itself and"
                " never here.\\n\\nIt is kept only because the run failed and"
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
