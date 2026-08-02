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
  E4  src/itsf/mc/ is the Monte-Carlo milestone: implementation is
      deliberately deferred and its stubs raise NotImplementedError to fail
      CLOSED if ever invoked early. The S0 runner-critical chain imports
      nothing from itsf.mc (verified: zero `itsf.mc` references in
      scripts/s0_real_run.py, src/itsf/s0/, contracts.py, guards.py).
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


def main() -> int:
    # M6.1 (Codex §5.3): tracked files PLUS untracked-unignored ones — an
    # untracked repo-root file is exactly what tripped SA-16's OPEN-1, and
    # secrets/placeholders must not hide in not-yet-added files either.
    tracked = subprocess.run(["git", "ls-files"], capture_output=True,
                             text=True, check=True).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    files = tracked + untracked
    texts = [f for f in files if f.endswith(
        (".py", ".md", ".yaml", ".yml", ".toml", ".txt", ".json"))]
    fails: list[str] = []

    for f in texts:
        body = pathlib.Path(f).read_text(encoding="utf-8",
                                         errors="replace")
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
        if (name not in HISTORICAL_FILES
                and not f.startswith(HISTORICAL)
                and not f.startswith("src/itsf/mc/")                    # E4
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
