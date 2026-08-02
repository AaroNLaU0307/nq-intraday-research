"""Final-candidate secret / placeholder / skip scans (Aaron M5-T5 §6).

Exit 0 = CLEAN, exit 1 = findings printed. Deterministic over `git ls-files`
so the final-readiness auditor can re-run it byte-identically at the
candidate commit.

Every exclusion below is STRUCTURAL and disclosed here — none is a
finding-specific waiver:

  E1  Secret values cannot contain whitespace: the credential-assignment
      pattern requires a 12+ char token with no spaces. This is what makes
      the F-05 sealing-test fixtures (`secret = "trading day ..."`) a
      non-match: they are sentences, not credentials.
  E2  (removed after SA-12) — the packet's TO_BE_SUPPLIED_BY_AARON literal
      never matched PH_PAT, so the packet is scanned like any other file.
  E3  ops/M4_TASKBOARD/, ops/M5_RUNNER_TASKBOARD/ and
      M5_T1_T2_INTEGRATION_REPORT.md are sealed historical audit records
      that quote scan patterns and findings verbatim.
  E4  src/itsf/mc/ is the Monte-Carlo milestone; several of its modules are
      deliberately deferred and raise NotImplementedError to fail CLOSED if
      ever invoked early. The exemption below is IMPORT-CLOSURE-DERIVED, not
      a blanket path prefix: `production_import_closure()` walks
      scripts/s0_real_run.py's imports (via `ast`, restricted to
      src/itsf/**), and only an src/itsf/mc/ file OUTSIDE that closure keeps
      the placeholder exemption. src/itsf/mc/bootstrap.py IS in the closure
      (itsf.s0.stats imports itsf.mc.bootstrap.stationary_bootstrap_indices)
      and is scanned like any other production file — no exemption;
      itsf.mc.account / itsf.mc.orchestrator / itsf.mc.platforms /
      itsf.mc.verdict are not reached from scripts/s0_real_run.py by any
      import path today (verified by the same walker) and stay exempt.
      (M6.1.1 S2: the previous text here claimed "zero itsf.mc references in
      scripts/s0_real_run.py, src/itsf/s0/, contracts.py, guards.py" — that
      was already false by the time it was read, since itsf.s0.stats had
      added its itsf.mc.bootstrap import; a hand-verified count goes stale
      silently, so the walker recomputes the real answer at scan time
      instead.)
  E5  A line that QUOTES a marker in order to forbid it is a guard, not a
      placeholder: negative assertions (`... "NotImplementedError" not in
      src`) and the SAN.6 gate docstring that names it.
  E6  `pytest.skip(... not generated yet)` in tests/test_preflight.py are
      artifact-presence guards for fresh clones. They are excluded from the
      static scan ONLY because the battery separately proves 0 tests
      skipped at the candidate commit (pytest -rs runtime evidence) — the
      skip branches are dead where it matters.
  E7  This scanner's own pattern-definition lines.
"""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys

HISTORICAL = ("ops/M4_TASKBOARD/", "ops/M5_RUNNER_TASKBOARD/")          # E3
HISTORICAL_FILES = {"M5_T1_T2_INTEGRATION_REPORT.md"}                   # E3

KEY_PAT = re.compile(r"db-[A-Za-z0-9]{20,}")
ASSIGN_PAT = re.compile(                                                # E1
    r"""(?i)(api[_-]?key|secret|token|passwd|password)"""
    r"""\s*[:=]\s*['"][^'"$\{<\s]{12,}['"]""")
PH_PAT = re.compile(
    r"TODO|FIXME|XXX\b|TBD\b|PLACEHOLDER|NotImplementedError")
GUARD_PAT = re.compile(r"not in src|no NotImplementedError")            # E5
SKIP_PAT = re.compile(
    r"pytest\.mark\.skip|pytest\.skip\(|unittest\.skip|@skip\b|xfail")
SKIP_GUARD = re.compile(r"pytest\.skip\([^)]*not generated yet")        # E6
SELF = ("_PAT", "re.compile")                                           # E7


# ===========================================================================
# E4 — real production import closure (M6.1.1 §7)
# ===========================================================================

def _module_file(module: str, src_root: pathlib.Path) -> pathlib.Path | None:
    """Dotted `itsf.*` module name -> its source file under `src_root`, or
    None if `module` is outside the itsf namespace or resolves to nothing.
    Anything outside `itsf.**` (numpy, pandas_market_calendars, stdlib, ...)
    is unresolvable BY CONSTRUCTION — the closure is "restricted to
    src/itsf/**" because nothing else can ever match here, not because of an
    exclusion list."""
    if module != "itsf" and not module.startswith("itsf."):
        return None
    rel = pathlib.Path(*module.split("."))
    py_file = src_root / rel.with_suffix(".py")
    if py_file.is_file():
        return py_file
    pkg_init = src_root / rel / "__init__.py"
    if pkg_init.is_file():
        return pkg_init
    return None


def _ast_imported_module_names(py_path: pathlib.Path) -> set[str]:
    """Every dotted module name referenced by an `import ...` or
    `from ... import ...` statement ANYWHERE in `py_path` — module level or
    nested inside a function/branch, since this codebase imports most of its
    itsf.* dependencies lazily (scripts/s0_real_run.py imports itsf.s0.stats
    and itsf.s0.gridmix inside a function body, for example). Pure
    `ast.parse`: the file is never imported/executed, so a stub's
    NotImplementedError body or a heavy optional dependency can neither fire
    nor break the walk.
    """
    tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"),
                     filename=str(py_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:            # relative import; unused in this repo
                continue
            if node.module:
                names.add(node.module)
                # `from itsf.mc import account as acct` also names the
                # SUBMODULE `account`, not just an attribute of `itsf.mc` —
                # record the joined form too so this idiom resolves exactly
                # like `import itsf.mc.account`.
                for alias in node.names:
                    names.add(f"{node.module}.{alias.name}")
    return names


def production_import_closure(entry: pathlib.Path, src_root: pathlib.Path,
                              ) -> dict[str, pathlib.Path]:
    """dotted itsf.** module name -> resolved file, for every itsf module
    `entry` (scripts/s0_real_run.py in production) reaches by import,
    TRANSITIVELY, at any nesting depth. See module docstring E4: this
    replaces a stale hand-verified claim with a walker that recomputes the
    real answer at scan time, and is what src/itsf/mc/'s placeholder
    exemption is now derived from instead of a blanket path prefix.
    """
    closure: dict[str, pathlib.Path] = {}
    frontier: list[pathlib.Path] = [entry]
    walked: set[pathlib.Path] = set()
    while frontier:
        path = frontier.pop()
        if path in walked or not path.is_file():
            continue
        walked.add(path)
        for name in _ast_imported_module_names(path):
            resolved = _module_file(name, src_root)
            if resolved is None:
                continue
            closure.setdefault(name, resolved)
            if resolved not in walked:
                frontier.append(resolved)
    return closure


def main(repo_root: pathlib.Path | str | None = None) -> int:
    # M6.1 (Codex §5.3): tracked files PLUS untracked-unignored ones — an
    # untracked repo-root file is exactly what tripped SA-16's OPEN-1, and
    # secrets/placeholders must not hide in not-yet-added files either.
    # `repo_root` defaults to the current working directory (production
    # usage); a mutation test points it at a scratch git repo instead.
    root = pathlib.Path(repo_root) if repo_root is not None else pathlib.Path(".")
    tracked = subprocess.run(["git", "ls-files"], capture_output=True,
                             text=True, check=True, cwd=root).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True,
        cwd=root).stdout.splitlines()
    files = tracked + untracked
    texts = [f for f in files if f.endswith(
        (".py", ".md", ".yaml", ".yml", ".toml", ".txt", ".json"))]
    fails: list[str] = []

    entry = root / "scripts" / "s0_real_run.py"
    closure = (production_import_closure(entry, root / "src")
              if entry.is_file() else {})
    closure_files = {p.relative_to(root).as_posix() for p in closure.values()}

    for f in texts:
        body = (root / f).read_text(encoding="utf-8", errors="replace")
        name = pathlib.Path(f).name

        # --- secrets: scanned EVERYWHERE, no path exclusions -------------
        for m in KEY_PAT.finditer(body):
            fails.append(f"SECRET {f}: databento-shaped literal "
                         f"{m.group()[:8]}…")
        for m in ASSIGN_PAT.finditer(body):
            line = m.group(0)
            if "PLACEHOLDER" in line or "example" in line.lower():
                continue
            fails.append(f"SECRET {f}: credential assignment: {line[:60]}")

        # --- placeholders ------------------------------------------------
        # E4: an src/itsf/mc/ file is exempt ONLY when the real production
        # import closure (computed above) does not reach it — NOT for every
        # file under that path prefix.
        mc_deferred_stub = (f.startswith("src/itsf/mc/")
                            and f not in closure_files)
        if (name not in HISTORICAL_FILES
                and not f.startswith(HISTORICAL)
                and not mc_deferred_stub                                # E4
                and f != "scripts/final_candidate_scans.py"):           # E7
            for i, line in enumerate(body.splitlines(), 1):
                if not PH_PAT.search(line):
                    continue
                if any(s in line for s in SELF) or GUARD_PAT.search(line):
                    continue
                fails.append(f"PLACEHOLDER {f}:{i}: {line.strip()[:70]}")

        # --- muted tests --------------------------------------------------
        if f.startswith("tests/"):
            for i, line in enumerate(body.splitlines(), 1):
                if (SKIP_PAT.search(line)
                        and not any(s in line for s in SELF)
                        and not SKIP_GUARD.search(line)):
                    fails.append(f"SKIP {f}:{i}: {line.strip()[:70]}")

    if fails:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print("\n".join(fails))
        print(f"SCANS=FAIL ({len(fails)})")
        return 1
    print("SCANS=CLEAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
