"""Governed-execution identity, environment pin, and the dependency register.

QROS-CF v2 §2.2 (DEC-0001, DEC-0006 I1, DEC-0008 Condition A).

WHY THIS EXISTS. A real-run authorization used to bind the WHOLE repository
tree: `authorized_commit_matches_head` compared the authorized 40-hex commit
with HEAD. Every documentation or governance-test commit therefore voided a
live authorization, which the supplement contract lets you repair only by
burning a P2S and obtaining a fresh owner signature -- measured on
MC-DS-S001: three pre-start commits, four signatures. The property the gate
is FOR is narrower: the code that runs, the tests that protect its research
numbers, and the frozen inputs it reads must be the ones that were
authorized. That set is what this module computes an identity over.

WHAT THE IDENTITY COVERS (Condition A: every production-semantic input must
be constrained by SOME fail-closed mechanism; not all of them by this one).

    GOVERNED_IDENTITY   git blob OIDs, at the commit, of: src/, scripts/,
                        gate1/, ops/requirements.lock.txt, .python-version,
                        tests/conftest.py, tests/tiers.py, and every
                        tests/*.py that tests/tiers.py does NOT list as
                        governance (tier C). Deleting a leakage test changes
                        the identity; editing a README-index test does not.
    LOCKFILE_GATE       installed package versions == ops/requirements.lock.txt
    PYTHON_VERSION_GATE running interpreter major.minor == .python-version
    ENVIRONMENT_GATE    none of the interpreter/git override variables is set
    DATA_MANIFEST       every vendor file read is verified against the
                        AUTHORIZED manifest (production_inputs)
    CUSTODY_BATTERY     the sealed S0-T001 bundle (real_input / consumer)
    CODE_PINNED_HASH    ops/S0_T001_POST_RUN_ATTESTATION.md (consumer pins it)
    FROZEN_HASH         guards.FROZEN_HASHES
    EXISTENCE_FLAG_GATE the two flag files (existence is the whole input)
    REGISTRY_CHAIN_GATE the external registry, resolved through the boundary
    NOT_SEMANTIC        inputs that cannot change a research number (git
                        binary, temp directories)

`DEPENDENCY_REGISTER` names every class Condition A lists and the mechanism
that constrains it; `tests/test_execution_identity.py` derives the set of
repository paths production code actually opens and refuses any path the
register does not cover. A new read is added to the register or refused --
never discovered by a verifier.

WHAT THIS MODULE DOES NOT DO. It never writes, never resolves the registry
(that is `registry_boundary`), and never decides anything: the gate in
`supplement_runner` decides, on a comparison this module hands it.
"""
from __future__ import annotations

import ast
import dataclasses as _dc
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

__all__ = [
    "REPO", "STATIC_GOVERNED", "GOVERNED_TEST_FILES_ALWAYS",
    "HOSTILE_ENV_VARS", "DEPENDENCY_CLASSES", "MECHANISMS",
    "Dependency", "DEPENDENCY_REGISTER",
    "ExecutionIdentity", "IdentityComparison", "EnvironmentReport",
    "SeamRefused", "IdentityError",
    "governance_files_at", "governed_entries", "identity_at", "compare",
    "measure_environment", "measure_for_context", "covering_mechanism",
    "governed_dirty_paths", "seam_recheck",
]

REPO = Path(__file__).resolve().parents[2]

#: Paths (directories or files) whose committed bytes are part of the
#: identity at every commit. Directories are expanded to every tracked file.
STATIC_GOVERNED = ("src", "scripts", "gate1",
                   "ops/requirements.lock.txt", ".python-version")

#: Test-tree files that are governed regardless of the tier map, because
#: they DEFINE the selection the run gate executes.
GOVERNED_TEST_FILES_ALWAYS = ("tests/conftest.py", "tests/tiers.py")

#: Override vectors the S0 runner already refuses in its own process
#: (`g_parent_env_clean`); the supplement path now refuses them too.
HOSTILE_ENV_VARS = ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME",
                    "PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE",
                    "GIT_CONFIG", "GIT_CONFIG_GLOBAL", "GIT_TEMPLATE_DIR",
                    "GIT_CEILING_DIRECTORIES")

LOCKFILE = REPO / "ops" / "requirements.lock.txt"
PYTHON_VERSION_FILE = REPO / ".python-version"

DEPENDENCY_CLASSES = ("REPO_FILE", "ENV_VAR", "EXTERNAL_CONFIG", "PACKAGE",
                      "CALENDAR", "DATA_IDENTITY", "RUNTIME")
MECHANISMS = ("GOVERNED_IDENTITY", "LOCKFILE_GATE", "PYTHON_VERSION_GATE",
              "ENVIRONMENT_GATE", "DATA_MANIFEST", "CUSTODY_BATTERY",
              "CODE_PINNED_HASH", "FROZEN_HASH", "EXISTENCE_FLAG_GATE",
              "REGISTRY_CHAIN_GATE", "NOT_SEMANTIC")


class IdentityError(RuntimeError):
    """The identity could not be computed. Callers fail closed on it."""


class SeamRefused(RuntimeError):
    """The pre-first-write re-check refused. `code` is machine-readable."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@_dc.dataclass(frozen=True)
class Dependency:
    locator: str            # repo-relative path, glob, env: name, or a label
    dependency_class: str   # one of DEPENDENCY_CLASSES
    mechanism: str          # one of MECHANISMS
    note: str = ""

    def __post_init__(self) -> None:
        if self.dependency_class not in DEPENDENCY_CLASSES:
            raise ValueError(f"unknown dependency class {self.dependency_class!r}")
        if self.mechanism not in MECHANISMS:
            raise ValueError(f"unknown mechanism {self.mechanism!r}")


#: Condition A, made mechanical. Every class appears; every entry names the
#: mechanism that constrains it. Repository paths not covered by a governed
#: prefix must appear here exactly, or the read-set test refuses them.
DEPENDENCY_REGISTER: tuple = (
    Dependency("src/**", "REPO_FILE", "GOVERNED_IDENTITY",
               "production code; blob OIDs at the authorized commit"),
    Dependency("scripts/**", "REPO_FILE", "GOVERNED_IDENTITY"),
    Dependency("tests/*.py minus tests/tiers.py GOVERNANCE_FILES", "REPO_FILE",
               "GOVERNED_IDENTITY", "tier A/B tests protect research numbers"),
    Dependency("tests/conftest.py", "REPO_FILE", "GOVERNED_IDENTITY",
               "defines the suite-wide guards and the tier markers"),
    Dependency("tests/tiers.py", "REPO_FILE", "GOVERNED_IDENTITY",
               "defines which tests the run gate executes"),
    Dependency("gate1/**", "REPO_FILE", "GOVERNED_IDENTITY",
               "frozen inputs, snapshots, flags"),
    Dependency("gate1/f10_event_calendar/f10_events.csv", "CALENDAR",
               "GOVERNED_IDENTITY", "the frozen event table"),
    Dependency("gate1/symbology/nq_v0_mapping.csv", "CALENDAR",
               "GOVERNED_IDENTITY", "the frozen roll mapping S0-T001 used"),
    Dependency("gate1/G9_RESOLVED.flag", "EXTERNAL_CONFIG",
               "EXISTENCE_FLAG_GATE", "existence is the whole input"),
    Dependency("ops/SECOND_COPY_ATTESTED.flag", "EXTERNAL_CONFIG",
               "EXISTENCE_FLAG_GATE", "existence is the whole input"),
    Dependency("ops/requirements.lock.txt", "REPO_FILE", "GOVERNED_IDENTITY",
               "also the reference of the LOCKFILE_GATE"),
    Dependency(".python-version", "REPO_FILE", "GOVERNED_IDENTITY",
               "also the reference of the PYTHON_VERSION_GATE"),
    Dependency("ops/S0_T001_POST_RUN_ATTESTATION.md", "REPO_FILE",
               "CODE_PINNED_HASH", "consumer.ATTESTATION_PATH pins its sha256"),
    Dependency("PROJECT_CHARTER.md", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES"),
    Dependency("STUDY_0_PREREGISTRATION.md", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES"),
    Dependency("purchase_plan.yaml", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES"),
    Dependency("MC_METHOD_SPEC.md", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES"),
    Dependency("gate1/platform_params.yaml", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES (also inside gate1/ identity)"),
    Dependency("gate1/evidence_registry.yaml", "REPO_FILE", "FROZEN_HASH",
               "guards.FROZEN_HASHES (also inside gate1/ identity)"),
    Dependency("gate1/snapshots/2026-07-28/snapshot_manifest_v5.json",
               "REPO_FILE", "FROZEN_HASH", "guards.FROZEN_HASHES"),
    Dependency("env:" + ",".join(HOSTILE_ENV_VARS), "ENV_VAR",
               "ENVIRONMENT_GATE", "any of them set -> environment unpinned"),
    Dependency("python interpreter", "RUNTIME", "PYTHON_VERSION_GATE",
               "major.minor must equal .python-version"),
    Dependency("installed packages", "PACKAGE", "LOCKFILE_GATE",
               "every name==version in the lockfile must be installed at "
               "exactly that version"),
    Dependency("pandas_market_calendars CME_Equity", "CALENDAR",
               "LOCKFILE_GATE", "the exchange calendar is package data"),
    Dependency("AUTHORIZED_JOB_DIR/manifest.json", "DATA_IDENTITY",
               "DATA_MANIFEST", "production_inputs pins its sha256"),
    Dependency("AUTHORIZED_JOB_DIR/*.dbn.zst", "DATA_IDENTITY",
               "DATA_MANIFEST", "load_real verifies each file's sha256"),
    Dependency("AUTHORIZED_JOB_DIR/condition.json", "DATA_IDENTITY",
               "DATA_MANIFEST", "verified before it is read (I1, Condition A)"),
    Dependency("sealed S0-T001 bundle (14 files)", "DATA_IDENTITY",
               "CUSTODY_BATTERY", "real_input.prepare_supplement_mc_input"),
    Dependency("external event registry (itsf-registry repository)",
               "EXTERNAL_CONFIG", "REGISTRY_CHAIN_GATE",
               "resolved once through registry_boundary; witness chain in "
               "registry-witness/itsf"),
    Dependency("git executable", "RUNTIME", "NOT_SEMANTIC",
               "rev-parse / status / ls-tree output is version-stable and "
               "carries no research semantics"),
    Dependency("temporary directories", "RUNTIME", "NOT_SEMANTIC",
               "scratch only; never an input"),
)

_GOVERNED_PREFIXES = ("src/", "scripts/", "gate1/")
_GOVERNED_EXACT = frozenset({"ops/requirements.lock.txt", ".python-version",
                             "tests/conftest.py", "tests/tiers.py"})


# ---------------------------------------------------------------------------
# git plumbing (read-only)
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if out.returncode != 0:
        raise IdentityError("git %s failed: %s"
                            % (" ".join(args), (out.stderr or "").strip()[:200]))
    return out.stdout


def governance_files_at(commit: str, repo: Path = REPO) -> frozenset:
    """`GOVERNANCE_FILES` from tests/tiers.py AS COMMITTED at `commit`.

    Parsed with `ast`, never executed: the bytes of a past commit are data.
    Absent tiers.py (every commit before P4 of the QROS-CF window) means no
    file is governance, i.e. EVERY test file is governed -- the inclusive,
    fail-closed reading."""
    try:
        source = _git(repo, "show", f"{commit}:tests/tiers.py")
    except IdentityError:
        return frozenset()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "GOVERNANCE_FILES" in targets:
                value = ast.literal_eval(node.value)
                return frozenset(str(v) for v in value)
    return frozenset()


def governed_entries(commit: str, repo: Path = REPO) -> tuple:
    """((path, blob_oid), ...) for every governed tracked file at `commit`,
    sorted by path. ONE `git ls-tree` call."""
    listing = _git(repo, "ls-tree", "-r", "--full-tree", commit, "--",
                   *STATIC_GOVERNED, "tests")
    governance = governance_files_at(commit, repo)
    entries = []
    for line in listing.splitlines():
        if not line.strip():
            continue
        meta, path = line.split("\t", 1)
        _mode, kind, oid = meta.split()
        if kind != "blob":
            continue
        if path.startswith("tests/"):
            name = path[len("tests/"):]
            if path in _GOVERNED_EXACT:
                pass
            elif "/" in name or not name.endswith(".py"):
                continue                    # nothing but top-level .py is a test here
            elif name in governance:
                continue                    # tier C: outside the identity
        entries.append((path, oid))
    return tuple(sorted(entries))


@_dc.dataclass(frozen=True)
class ExecutionIdentity:
    commit: str
    entries: tuple          # ((path, oid), ...) sorted
    digest: str             # sha256 over the canonical entry list

    @property
    def paths(self) -> tuple:
        return tuple(p for p, _o in self.entries)


def identity_at(commit: str, repo: Path = REPO) -> ExecutionIdentity:
    entries = governed_entries(commit, repo)
    canonical = "\n".join(f"{p}\t{o}" for p, o in entries).encode("utf-8")
    return ExecutionIdentity(commit=commit, entries=entries,
                             digest=hashlib.sha256(canonical).hexdigest())


@_dc.dataclass(frozen=True)
class IdentityComparison:
    matches: bool
    head_commit: str
    authorized_commit: str
    head_digest: str = ""
    authorized_digest: str = ""
    differing: tuple = ()
    error: str = ""

    @property
    def detail(self) -> str:
        if self.error:
            return f"identity could not be measured: {self.error}"
        if self.matches:
            return (f"governed-execution identity {self.head_digest[:12]} equal "
                    f"at {self.authorized_commit[:12]} and HEAD "
                    f"{self.head_commit[:12]}")
        shown = ", ".join(self.differing[:5])
        more = "" if len(self.differing) <= 5 else f" (+{len(self.differing) - 5})"
        return (f"governed-execution identity differs between authorized "
                f"{self.authorized_commit[:12]} and HEAD {self.head_commit[:12]}: "
                f"{shown}{more}")


def compare(head_commit: str, authorized_commit: str,
            repo: Path = REPO) -> IdentityComparison:
    """Fail-closed: any failure to compute either side is `matches=False`."""
    try:
        head = identity_at(head_commit, repo)
        auth = identity_at(authorized_commit, repo)
    except IdentityError as exc:
        return IdentityComparison(False, head_commit, authorized_commit,
                                  error=str(exc))
    if head.entries == auth.entries:
        return IdentityComparison(True, head_commit, authorized_commit,
                                  head.digest, auth.digest)
    a, b = dict(head.entries), dict(auth.entries)
    differing = tuple(sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p)))
    return IdentityComparison(False, head_commit, authorized_commit,
                              head.digest, auth.digest, differing)


# ---------------------------------------------------------------------------
# environment pin
# ---------------------------------------------------------------------------

@_dc.dataclass(frozen=True)
class EnvironmentReport:
    pinned: bool
    detail: str
    packages_checked: int = 0


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _installed_version(name: str) -> str | None:
    import importlib.metadata as md
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def measure_environment(*, lockfile: Path = LOCKFILE,
                        python_version_file: Path = PYTHON_VERSION_FILE,
                        environ=None, version_of=None,
                        running=None) -> EnvironmentReport:
    """Compare the running environment with the pinned one. Injectable for
    tests; production calls it bare."""
    env = os.environ if environ is None else environ
    version_of = _installed_version if version_of is None else version_of
    running = sys.version_info[:2] if running is None else tuple(running)
    problems = []

    hostile = [v for v in HOSTILE_ENV_VARS if env.get(v)]
    if hostile:
        problems.append(f"override variables set: {hostile}")

    try:
        want_py = python_version_file.read_text(encoding="utf-8").strip()
        major, minor = (int(x) for x in want_py.split(".")[:2])
        if tuple(running[:2]) != (major, minor):
            problems.append(f"python {running[0]}.{running[1]} != "
                            f".python-version {want_py}")
    except Exception as exc:                                  # noqa: BLE001
        problems.append(f".python-version unreadable: {exc}")

    checked = 0
    try:
        text = lockfile.read_text(encoding="utf-8-sig")
    except Exception as exc:                                  # noqa: BLE001
        problems.append(f"lockfile unreadable: {exc}")
        text = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, want = (s.strip() for s in line.split("==", 1))
        got = version_of(name)
        if got is None:
            got = version_of(_normalise(name))
        checked += 1
        if got != want:
            problems.append(f"{name}: installed {got!r} != locked {want!r}")
    if checked == 0:
        problems.append("lockfile pins no package")

    if problems:
        return EnvironmentReport(False, "; ".join(problems), checked)
    return EnvironmentReport(
        True, f"python {running[0]}.{running[1]}; {checked} packages match "
              f"{lockfile.name}; no override variable set", checked)


def measure_for_context(head_commit: str, chain, repo: Path = REPO):
    """`(IdentityComparison | None, EnvironmentReport)` for a gate context.

    The comparison is None when the chain does not carry exactly one live
    authorization -- the liveness gate refuses before identity matters --
    or when the authorized commit equals HEAD (nothing to compare)."""
    env = measure_environment()
    live = tuple(getattr(chain, "live_authorizations", ()) or ())
    if len(live) != 1:
        return (None, env)
    authorized = (getattr(live[0], "authorized_commit", "") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", authorized) or authorized == head_commit:
        return (None, env)
    return (compare(head_commit, authorized, repo), env)


# ---------------------------------------------------------------------------
# dependency coverage and the seam re-check
# ---------------------------------------------------------------------------

def covering_mechanism(repo_relative: str, governance=()) -> str | None:
    """Which mechanism constrains a repository path, or None (uncovered)."""
    rel = repo_relative.replace("\\", "/")
    if rel in _GOVERNED_EXACT or any(rel.startswith(p) for p in _GOVERNED_PREFIXES):
        return "GOVERNED_IDENTITY"
    if rel.startswith("tests/") and rel.endswith(".py") and "/" not in rel[6:]:
        return None if rel[6:] in governance else "GOVERNED_IDENTITY"
    for dep in DEPENDENCY_REGISTER:
        if dep.locator == rel:
            return dep.mechanism
    return None


def governed_dirty_paths(repo: Path = REPO, head_commit: str | None = None) -> tuple:
    """`git status --porcelain` paths that fall inside the governed set."""
    head = head_commit or _git(repo, "rev-parse", "HEAD").strip()
    governance = governance_files_at(head, repo)
    dirty = []
    for line in _git(repo, "status", "--porcelain").splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if covering_mechanism(path, governance) == "GOVERNED_IDENTITY":
            dirty.append(path)
    return tuple(sorted(dirty))


def seam_recheck(expected_head: str, repo: Path = REPO, *,
                 environment=None) -> None:
    """Re-verify at the first-write seam what A_PRECHECK verified earlier.

    Closes the check-then-replace race Condition A names: between the
    precheck and the first side effect, HEAD may move, a governed file may
    be edited, or the environment may change. Raises `SeamRefused`."""
    head = _git(repo, "rev-parse", "HEAD").strip()
    if head != expected_head:
        raise SeamRefused("seam_head_moved",
                          f"HEAD is {head[:12]}, the precheck saw "
                          f"{expected_head[:12]}")
    dirty = governed_dirty_paths(repo, head)
    if dirty:
        raise SeamRefused("seam_governed_tree_dirty",
                          f"{len(dirty)} governed path(s) modified since the "
                          f"precheck: {list(dirty)[:3]}")
    env = measure_environment() if environment is None else environment
    if not env.pinned:
        raise SeamRefused("seam_environment_unpinned", env.detail)
