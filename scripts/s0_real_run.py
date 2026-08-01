"""S0-T001 real-run entrypoint (MAIN-AGENT OWNED; zero CLI arguments).

INERT BY CONSTRUCTION until authorization: Stage-A gate #12/#13 require the
TRIAL_REGISTRY event chain to contain a RUN_AUTHORIZED event row whose note
carries Aaron's verbatim packet-§10 sentence, and HEAD to equal the 40-hex
commit named INSIDE that sentence. Neither exists today, so every invocation
terminates as a PRE_RUN_ATTEMPT_FAILURE before any data is opened (exposure
NOT consumed). Stage B additionally holds the `stage_c_wiring_activated`
gate, so even a fully authorized invocation stops BEFORE the atomic run-start
until the Stage-C wiring lands (SA-6 F-02: the old placeholder raised AFTER
the atomic transition, which would have burned S0-T001 and exposure for zero
output).

No argparse, no environment overrides (packet §5): every parameter comes
from approved artifacts on disk at the authorized commit, and every child
process (git, pytest, seal_check) runs with a scrubbed minimal environment
so PYTEST_ADDOPTS / GIT_DIR-family variables cannot weaken a gate (F-09).
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
sys.path.insert(0, str(REPO / "src"))

USES_ARGPARSE = False          # pinned by tests/test_s0_runner.py

TRIAL_ID = "S0-T001"
SEED = 20260731                # packet §5
REGISTRY = REPO / "ops" / "TRIAL_REGISTRY.md"
RUNS_ROOT = REPO / "runs"
ATTEMPTS_ROOT = REPO / "attempts"

# Baseline collected-test count at the SA-6 audit commit. The pytest gate
# requires the suite to still COLLECT at least this many tests, so a muted
# or filtered run cannot satisfy the gate with a handful of tests (F-09).
MIN_COLLECTED_TESTS = 509                  # SA-11 N-A: floor = current suite

# External read-only tooling (packet §9 gate 4). Invoked as a subprocess;
# the tool itself only reads repository files.
SEAL_CHECK_TOOL = Path(r"C:\Users\Aaron\quant-data\tools\seal_check.py")

# packet §4: A1 job directory (metadata only — the runner never opens a
# dbn.zst here; only the official manifest.json is read, and only to
# re-derive the locked set digest).
A1_JOB_DIR = Path(
    r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
    r"\development_signal\GLBX-20260727-DL3BEBCHJA")
A1_EXPECTED_FILE_COUNT = 139
A1_EXPECTED_TOTAL_BYTES = 58_711_328

# packet §4 locked input hashes (compare-only at Stage A). Repo-relative.
LOCKED = {
    "f10": ("gate1/f10_event_calendar/f10_events.csv",
            "5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c"),
    "symbology": ("gate1/symbology/nq_v0_mapping.csv",
                  "85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850"),
    "spread": ("spread_cost_table.csv",
               "b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf"),
    "attestation": ("ops/physical_copy_attestation.json",
                    "51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813"),
    # SA-6 F-07: the assertion FILE itself must be hash-locked, otherwise the
    # Stage-B comparison can be moved by editing the expectations.
    # M5-T5 re-lock: rerun under IR-22/23/24; IR-24 divergence==0 evidenced.
    "preflight_json": ("S0_INPUT_PREFLIGHT.json",
                       "9d6dd1c15602f6188e0b85754118dd51eb81b65cd60a086a133dee1bb14debd6"),
}

# packet §4 locked inputs that live OUTSIDE the repository.
LOCKED_EXTERNAL = {
    "a1_manifest": (A1_JOB_DIR / "manifest.json",
                    "d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8"),
}

RAW_FILE_SET_SHA256 = (
    "08fca11b7a9aea1f96f740409c099696e48907a408f409dfbadd82c5ac584298")

# Structure-assertion gate (packet §9 gate 5): the frozen platform params
# must still parse as YAML and still expose exactly the recorded top-level
# key count (DATA_QA_ADDENDUM "pyyaml structure assertion" evidence block).
STRUCTURE_YAML = "gate1/platform_params.yaml"
STRUCTURE_YAML_TOP_LEVEL_KEYS = 10

# packet §10 — the ONLY authorization sentence, verbatim. `{commit}` is the
# single substitution point (a full 40-hex commit hash).
AUTHORIZATION_SENTENCE_TEMPLATE = (
    "启动第一次真实S0，授权trial_id: {trial_id}，使用commit: {commit}")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")

# Paths whose presence in `git status --porcelain` does NOT dirty the tree
# for gate 1 purposes (SA-6 F-03: the registry is append-only BY DESIGN and
# attempt/run outputs are created by the run itself, so requiring a literally
# empty porcelain made the authorization procedure unsatisfiable).
CLEAN_GATE_ALLOWLIST_FILES = ("ops/TRIAL_REGISTRY.md",)
CLEAN_GATE_ALLOWLIST_DIRS = ("attempts/", "runs/")

# Environment allowlist for every child process (F-09). Everything else —
# including GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE / GIT_CONFIG* and
# PYTEST_ADDOPTS / PYTHONPATH / PYTHONSTARTUP — is dropped.
#
# SYSTEMDRIVE / PROGRAMDATA / HOMEDRIVE / HOMEPATH are on the list for a
# concrete reason found while testing this gate: without them Windows
# expands the LITERAL string "%SystemDrive%" when a child process resolves
# a shell folder, and the child silently materialises a "%SystemDrive%"
# directory inside its cwd — which is the repository, which would then fail
# the git-clean gate on the next attempt.
_ENV_ALLOWLIST = ("SYSTEMROOT", "SystemRoot", "SYSTEMDRIVE", "SystemDrive",
                  "COMSPEC", "ComSpec", "PATH", "PATHEXT", "TEMP", "TMP",
                  "WINDIR", "windir", "NUMBER_OF_PROCESSORS",
                  "PROCESSOR_ARCHITECTURE", "PROGRAMDATA", "ProgramData",
                  "ALLUSERSPROFILE", "HOMEDRIVE", "HOMEPATH",
                  "LOCALAPPDATA", "APPDATA", "USERPROFILE", "HOME", "LANG")


def clean_env() -> dict[str, str]:
    """Minimal explicit-allowlist environment for child processes (F-09)."""
    env = {k: v for k, v in os.environ.items() if k in _ENV_ALLOWLIST}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True,
                          env=clean_env()).stdout.strip()


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8")


# =========================================================================
# registry event-table parsing (SA-6 F-01 / F-11)
# =========================================================================

def parse_registry_events(text: str) -> list[dict[str, str]]:
    """Parse ops/TRIAL_REGISTRY.md markdown event ROWS into dicts.

    Only real table rows are returned: a line must start with '|', split into
    exactly 6 cells (#, utc, event, commit, actor, note) and must not be the
    header or its separator. Prose that merely mentions an event name is NOT
    a row and can never satisfy a gate (the old `"RUN_AUTHORIZED" in text`
    substring test was satisfied by the registry's own RULES paragraph).
    """
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if set(cells[0]) <= set("-: ") and cells[0]:
            continue                                  # separator row
        if cells[0] == "#" and cells[1] == "utc":
            continue                                  # header row
        rows.append({"seq": cells[0], "utc": cells[1],
                     "event": cells[2].strip("*").strip(),
                     "commit": cells[3], "actor": cells[4], "note": cells[5]})
    return rows


def find_authorization_event(text: str, trial_id: str = TRIAL_ID
                             ) -> tuple[dict[str, str] | None, str, str]:
    """Locate the RUN_AUTHORIZED row and extract its authorized commit.

    Returns (row, commit, detail). `commit` is non-empty ONLY when a row
    whose `event` cell is EXACTLY 'RUN_AUTHORIZED' carries a note containing
    the verbatim packet-§10 sentence with a full 40-hex commit hash. Anything
    weaker — a near-miss sentence, a 7-char hash, an event mentioned in prose
    — yields ("", <why>) and therefore a failed gate.
    """
    candidates = [r for r in parse_registry_events(text)
                  if r["event"] == "RUN_AUTHORIZED"]
    if not candidates:
        return (None, "", "registry event table has no RUN_AUTHORIZED row "
                          "(packet §10 sentence not issued)")
    if len(candidates) > 1:
        return (None, "", f"registry event table has {len(candidates)} "
                          f"RUN_AUTHORIZED rows; exactly one is expected")
    row = candidates[0]
    prefix = AUTHORIZATION_SENTENCE_TEMPLATE.format(trial_id=trial_id,
                                                    commit="")
    idx = row["note"].find(prefix)
    if idx < 0:
        return (row, "", "RUN_AUTHORIZED row does not contain the verbatim "
                         "packet §10 authorization sentence")
    tail = row["note"][idx + len(prefix):]
    commit = tail[:40]
    if not _HEX40_RE.match(commit):
        return (row, "", "packet §10 sentence does not name a full 40-hex "
                         "commit hash")
    expected = AUTHORIZATION_SENTENCE_TEMPLATE.format(trial_id=trial_id,
                                                      commit=commit)
    if expected not in row["note"]:
        return (row, "", "authorization sentence is not verbatim")
    return (row, commit, "ok")


# =========================================================================
# packet §4 raw-file-set digest (SA-6 F-07)
# =========================================================================

def compute_raw_file_set_sha256(entries) -> str:
    """Packet §4 set digest: SHA256(sorted(relative_path|size|file_sha256)).

    `entries` is a sequence of (relative_path, size, file_sha256) triples
    supplied by the caller — this function performs NO I/O, so it is fully
    unit-testable on synthetic input.

    Pre-image convention RESOLVED by its author (main agent, 2026-08-01;
    DECISION_PACKET_RAW_FILE_SET_PREIMAGE.md closed as a mechanical fact,
    not a method decision — the digest was generated by the main agent's
    own recorded script): records are `f"{rel}|{size}|{sha}"`, sorted(),
    joined by '\\n' with **NO trailing newline**, UTF-8; rel = the
    manifest-declared filename of each .dbn.zst entry; sha = the manifest
    hash with its "sha256:" prefix stripped. Verified to reproduce
    08fca11b... against the real A1 manifest at integration time.
    """
    records = sorted(f"{rel}|{size}|{sha}" for rel, size, sha in entries)
    payload = "\n".join(records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def a1_manifest_entries(manifest_path: Path) -> list[tuple[str, int, str]]:
    """(relative_path, size, sha256) triples from an official Databento
    manifest.json. METADATA ONLY — no .dbn.zst byte is ever read here.

    Sizes come from the manifest when it declares them, otherwise from
    os.stat (still metadata). Any entry that yields neither a size nor a
    64-hex hash raises, so the gate fails closed rather than digesting a
    partially-understood document.
    """
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest.json has no 'files' list")
    out: list[tuple[str, int, str]] = []
    for entry in files:
        name = entry.get("filename")
        raw_hash = str(entry.get("hash", ""))
        if not name or not raw_hash.startswith("sha256:"):
            raise ValueError(f"manifest entry lacks filename/sha256: {entry!r}")
        sha = raw_hash.split(":", 1)[1]
        size = entry.get("size", entry.get("bytes"))
        if size is None:
            size = (manifest_path.parent / name).stat().st_size
        out.append((str(name), int(size), sha))
    return out


# =========================================================================
# packet §9 hard gates
# =========================================================================

def build_gates(*, repo: Path = REPO, registry: Path = REGISTRY,
                runs_root: Path = RUNS_ROOT,
                seal_check_tool: Path = SEAL_CHECK_TOOL,
                a1_manifest: Path | None = None,
                trial_id: str = TRIAL_ID):
    """Packet §9 hard gates as an ordered GateCheck list.

    Every path is a parameter so the gate LOGIC can be exercised against
    synthetic fixtures in tests without touching the real archive; production
    calls use the module defaults.
    """
    from itsf.s0.runner import GateCheck

    a1_manifest_path = (a1_manifest if a1_manifest is not None
                        else LOCKED_EXTERNAL["a1_manifest"][0])

    def g_real_run_allowed():
        # SA-6 F-34: single implementation — guards.assert_real_run_allowed()
        # already re-verifies the 7 frozen hashes AND both attestation flags,
        # so the runner must call it rather than re-deriving the same checks.
        try:
            from itsf import guards
            guards.assert_real_run_allowed()
            return (True, "guards.assert_real_run_allowed passed")
        except Exception as exc:                     # noqa: BLE001
            return (False, f"{type(exc).__name__}: {exc}")

    def g_clean():
        porcelain = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True, env=clean_env()).stdout
        offenders = [ln for ln in porcelain.splitlines()
                     if ln.strip() and not _clean_gate_exempt(ln)]
        return (not offenders,
                "; ".join(offenders) if offenders
                else "clean (registry/attempts/runs exempt)")

    def g_authorized_event():
        row, commit, detail = find_authorization_event(
            registry.read_text(encoding="utf-8"), trial_id)
        return (bool(row) and bool(commit), detail)

    def g_head_matches():
        _, commit, detail = find_authorization_event(
            registry.read_text(encoding="utf-8"), trial_id)
        if not commit:
            return (False, detail)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              env=clean_env()).stdout.strip()
        return (head == commit,
                "HEAD equals the authorized commit" if head == commit
                else "HEAD does not equal the commit named in the §10 sentence")

    def g_key_closure():
        path = repo / "M4_KEY_CLOSURE_ATTESTATION.md"
        return (path.exists(), "M4_KEY_CLOSURE_ATTESTATION.md")

    def g_inputs():
        for name, (rel, want) in LOCKED.items():
            path = repo / rel
            if not path.exists():
                return (False, f"locked input missing: {name}")
            got = _sha(path)
            if got != want:
                return (False, f"input hash drift: {name} {got[:16]}...")
        for name, (path, want) in LOCKED_EXTERNAL.items():
            target = a1_manifest_path if name == "a1_manifest" else path
            if not target.exists():
                return (False, f"locked external input missing: {name}")
            got = _sha(target)
            if got != want:
                return (False, f"input hash drift: {name} {got[:16]}...")
        return (True, "all locked input hashes match")

    def g_raw_file_set():
        try:
            entries = [e for e in a1_manifest_entries(a1_manifest_path)
                       if e[0].endswith(".dbn.zst")]   # packet §4: 139 raw
        except Exception as exc:                     # noqa: BLE001
            return (False, f"A1 manifest unreadable/unrecognised: "
                           f"{type(exc).__name__}: {exc}")
        if len(entries) != A1_EXPECTED_FILE_COUNT:
            return (False, f"A1 file count {len(entries)} != "
                           f"{A1_EXPECTED_FILE_COUNT}")
        total = sum(size for _, size, _ in entries)
        if total != A1_EXPECTED_TOTAL_BYTES:
            return (False, f"A1 total bytes {total} != {A1_EXPECTED_TOTAL_BYTES}")
        got = compute_raw_file_set_sha256(entries)
        return (got == RAW_FILE_SET_SHA256,
                "raw_file_set digest matches packet §4" if got == RAW_FILE_SET_SHA256
                else f"raw_file_set digest {got[:16]}... != packet §4 value "
                     f"(see DECISION_PACKET_RAW_FILE_SET_PREIMAGE.md: the "
                     f"pre-image convention is UNCONFIRMED)")

    def g_seal_check():
        if not seal_check_tool.exists():
            return (False, f"seal_check tool not found: {seal_check_tool}")
        proc = subprocess.run([sys.executable, str(seal_check_tool)],
                              capture_output=True, text=True, cwd=str(repo),
                              env=clean_env())
        out = (proc.stdout or "") + (proc.stderr or "")
        ok = proc.returncode == 0 and "SEAL_CHECK: PASS" in out
        return (ok, "seal_check PASS" if ok
                else f"seal_check exit={proc.returncode}")

    def g_structure_assertions():
        try:
            import yaml
        except Exception as exc:                     # noqa: BLE001
            return (False, f"pyyaml unavailable: {type(exc).__name__}")
        path = repo / STRUCTURE_YAML
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:                     # noqa: BLE001
            return (False, f"{STRUCTURE_YAML} does not parse: "
                           f"{type(exc).__name__}")
        if not isinstance(parsed, dict):
            return (False, f"{STRUCTURE_YAML} is not a YAML mapping")
        n = len(parsed)
        return (n == STRUCTURE_YAML_TOP_LEVEL_KEYS,
                f"structural parse OK, {n} top-level keys")

    def g_runs_dir_absent():
        # SA-6 F-08: scan by trial-id prefix — a second-resolution timestamp
        # in the directory name made the literal "must not exist" test
        # vacuous (every invocation proposed a fresh name).
        if not runs_root.exists():
            return (True, "runs root does not exist yet")
        prior = sorted(p.name for p in runs_root.glob(f"{trial_id}*"))
        return (not prior,
                f"runs root already holds {len(prior)} {trial_id} "
                f"directory/ies" if prior else "no prior run directory")

    def g_tests():
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q",
             "-p", "no:cacheprovider"],
            capture_output=True, text=True, cwd=str(repo), env=clean_env())
        out = proc.stdout or ""
        collected = parse_pytest_collected(out)
        if proc.returncode != 0:
            return (False, f"pytest exit={proc.returncode}")
        if collected is None:
            return (False, "pytest summary line could not be parsed")
        if collected < MIN_COLLECTED_TESTS:
            return (False, f"pytest collected {collected} tests, below the "
                           f"{MIN_COLLECTED_TESTS} baseline (suite muted?)")
        return (True, f"pytest passed, {collected} tests collected")

    def g_parent_env_clean():
        # SA-10 N4 / F-09(b): the runner's OWN interpreter must not carry
        # override vectors either (children are already hermetic).
        hostile = [v for v in ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME",
                               "PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE",
                               "GIT_CONFIG", "GIT_CONFIG_GLOBAL",
                               "GIT_TEMPLATE_DIR", "GIT_CEILING_DIRECTORIES")
                   if os.environ.get(v)]
        return (not hostile,
                f"hostile env vars set in the runner's own process: {hostile}"
                if hostile else "parent interpreter env clean")

    def g_frozen_constants_in_process():
        # SA-10 F-19: re-verify frozen module constants inside THIS
        # interpreter (the pytest-child pins cannot see an in-process rebind).
        from itsf.s0 import context as _ctx, dataset as _ds
        expected = (
            ("dataset.THETA_PRIMARY", _ds.THETA_PRIMARY, 0.5),
            ("dataset.THETA_SECONDARY", _ds.THETA_SECONDARY, 0.3),
            ("dataset.DECILE_COUNT", _ds.DECILE_COUNT, 10),
            ("dataset.DEV_START", _ds.DEV_START, "2010-06-06"),
            ("dataset.DEV_END_EXCL", _ds.DEV_END_EXCL, "2022-01-01"),
            ("context.F4_LOOKBACK_DAYS", _ctx.F4_LOOKBACK_DAYS, 60),
            ("context.MICRO_ERA_BOUNDARY", _ctx.MICRO_ERA_BOUNDARY,
             "2019-05-06"),
            ("config.seed", SEED, 20260731),
        )
        bad = [name for name, got, want in expected if got != want]
        return (not bad, f"frozen-constant drift in-process: {bad}"
                if bad else f"{len(expected)} frozen constants verified "
                            "in the runner interpreter")

    return [
        GateCheck("parent_env_clean", g_parent_env_clean),
        GateCheck("frozen_constants_in_process", g_frozen_constants_in_process),
        GateCheck("real_run_allowed", g_real_run_allowed),
        GateCheck("git_clean", g_clean),
        GateCheck("run_authorized_event", g_authorized_event),
        GateCheck("head_matches_authorized_commit", g_head_matches),
        GateCheck("key_closure_attestation_present", g_key_closure),
        GateCheck("locked_input_hashes", g_inputs),
        GateCheck("raw_file_set_digest", g_raw_file_set),
        GateCheck("seal_check", g_seal_check),
        GateCheck("structure_assertions", g_structure_assertions),
        GateCheck("runs_dir_absent_for_trial", g_runs_dir_absent),
        GateCheck("full_pytest", g_tests),
    ]


def _clean_gate_exempt(porcelain_line: str) -> bool:
    """True if a `git status --porcelain` line names an allowlisted path."""
    path = porcelain_line[3:] if len(porcelain_line) > 3 else ""
    if " -> " in path:                                # rename: judge the target
        path = path.split(" -> ", 1)[1]
    path = path.strip().strip('"').replace("\\", "/")
    if path in CLEAN_GATE_ALLOWLIST_FILES:
        return True
    return any(path.startswith(d) for d in CLEAN_GATE_ALLOWLIST_DIRS)


def parse_pytest_collected(output: str) -> int | None:
    """Total tests reported by a `pytest -q` summary line, or None.

    Sums every outcome bucket on the summary line so a suite that is
    partially deselected/skipped cannot pass the count floor by hiding
    tests behind a filter.
    """
    total = None
    for match in re.finditer(
            r"(\d+)\s+(passed|failed|error|errors|skipped|deselected|xfailed|"
            r"xpassed)\b", output):
        total = (total or 0) + int(match.group(1))
    return total


# =========================================================================
# Stage B structural checks (SA-6 F-02 / F-06 / F-14)
# =========================================================================

def load_expected_assertions(assertions_path: Path) -> dict[str, int]:
    """Read the (hash-locked) preflight JSON and translate it into the
    contracts-vocabulary expected mapping.

    The FILE READ happens here, in the main-agent entrypoint — runinfra
    stays a pure comparator that never opens S0_INPUT_PREFLIGHT.json
    (packet §5 / SA-5 contract).
    """
    from itsf.s0 import runinfra
    document = json.loads(assertions_path.read_text(encoding="utf-8"))
    return runinfra.translate_preflight_assertions(document)


def stage_c_actuals_unavailable():
    """Stage-C structural actuals provider — not wired yet.

    Kept as an explicit provider (rather than a bare raise inside the check)
    so the real provider can be dropped in without touching the gate wiring.
    """
    from itsf.contracts import RunGateError
    raise RunGateError(
        "Stage C wiring not yet activated — final packet re-render pending "
        "(packet §0); no structural actuals can be produced")


def build_structural_checks(assertions_path: Path, *,
                            expected_loader=load_expected_assertions,
                            actuals_provider=stage_c_actuals_unavailable,
                            wiring_status=None):
    """Stage-B checks (pre-exposure, packet §7).

    The assertion comparison is REAL wiring: `expected` comes from the locked
    preflight file via the translation layer, `actual` from the injected
    structural-actuals provider, and the verdict comes from
    runinfra.compare_preflight_assertions (SA-6 F-06 — previously the
    comparator had no non-test caller at all).
    """
    from itsf.s0 import runinfra
    from itsf.s0.runner import GateCheck

    def c_file_present():
        return (assertions_path.exists(), str(assertions_path))

    def c_assertions_translate():
        expected = expected_loader(assertions_path)
        return (bool(expected),
                f"{len(expected)} expected assertions translated")

    def c_assertions_match():
        expected = expected_loader(assertions_path)
        actual = actuals_provider()
        result = runinfra.compare_preflight_assertions(expected, actual)
        if result.all_pass:
            return (True, f"{len(result.items)} assertions match")
        return (False,
                f"shape_ok={result.shape_ok} missing={result.missing_keys} "
                f"extra={result.extra_keys} mismatched={result.mismatched_keys}")

    def c_stage_c_wiring_activated():
        # SA-6 F-02: this used to be a RuntimeError raised inside `compute`,
        # i.e. AFTER the atomic run-start — a fully-authorized invocation
        # would have burned S0-T001 and researcher exposure for zero output.
        # As a Stage-B gate it fails PRE-exposure, costing nothing.
        # Since Aaron 2026-08-01 §三.4 the REAL wiring exists (RealChain);
        # callers pass its readiness probe. A caller that supplies none gets
        # the historical inert message (used by injection tests only).
        if wiring_status is not None:
            return wiring_status()
        return (False,
                "Stage C wiring status not supplied — inert by default")

    # `stage_c_wiring_activated` sits BEFORE the comparison so that today's
    # inert run stops with that exact, honest message rather than with a
    # confusing "actuals provider raised" from the comparison check.
    return [
        GateCheck("preflight_assertions_file_present", c_file_present),
        GateCheck("preflight_assertions_translatable", c_assertions_translate),
        GateCheck("stage_c_wiring_activated", c_stage_c_wiring_activated),
        GateCheck("preflight_assertions_match", c_assertions_match),
    ]


# =========================================================================
# Stage D integrity checks (SA-6 F-06)
# =========================================================================

def build_integrity_checks():
    """Stage-D checks (packet §7 NA conservation).

    The Stage-C result object must expose `na_reason_counts` (itemized
    {column: {approved_reason: count}}) and `reported_total_na` ({column:
    observed_total}); the check raises NAConservationError on violation so
    the runner's isinstance-based classifier (F-27) records the real error
    type in the failure report.
    """
    from itsf.contracts import NAConservationError
    from itsf.s0 import runinfra

    def na_conservation(result) -> tuple[bool, str]:
        counts = _attr(result, "na_reason_counts")
        totals = _attr(result, "reported_total_na")
        if counts is None or totals is None:
            raise NAConservationError(
                "Stage-C result exposes no na_reason_counts/reported_total_na; "
                "NA conservation cannot be evaluated")
        verdict = runinfra.check_na_conservation(
            counts, reported_total_na=totals)
        if not verdict.ok:
            raise NAConservationError("; ".join(verdict.errors))
        return (True, f"NA conserved across {len(verdict.per_column_ok)} columns")

    return [na_conservation]


def _attr(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


# =========================================================================
# Stage C real computation chain (MAIN-AGENT OWNED; Aaron 2026-08-01 §三.4)
# context -> dataset -> integrity adapters -> report render. No placeholder,
# no not-implemented sentinel. Real-data loading happens ONLY here, only when
# the Stage-A authorization gates have passed; the e2e tests drive exactly
# these functions with synthetic universes instead.
# =========================================================================

# IR-13 enumerated non-scheduled FOMC actions (diagnostic-only, frozen)
UNSCHEDULED_FOMC = ("2019-10-11", "2020-03-03", "2020-03-15", "2020-03-23")
F10_CSV = REPO / "gate1" / "f10_event_calendar" / "f10_events.csv"
SYMBOLOGY_CSV = REPO / "gate1" / "symbology" / "nq_v0_mapping.csv"

FEATURE_FIELD_TO_F = {
    "ret_open30": "F1", "or_width": "F2", "de_open30": "F3",
    "rvol_open30": "F4", "gap": "F5", "open_loc_on": "F6", "on_range": "F7",
    "retrace_open30": "F8", "close_pos_open30": "F9", "is_event_day": "F10",
}
LABEL_KEY_TO_NAME = {"y_cont": "Y_cont", "y1": "Y1", "y2_de_pm": "Y2",
                     "y3_close_pos_pm": "Y3", "y4_mfe": "Y4", "y5_mae": "Y5"}
PRICE_ANCHORS = ("O0930", "C0959", "O1000", "C1544")


def _norm_reason(word: str) -> str:
    """Fold vocabulary via the F-14 table when it knows the word; contract
    words pass through unchanged."""
    from itsf.s0 import runinfra
    try:
        return runinfra.translate_na_reason(word)
    except ValueError:
        return word


def load_real_event_calendar():
    import csv as _csv
    from collections import Counter as _Counter
    from itsf.s0.context import EventCalendar
    with F10_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    cpi = {r["date_et"] for r in rows if r["is_cpi_release_day"] == "true"}
    nfp = {r["date_et"] for r in rows if r["is_nfp_release_day"] == "true"}
    stmt = {r["date_et"] for r in rows
            if r["is_fomc_statement_day"] == "true"}
    kinds: dict[str, set[str]] = {}
    for r in rows:
        kinds.setdefault(r["date_et"], set()).add(r["event_type"])
    raw_multi = {d for d, k in kinds.items() if len(k) > 1}
    return EventCalendar(cpi, nfp, stmt, frozenset(UNSCHEDULED_FOMC),
                         frozenset(raw_multi))


def load_real_roll_intervals():
    import csv as _csv
    from itsf.s0.context import RollInterval
    with SYMBOLOGY_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    return tuple(RollInterval(r["start_date_utc"], r["end_date_utc_excl"],
                              r["raw_symbol"], int(r["instrument_id"]))
                 for r in rows)


def load_real_session_schedule():
    from itsf.s0.context import SessionSchedule
    import pandas_market_calendars as pmc
    cal = pmc.get_calendar("CME_Equity")
    sched = cal.schedule(start_date="2010-06-06", end_date="2021-12-31")
    closes = sched["market_close"].dt.tz_convert("America/New_York")
    close_minute = {str(d.date()): c.hour * 60 + c.minute
                    for d, c in closes.items()}
    cond = json.loads((A1_JOB_DIR / "condition.json").read_text("utf-8"))
    degraded = frozenset(r["date"] for r in cond
                         if r["condition"] != "available")
    return SessionSchedule(close_minute=close_minute,
                           vendor_degraded_dates=degraded)


def structural_actuals_from(ds, universe) -> dict:
    """Independently-computed actuals mirroring translate_preflight_assertions
    key families. Compare-only output (packet §5)."""
    import numpy as np
    out: dict[str, int] = {}
    fc = dict(ds.funnel_counts)
    for key in ("L0_scheduled_trading_days", "L1_observed_rth_days",
                "L2_regular_full_session_candidates",
                "L3_structurally_eligible_days",
                "L4_final_feature_construction_dates"):
        out[f"funnel.{key}"] = int(fc[key])
    for cat, n in ds.f10_counts.items():
        out[f"f10.{cat}"] = int(n)
    per = ds.na_table["per_field"]["features"]
    pop = int(ds.na_table["population"])
    for field, fname in FEATURE_FIELD_TO_F.items():
        row = per[field]
        out[f"feature.{fname}.constructible"] = int(row["not_na"])
        out[f"feature.{fname}.na"] = int(row["na"])
        for word, n in row["reasons"].items():
            k = f"na_reason.{fname}.{_norm_reason(word)}"
            out[k] = out.get(k, 0) + int(n)
    out["feature.F11.constructible"] = pop          # structural booleans
    out["feature.F11.na"] = 0
    # anchors over the eligible population
    elig = [r.trade_date for r in ds.records]
    for name, attr in (("O0930", "o0930"), ("C0959", "c0959"),
                       ("O1000", "o1000"), ("C1544", "c1544")):
        missing = sum(1 for d in elig
                      if np.isnan(getattr(universe.summaries[d], attr)))
        out[f"anchor.{name}.available"] = len(elig) - missing
        out[f"anchor.{name}.missing"] = missing
        if missing:
            out[f"na_reason.anchor.{name}.anchor_missing"] = missing
    prev_missing = [d for d in elig
                    if d not in universe.prev_rth_close]
    out["anchor.prev_rth_close.available"] = len(elig) - len(prev_missing)
    out["anchor.prev_rth_close.missing"] = len(prev_missing)
    for d in prev_missing:
        word = _norm_reason(universe.prev_rth_close_cause.get(
            d, "prev_rth_close_anchor_missing"))
        k = f"na_reason.anchor.prev_rth_close.{word}"
        out[k] = out.get(k, 0) + 1
    for key, name in LABEL_KEY_TO_NAME.items():
        row = ds.label_anchor_availability[key]
        out[f"label.{name}.available"] = int(row["available_days"])
        out[f"label.{name}.unavailable"] = int(row["unavailable_days"])
    return out


def stage_c_result(ds):
    """Wrap the dataset with the Stage-D adapters the integrity checks read
    (na_reason_counts itemized per column + reported_total_na)."""
    counts: dict[str, dict[str, int]] = {}
    totals: dict[str, int] = {}
    for table in ("features", "labels"):
        for field, row in ds.na_table["per_field"][table].items():
            col = f"{table}.{field}"
            counts[col] = dict(row["reasons"])
            totals[col] = int(row["na"])
    return {"dataset": ds, "na_reason_counts": counts,
            "reported_total_na": totals}


def render_s0_report(result) -> dict[str, str]:
    """Stage-E sealed release: the FORMAL S0 report, whole-document only
    (packet §7 — nothing here reaches a log line)."""
    ds = result["dataset"]
    payload = {
        "trial_report": "S0_REPORT",
        "y6_rule": ds.y6_rule,
        "funnel": dict(ds.funnel_counts),
        "f10_final_mutually_exclusive": dict(ds.f10_counts),
        "f10_raw_membership": dict(ds.f10_raw_membership_counts),
        "na_table": ds.na_table,
        "frequency": ds.frequency,
        "label_anchor_availability": ds.label_anchor_availability,
        "eras": {k: len(v) for k, v in ds.eras.items()},
        "groups": {g: {k: len(v) for k, v in m.items()}
                   for g, m in ds.groups.items()},
        "pending_decisions": list(ds.pending_decisions),
    }
    md = ["# S0 FORMAL REPORT (sealed at Stage E)", "",
          f"- y6_rule: {ds.y6_rule}",
          f"- records: {len(ds.records)}",
          "- full structures in S0_REPORT.json (single sealed release)"]
    return {"S0_REPORT.json": json.dumps(payload, indent=1, sort_keys=True,
                                         default=str),
            "S0_REPORT.md": "\n".join(md)}


class RealChain:
    """Cached real-data chain. Universe/dataset are built at most once per
    process; Stage B reads only structural counts from them, Stage C returns
    the same cached dataset (no recompute, no drift)."""

    def __init__(self) -> None:
        self._ds = None
        self._uni = None

    def ready(self) -> tuple[bool, str]:
        missing = [str(p) for p in (F10_CSV, SYMBOLOGY_CSV,
                                    A1_JOB_DIR / "condition.json",
                                    A1_JOB_DIR / "manifest.json")
                   if not p.exists()]
        if missing:
            return (False, f"stage-C artifacts missing: {missing}")
        return (True, "stage C wiring ready (context->dataset->report)")

    def _ensure(self):
        if self._ds is None:
            from itsf.data.dbn_loader import DevelopmentSignalLoader
            from itsf.s0.context import build_universe
            from itsf.s0.dataset import build_s0_dataset
            loader = DevelopmentSignalLoader(A1_JOB_DIR)
            bars_by_date: dict = {}
            for name in sorted(p.name for p in A1_JOB_DIR.glob("*.dbn.zst")):
                df, _events = loader.load_real(name, source_format="dbn")
                for d, block in df.groupby(df["ts"].dt.date.astype(str)):
                    bars_by_date[d] = (block if d not in bars_by_date else
                                       __import__("pandas").concat(
                                           [bars_by_date[d], block]))
            uni = build_universe(bars_by_date, load_real_session_schedule(),
                                 load_real_event_calendar(),
                                 load_real_roll_intervals())
            self._uni = uni
            self._ds = build_s0_dataset(bars_by_date, uni)
        return self._ds, self._uni

    def structural_actuals(self) -> dict:
        ds, uni = self._ensure()
        return structural_actuals_from(ds, uni)

    def authorization_snapshot(self) -> dict:
        """Aaron 2026-08-02 §三: structured snapshot of the authorization
        state, taken at Stage A and re-verified immediately before the atomic
        RUN_STARTED transition."""
        raw = REGISTRY.read_bytes()
        text = raw.decode("utf-8")
        events = parse_registry_events(text)
        _row, commit, _reason = find_authorization_event(text)
        # SA-11 N-C: the parser's third return is a REASON string, not the
        # sentence. The verbatim §10 sentence is fully determined by
        # (trial_id, commit) — the parser only authorizes on an exact match —
        # so reconstruct it and hash THAT (binds the snapshot to the sentence;
        # distinct commits now yield distinct hashes).
        sentence = (f"启动第一次真实S0，授权trial_id: {TRIAL_ID}，"
                    f"使用commit: {commit}") if commit else ""
        return {
            "registry_sha256": hashlib.sha256(raw).hexdigest(),
            "event_sequence": len(events),
            "trial_id": TRIAL_ID,
            "authorized_commit": commit,
            "exact_authorization_text_sha256":
                hashlib.sha256(sentence.encode("utf-8")).hexdigest()
                if sentence else "",
        }

    def ir24_divergence_guard(self) -> tuple[bool, str]:
        """SA-10 N6 (blocking): the F8 NA-reason vocabulary and the IR-24 day
        class diverge exactly on the opening_numerator_zero set. A non-empty
        set must STOP pre-exposure and go to Aaron — never into a sealed
        one-shot report that would contradict IR-24."""
        ds, _uni = self._ensure()
        diag = ds.na_table.get("diagnostics")
        key = "opening_numerator_zero_ret_open30_undefined"
        # SA-11 N-G: a MISSING diagnostics key is fail-closed, never a pass.
        if diag is None or key not in diag:
            return (False, "diagnostics counter absent from na_table — "
                           "fail closed (cannot evidence divergence == 0)")
        n = int(diag[key])
        if n == 0:
            return (True, "IR-24 F8 divergence set empty")
        return (False, f"IR-24 F8 divergence set NON-EMPTY (count={n}) — "
                       "STOP; requires an Aaron ruling before any run")

    def compute(self):
        ds, _uni = self._ensure()
        return stage_c_result(ds)


# =========================================================================
# entrypoint
# =========================================================================

def main() -> int:
    from itsf.contracts import RunConfig, TrialState
    from itsf.s0 import runinfra
    from itsf.s0.runner import GateCheck, RunnerDeps, S0Runner
    from itsf.s0.runner import append_registry_event_line

    # whole-second UTC: the guarded log schemas admit no fractional seconds
    # (a fractional timestamp would also trip the float-leak scanner).
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    clock = lambda: now.isoformat()                  # noqa: E731

    head = _git("rev-parse", "HEAD")
    # SA-6 F-11: authorized_commit is the value PARSED OUT of Aaron's §10
    # sentence, never HEAD. The head_matches_authorized_commit gate is what
    # asserts the two agree; filling HEAD in here would have made that gate
    # compare a value with itself.
    _, authorized_commit, _ = find_authorization_event(_registry_text())

    cfg = RunConfig(
        trial_id=TRIAL_ID,
        authorized_commit=authorized_commit,
        seed=SEED,
        attempts_dir=str(ATTEMPTS_ROOT / f"{TRIAL_ID}-A{stamp}"),
        runs_dir=str(RUNS_ROOT / f"{TRIAL_ID}_{stamp}"),
        assertions_path=str(REPO / "S0_INPUT_PREFLIGHT.json"))

    def registry_append(event: str, note: str) -> None:
        append_registry_event_line(REGISTRY, TRIAL_ID, event, note,
                                   clock(), head[:7] or "unknown",
                                   "main agent (s0_real_run)")

    def guarded_log(message: str) -> None:
        # SA-6 F-04: the Stage-C log guard is now actually ON the wire. Any
        # message that is not a whitelisted schema raises LogLeakError, which
        # the runner escalates to a stage failure ("宁可误杀").
        runinfra.validate_log_event(message)
        print(f"[s0-runner] {message}", flush=True)

    # Aaron 2026-08-01 §三.4: the REAL chain — context -> dataset ->
    # integrity adapters -> sealed report. No placeholder anywhere.
    chain = RealChain()

    # Aaron 2026-08-02 §三: authorization snapshot control ------------------
    snap_state: dict = {}

    def g_authorization_snapshot():
        snap = chain.authorization_snapshot()
        if not snap["authorized_commit"]:
            return (False, "no RUN_AUTHORIZED event to snapshot")
        adir = Path(cfg.attempts_dir)
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "AUTHORIZATION_SNAPSHOT.json").write_text(
            json.dumps(snap, indent=1, sort_keys=True), encoding="utf-8")
        snap_state["snapshot"] = snap
        return (True, "authorization snapshot recorded")

    def pre_exposure_recheck():
        before = snap_state.get("snapshot")
        if before is None:
            return (False, "no Stage-A authorization snapshot in memory")
        now = chain.authorization_snapshot()
        same = (now["registry_sha256"] == before["registry_sha256"]
                and now["event_sequence"] == before["event_sequence"]
                and now["authorized_commit"] == before["authorized_commit"])
        return (same, "registry unchanged since authorization snapshot"
                if same else "registry CHANGED between authorization and "
                             "run start — possible event insertion")

    def post_run_started_hook(rdir: Path) -> None:
        after = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
        (rdir / "REGISTRY_AFTER_RUN_STARTED.json").write_text(
            json.dumps({"registry_sha256_after_run_started": after,
                        "snapshot_before": snap_state.get("snapshot", {})},
                       indent=1, sort_keys=True), encoding="utf-8")

    deps = RunnerDeps(
        config=cfg,
        trial_state=TrialState.PACKET_APPROVED,
        gates=(*build_gates(),
               GateCheck("authorization_snapshot_recorded",
                         g_authorization_snapshot)),   # Aaron §三.1-4
        structural_checks=(*build_structural_checks(
            Path(cfg.assertions_path),
            actuals_provider=chain.structural_actuals,
            wiring_status=chain.ready),
            GateCheck("ir24_f8_divergence_empty",
                      chain.ir24_divergence_guard)),   # SA-10 N6, blocking
        compute=chain.compute,
        integrity_checks=build_integrity_checks(),
        render_report=render_s0_report,
        append_registry_event=registry_append,
        clock_utc=clock,
        log=guarded_log,
        pre_exposure_recheck=pre_exposure_recheck,     # Aaron §三.5
        post_run_started_hook=post_run_started_hook)   # Aaron §三.6

    out = S0Runner(deps).run()
    print(f"terminal: stage={out.terminal_stage.value} ok={out.ok} "
          f"exposure_consumed={out.exposure_consumed} "
          f"kind={out.failure_kind or 'success'} "
          f"incident={out.incident_id or 'none'}")
    return 0 if out.ok else 2


if __name__ == "__main__":
    sys.exit(main())
