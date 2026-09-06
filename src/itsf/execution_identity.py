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
from types import MappingProxyType

__all__ = [
    "REPO", "STATIC_GOVERNED", "GOVERNED_TEST_FILES_ALWAYS",
    "HOSTILE_ENV_VARS", "DEPENDENCY_CLASSES", "MECHANISMS",
    "Dependency", "DEPENDENCY_REGISTER",
    "ExecutionIdentity", "IdentityComparison", "EnvironmentReport",
    "SeamRefused", "IdentityError",
    "governance_files_at", "governed_entries", "identity_at", "compare",
    "measure_environment", "measure_for_context", "covering_mechanism",
    "governed_dirty_paths", "seam_recheck",
    "BytecodeReport", "bytecode_report",
    "StartupReport", "startup_report", "EXPECTED_EXECUTABLE_PTH",
    "LaunchAttestation", "assert_governed_launch", "launch_attestation",
    "BOOTSTRAP_IMPORT_CLOSURE", "LAUNCH_FLAGS_REQUIRED",
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


#: The `.pth` files in this machine's site directories that carry an
#: executable `import` line, censused 2026-09-07 and required by installed
#: packages the lockfile pins -- MAPPED TO THE SHA256 OF THEIR BYTES.
#:
#: QROS-CF F02, SECOND ROUND. The first repair censused these by FILENAME,
#: and the re-review named the hole precisely: a filename allowlist accepts
#: arbitrary content under an allowed name. Reproduced 2026-09-07 on the
#: repaired tree -- `a1_coverage.pth` rewritten to `import hook_payload`
#: executed an attacker's module at startup while `startup_report` still
#: answered `pinned=True`. A `.pth` is executable code; its identity is its
#: bytes, and only its bytes.
#:
#: WHY BYTES AND NOT SUPPRESSION. Launching with `-S` stops `.pth`
#: processing outright and would close this finding by construction. It was
#: measured first and it is not available: under `-S` (and under `-I`, which
#: implies it) `import pandas` fails outright, so suppression trades a
#: startup surface for the pinned environment itself. Content pinning is the
#: mechanism that survives the measurement.
#:
#: WHAT EACH ONE IS, so the pin is reviewable rather than two magic digests:
#:   * `pip_system_certs.pth` imports `pip_system_certs.bootstrap`, and that
#:     package IS version-pinned in the lockfile (`pip_system_certs==5.3`),
#:     so the entry point is pinned here and the code it reaches is pinned
#:     there.
#:   * `a1_coverage.pth` executes coverage's subprocess startup ONLY when
#:     `COVERAGE_PROCESS_START` or `COVERAGE_PROCESS_CONFIG` is set, and
#:     swallows an absent `coverage`. Its bytes are pinned here; the env
#:     gate is reported by `startup_report` rather than refused, because
#:     `coverage` measures this project's own test suite and refusing the
#:     variable would break the measurement rather than the threat.
#:
#: A pinned file that is ABSENT is not a problem -- nothing executes. A
#: pinned name whose bytes differ, or any unlisted executable `.pth`, is.
EXPECTED_EXECUTABLE_PTH = MappingProxyType({
    "a1_coverage.pth":
        "f1498191b7f52180654ccdb6195233612805e26344100c093058343ea04afd36",
    "pip_system_certs.pth":
        "da91bb35c03c2131243d09401f1351a12716d54fbbce0347b5749b822d5493ef",
})

#: Modules the interpreter imports automatically at startup if they are
#: importable. Neither exists on this machine and neither may appear.
FORBIDDEN_STARTUP_MODULES = ("sitecustomize", "usercustomize")


@_dc.dataclass(frozen=True)
class StartupReport:
    pinned: bool
    detail: str
    executable_pth: tuple = ()


def startup_report(*, sitedirs=None, find_spec=None) -> StartupReport:
    """Constrain the startup/import surfaces that can change semantics.

    QROS-CF F02. Reproduced 2026-09-07: a `.pth` file whose line begins
    `import ` executes at interpreter startup, so it can rebind calendar or
    runtime behaviour before a single gate runs -- while every one of the 49
    locked package versions still matches and `measure_environment` reports
    `pinned=True`. Version metadata is not a control over executable code.

    TRUST IS BY BYTES, NOT BY FILENAME (F02, second round). The first
    repair allowed two `.pth` names; the re-review reproduced an allowed
    name carrying arbitrary executable content. Every executable `.pth` is
    now hashed and matched against `EXPECTED_EXECUTABLE_PTH`, so an allowed
    name with changed bytes refuses exactly like an unlisted one.

    DELIBERATELY NOT A MACHINE HASH. Only the surfaces that actually execute
    in this process at startup are constrained: `.pth` files carrying an
    `import` line, and the two automatic startup modules. Data-only `.pth`
    files (bare path lines) add import PATHS, which `HOSTILE_ENV_VARS`
    already covers for the variable case and which cannot execute on their
    own, so they are listed but not refused.

    Required packages are preserved: the pin is the census of what is
    genuinely installed and needed, not an empty set.
    """
    import importlib.util
    import site
    if sitedirs is None:
        cand = list(site.getsitepackages())
        if site.ENABLE_USER_SITE:
            try:
                cand.append(site.getusersitepackages())
            except Exception:                                 # noqa: BLE001
                pass
        sitedirs = [p for p in dict.fromkeys(cand) if Path(p).is_dir()]
    find_spec = importlib.util.find_spec if find_spec is None else find_spec

    problems = []
    executable = []
    for sd in sitedirs:
        for pth in sorted(Path(sd).glob("*.pth")):
            try:
                lines = pth.read_text(encoding="utf-8",
                                      errors="replace").splitlines()
            except Exception as exc:                          # noqa: BLE001
                problems.append(f"{pth.name} unreadable: {exc}")
                continue
            if any(ln.strip().startswith(("import ", "import\t"))
                   for ln in lines):
                executable.append(pth.name)
                # F02: the name is not the identity. Hash what will execute.
                got = hashlib.sha256(pth.read_bytes()).hexdigest()
                want = EXPECTED_EXECUTABLE_PTH.get(pth.name)
                if want is None:
                    problems.append(
                        "unexpected executable .pth: %s (sha %s)"
                        % (pth.name, got[:12]))
                elif got != want:
                    problems.append(
                        "executable .pth %s has changed content: pinned %s..., "
                        "found %s... -- an allowed NAME is not an allowed FILE"
                        % (pth.name, want[:12], got[:12]))
    for name in FORBIDDEN_STARTUP_MODULES:
        try:
            if find_spec(name) is not None:
                problems.append(f"{name} is importable and runs at startup")
        except Exception:                                     # noqa: BLE001
            problems.append(f"{name} probe failed")
    if problems:
        return StartupReport(False, "; ".join(problems), tuple(sorted(executable)))
    return StartupReport(
        True, "startup surface pinned: executable .pth %s; no sitecustomize "
              "or usercustomize" % sorted(set(executable)),
        tuple(sorted(executable)))


@_dc.dataclass(frozen=True)
class BytecodeReport:
    """Whether this process could have executed a pre-existing governed
    bytecode cache."""
    from_source: bool
    detail: str
    caches_found: int = 0


def bytecode_report(repo: Path = REPO, *, dont_write=None, prefix=None,
                    governed_sources=None) -> BytecodeReport:
    """Can a pre-existing `.pyc` have supplied this process's semantics?

    QROS-CF F01. The governed identity is built from git-tracked blobs and
    `__pycache__/` is `.gitignore` line 1, so no cache file is in the
    identity, `git status` never reports one, and `seam_recheck`'s dirty-path
    check cannot see one. Reproduced 2026-09-07: a `.pyc` whose 16-byte
    header still matched its untouched source, carrying different bytecode,
    executed -- `rth_close_minute()` returned 1 where the authorized source
    says 960, with source bytes, identity and dirty paths all clean.

    WHY THIS CHECKS THE LAUNCH CONDITIONS AND NOT THE CACHE CONTENT. The
    other acceptable direction -- validate each cache against a fresh
    compilation -- was implemented and measured first, and it does not hold:
    `marshal.dumps` of an equal code object is not byte-stable (interning
    order), a structural digest needs `co_lnotab`, which is deprecated, and
    both produced mismatches on files nobody had touched (3 and 7 of 68).
    A gate that false-refuses is worse than none, so the mechanism is the
    one that is decidable: run so that no pre-existing cache CAN be read.

    THE THREE FACTS, together sufficient. `-B` (`sys.dont_write_bytecode`)
    means this process writes no cache; `sys.pycache_prefix` moves every
    lookup away from the repository's `__pycache__` directories; and if no
    cache file exists under that prefix for any governed source, then none
    was read, because reading one requires it to exist. Measured: under an
    empty private prefix the tampered cache above is ignored and the
    authorized source semantics execute.
    """
    dont_write = sys.dont_write_bytecode if dont_write is None else dont_write
    prefix = sys.pycache_prefix if prefix is None else prefix
    problems = []
    if not dont_write:
        problems.append("sys.dont_write_bytecode is False (launch with -B)")
    if not prefix:
        problems.append("sys.pycache_prefix is unset (launch with "
                        "PYTHONPYCACHEPREFIX pointing at a private "
                        "directory)")
    found = 0
    if prefix:
        import importlib.util
        sources = (sorted((repo / "src").rglob("*.py"))
                   if governed_sources is None else list(governed_sources))
        present = []
        for s in sources:
            cache = Path(importlib.util.cache_from_source(str(s)))
            if cache.exists():
                found += 1
                if len(present) < 3:
                    present.append(cache.name)
        if found:
            problems.append(
                "%d governed source(s) already have a cache under the active "
                "prefix (%s...) -- a cache that exists can be read"
                % (found, ", ".join(present)))
    if problems:
        return BytecodeReport(False, "; ".join(problems), found)
    return BytecodeReport(
        True, "no readable governed bytecode cache: -B set, pycache_prefix "
              "%s, 0 cache files for governed sources" % prefix, 0)


#: The only modules that are necessarily already imported when the launch
#: attestation is taken, because the attestation function lives in one of
#: them. Measured, not assumed: `src/itsf/__init__.py` is 0 bytes, so
#: importing this module pulls in exactly these two.
BOOTSTRAP_IMPORT_CLOSURE = frozenset({"itsf", "itsf.execution_identity"})

#: The MINIMUM COMPATIBLE launch semantics, measured 2026-09-07 rather than
#: copied from a hardening guide:
#:
#:   -B                     -> sys.flags.dont_write_bytecode == 1, READ-ONLY
#:   PYTHONPYCACHEPREFIX=D  -> every cache lookup leaves the repo tree
#:
#: and explicitly NOT these, each of which was tried and rejected on
#: measurement:
#:   -S  `import pandas` fails    (it would also close F02, and cannot be used)
#:   -I  implies -s -E, same failure
#:   -E  ignores PYTHONPYCACHEPREFIX, so the prefix silently goes unset and
#:       the repository's own __pycache__ becomes readable again
LAUNCH_FLAGS_REQUIRED = ("-B", "PYTHONPYCACHEPREFIX")


@_dc.dataclass(frozen=True)
class LaunchAttestation:
    """Proof, taken BEFORE the governed imports, that no pre-existing
    bytecode cache can have supplied this process's semantics."""
    pycache_prefix: str
    caches_under_prefix: int
    detail: str


_LAUNCH_ATTESTATION: "LaunchAttestation | None" = None


def launch_attestation() -> "LaunchAttestation | None":
    """The attestation this process took, or None if it never took one."""
    return _LAUNCH_ATTESTATION


def assert_governed_launch(*, flags=None, prefix=None,
                           modules=None) -> LaunchAttestation:
    """Establish, before any governed import, that this process cannot have
    executed a pre-existing governed bytecode cache. Raises `SeamRefused`.

    QROS-CF F01, SECOND ROUND. The first repair took a CENSUS at the seam --
    are there cache files under the active prefix right now -- and the
    re-review broke it in one move: the attacker deletes the forged cache
    after it has executed and before the census runs. Reproduced 2026-09-07
    on the repaired tree: a tampered cache returned 1 where the source says
    960, the file was removed, and `bytecode_report` then answered
    `from_source=True`. A current-state census cannot prove a historical
    negative, and no amount of strengthening the census fixes that.

    SO THE PROOF MOVED EARLIER INSTEAD OF GETTING STRONGER. Three facts,
    taken together and taken BEFORE the governed modules are imported:

      1. `sys.flags.dont_write_bytecode` is set. This is the LAUNCH flag on
         the read-only `sys.flags` structseq -- measured: assigning to it
         raises AttributeError. The first repair read `sys.dont_write_bytecode`,
         the plain writable mirror, which in-process code can set at will.
         So: this process writes no cache, and cannot pretend to.
      2. `sys.pycache_prefix` names an existing directory holding zero
         `.pyc` files. Every cache lookup for a governed source therefore
         resolves under a tree that contains nothing to read.
      3. No governed `itsf.*` module beyond `BOOTSTRAP_IMPORT_CLOSURE` is in
         `sys.modules` yet. This is the fact that makes 1 and 2 a PROOF
         rather than an observation: at this instant no governed module has
         been imported, so there is no earlier window whose evidence could
         have been deleted. Every governed import happens after this line,
         under a process that cannot write caches into a tree that has none.

    WHAT REMAINS, STATED RATHER THAN HIDDEN. A pre-planted file cannot be
    read, because the launcher creates the prefix fresh per run at a path
    nobody can predict. What is left is an adversary WRITING into that
    private directory concurrently with the governed process -- active
    concurrent code, not the on-disk tamper F01 is about -- and
    `sys.pycache_prefix` being reassigned mid-run, which
    `tests/test_qros_cf_astra_repairs.py` forbids by AST across all of
    `src/` and `scripts/`. Neither is a one-shot local tamper, which is the
    threat class that made F01 blocking.

    NOT A GUARD OF A GUARD. This function proves nothing about ITSELF and
    does not try to: facts 1 and 2 cover its own two modules by exactly the
    same argument they cover every later one -- nothing was written, and
    there was nothing to read.
    """
    flags = sys.flags if flags is None else flags
    prefix = sys.pycache_prefix if prefix is None else prefix
    modules = sys.modules if modules is None else modules

    if not getattr(flags, "dont_write_bytecode", 0):
        raise SeamRefused(
            "launch_bytecode_writing_enabled",
            "sys.flags.dont_write_bytecode is not set; launch with -B "
            "(the read-only launch flag, not the writable sys mirror)")
    if not prefix:
        raise SeamRefused(
            "launch_pycache_prefix_unset",
            "sys.pycache_prefix is unset; launch with PYTHONPYCACHEPREFIX "
            "pointing at a private directory created for this run")
    root = Path(prefix)
    if not root.is_dir():
        raise SeamRefused(
            "launch_pycache_prefix_absent",
            "sys.pycache_prefix %s is not a directory" % prefix)
    caches = sorted(q.name for q in root.rglob("*.pyc"))
    if caches:
        raise SeamRefused(
            "launch_pycache_prefix_not_empty",
            "%d cache file(s) already under the active prefix %s (%s); a "
            "cache that exists can be read" % (len(caches), prefix,
                                               ", ".join(caches[:3])))
    premature = sorted(name for name in list(modules)
                       if (name == "itsf" or name.startswith("itsf."))
                       and name not in BOOTSTRAP_IMPORT_CLOSURE)
    if premature:
        raise SeamRefused(
            "launch_governed_modules_already_imported",
            "%d governed module(s) were imported before the launch was "
            "attested (%s); the attestation must precede every governed "
            "import or it proves nothing about them"
            % (len(premature), ", ".join(premature[:5])))

    global _LAUNCH_ATTESTATION
    _LAUNCH_ATTESTATION = LaunchAttestation(
        str(prefix), 0,
        "attested before any governed import: -B set (read-only launch "
        "flag), pycache_prefix %s holds 0 caches, only %s imported"
        % (prefix, sorted(BOOTSTRAP_IMPORT_CLOSURE)))
    return _LAUNCH_ATTESTATION


def seam_recheck(expected_head: str, repo: Path = REPO, *,
                 environment=None, bytecode=None,
                 startup=None, launch=None) -> None:
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
    # F01: the seam is the last point before the first production write, so
    # it is where a readable governed bytecode cache must stop the run.
    bc = bytecode_report(repo) if bytecode is None else bytecode
    if not bc.from_source:
        raise SeamRefused("seam_bytecode_cache_readable", bc.detail)
    # F02: a startup hook that changed calendar or runtime semantics leaves
    # every package version matching, so the environment gate above cannot
    # see it. Checked here for the same reason.
    st = startup_report() if startup is None else startup
    if not st.pinned:
        raise SeamRefused("seam_startup_surface_unpinned", st.detail)
    # F01: the census above is a useful current-state check and it is NOT the
    # proof. The proof is the attestation taken before the governed imports,
    # and requiring it HERE is what makes the launch boundary mechanically
    # enforced rather than merely available -- this is the one production
    # call site, so a run that skipped the launcher stops before its first
    # side effect instead of producing evidence nobody can vouch for.
    la = _LAUNCH_ATTESTATION if launch is None else launch
    if la is None:
        raise SeamRefused(
            "seam_launch_not_attested",
            "no launch attestation: this process never called "
            "assert_governed_launch() before importing the governed modules, "
            "so a pre-existing bytecode cache cannot be ruled out. Launch "
            "through scripts/run_governed.py.")
