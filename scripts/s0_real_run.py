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
# DR-02: run-infra provenance stamp ONLY — never a research RNG seed.
# Research randomness derives exclusively from
# contracts.RESEARCH_BOOTSTRAP_SEEDS (7/13/31, frozen S0 §9/App A).
ENGINEERING_SEED = 20260731    # packet §5 (re-rendered per DR-02)
REGISTRY = REPO / "ops" / "TRIAL_REGISTRY.md"
RUNS_ROOT = REPO / "runs"
ATTEMPTS_ROOT = REPO / "attempts"

# Baseline collected-test count at the SA-6 audit commit. The pytest gate
# requires the suite to still COLLECT at least this many tests, so a muted
# or filtered run cannot satisfy the gate with a handful of tests (F-09).
MIN_COLLECTED_TESTS = 782                  # M6.1: floor = current suite

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
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        # IR-25 fixture 4: a row-shaped line quoted inside a fenced code
        # block is documentation, never an event.
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
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


_SUPERSEDE_NOTE_RE = re.compile(
    r"\[(?P<trial>[A-Z0-9-]+)\]\s*"
    r"supersedes_event_sequence:\s*(?P<seq>\d+);\s*"
    r"superseded_commit:\s*(?P<commit>[0-9a-f]{40});\s*"
    r"reason_code:\s*(?P<reason>[A-Z0-9_]+);\s*"
    r"incident_id:\s*(?P<incident>INC-[0-9a-f]{12})")


def _validate_authorized_row(row: dict[str, str], trial_id: str
                             ) -> tuple[str, str]:
    """Strict per-row validation of one RUN_AUTHORIZED row.

    Returns (commit, "") on success, ("", why) on any defect. IR-25: a
    malformed authorization row is NEVER silently ignored — the caller
    fails the whole resolution closed.
    """
    prefix = AUTHORIZATION_SENTENCE_TEMPLATE.format(trial_id=trial_id,
                                                    commit="")
    idx = row["note"].find(prefix)
    if idx < 0:
        return ("", "RUN_AUTHORIZED row does not contain the verbatim "
                    "packet §10 authorization sentence")
    tail = row["note"][idx + len(prefix):]
    commit = tail[:40]
    if not _HEX40_RE.match(commit):
        return ("", "packet §10 sentence does not name a full 40-hex "
                    "commit hash")
    expected = AUTHORIZATION_SENTENCE_TEMPLATE.format(trial_id=trial_id,
                                                      commit=commit)
    if expected not in row["note"]:
        return ("", "authorization sentence is not verbatim")
    # IR-25 fixture 7: the row's commit CELL must equal the sentence commit
    # exactly — an internal inconsistency fails closed.
    if row["commit"] != commit:
        return ("", "RUN_AUTHORIZED row commit cell does not equal the "
                    "sentence commit — internal inconsistency")
    return (commit, "")


def resolve_authorizations(text: str, trial_id: str = TRIAL_ID
                           ) -> tuple[list[tuple[dict, str]], str]:
    """IR-25 (Aaron P2-A): resolve the LIVE authorization set.

    live = every format-legal RUN_AUTHORIZED row minus those precisely
    referenced by a format-legal RUN_AUTHORIZATION_SUPERSEDED row.

    Returns (live, problem) where live is [(row, commit), ...] and
    problem != "" means the chain itself is malformed — every such case
    fails CLOSED: malformed authorization row, malformed supersede note,
    supersede of a nonexistent/ambiguous sequence, forward reference,
    duplicate supersede, trial/commit reference mismatch.
    """
    rows = parse_registry_events(text)
    auth: list[tuple[int, dict, str]] = []          # (position, row, commit)
    for pos, row in enumerate(rows):
        if row["event"] != "RUN_AUTHORIZED":
            continue
        commit, why = _validate_authorized_row(row, trial_id)
        if why:
            return ([], f"registry row #{row['seq']}: {why}")
        auth.append((pos, row, commit))

    superseded_positions: set[int] = set()
    seen_targets: set[str] = set()
    for pos, row in enumerate(rows):
        if row["event"] != "RUN_AUTHORIZATION_SUPERSEDED":
            continue
        m = _SUPERSEDE_NOTE_RE.search(row["note"])
        if not m:
            return ([], f"registry row #{row['seq']}: "
                        "RUN_AUTHORIZATION_SUPERSEDED note is not "
                        "machine-parsable (required fields: trial_id, "
                        "supersedes_event_sequence, superseded_commit, "
                        "reason_code, incident_id)")
        if m.group("trial") != trial_id:
            return ([], f"registry row #{row['seq']}: supersede names "
                        f"trial {m.group('trial')!r}, expected "
                        f"{trial_id!r}")
        target_seq = m.group("seq")
        if target_seq in seen_targets:
            return ([], f"registry row #{row['seq']}: duplicate supersede "
                        f"of event sequence {target_seq}")
        seen_targets.add(target_seq)
        targets = [(p, r, c) for p, r, c in auth if r["seq"] == target_seq]
        if not targets:
            return ([], f"registry row #{row['seq']}: supersede references "
                        f"event sequence {target_seq}, which is not an "
                        "existing RUN_AUTHORIZED row")
        if len(targets) > 1:
            return ([], f"registry row #{row['seq']}: supersede reference "
                        f"{target_seq} is ambiguous ({len(targets)} rows)")
        t_pos, _t_row, t_commit = targets[0]
        if t_pos >= pos:
            return ([], f"registry row #{row['seq']}: supersede is a "
                        "forward reference — it must appear after the row "
                        "it supersedes")
        if m.group("commit") != t_commit:
            return ([], f"registry row #{row['seq']}: superseded_commit "
                        "does not equal the referenced row's authorized "
                        "commit")
        superseded_positions.add(t_pos)

    live = [(row, commit) for pos, row, commit in auth
            if pos not in superseded_positions]
    return (live, "")


def find_authorization_event(text: str, trial_id: str = TRIAL_ID
                             ) -> tuple[dict[str, str] | None, str, str]:
    """Locate THE live RUN_AUTHORIZED row and extract its commit.

    Returns (row, commit, detail). `commit` is non-empty ONLY when the
    live authorization set (IR-25: format-legal RUN_AUTHORIZED rows minus
    precisely-superseded ones) contains exactly one row carrying the
    verbatim packet-§10 sentence with a full 40-hex commit. 0 live rows =
    not authorized; >1 live rows or ANY malformed chain element fails
    closed. Prose mentions and fenced examples are never rows.
    """
    live, problem = resolve_authorizations(text, trial_id)
    if problem:
        return (None, "", problem)
    if not live:
        return (None, "", "registry event table has no RUN_AUTHORIZED row "
                          "(packet §10 sentence not issued)")
    if len(live) > 1:
        return (None, "", f"registry event table has {len(live)} live "
                          f"RUN_AUTHORIZED rows; exactly one is expected")
    row, commit = live[0]
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
        from itsf import contracts as _c
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
            ("config.engineering_seed", ENGINEERING_SEED, 20260731),
            ("contracts.RESEARCH_BOOTSTRAP_SEEDS",
             _c.RESEARCH_BOOTSTRAP_SEEDS, (7, 13, 31)),
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
    # IR-26 rule A: the map holds an entry for EVERY eligible day (missing
    # anchors are stored as None + cause) — membership alone can never
    # detect a miss; `is None` is the missing test.
    prev_missing = [d for d in elig
                    if universe.prev_rth_close[d] is None]
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


def render_s0_report(result, *, expected_governance=None) -> dict[str, str]:
    """Stage-E sealed release: the FORMAL S0 report, whole-document only
    (packet §7 — nothing here reaches a log line).

    M6: a full-study payload (key "study") is contract-validated
    (S0_REPORT_CONTENT_CONTRACT §B — ANY problem refuses sealing) and the
    §10.1 atomic records are serialized to per-engine/scenario JSONL files
    with sha256 in the manifest. A legacy structural-only result renders as
    before.
    """
    if isinstance(result, dict) and "study" in result:
        from itsf.s0 import handoff as ho
        from itsf.s0 import report as rep
        if expected_governance is None:
            expected_governance = _expected_governance()
        internal, formal = rep.split_envelope(result)
        problems = rep.validate_formal_payload(
            formal, expected_governance=expected_governance)
        if problems:
            raise ValueError("report contract violations: "
                             + "; ".join(problems))
        files: dict[str, str] = {}
        file_manifest: dict[str, object] = {}
        for eng, by_scn in result["records"].items():
            for scn, recs in by_scn.items():
                name = f"MC_HANDOFF_{eng}_{scn}.jsonl"
                body = "\n".join(
                    json.dumps(rep.record_to_formal_dict(r),
                               sort_keys=True, allow_nan=False)
                    for r in recs)
                files[name] = body
                file_manifest[f"{eng}|{scn}"] = {
                    "file": name, "n_records": len(recs),
                    "sha256": hashlib.sha256(
                        body.encode("utf-8")).hexdigest()}
        files["SEED_MANIFEST.json"] = ho.dumps_canonical(
            ho.build_seed_manifest())
        formal = dict(formal)
        formal["mc_handoff_manifest"] = {
            **formal["mc_handoff_manifest"], "files": file_manifest}
        # M6.1.1 S1 two-call contract: the FULL payload validation runs
        # AGAIN after manifest injection (a payload that only becomes
        # invalid post-injection must still refuse to seal).
        problems2 = rep.validate_formal_payload(
            formal, expected_governance=expected_governance)
        if problems2:
            raise ValueError("report contract violations (post-manifest): "
                             + "; ".join(problems2))
        files["S0_REPORT.json"] = rep.to_formal_json(formal)
        # E2: the manifest is generated AFTER file serialization and then
        # re-verified against the actual bytes before sealing.
        univ = {d for t in formal["oracle_daily"].values()
                for d in (*t["day_universe"]["tp_days"],
                          *t["day_universe"]["fp_days"])}
        post = rep.validate_sealed_files(files, formal,
                                         trade_date_universe=univ)
        if post:
            raise ValueError("sealed-file verification failed: "
                             + "; ".join(post))
        files["S0_REPORT.md"] = "\n".join([
            "# S0 FORMAL REPORT (sealed at Stage E)", "",
            "- formal payload: S0_REPORT.json (single sealed release)",
            "- MC handoff records: MC_HANDOFF_<engine>_<scenario>.jsonl",
            "- seed manifest: SEED_MANIFEST.json",
            "- DAY_STRATA/GRID_SAMPLES: wired after the DR-M6 rulings "
            "(schema skeletons in src/itsf/s0/handoff.py)"])
        return files
    raise ValueError(
        "render_s0_report: refusing non-study payload — the legacy "
        "structural-only seal path was removed (M6.1 O1); production "
        "sealing requires the full formal payload")

def _resolved_methods():
    """M6.1 E1 — the ONLY method-ruling state source (contracts dataclass).
    Every field is None until Aaron's ruling lands here with its IR ref."""
    from itsf.contracts import ResolvedS0Methods
    return ResolvedS0Methods()


# Derived, never hand-written (E1): the live pending list.
PENDING_METHOD_DECISIONS: tuple[str, ...] = _resolved_methods().pending_fields()


from itsf.contracts import StudyConfig    # noqa: E402 (after sys.path setup)


_CONFIG_CACHE: dict = {}


def resolved_study_config() -> tuple[StudyConfig | None, str]:
    """Shared readiness/compute predicate (E1/M6.1.1). ready() and
    compute() consume the SAME cached immutable instance — ready=False and
    compute-raises can never diverge. A test_only config is refused here
    (production path) even if one were cached."""
    if "cfg" in _CONFIG_CACHE:
        cfg, why = _CONFIG_CACHE["cfg"]
        if cfg is not None and cfg.methods.test_only:
            return (None, "test_only config refused on the production path")
        return (cfg, why)
    pend = _resolved_methods().pending_fields()
    if pend:
        out = (None, "pending method rulings: " + ", ".join(pend))
    else:
        # Reached only after ALL rulings land. Deriving the concrete
        # injectables (spread scalars per the ruled reduction rule, the
        # ruled regime/vol mappings) is the main-agent wiring step that
        # accompanies the rulings; until it exists this fails CLOSED and
        # Stage B blocks pre-exposure.
        out = (None, "rulings landed but config derivation not implemented "
                     "(M6.1 wiring step) — fail closed pre-exposure")
    _CONFIG_CACHE["cfg"] = out
    return out

FROZEN_N_BOOT = 10_000                 # frozen: S0 §9 — 10,000 resamples
FROZEN_BLOCKS = (5, 21)                # frozen: S0 §9 — Primary 5 / Sens 21
_CONTRACT_ENGINES = ("E1", "E2")
_CONTRACT_SCENARIOS = ("Base", "Conservative", "Stress", "Severe")


def make_day_inputs(ds, bars_by_date):
    """StudyDayInput per DIRECTIONAL record day.

    or_high/or_low = the 09:30-09:59 opening-range extremes taken from the
    OBS window ONLY — no bar at or after 10:00 may contribute (# frozen:
    S0 §7 止损=开盘区间对侧极值; no-lookahead). d_open comes from the
    dataset's authoritative column (IR-23). Directional days whose price
    frame cannot carry the trade are NOT silently dropped here — they are
    simply absent from the mapping and build_study discloses them.
    """
    from itsf.s0 import context as _ctx
    from itsf.s0.study import StudyDayInput
    out: dict[str, object] = {}
    for r in ds.records:
        if r.labels.d_open not in (1, -1):      # IR-23 authoritative column
            continue
        bars = bars_by_date.get(r.trade_date)
        if bars is None:
            continue
        obs = _ctx.window_bars(bars, _ctx.OBS_LO_MINUTE, _ctx.OBS_HI_MINUTE)
        pm = _ctx.window_bars(bars, _ctx.PM_LO_MINUTE, _ctx.PM_HI_MINUTE)
        if not len(obs) or not len(pm):
            continue
        out[r.trade_date] = StudyDayInput(
            trade_date=r.trade_date, pm_bars=pm,
            or_high=float(obs["high"].max()),
            or_low=float(obs["low"].min()),
            d_open=int(r.labels.d_open))
    return out


def _strkeys(obj):
    """Recursively stringify non-str dict keys (formal JSON boundary)."""
    if isinstance(obj, dict):
        return {str(k): _strkeys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_strkeys(v) for v in obj]
    return obj


def build_full_study_result(ds, bars_by_date, *, config: StudyConfig,
                            governance_meta, n_boot=FROZEN_N_BOOT):
    """Assemble the FULL S0 payload per S0_REPORT_CONTENT_CONTRACT §A.

    spread_scalars (DR-M6-A) and regime_of (DR-M6-B) are INJECTED so the
    synthetic e2e can exercise the whole chain; the real-run caller does
    not exist until the rulings land, and pending_decisions travels into
    disclosures where the contract validator fails Stage E closed.
    Research randomness lives entirely inside stats/gridmix (frozen seeds
    {7,13,31}); this function is deterministic.
    """
    from itsf.s0 import costs as _costs
    from itsf.s0.gridmix import build_grid
    from itsf.s0.stats import bootstrap_mean_ci
    from itsf.s0.study import build_study

    scenarios = _costs.build_scenarios(*config.spread_scalars)
    study = build_study(ds, make_day_inputs(ds, bars_by_date), scenarios)

    # M6.1.1: NO invented vocabulary. A None flag (F10 multi-event NA,
    # IR-12/18) may only enter the strata under the RULED event mapping;
    # while DR-M6-F pends no config exists, and an unrecognized rule
    # blocks explicitly rather than defaulting.
    def _event_stratum(flag):
        if flag is not None:
            return flag
        rule = config.methods.event_na_mapping
        if rule == "five_stratum":         # IR-12/18 vocabulary, TEST_ONLY
            return "NA_multi_event"
        raise ValueError(
            f"event-NA stratum mapping {rule!r} not implemented — "
            "DR-M6-F ruling required (fail closed)")

    event_of = {r.trade_date: _event_stratum(r.features.is_event_day)
                for r in ds.records}
    bootstrap_ci: dict[str, object] = {}
    feasibility_grid: dict[str, object] = {}
    for tkey, tblock in study["per_theta"].items():
        p = tblock["frequency"]["pooled"]["continuation_base_rate_p"]
        for eng in _CONTRACT_ENGINES:
            for scn in study["scenarios_used"]:
                d_tp = tblock["d_tp"][eng][scn]
                d_fp = tblock["d_fp"][eng][scn]
                series = [d_tp[d] for d in sorted(d_tp)]
                for blk in FROZEN_BLOCKS:
                    bootstrap_ci[f"{tkey}|{eng}|{scn}|block{blk}"] = \
                        bootstrap_mean_ci(series, block_len=blk,
                                          n_boot=n_boot)
                strata = {d: (d[:4], str(config.regime_of(d)), event_of[d])
                          for d in {**d_tp, **d_fp}}
                feasibility_grid[f"{tkey}|{eng}|{scn}"] = build_grid(
                    d_tp, d_fp, strata, p)

    records = study["records"]
    manifest = {
        eng: {scn: {"n_records": len(records[eng][scn])}
              for scn in study["scenarios_used"]}
        for eng in _CONTRACT_ENGINES}

    from itsf.s0.stability import build_stability_views
    structural = stage_c_result(ds)
    day_meta = {r.trade_date: {"year": r.year, "era": r.era,
                               "d_open": int(r.labels.d_open or 0)}
                for r in ds.records}
    return {
        # ---- internal envelope (split_envelope; never sealed) -----------
        "dataset": structural["dataset"],
        "na_reason_counts": structural["na_reason_counts"],
        "reported_total_na": structural["reported_total_na"],
        "records": records,
        "study": study,
        # ---- formal sections (report.FORMAL_SECTIONS, flat) -------------
        "structural": _strkeys({
            "funnel_counts": dict(ds.funnel_counts),
            "f10_counts": dict(ds.f10_counts),
            "f10_raw_membership_counts":
                dict(ds.f10_raw_membership_counts),
            "na_table": ds.na_table,
            "label_anchor_availability": ds.label_anchor_availability,
            "eras": {k: list(v) for k, v in ds.eras.items()},
            "groups": {g: {k: list(v) for k, v in m.items()}
                       for g, m in ds.groups.items()},
        }),
        "oracle_daily": {t: {"day_universe":
                             study["per_theta"][t]["day_universe"],
                             "executable":
                             study["per_theta"][t]["executable"]}
                         for t in study["per_theta"]},
        "theoretical_oracle": {t: study["per_theta"][t]["theoretical_oracle"]
                               for t in study["per_theta"]},
        "e2_worst_days": {
            t: {scn: study["per_theta"][t]["executable"]["E2"][scn]
                ["worst_day_report"] for scn in study["scenarios_used"]}
            for t in study["per_theta"]},
        "sizing_outputs": {t: {"rows": study["per_theta"][t]["sizing_rows"],
                               "coverage":
                               study["per_theta"][t]["sizing_coverage"]}
                           for t in study["per_theta"]},
        "frequency": {t: study["per_theta"][t]["frequency"]
                      for t in study["per_theta"]},
        "stability_views": {t: build_stability_views(
            study["per_theta"][t], day_meta,
            vol_axis={d: str(config.vol_axis_of(d)) for d in day_meta})
            for t in study["per_theta"]},
        "bootstrap_ci": _strkeys(bootstrap_ci),
        "feasibility_grid": {"cells": _strkeys(feasibility_grid),
                             "regions": {"status": "pending_mc"}},
        "mc_handoff_manifest": {"counts": manifest},
        "era_axis": {
            "axes": list(ds.eras),
            "counterfactual_disclosure": (
                "counterfactual_micro_execution results are NQ price paths "
                "under MNQ multiplier + 2025Q1 friction — NOT a tradeable "
                "MNQ history (frozen §6).")},
        "disclosures": {
            "untradeable": study["untradeable_disclosure"],
            # single truth source: DERIVED from ResolvedS0Methods (empty by
            # construction — derive_study_config refuses pending methods)
            "pending_method_decisions":
                list(config.methods.pending_fields()),
            "methods_test_only": bool(config.methods.test_only),
            "method_conventions": {
                "quoted_seed_convention": "first frozen seed (7), fixed "
                                          "before any data was seen",
                "stream_tags": "stats 9001 / gridmix 9002 (SeedSequence "
                               "array derivation, disclosed engineering "
                               "convention)",
                "spread_scalars_used": list(config.spread_scalars),
            }},
        "governance": dict(governance_meta),
    }


def _expected_governance() -> dict:
    """Independently RE-derive the governance context from primary sources
    (registry bytes + guards constants) — never from the payload's own
    governance block, so the cross-check catches drift/tampering between
    compute and seal (M6.1.1 S1 wiring)."""
    from itsf import guards as _g
    text = REGISTRY.read_text(encoding="utf-8")
    _row, commit, _reason = find_authorization_event(text)
    return {
        "trial_id": TRIAL_ID,
        "authorized_commit": commit,
        "engineering_seed": ENGINEERING_SEED,
        "frozen_hashes": dict(_g.FROZEN_HASHES),
        "registry_sequence_snapshot": len(parse_registry_events(text)),
    }


def validate_report_contract(payload, *, expected_governance=None
                             ) -> list[str]:
    """M6.1 E3: thin alias — the authoritative validator lives in
    src/itsf/s0/report.py (validate_formal_payload). Kept so older callers
    and tests share one implementation."""
    from itsf.s0 import report as rep
    return rep.validate_formal_payload(
        payload, expected_governance=expected_governance)


class RealChain:
    """Cached real-data chain. Universe/dataset are built at most once per
    process; Stage B reads only structural counts from them, Stage C returns
    the same cached dataset (no recompute, no drift)."""

    def __init__(self) -> None:
        self._ds = None
        self._uni = None
        self._bars = None

    def ready(self) -> tuple[bool, str]:
        missing = [str(p) for p in (F10_CSV, SYMBOLOGY_CSV,
                                    A1_JOB_DIR / "condition.json",
                                    A1_JOB_DIR / "manifest.json")
                   if not p.exists()]
        if missing:
            return (False, f"stage-C artifacts missing: {missing}")
        # M6.1 E1: readiness and compute share resolved_study_config —
        # ready() can never say True while compute() would refuse.
        cfg, why = resolved_study_config()
        if cfg is None:
            return (False, f"stage-C fail-closed pre-exposure: {why}")
        return (True, "stage C wiring ready (full study chain)")

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
            self._bars = bars_by_date          # M6: retained for the study
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
        # so reconstruct it FROM THE TEMPLATE and hash that (binds the
        # snapshot to the sentence; distinct commits yield distinct hashes;
        # SA-12: deriving here keeps template/snapshot in lockstep while the
        # regression test pins the exact bytes independently).
        sentence = AUTHORIZATION_SENTENCE_TEMPLATE.format(
            trial_id=TRIAL_ID, commit=commit) if commit else ""
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
        # M6.1 E1: SAME predicate as ready() — refusal here is unreachable
        # when Stage B passed, and precedes any data load either way.
        cfg, why = resolved_study_config()
        if cfg is None:
            raise RuntimeError(f"stage-C config unavailable: {why}")
        ds, _uni = self._ensure()
        from itsf import guards as _g
        text = REGISTRY.read_text(encoding="utf-8")
        _row, commit, _reason = find_authorization_event(text)
        gov = {
            "trial_id": TRIAL_ID,
            "authorized_commit": commit,
            "engineering_seed": ENGINEERING_SEED,
            "frozen_hashes": dict(_g.FROZEN_HASHES),
            "registry_sequence_snapshot": len(parse_registry_events(text)),
        }
        return build_full_study_result(ds, self._bars, config=cfg,
                                       governance_meta=gov)


# =========================================================================
# Aaron 2026-08-02 §三: authorization snapshot control
# =========================================================================

def make_snapshot_control(chain: "RealChain", attempts_dir: Path):
    """Build the three §三 mechanisms around one shared in-memory snapshot.

    Module-level factory (SA-12 N-B): tests execute THESE closures — the
    same objects main() wires into RunnerDeps — so the production
    comparison and both side-effects are directly regression-tested. A
    fail-open mutation of the recheck comparison turns the suite red.

    Returns (stage_a_gate, pre_exposure_recheck, post_run_started_hook).
    """
    state: dict = {}

    def g_authorization_snapshot():
        snap = chain.authorization_snapshot()
        if not snap["authorized_commit"]:
            return (False, "no RUN_AUTHORIZED event to snapshot")
        attempts_dir.mkdir(parents=True, exist_ok=True)
        (attempts_dir / "AUTHORIZATION_SNAPSHOT.json").write_text(
            json.dumps(snap, indent=1, sort_keys=True), encoding="utf-8")
        state["snapshot"] = snap
        return (True, "authorization snapshot recorded")

    def pre_exposure_recheck():
        before = state.get("snapshot")
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
                        "snapshot_before": state.get("snapshot", {})},
                       indent=1, sort_keys=True), encoding="utf-8")

    return (g_authorization_snapshot, pre_exposure_recheck,
            post_run_started_hook)


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
        engineering_seed=ENGINEERING_SEED,
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

    # Aaron 2026-08-02 §三 — built by the module-level factory so the
    # EXACT production closures are what tests execute (SA-12 N-B).
    (g_authorization_snapshot, pre_exposure_recheck,
     post_run_started_hook) = make_snapshot_control(
        chain, Path(cfg.attempts_dir))

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
