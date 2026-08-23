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
# L-5 ruling (Aaron 2026-08-10): governed output roots move OUT of the
# OneDrive-synced repo tree to the ruled local roots in contracts. The
# constants below keep their historical ROLES (build_gates()'s runs_root
# param; direct parents of the per-run dirs) — only their VALUES move.
# Monkeypatchable exactly like before.
from itsf.contracts import (RULED_ARCHIVE_ROOT as _RULED_ARCHIVE_ROOT,
                            RULED_RUNS_ROOT as _RULED_RUNS_ROOT)
GOVERNED_RUNS_ROOT = Path(_RULED_RUNS_ROOT)     # == RunConfig.runs_root default
GOVERNED_ARCHIVE_ROOT = Path(_RULED_ARCHIVE_ROOT)
RUNS_ROOT = GOVERNED_RUNS_ROOT / "runs"
ATTEMPTS_ROOT = GOVERNED_RUNS_ROOT / "attempts"

# Baseline collected-test count at the SA-6 audit commit. The pytest gate
# requires the suite to still COLLECT at least this many tests, so a muted
# or filtered run cannot satisfy the gate with a handful of tests (F-09).
MIN_COLLECTED_TESTS = 3977                  # N06 round-3 seal redesign: floor = current suite

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
            # L-5 ruling (Aaron 2026-08-10): the governed output roots are
            # in-process pinned facts like every other frozen constant.
            ("contracts.RULED_RUNS_ROOT", _c.RULED_RUNS_ROOT,
             r"C:\Users\Aaron\quant-data\itsf-runs"),
            ("contracts.RULED_ARCHIVE_ROOT", _c.RULED_ARCHIVE_ROOT,
             r"C:\Users\Aaron\quant-data\itsf-runs-archive"),
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


def _partition_admission(candidates, all_probs):
    """M6.1.3 fix-round-2 (blind-audit N1b): per-name attribution of the
    batched formal_seal_admission problems. The '{name}: ' prefix scheme
    is only injective while no candidate name embeds the delimiter —
    enforced here, so a colliding name can never misattribute another
    artifact's refusal reasons into the sealed admission record. Any
    problem string attributable to no candidate fails the render closed."""
    # auditor-2 LOW-4: names must be STRINGS before any substring test —
    # a non-str name is its own refusal, never a TypeError out of the gate.
    nonstr = sorted(repr(n) for n in candidates if not isinstance(n, str))
    if nonstr:
        raise ValueError("candidate artifact names must be strings: "
                         + ", ".join(nonstr))
    bad = sorted(n for n in candidates if ": " in n)
    if bad:
        raise ValueError("candidate artifact names must not contain the "
                         "': ' attribution delimiter: " + ", ".join(bad))
    stray = [p for p in all_probs
             if not any(p.startswith(f"{n}: ") for n in candidates)]
    if stray:
        raise ValueError("admission problems not attributable to any "
                         "candidate artifact: " + "; ".join(stray))
    admitted: dict[str, object] = {}
    withheld: dict[str, list[str]] = {}
    for fname, artifact in candidates.items():
        probs = [p for p in all_probs if p.startswith(f"{fname}: ")]
        (withheld if probs else admitted)[fname] = probs or artifact
    return admitted, withheld


def render_s0_report(result, *, expected_governance=None,
                     governance_context=None,
                     methods=None,
                     key_claims_authority=None) -> dict[str, str]:
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
        # M6.1.4 (main-2): the renderer REFUSES to seal without captured
        # canonical evidence, and the formal payload's evidence-covered
        # sections are BUILT from the evidence via pure reducers — the
        # compute tree's pre-aggregated copies are no longer authoritative
        # for them (reconcile_with_internal below still cross-checks the
        # producer aggregates against the result, so a reducer-vs-producer
        # divergence is a hard failure, not a silent override).
        from itsf.s0 import evidence as ev
        evd = result.get("evidence")
        if evd is None:
            raise ValueError("canonical evidence missing from the compute "
                             "result — refusing to seal (the formal payload "
                             "must be rebuilt from captured atoms)")
        formal = {k: (dict(v) if isinstance(v, dict) else v)
                  for k, v in formal.items()}

        def _differs(a, b):
            try:
                return a != b
            except Exception:
                return True     # unequal-on-exception: fail closed

        # The evidence-built value REPLACES the producer copy in the sealed
        # payload — but a DIVERGENCE between them is a hard refusal, never a
        # silent repair: it means the producer aggregate and the captured
        # atoms disagree (a bug or a tamper), and sealing over either
        # version would hide that.
        diverged: list[str] = []
        for red_key, reducer in ev.reducers.items():
            built = ev.to_plain(reducer(evd))
            if red_key == "oracle_daily.day_universe":
                for tk, du in built.items():
                    cell = dict(formal["oracle_daily"][tk])
                    if _differs(du, cell.get("day_universe")):
                        diverged.append(f"{red_key}:{tk}")
                    cell["day_universe"] = du
                    formal["oracle_daily"] = {**formal["oracle_daily"],
                                              tk: cell}
            elif "." in red_key:
                sect, sub = red_key.split(".", 1)
                if _differs(built, formal[sect].get(sub)):
                    diverged.append(red_key)
                formal[sect] = {**formal[sect], sub: built}
            else:
                if _differs(built, formal.get(red_key)):
                    diverged.append(red_key)
                formal[red_key] = built
        if diverged:
            raise ValueError(
                "evidence-reducer divergence from producer output — "
                "refusing to seal: " + "; ".join(sorted(diverged)))
        problems = rep.validate_formal_payload(
            formal, expected_governance=expected_governance)
        if problems:
            raise ValueError("report contract violations: "
                             + "; ".join(problems))
        # M6.1.3 (main-4): INDEPENDENT reconciliation of the formal payload
        # against the internal producer envelope — `result` is the RAW
        # build_full_study_result dict (carries "study"/"records"), never
        # the formal payload passed back to itself (reconcile_with_internal
        # rejects that shape as missing internal keys).
        rec = rep.reconcile_with_internal(result, formal)
        if rec:
            raise ValueError("internal reconciliation failed: "
                             + "; ".join(rec))
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
        # M6.1.2 (Codex S2-3): the `formal_sealable` flags are now CONSUMED.
        # An artifact that is not sealable is WITHHELD from the sealed set —
        # it is never sealed while carrying a False flag — and the refusal
        # is itself recorded in a sealed admission record, so the withheld
        # state is disclosed rather than silent.
        candidates = {"SEED_MANIFEST.json":
                      ho.build_seed_manifest(methods=methods)}
        # M6.1.3 fix-round (blind-audit D44/F9): ONE admission call over
        # the WHOLE candidate set — formal_seal_admission's cross-artifact
        # checks (grid per-cell seeds vs the seed manifest) only see
        # artifacts supplied in the SAME call, so the earlier per-file
        # loop made that check unreachable in production.
        admitted, withheld = _partition_admission(
            candidates,
            ho.formal_seal_admission(
                candidates,
                source=ho.source_context_for_methods(methods))
            if methods is not None
            else ho.formal_seal_admission(candidates))
        for fname, artifact in admitted.items():
            files[fname] = ho.dumps_canonical(artifact)
        # M6.1.4 (main-2): EVIDENCE RECONCILIATION over the ACTUAL bytes
        # about to be sealed — the JSONL records are parsed back and the
        # formal payload is reconciled against the captured atoms. HARD
        # problems refuse the seal; PARTIAL markers are DISCLOSED in the
        # sealed admission record (honest coverage, never a silent claim).
        ev_flat = ev.reconcile_with_evidence(evd, formal, files)
        ev_hard, ev_partial = ev.split_problems(ev_flat)
        if ev_hard:
            raise ValueError("evidence reconciliation failed: "
                             + "; ".join(ev_hard))
        # DR-5 staged boundary (explicit Fable delegation, 2026-08-10;
        # R5.1 B2): the block comes from handoff.build_dr5_staged_boundary
        # — the SINGLE source the seal-time validator and the default-refuse
        # consumer gate share — and is VALIDATED before the admission record
        # is serialized. A non-empty problem list refuses the seal.
        admission_record = {
            "schema_version": ho.SCHEMA_VERSION,
            "admitted": sorted(admitted),
            "withheld": dict(sorted(withheld.items())),
            "dr5_staged_boundary": ho.build_dr5_staged_boundary(),
            "evidence_reconciliation": {
                # computed from the actual reconcile result — reaching this
                # line proves it was empty (a non-empty list raised above),
                # but the sealed claim is never a hardcoded literal.
                "hard_problems": list(ev_hard),
                "partial_coverage": list(ev_partial)},
            "note": ("artifacts whose formal_sealable flag is not True are "
                     "WITHHELD from the sealed set (condition-driven; the "
                     "DR-M6 rulings landed 2026-08-10 — remaining blockers "
                     "are per-artifact: TEST_ONLY methods, an absent "
                     "methods context, or the MC-side replay wiring); "
                     "DAY_STRATA / GRID_SAMPLES are not built by this "
                     "renderer yet (schema skeletons in "
                     "src/itsf/s0/handoff.py)"),
        }
        dr5_problems = ho.validate_dr5_staged_boundary(
            admission_record["dr5_staged_boundary"])
        if dr5_problems:
            raise ValueError("dr5 staged boundary invalid at seal: "
                             + "; ".join(dr5_problems))
        files["HANDOFF_ADMISSION.json"] = ho.dumps_canonical(admission_record)
        files["S0_REPORT.md"] = "\n".join([
            "# S0 FORMAL REPORT (sealed at Stage E)", "",
            "- formal payload: S0_REPORT.json (single sealed release)",
            "- MC handoff records: MC_HANDOFF_<engine>_<scenario>.jsonl",
            "- handoff admission: HANDOFF_ADMISSION.json (which handoff "
            "artifacts were admitted / withheld and why)",
            "- DAY_STRATA/GRID_SAMPLES/SEED_MANIFEST: admitted to the "
            "sealed set ONLY while their formal_sealable flag is True "
            "(condition-driven; the DR-M6 rulings landed 2026-08-10 — "
            "remaining per-artifact blockers are TEST_ONLY methods or the "
            "MC-side replay wiring); schema skeletons in "
            "src/itsf/s0/handoff.py"])
        formal = dict(formal)
        # M6.1.2 (audit N18): EVERY file this renderer writes carries an
        # integrity entry — an extra planted file, or a sealed file with
        # no hash, is refused. S0_REPORT.json is SELF-EXCLUDED because it
        # carries the manifest (same discipline as the runinfra JSONL
        # hash chain); Stage F's chain seal covers it.
        formal["mc_handoff_manifest"] = {
            **formal["mc_handoff_manifest"], "files": file_manifest,
            "sealed_files": {
                name: {"sha256": hashlib.sha256(
                           body.encode("utf-8")).hexdigest(),
                       "bytes": len(body.encode("utf-8"))}
                for name, body in sorted(files.items())},
            "self_excluded": ["S0_REPORT.json"]}
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
        # re-verified against the actual bytes before sealing. M6.1.4
        # (B0 CR-7): the renderer no longer passes its own universe — the
        # validator's INDEPENDENT derivation from the payload is the live
        # path, not dead code shadowed by a caller override.
        post = rep.validate_sealed_files(files, formal)
        if post:
            raise ValueError("sealed-file verification failed: "
                             + "; ".join(post))
        # F-2 key-claims PRE-WRITE screen (Aaron 2026-08-10): the closed
        # six-claim battery against independent sources — locked assertions
        # bytes, the caller's validated method rulings, the evidence verdict
        # taken above. Runs AFTER manifest injection so KC4 sees the sealed
        # name set. Gated on `methods` exactly like the admission context and
        # the governance screen: the PRODUCTION chain always supplies it
        # (pinned by the chain tests); a direct legacy call without methods
        # renders unscreened, same as it renders un-admitted.
        if methods is not None:
            from itsf.s0 import output_proof as _op_kc
            kc = _op_kc.verify_key_claims(
                formal,
                _op_kc.ResearchClaimsContext(
                    # R4 B2: the PRODUCTION chain supplies the prepared
                    # run-scoped authority (bytes + exact L3); the module
                    # fallback read is a pre-exposure/legacy-direct-call
                    # convenience only (chain-pinned).
                    assertions_bytes=(key_claims_authority[0]
                                      if key_claims_authority is not None
                                      else _read_key_claims_assertions()),
                    exact_l3_dates=(key_claims_authority[1]
                                    if key_claims_authority is not None
                                    else None),
                    ruled_methods=methods,
                    evidence_problems=list(ev_flat),
                    disk_report=None),
                phase="pre_write")
            if not kc.sealable_pre_write:
                raise ValueError("key-claims pre-write screen failed: "
                                 + "; ".join(kc.problems))
        # M6.1.6 (S2 slice) — INDEPENDENT governance proof, run LAST, on the
        # FINAL S0_REPORT.json bytes. Placement is the whole point: the
        # M6.1.4 evidence pass ran before three of the eleven sealed files
        # existed, so its target could not have been the sealed set. This
        # runs after every file is in `files`.
        #
        # The expected side is built from a PRE-RUN context supplied by the
        # caller — never from `result`, `formal`, or the evidence mirror. A
        # renderer that is not given a context cannot manufacture one from
        # the thing it is verifying, so the proof is SKIPPED rather than
        # faked; production wires it (see `main()`), and that wiring is
        # pinned by test. Scope: this proves the five contract keys of
        # `governance.*` against independent sources — it does NOT byte-bind
        # the report to the registry (see the proof's own PARTIAL list).
        # M6.1.7: what runs HERE is only a PRE-WRITE SCREEN. The renderer
        # holds strings, not files, so a verdict taken here can only say
        # "what I am about to write is correct" — which is what M6.1.6's
        # CLOSED actually meant, and precisely why it missed that 9 of 10
        # artifacts landed on disk with different bytes than the manifest
        # declared. The screen's job is to stop a wrong governance block
        # from ever becoming a file; the RELEASE verdict is taken after the
        # bytes exist, by `RealChain.post_write_verify`. The screen returns
        # a `DraftScreen`, which has no `ok` field and raises on `bool()`,
        # so this cannot be mistaken for the release gate.
        if governance_context is not None:
            from itsf.s0 import output_proof as _op
            screen = _op.screen_governance_draft(governance_context,
                                                 draft_artifacts=files)
            if screen.blocking_problems:
                raise ValueError("governance draft screen failed: "
                                 + "; ".join(screen.blocking_problems))
        return files
    raise ValueError(
        "render_s0_report: refusing non-study payload — the legacy "
        "structural-only seal path was removed (M6.1 O1); production "
        "sealing requires the full formal payload")

def _resolved_methods():
    """M6.1 E1 — the ONLY method-ruling state source (contracts dataclass).

    S0 closeout (Aaron 2026-08-10, IR-27): ALL EIGHT DR rulings landed —
    this now returns the fully-resolved ruled instance from the single
    ruled source in contracts. The fail-closed machinery downstream
    (pending_fields / structural_problems / Stage-B refusal) is unchanged
    and still guards against any future un-ruling or drive-by edit."""
    from itsf.contracts import aaron_ruled_methods
    return aaron_ruled_methods()


# Derived, never hand-written (E1): the live pending list.
PENDING_METHOD_DECISIONS: tuple[str, ...] = _resolved_methods().pending_fields()


from itsf.contracts import (StudyConfig,          # noqa: E402
                            is_canonical_spread_scalars as _is_canon_scalars,
                            is_canonical_ticks as _is_canon_ticks,
                            ResolvedS0Methods as _RSM,
                            SpreadCostMethod as _SCM,
                            VolatilityRegimeMethod as _VRM,
                            FpAllocationMethod as _FAM,
                            BootstrapMethod as _BM,
                            GridRepeatPolicy as _GRP)
import math as _math                                     # noqa: E402
from types import MappingProxyType as _MProxy            # noqa: E402
from collections.abc import Mapping as _Mapping          # noqa: E402


_CONFIG_CACHE: dict = {}


#: sha256 pin of the ONLY approved cost-side input (S0 authorization packet
#: line "spread_cost_table.csv SHA-256 ... 唯一允许的成本侧输入"). The
#: injectable source refuses a table whose bytes drift from this pin.
SPREAD_COST_TABLE_PATH = REPO / "spread_cost_table.csv"
SPREAD_COST_TABLE_SHA256 = (
    "b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf")

#: F-2 key-claims independent source: the locked compare-only assertions
#: file. Module-level so the synthetic e2e can point it at a synthetic
#: assertions file matching its synthetic market; production leaves it at
#: the locked artifact (same discipline as RUNS_ROOT). Codex r2: the BYTES
#: are sha256-pinned exactly like the spread table — the KC gate's
#: independent source cannot drift silently. Tests patch BOTH names.
KEY_CLAIMS_ASSERTIONS_PATH = REPO / "S0_INPUT_PREFLIGHT.json"
KEY_CLAIMS_ASSERTIONS_SHA256 = (
    "9d6dd1c15602f6188e0b85754118dd51eb81b65cd60a086a133dee1bb14debd6")


def _read_key_claims_assertions() -> bytes:
    """The locked assertions bytes, sha256-verified against the pin.
    A drifted file is a hard refusal, never a silent acceptance."""
    raw = Path(KEY_CLAIMS_ASSERTIONS_PATH).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != KEY_CLAIMS_ASSERTIONS_SHA256:
        raise RunGateError(
            "key-claims assertions file drifted from its pin: "
            f"{digest} != {KEY_CLAIMS_ASSERTIONS_SHA256}")
    return raw


class _BindableDayLabelResolver:
    """A STABLE injectable callable (G11 identity rule: the source must hand
    out the same object on every call — never a fresh lambda).

    Unbound until Stage B binds it to the per-day label mapping built from
    the loaded universe (pre-exposure); calling it unbound raises. Post-
    exposure code never calls it at all — `RealChain.prepare` materializes
    an immutable value snapshot (context.materialize_day_value_snapshot)
    and the compute path consumes ONLY the snapshot (F-1 boundary)."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._mapping = None

    def bind(self, mapping) -> None:
        self._mapping = dict(mapping)

    def __call__(self, trade_date):
        if self._mapping is None:
            raise RuntimeError(
                f"injectable {self._name} is unbound — it binds in Stage B "
                "from the loaded universe (pre-exposure) and may never be "
                "called before binding or after exposure (F-1: the compute "
                "path consumes the prepared value snapshot instead)")
        return self._mapping[trade_date]


# Module singletons — STABLE object identity across gateway calls (G11).
_REGIME_RESOLVER = _BindableDayLabelResolver("regime_of")
_VOL_AXIS_RESOLVER = _BindableDayLabelResolver("vol_axis_of")


def _read_locked_spread_table():
    """Locked cost-side table bytes -> parsed rows, sha256-pinned first.
    Cost-calibration output only (prereg §1: the alpha side may read this
    table and nothing rawer); NOT research price data."""
    raw = SPREAD_COST_TABLE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SPREAD_COST_TABLE_SHA256:
        raise RunGateError(
            "spread_cost_table.csv drifted from the authorization-packet "
            f"pin: {digest} != {SPREAD_COST_TABLE_SHA256}")
    import io
    import pandas as _pd
    return _pd.read_csv(io.BytesIO(raw))


def _approved_injectables():
    """M6.1.3 fix-round (blind-audit F3) -> S0 closeout (Aaron 2026-08-10):
    the production source of the DERIVED StudyConfig inputs.

    spread_scalars: RE-DERIVED on EVERY call from the sha256-pinned locked
    spread_cost_table.csv per the RULED DR-1 reduction
    (costs.derive_spread_scalars, rule B-i). No cache: the gateway is
    built on distrusting caches (conformance F2.2 — a poisoned-but-
    schema-valid cached triple would trivially equal its own fingerprint),
    and the derivation is milliseconds. The triple is value-stable across
    calls because the pinned bytes are.
    regime_of / vol_axis_of: the module-singleton bindable resolvers
    (STABLE identity per G11); both resolve from the ONE shared DR-2
    mapping (mapping_scope=shared_s2_and_appendixA) once Stage B binds it.
    Any failure here surfaces as a Stage-B refusal (fail closed), never a
    silent None-derived default."""
    from itsf.s0 import costs as _costs
    methods = _resolved_methods()
    table = _read_locked_spread_table()
    scalars = _costs.derive_spread_scalars(table, methods.spread_cost)
    return {
        "spread_scalars": tuple(float(v) for v in scalars),
        "regime_of": _REGIME_RESOLVER,
        "vol_axis_of": _VOL_AXIS_RESOLVER,
    }


# =========================================================================
# THE CONFIGURATION GATEWAY (M6.1.4-ARCH, finding F-1)
# =========================================================================
# ONE deterministic path resolves the study configuration, and BOTH
# RealChain.ready() and RealChain.compute() consume it through the single
# entry `resolved_study_config()`.
#
# WHY A GATEWAY AND NOT MORE GUARDS. F-1 was raised, patched at the three
# sites it named, and RECURRED. An independent read-only reproduction on
# this worktree found FOUR live escapes through the public `ready()`
# contract, not the two the report named: the cache 2-tuple unpack, the
# `cfg.methods !=` comparison, AND BOTH HALVES of the `cfg != fresh_cfg`
# comparison a few lines below it (a hostile `__eq__` on a callable field,
# and a numpy `spread_scalars` whose truth value is ambiguous). Enumerating
# sites is precisely what failed. The defence is therefore STRUCTURAL:
#
#   1. no evaluation point executes foreign code in the first place --
#      types are pinned with `type(x) is C` BEFORE any attribute read,
#      equivalence is decided on NON-EXECUTING fingerprints built only from
#      strictly-normalized atoms (str/int/float/bool/None and tuples
#      thereof), and the two config callables are compared by in-process
#      object IDENTITY, never by `==`/`!=`;
#   2. a SINGLE trust boundary (`_run_guarded`) converts anything that
#      still escapes into a deterministic, stage-attributed refusal.
#
# (2) is the backstop, never the primary defence. Every refusal happens
# before the compute builder, before any real data load, before runs/
# creation and before exposure -- Stage B holds the whole thing.


#: Gateway stages in EXECUTION order. The G-numbers follow the M6.1.4-ARCH
#: enumeration of evaluation points (see `_EVALUATION_POINTS`); the tuple
#: order is the pipeline order, which differs -- G7 runs before G6/G10
#: because the FRESH approved source is the authority: if the authority is
#: not ready, nothing about a cached object matters.
_GATE_STAGES: tuple[str, ...] = (
    "G1_cache_read",
    "G2_cache_envelope",
    "G3_config_type",
    "G4_methods_type",
    "G4b_test_only",
    "G5_method_source",
    "G5b_source_test_only",
    "G7_pending",
    "G7b_structural",
    "G10_methods_fingerprint",
    "G10_methods_canonical_form",
    "G10_methods_equivalence",
    "G6_injectable_source",
    "G8_injectable_schema",
    "G9_derivation",
    "G11_config_fingerprint",
    "G11_config_canonical_form",
    "G11_callable_identity",
    "G11_config_equivalence",
    "G12_cache_write",
    "G13_point_of_use",
)

#: Mandated evaluation point -> the stage(s) that cover it. NO GATE-COUNT
#: THEATRE: eleven of the thirteen are real stages with their own refusal,
#: but (12) is ATTRIBUTION-ONLY -- an in-process cache write has no
#: legitimate failure mode unless `_CONFIG_CACHE` has itself been replaced
#: -- and (13) is not a stage at all but the SINGLE-PATH INVARIANT: the
#: gateway has exactly one code path, so G3..G11 execute on EVERY call,
#: whether the config came from the cache or was derived this call.
_EVALUATION_POINTS: dict[int, tuple[str, ...]] = {
    1: ("G1_cache_read",),
    2: ("G2_cache_envelope",),
    3: ("G3_config_type",),
    4: ("G4_methods_type", "G4b_test_only"),
    5: ("G5_method_source", "G5b_source_test_only"),
    6: ("G6_injectable_source",),
    7: ("G7_pending", "G7b_structural"),
    8: ("G8_injectable_schema",),
    9: ("G9_derivation",),
    # M6.1.4-R2: points (10) and (11) each carry TWO SEPARATE OBLIGATIONS --
    # value EQUIVALENCE against a fresh derivation (binary), and
    # REPRESENTATION IDENTITY of the object itself (unary). They are distinct
    # STAGES with distinct refusals rather than new evaluation points: the
    # thirteen points are the M6.1.4-ARCH enumeration and are not rewritten
    # here. Representation is checked BEFORE equivalence on each side, so a
    # non-canonical cache refuses AS non-canonical.
    10: ("G10_methods_fingerprint", "G10_methods_canonical_form",
         "G10_methods_equivalence"),
    11: ("G11_config_fingerprint", "G11_config_canonical_form",
         "G11_callable_identity", "G11_config_equivalence"),
    12: ("G12_cache_write",),
    13: ("G13_point_of_use",),
}

_MISSING = object()                      # "no cache entry", never a value
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.]")


class _ConfigCacheEntry:
    """The ONLY admissible value of ``_CONFIG_CACHE['cfg']``.

    An EXACT internal envelope, never an arbitrary 2-iterable. It is
    identified by ``type(x) is _ConfigCacheEntry`` and is NEVER unpacked,
    iterated, measured or compared -- so a plain object, a 1/2/3-tuple, a
    dict, or an iterator that detonates on read all refuse identically at
    G2 WITHOUT a single attribute being touched. That retires the whole
    ``too many values to unpack`` class, not the three shapes F-1 named.

    A ``__slots__`` immutable class rather than a frozen dataclass, for
    two reasons. (a) `scripts/s0_real_run.py` is loaded by its tests via
    `spec_from_file_location` WITHOUT being registered in `sys.modules`,
    and `@dataclass` cannot resolve a string annotation under that import
    style. (b) It is strictly MORE INERT: no generated ``__eq__`` (which
    would be a comparison surface we never want), no generated ``__repr__``
    (which would stringify an attacker-influenced config into a diagnostic).

    REFUSALS ARE NOT CACHED (`config` is never None). The cache exists for
    exactly one purpose: giving ready() and compute() the SAME validated
    INSTANCE. A refusal has no instance to share, and caching one would
    make a transient source failure sticky for the process lifetime and
    make the reported reason depend on call order.
    """

    __slots__ = ("config", "reason")

    def __init__(self, config, reason: str) -> None:
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "reason", reason)

    def __setattr__(self, name, value):
        raise AttributeError("_ConfigCacheEntry is immutable")

    def __delattr__(self, name):
        raise AttributeError("_ConfigCacheEntry is immutable")


class _Refusal(Exception):
    """An ENUMERATED, deliberate refusal raised inside a guarded body."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _StageCursor:
    """Names the evaluation point currently executing, for attribution."""

    __slots__ = ("domain", "name")

    def __init__(self, domain: str, first: str) -> None:
        self.domain = domain
        self.name = first

    def at(self, name: str) -> None:
        self.name = name

    def token(self) -> str:
        return f"{self.domain}:{self.name}"


def _safe_type_name(exc) -> str:
    """Sanitized ``type(exc).__name__`` -- ``[A-Za-z0-9_.]``, <= 40 chars.

    The exception TYPE is diagnosable and belongs in the reason string, but
    it is ALSO attacker-controlled: a hostile ``__eq__``/``__iter__`` may
    raise an instance of a class whose ``__name__`` is a multi-kilobyte
    string containing newlines, and that string would travel into
    attempts/PRE_RUN_ATTEMPT_FAILURE.md and past
    runinfra.validate_log_event. So the type name is a payload too, and is
    sanitized rather than trusted.
    """
    try:
        raw = type(exc).__name__
    except BaseException:                            # noqa: BLE001
        return "UNPRINTABLE"
    if type(raw) is not str:
        return "UNPRINTABLE"
    return _SAFE_NAME_RE.sub("?", raw)[:40] or "UNPRINTABLE"


def _code_heads(codes) -> str:
    """Deterministic, PAYLOAD-FREE summary of a problem-code list.

    `contracts.validate_injectables` emits ``extra_key:<repr(key)>`` and
    `ResolvedS0Methods.structural_problems` emits
    ``...adverse_slippage_ticks_value_invalid:<key>`` -- both embed
    attacker-controlled text. Only the code HEAD (a closed vocabulary) is
    reported; the variable tail is dropped.
    """
    heads = set()
    for code in codes:
        if type(code) is not str:
            heads.add("UNPRINTABLE")
            continue
        heads.add(_SAFE_NAME_RE.sub("?", code.split(":", 1)[0])[:80])
    return ", ".join(sorted(heads)) or "none"


def _refuse(cursor: _StageCursor, stage: str, clause: str):
    """Advance the cursor and raise the enumerated refusal for `stage`."""
    cursor.at(stage)
    raise _Refusal(f"{cursor.domain}:{stage}: {clause}")


def _run_guarded(body, cursor: _StageCursor, failure):
    """THE SINGLE TRUST BOUNDARY of the configuration path (finding F-1).

    `body(cursor)` is a straight-line pipeline that contains NO try/except
    of its own: it raises `_Refusal` for every ENUMERATED refusal, and it
    advances `cursor` before every evaluation point, so that an
    UNENUMERATED explosion -- including one raised by foreign code we never
    intended to run -- is attributed to the exact stage that was executing.

    Coverage here is STRUCTURAL, not per-site: any evaluation point added
    to `body` in future is already guarded and already attributed, without
    anyone remembering to wrap it. The previous round of this defect
    recurred precisely because it patched named line numbers instead of
    installing a boundary.

    COST OF `BaseException`: a KeyboardInterrupt or SystemExit raised
    inside `body` is converted into a refusal rather than propagating.
    That is deliberate and it is not free. It is the right trade here
    because the guarded bodies are short, deterministic and entirely
    PRE-EXPOSURE (no data load, no runs/ creation, no atomic run-start),
    so refusing is the safe direction -- and because a hostile
    ``__eq__``/``__iter__`` may raise a non-`Exception` class, which a bare
    ``except Exception`` would let escape the public (bool, str) contract.
    """
    try:
        return body(cursor)
    except _Refusal as ref:
        return failure(ref.reason)
    except BaseException as exc:                     # noqa: BLE001
        return failure(f"{cursor.token()}: unexpected "
                       f"{_safe_type_name(exc)} inside the guarded body "
                       f"— fail closed")


# --- non-executing normalization atoms ------------------------------------
# Every atom pins the EXACT type before it does anything else, and a value
# that cannot be normalized without executing foreign code is ITSELF A
# REFUSAL (the `_NotNormalizable` sentinel), never a silent skip.

class _NotNormalizable:
    """Sentinel: this value cannot be normalized without executing foreign
    code. Deliberately inert -- no ``__eq__``, no ``__getattr__``, no
    ``__iter__``; it is recognised by ``type(x) is _NotNormalizable``."""

    __slots__ = ("rule",)

    def __init__(self, rule: str) -> None:
        self.rule = rule


def _atom_str(value):
    # `type(...) is str`, not isinstance: a str SUBCLASS can override
    # __eq__, and the fingerprint tuples are compared with `==`.
    return value if type(value) is str else _NotNormalizable("expected_str")


def _atom_int(value):
    # `type(...) is int` deliberately EXCLUDES bool (a subclass of int), so
    # True can never occupy an int slot and compare equal to 1.
    return value if type(value) is int else _NotNormalizable("expected_int")


def _atom_bool(value):
    return (value if type(value) is bool
            else _NotNormalizable("expected_bool"))


def _atom_number(value):
    """Exact int/float -> canonical finite non-negative plain float.

    numpy scalars, Decimal and custom ``numbers.Real`` registrations are
    REFUSED: admitting them would put ``__float__``/``__index__`` dispatch
    inside the gate. This costs nothing, because both sides of every
    fingerprint comparison are StudyConfig instances whose __post_init__
    has already rewritten spread_scalars to plain floats via
    contracts.canonical_spread_scalars.
    """
    if type(value) is int:
        if value < 0 or value >= 9007199254740993:   # 2**53 + 1
            return _NotNormalizable("int_out_of_exact_float_range")
        value = float(value)
    elif type(value) is not float:
        return _NotNormalizable("expected_int_or_float")
    if not _math.isfinite(value):
        return _NotNormalizable("expected_finite_number")
    if value < 0.0:
        return _NotNormalizable("expected_non_negative_number")
    return 0.0 if value == 0.0 else value            # collapses -0.0


def _atom_ticks(value):
    """Adverse-slippage mapping -> sorted tuple of (str, float) atoms.

    BOUNDARY-GUARDED, NOT NON-EXECUTING -- the one documented residual of
    this design. `contracts._canonical_ticks` rewrites a Mapping to
    ``MappingProxyType(dict(...))`` but returns a caller-supplied
    MappingProxyType UNCHANGED, and a mappingproxy delegates
    ``__iter__``/``items()`` to its underlying mapping, which may be a dict
    SUBCLASS with an overridden ``__iter__``. CPython exposes no API to
    reach the underlying object, and refusing MappingProxyType outright
    would refuse every legitimately-constructed SpreadCostMethod. So this
    single read may run foreign code; it cannot ESCAPE (the boundary in
    `_run_guarded` turns it into a deterministic, stage-attributed
    refusal), and no COMPARISON is involved. Sorting is safe because both
    members of every pair are already pinned to exact builtins.
    """
    if type(value) is not dict and type(value) is not _MProxy:
        return _NotNormalizable("expected_dict_or_mappingproxy")
    pairs = []
    for key, val in value.items():
        k = _atom_str(key)
        if type(k) is _NotNormalizable:
            return _NotNormalizable("ticks_key." + k.rule)
        v = _atom_number(val)
        if type(v) is _NotNormalizable:
            return _NotNormalizable("ticks_value." + v.rule)
        pairs.append((k, v))
    return tuple(sorted(pairs))


#: EXPLICIT per-field rules for the structured method sub-items. Never
#: reflection: tests/test_m6_chain.py pins that each table's key set equals
#: the dataclass's field set, so a NEW field turns the suite RED instead of
#: being silently dropped from the fingerprint.
_METHOD_SUB_RULES: dict = {
    "SpreadCostMethod": (_SCM, (
        ("scalar_rule", _atom_str),
        ("adverse_slippage_ticks", _atom_ticks),
        ("adverse_semantics", _atom_str))),
    "VolatilityRegimeMethod": (_VRM, (
        ("close_source", _atom_str),
        ("return_basis", _atom_str),
        ("ddof", _atom_int),
        ("roll_crossing_rule", _atom_str),
        ("tercile_reference", _atom_str),
        # DR-2 ruling 2026-08-10: mapping_scope is fingerprint-carried like
        # every other ruled string (explicit, never reflection).
        ("mapping_scope", _atom_str),
        ("na_rule", _atom_str))),
    "FpAllocationMethod": (_FAM, (
        ("basis", _atom_str),
        ("weight_source", _atom_str),
        ("shortfall_rule", _atom_str))),
    "BootstrapMethod": (_BM, (
        ("population", _atom_str),
        ("na_day_rule", _atom_str),
        ("statistic", _atom_str),
        ("n_boot_per_seed", _atom_bool),
        ("quoted_seed_rule", _atom_str),
        ("percentile_interpolation", _atom_str),
        ("crn_scope", _atom_str))),
    "GridRepeatPolicy": (_GRP, (
        ("k_per_seed", _atom_int),
        ("k_start_index", _atom_int),
        ("stream_includes_theta", _atom_bool),
        ("convergence_rule", _atom_str),
        ("max_doublings", _atom_int))),
}


def _norm_sub(kind: str, value):
    """Normalize one structured method sub-item, or return the sentinel."""
    cls, rules = _METHOD_SUB_RULES[kind]
    # EXACT type pin BEFORE any attribute read -- stricter than
    # structural_problems()'s isinstance, and that is the point: a subclass
    # with an overriding property must refuse, not run.
    if type(value) is not cls:
        return _NotNormalizable("expected_exact_" + kind)
    out = [kind]
    for name, atom in rules:
        got = atom(getattr(value, name))
        if type(got) is _NotNormalizable:
            return _NotNormalizable(f"{kind}.{name}.{got.rule}")
        out.append(got)
    return tuple(out)


def _sub_rule(kind: str):
    def _rule(value):
        return None if value is None else _norm_sub(kind, value)
    return _rule


def _opt_str(value):
    return None if value is None else _atom_str(value)


#: EXPLICIT per-field rules for ResolvedS0Methods (see _METHOD_SUB_RULES).
_METHODS_FIELD_RULES: tuple = (
    ("spread_cost", _sub_rule("SpreadCostMethod")),
    ("volatility_regime", _sub_rule("VolatilityRegimeMethod")),
    ("fp_allocation", _sub_rule("FpAllocationMethod")),
    ("bootstrap_method", _sub_rule("BootstrapMethod")),
    ("grid_policy", _sub_rule("GridRepeatPolicy")),
    ("event_na_mapping", _opt_str),
    ("stability_population", _opt_str),
    ("worst_day_estimator", _opt_str),
    ("test_only", _atom_bool),
)

#: EXPLICIT rules for the derived injectables. The two callables are NOT
#: fingerprinted -- see G11_callable_identity.
_INJECTABLE_FIELD_RULES: dict = {
    "spread_scalars": "canonical_float_triple_median_le_p90_le_p95",
    "regime_of": "object_identity_only",
    "vol_axis_of": "object_identity_only",
}


#: --- CANONICAL-REPRESENTATION OBLIGATIONS (M6.1.4-R2, F-1 reopened) -------
#: ONE ROW PER FIELD `contracts` REWRITES in a `__post_init__`, and nothing
#: else. F-1 recurred because equivalence was mistaken for interchangeability:
#: the fingerprints above are a NORMALIZING map, and normalization is exactly
#: what erases representation (`_atom_number` widens int->float and collapses
#: -0.0; `_atom_ticks` maps a mutable dict and the canonical read-only
#: mappingproxy to the SAME sorted tuple). So a cached object can be
#: fingerprint-EQUAL to a fresh derivation and still not be the canonical
#: object contracts promises -- and it is the cached INSTANCE that gets
#: handed out.
#:
#: THE CLAIM THESE TABLES MAKE, exactly, and never widened: CANONICAL
#: WHEREVER CONTRACTS SPECIFIES CANONICAL, exact-type-pinned everywhere else.
#: Every predicate below IS the contracts function (by object identity, pinned
#: in tests), so contracts stays the single source and this file defines no
#: second canonicalization rule.
#:
#: EXPLICIT, never reflection: tests/test_m6_chain.py scans contracts for its
#: `object.__setattr__` rewrites and turns RED if a new one appears without a
#: row here -- which is also what automatically extends the ACCEPT-SIDE
#: assertions (see `canonical_form_obligations`).
_METHODS_CANONICAL_RULES: tuple = (
    ("spread_cost", _SCM, "adverse_slippage_ticks", _is_canon_ticks),
)

_CONFIG_CANONICAL_RULES: tuple = (
    ("spread_scalars", _is_canon_scalars),
)


def _methods_canonical_defect(methods) -> str:
    """`""` if every methods-side representation obligation holds, else a
    CLOSED-VOCABULARY description of the first violated one.

    The caller MUST have pinned `type(methods) is _RSM` first. Each row then
    re-pins its own sub-item's EXACT type before reading the canonicalized
    field, so this never relies on a previous stage's side effect. Nothing
    here executes a user object's `__eq__`/`__repr__` or coerces a number:
    the contracts predicates are type pins plus their own producers.
    """
    for name, cls, sub, is_canonical in _METHODS_CANONICAL_RULES:
        value = getattr(methods, name)
        if type(value) is not cls:
            return f"methods.{name} is not exactly a {cls.__name__}"
        if not is_canonical(getattr(value, sub)):
            return (f"methods.{name}.{sub} is not the canonical form "
                    f"contracts specifies")
    return ""


def _config_canonical_defect(cfg) -> str:
    """As `_methods_canonical_defect`, for the config's own fields. The
    caller MUST have pinned `type(cfg) is StudyConfig` first.

    THE TWO CALLABLES ARE DELIBERATELY ABSENT and no canonical form is
    invented for them: they are settled at G11_callable_identity by in-process
    object identity. That is an ENGINEERING CACHE-COHERENCE RULE -- it answers
    "is this the very object the approved injectable source hands out in this
    process?" and NOTHING about what regime_of / vol_axis_of compute. It does
    not define, approve, rank or narrow their research output (DR-1/DR-2 are
    ruled upstream in contracts; this rule is about identity, not content).
    """
    for name, is_canonical in _CONFIG_CANONICAL_RULES:
        if not is_canonical(getattr(cfg, name)):
            return (f"config.{name} is not the canonical form contracts "
                    f"specifies")
    return ""


def canonical_form_obligations(cfg):
    """`(label, holds)` for EVERY canonical-representation obligation,
    evaluated on a config the gateway has ACCEPTED.

    THE ACCEPT-SIDE EXTENSION POINT, and the answer to the root cause of this
    round. The in-repo F-1 regression set (`_F1_CASES` in
    tests/test_m6_chain.py) was TWELVE named hostile shapes and every single
    one asserted a REFUSAL; not one asserted anything about a config the
    gateway ACCEPTS. Two defects that produce an ACCEPT of a non-canonical
    instance therefore sailed straight through it. Tests consume this to
    assert the accepted instance is canonical ON THE WAY OUT, and because it
    is derived from the same tables the gateway stages use, a future
    canonicalized field joins those assertions by adding one table row --
    never by someone remembering to write a new test.

    Read-only and total: it reports, it never refuses. The gateway's own
    refusals live in the two `_..._canonical_defect` helpers.
    """
    out = []
    methods = cfg.methods
    for name, cls, sub, is_canonical in _METHODS_CANONICAL_RULES:
        value = getattr(methods, name)
        out.append((f"methods.{name}.{sub}",
                    type(value) is cls
                    and bool(is_canonical(getattr(value, sub)))))
    for name, is_canonical in _CONFIG_CANONICAL_RULES:
        out.append((f"config.{name}", bool(is_canonical(getattr(cfg, name)))))
    return tuple(out)


def _methods_fingerprint(methods):
    """NON-EXECUTING fingerprint of an EXACT ResolvedS0Methods.

    The caller MUST have pinned ``type(methods) is _RSM`` first; every
    attribute read below is then a plain frozen-dataclass slot on a class
    we own, and every leaf is an exact builtin atom.
    """
    out = ["ResolvedS0Methods"]
    for name, rule in _METHODS_FIELD_RULES:
        got = rule(getattr(methods, name))
        if type(got) is _NotNormalizable:
            return _NotNormalizable(f"{name}.{got.rule}")
        out.append(got)
    return tuple(out)


def _config_fingerprint(cfg, methods_fp):
    """NON-EXECUTING fingerprint of an EXACT StudyConfig.

    CALLABLES ARE DELIBERATELY EXCLUDED: `regime_of` / `vol_axis_of` are
    settled at G11_callable_identity by object identity (see there).
    """
    scal = cfg.spread_scalars
    if type(scal) is not tuple:
        return _NotNormalizable("spread_scalars.expected_tuple")
    if len(scal) != 3:
        return _NotNormalizable("spread_scalars.expected_length_3")
    vals = []
    for i, v in enumerate(scal):
        got = _atom_number(v)
        if type(got) is _NotNormalizable:
            return _NotNormalizable(f"spread_scalars[{i}].{got.rule}")
        vals.append(got)
    m, p90, p95 = vals
    if not (0.0 <= m <= p90 <= p95):
        return _NotNormalizable("spread_scalars.expected_ordered")
    return ("StudyConfig", methods_fp, (m, p90, p95))


def _gateway_body(cursor: _StageCursor):
    """The ONE configuration resolution path. CONTAINS NO try/except.

    Every enumerated refusal raises `_Refusal`; anything unenumerated is
    caught and attributed by the single boundary in `_run_guarded`.
    """
    # ---- (1) cache read --------------------------------------------------
    cursor.at("G1_cache_read")
    entry = _CONFIG_CACHE.get("cfg", _MISSING)

    # ---- (2) EXACT envelope: no unpack, no len, no iteration -------------
    cursor.at("G2_cache_envelope")
    have_cache = entry is not _MISSING
    cached_cfg = None
    cached_reason = ""
    if have_cache:
        if type(entry) is not _ConfigCacheEntry:
            _refuse(cursor, "G2_cache_envelope",
                    "cached entry is not the internal _ConfigCacheEntry "
                    "envelope — fail closed")
        cached_cfg = entry.config
        cached_reason = entry.reason
        if type(cached_reason) is not str:
            _refuse(cursor, "G2_cache_envelope",
                    "cached envelope reason is not a str — fail closed")

    cached_methods = None
    if have_cache:
        # ---- (3) EXACT config type BEFORE any attribute read -------------
        cursor.at("G3_config_type")
        if type(cached_cfg) is not StudyConfig:
            _refuse(cursor, "G3_config_type",
                    "cached object is not exactly a StudyConfig — a "
                    "subclass could override attribute reads; fail closed")
        # ---- (4) EXACT methods type BEFORE any read of a methods field --
        cursor.at("G4_methods_type")
        cached_methods = cached_cfg.methods
        if type(cached_methods) is not _RSM:
            _refuse(cursor, "G4_methods_type",
                    "config.methods is not exactly a ResolvedS0Methods — "
                    "equality is never delegated to a foreign methods "
                    "type")
        cursor.at("G4b_test_only")
        flag = cached_methods.test_only
        if type(flag) is not bool:
            _refuse(cursor, "G4b_test_only",
                    "methods.test_only is not a bool — fail closed")
        if flag:
            _refuse(cursor, "G4b_test_only",
                    "test_only config refused on the production path")

    # ---- (5) approved METHOD source (the AUTHORITY) ----------------------
    cursor.at("G5_method_source")
    fresh_methods = _resolved_methods()
    if type(fresh_methods) is not _RSM:
        _refuse(cursor, "G5_method_source",
                "approved method source did not return exactly a "
                "ResolvedS0Methods — fail closed")
    cursor.at("G5b_source_test_only")
    fresh_flag = fresh_methods.test_only
    if type(fresh_flag) is not bool:
        _refuse(cursor, "G5b_source_test_only",
                "approved method source test_only is not a bool — fail "
                "closed")
    if fresh_flag:
        _refuse(cursor, "G5b_source_test_only",
                "approved method source is marked test_only — refused on "
                "the production path")

    # ---- (7) pending + structural validation, on the FRESH instance ------
    # Deliberately NOT on the cached one: structural_problems() calls
    # isinstance/float() and iterates the ticks mapping, which for a cached
    # config are attacker-influenced values. The cached config's structural
    # legality is instead established DERIVATIVELY at G10 -- its fingerprint
    # must equal that of this instance, which has just been validated.
    cursor.at("G7_pending")
    pend = fresh_methods.pending_fields()
    if pend:
        _refuse(cursor, "G7_pending",
                "pending method rulings: " + ", ".join(pend))
    cursor.at("G7b_structural")
    bad = fresh_methods.structural_problems()
    if bad:
        _refuse(cursor, "G7b_structural",
                "structurally invalid methods: " + _code_heads(bad))

    # ---- (10) methods EQUIVALENCE by non-executing fingerprint -----------
    cursor.at("G10_methods_fingerprint")
    fresh_m_fp = _methods_fingerprint(fresh_methods)
    if type(fresh_m_fp) is _NotNormalizable:
        _refuse(cursor, "G10_methods_fingerprint",
                "fresh methods field " + fresh_m_fp.rule + " cannot be "
                "normalized without executing foreign code — fail closed")
    # ---- (10) REPRESENTATION IDENTITY -- a SEPARATE obligation -----------
    # The fingerprint just above decides EQUIVALENCE and is deliberately
    # LOSSY (contracts widens int->float so (0,1,1) and (0.0,1.0,1.0) compare
    # EQUAL, and a mappingproxy compares equal to the dict it wraps). This
    # stage asks the other question -- is THIS object in the exact canonical
    # form contracts specifies? -- and it is asked of the object ITSELF, not
    # of a comparison. Fixing this inside the fingerprint instead would also
    # refuse value-equal pairs contracts declares EQUAL.
    cursor.at("G10_methods_canonical_form")
    m_defect = _methods_canonical_defect(fresh_methods)
    if m_defect:
        _refuse(cursor, "G10_methods_canonical_form",
                "fresh " + m_defect + " — fail closed")
    cached_m_fp = None
    if have_cache:
        cursor.at("G10_methods_fingerprint")
        cached_m_fp = _methods_fingerprint(cached_methods)
        if type(cached_m_fp) is _NotNormalizable:
            _refuse(cursor, "G10_methods_fingerprint",
                    "cached methods field " + cached_m_fp.rule + " cannot "
                    "be normalized without executing foreign code — fail "
                    "closed")
        cursor.at("G10_methods_canonical_form")
        m_defect = _methods_canonical_defect(cached_methods)
        if m_defect:
            _refuse(cursor, "G10_methods_canonical_form",
                    "cached " + m_defect + " — value equivalence is not "
                    "representation identity; fail closed")
        cursor.at("G10_methods_equivalence")
        # Both operands are tuples of exact builtin atoms, so `!=` cannot
        # dispatch to foreign code. This REPLACES the old
        # `cfg.methods != fresh_methods`, which did.
        if cached_m_fp != fresh_m_fp:
            _refuse(cursor, "G10_methods_equivalence",
                    "config does not match the fresh approved method "
                    "source — cache is not a method source")

    # ---- (6) approved INJECTABLE source ----------------------------------
    cursor.at("G6_injectable_source")
    injectables = _approved_injectables()
    if injectables is None:
        _refuse(cursor, "G6_injectable_source",
                "no approved injectable source (spread_scalars / "
                "regime_of / vol_axis_of) exists yet — a cached config "
                "cannot be its own injectable source; fail closed")

    # ---- (8) injectable SCHEMA (validate_injectables never raises) -------
    cursor.at("G8_injectable_schema")
    from itsf.contracts import validate_injectables as _vinj
    inj_problems = _vinj(injectables)
    if inj_problems:
        _refuse(cursor, "G8_injectable_schema",
                "approved injectable source malformed — fail closed: "
                + _code_heads(inj_problems))

    # ---- (9) config DERIVATION from the approved sources -----------------
    cursor.at("G9_derivation")
    from itsf.contracts import derive_study_config as _derive
    fresh_cfg = _derive(fresh_methods, **injectables)
    if type(fresh_cfg) is not StudyConfig:
        _refuse(cursor, "G9_derivation",
                "fresh derivation did not return exactly a StudyConfig — "
                "fail closed")

    # ---- (11) config EQUIVALENCE: fingerprint + callable identity --------
    cursor.at("G11_config_fingerprint")
    fresh_c_fp = _config_fingerprint(fresh_cfg, fresh_m_fp)
    if type(fresh_c_fp) is _NotNormalizable:
        _refuse(cursor, "G11_config_fingerprint",
                "fresh config field " + fresh_c_fp.rule + " cannot be "
                "normalized without executing foreign code — fail closed")
    cursor.at("G11_config_canonical_form")
    c_defect = _config_canonical_defect(fresh_cfg)
    if c_defect:
        _refuse(cursor, "G11_config_canonical_form",
                "fresh " + c_defect + " — fail closed")
    cursor.at("G11_callable_identity")
    for _name in ("regime_of", "vol_axis_of"):
        if not callable(getattr(fresh_cfg, _name)):
            _refuse(cursor, "G11_callable_identity",
                    "fresh config." + _name + " is not callable — fail "
                    "closed")

    out_cfg = fresh_cfg
    out_reason = ("derived from the approved method source and the "
                  "approved injectable source")
    if have_cache:
        cursor.at("G11_config_fingerprint")
        cached_c_fp = _config_fingerprint(cached_cfg, cached_m_fp)
        if type(cached_c_fp) is _NotNormalizable:
            _refuse(cursor, "G11_config_fingerprint",
                    "cached config field " + cached_c_fp.rule + " cannot "
                    "be normalized without executing foreign code — fail "
                    "closed")
        # REFUSE, NEVER REPAIR. Handing back `contracts.canonical_config(
        # cached_cfg)` would mint a NEW object on every call -- destroying the
        # identity guarantee ready() and compute() depend on -- while
        # silently accepting a tampered cache. It would also re-run
        # __post_init__, whose structural_problems() calls float() on
        # attacker-influenced values: a numeric coercion inside the gate.
        cursor.at("G11_config_canonical_form")
        c_defect = _config_canonical_defect(cached_cfg)
        if c_defect:
            _refuse(cursor, "G11_config_canonical_form",
                    "cached " + c_defect + " — value equivalence is not "
                    "representation identity; fail closed")
        cursor.at("G11_callable_identity")
        # ENGINEERING IDENTITY RULE -- NOT A RESEARCH STATEMENT.
        # `is` is used here solely for CACHE COHERENCE: it answers "is this
        # the very object the approved injectable source hands out in this
        # process?", and nothing else. It does NOT define, approve, rank or
        # narrow what regime_of / vol_axis_of compute; DR-1 and DR-2 stay
        # open. Two callables that agree on every input are DIFFERENT here
        # by design -- weakening this to semantic comparison would reopen
        # blind-audit F3 (a cached config supplying its own mappings).
        # Consequence the future _approved_injectables() must honour: it
        # must return STABLE callable objects, not fresh lambdas per call.
        # A hostile __eq__ on a callable is therefore never invoked.
        for _name in ("regime_of", "vol_axis_of"):
            got = getattr(cached_cfg, _name)
            if not callable(got):
                _refuse(cursor, "G11_callable_identity",
                        "config." + _name + " is not callable — fail "
                        "closed")
            if got is not getattr(fresh_cfg, _name):
                _refuse(cursor, "G11_callable_identity",
                        "config." + _name + " is not the same object the "
                        "approved injectable source hands out — a fresh "
                        "derivation is not interchangeable with an "
                        "equivalent-looking callable; fail closed")
        cursor.at("G11_config_equivalence")
        # Again atoms only. This REPLACES the old `cfg != fresh_cfg`, which
        # dispatched to whatever __eq__ the config's fields carried.
        if cached_c_fp != fresh_c_fp:
            _refuse(cursor, "G11_config_equivalence",
                    "config does not match a fresh derivation from the "
                    "approved sources — cache is not a config source")
        out_cfg = cached_cfg               # the SAME INSTANCE, by identity
        out_reason = cached_reason
    else:
        # ---- (12) cache write: the ONLY construction site ----------------
        cursor.at("G12_cache_write")
        _CONFIG_CACHE["cfg"] = _ConfigCacheEntry(config=fresh_cfg,
                                                 reason=out_reason)

    # ---- (13) point-of-use revalidation ----------------------------------
    # Not a gate but the SINGLE-PATH INVARIANT: everything above ran on
    # THIS call, cache hit or miss, so the config handed out has just been
    # revalidated against a fresh read of the approved sources.
    cursor.at("G13_point_of_use")
    if type(out_cfg) is not StudyConfig:
        _refuse(cursor, "G13_point_of_use",
                "gateway post-condition violated — fail closed")
    return (out_cfg, out_reason)


def resolved_study_config() -> tuple[StudyConfig | None, str]:
    """Shared readiness/compute predicate -- THE single gateway entry.

    ready() and compute() both call this and therefore consume the SAME
    validated instance (identity, not equality), so ready=False and
    compute-raises can never diverge. Returns (None, reason) for every
    failure; NO exception ever crosses this boundary.
    """
    cursor = _StageCursor("config_gate", _GATE_STAGES[0])
    return _run_guarded(_gateway_body, cursor, lambda why: (None, why))

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


def _na_conservation_block(structural) -> dict:
    """A11 NA-conservation restatement for the sealed report.

    Re-runs the SAME production checker Stage D uses (runinfra.
    check_na_conservation) over the itemized reasons and the independently
    reported totals, and restates both plus the verdict — so the formal
    report carries the conservation evidence, not merely a claim.
    """
    from itsf.s0 import runinfra as _ri
    counts = structural["na_reason_counts"]
    totals = structural["reported_total_na"]
    res = _ri.check_na_conservation(counts, reported_total_na=totals)
    per_table: dict[str, int] = {"features": 0, "labels": 0}
    for col, n in totals.items():
        table = col.split(".", 1)[0]
        if table in per_table:
            per_table[table] += int(n)
    return {
        # contract §A11 minimal shape (report.validate_formal_payload)
        "per_table_total_na": per_table,
        "conservation_ok": bool(res.ok),
        # richer evidence (superset of the minimal shape)
        "conserved": bool(res.ok),
        "reported_total_na": {k: int(v) for k, v in totals.items()},
        "itemized_reason_counts": {
            col: {reason: int(n) for reason, n in reasons.items()}
            for col, reasons in counts.items()},
        "checker": "itsf.s0.runinfra.check_na_conservation "
                   "(APPROVED_NA_REASONS not a parameter; totals mandatory)",
        "per_column_ok": {k: bool(v) for k, v in res.per_column_ok.items()},
        "unregistered_reasons": list(res.unregistered_reasons),
        "miscounted_columns": list(res.miscounted_columns),
    }


def _strkeys(obj):
    """Recursively stringify non-str dict keys (formal JSON boundary)."""
    if isinstance(obj, dict):
        return {str(k): _strkeys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_strkeys(v) for v in obj]
    return obj


def _sensitivity_adverse_plus1_block(study) -> dict:
    """IR-28c — the formal Option-ii (+1 tick) sensitivity block.

    Effective per-scenario adverse ticks come STRUCTURALLY from the ruled
    constant (never restated); the P&L impact is exact arithmetic on the
    Primary records: each E1 stop-triggered day pays one extra tick on the
    stop side = MNQ_TICK_VALUE_USD per contract. E2 places no stop orders,
    so its sensitivity delta is zero BY CONSTRUCTION (stated, not padded).
    """
    from itsf.contracts import (AARON_RULED_ADVERSE_TICKS_SENSITIVITY,
                                MNQ_TICK_VALUE_USD)
    per_scenario = {}
    for scn, recs in study["records"]["E1"].items():
        n_stop = sum(1 for r in recs if r.stop_triggered)
        per_scenario[scn] = {
            "n_stop_triggered_days": n_stop,
            "total_pnl_delta_usd_per_contract":
                -MNQ_TICK_VALUE_USD * n_stop,
        }
    return {
        "channel": "sensitivity_plus1",
        "role": "sensitivity_only_never_primary",
        "effective_adverse_ticks":
            dict(AARON_RULED_ADVERSE_TICKS_SENSITIVITY),
        "per_stop_side_delta_usd_per_contract": -MNQ_TICK_VALUE_USD,
        "scope": "E1_stop_fills_only",
        "e2_delta": "zero_by_construction_no_stop_orders",
        "e1_per_scenario": per_scenario,
    }


def build_full_study_result(ds, bars_by_date, *, config: StudyConfig,
                            governance_meta, n_boot=FROZEN_N_BOOT,
                            universe=None, frozen_hash_observations=None,
                            day_value_snapshot=None):
    """Assemble the FULL S0 payload per S0_REPORT_CONTENT_CONTRACT §A.

    spread_scalars (DR-M6-A) and regime_of (DR-M6-B) are INJECTED so the
    synthetic e2e can exercise the whole chain; the real-run caller does
    not exist until the rulings land, and pending_decisions travels into
    disclosures where the contract validator fails Stage E closed.
    Research randomness lives entirely inside stats/gridmix (frozen seeds
    {7,13,31}); this function is deterministic.
    """
    from itsf.s0 import costs as _costs
    from itsf.s0.dataset import event_stratum_of as _event_stratum_of
    from itsf.s0.gridmix import build_grid
    from itsf.s0.stats import (bootstrap_mean_ci_ruled,
                               build_bootstrap_day_sequence)
    from itsf.s0.study import FROZEN_THETAS, build_study, theta_key

    # DR-1 (Aaron 2026-08-10): scenarios come from the RULED method object —
    # adverse ticks sourced from the ruling, Stress never re-multiplied.
    scenarios = _costs.build_scenarios_from_method(
        config.spread_scalars, config.methods.spread_cost)
    # DR-8: the E2 worst-day estimator is the RULED value on the config.
    study = build_study(ds, make_day_inputs(ds, bars_by_date), scenarios,
                        worst_day_estimator=config.methods
                        .worst_day_estimator,
                        estimator_test_only=config.methods.test_only)

    # DR-6 (Aaron 2026-08-10): the event stratum routes through the single
    # ruled consumer — IR-12/18 vocabulary, F10 None -> NA_multi_event,
    # unknown mapping raises, TEST_ONLY value test-gated in dataset.py.
    event_of = {r.trade_date: _event_stratum_of(
                    r.features.is_event_day, config.methods.event_na_mapping,
                    config.methods.test_only)
                for r in ds.records}

    # F-1 boundary: strata/vol labels come from the PREPARED value snapshot
    # when one is supplied (the production compute path always supplies it);
    # the direct-call fallback below is a PRE-exposure test convenience and
    # is pinned as such by the chain tests.
    if day_value_snapshot is not None:
        _regime_label = day_value_snapshot.regime
        _vol_label = day_value_snapshot.vol_axis
    else:
        _regime_label = lambda d: str(config.regime_of(d))    # noqa: E731
        _vol_label = lambda d: str(config.vol_axis_of(d))     # noqa: E731

    _theta_of = {theta_key(t): float(t) for t in FROZEN_THETAS}
    bootstrap_ci: dict[str, object] = {}
    feasibility_grid: dict[str, object] = {}
    for tkey, tblock in study["per_theta"].items():
        p = tblock["frequency"]["pooled"]["continuation_base_rate_p"]
        for eng in _CONTRACT_ENGINES:
            for scn in study["scenarios_used"]:
                d_tp = tblock["d_tp"][eng][scn]
                d_fp = tblock["d_fp"][eng][scn]
                # DR-4 (Aaron 2026-08-10): the bootstrap population is the
                # FULL eligible trading-day sequence — oracle-traded days
                # carry their USD P&L, eligible-but-unselected days carry
                # an explicit 0.0, NA days (undeterminable direction /
                # Y_cont NA) are dropped n1-style with a disclosed count.
                day_states = []
                for r in sorted(ds.records, key=lambda x: x.trade_date):
                    if r.trade_date in d_tp:
                        day_states.append((r.trade_date, "oracle_traded",
                                           float(d_tp[r.trade_date])))
                    elif (r.labels.y_cont is None
                          or int(r.labels.d_open or 0) == 0):
                        day_states.append((r.trade_date, "na"))
                    else:
                        day_states.append(
                            (r.trade_date, "eligible_not_selected"))
                seq = build_bootstrap_day_sequence(
                    day_states, config.methods.bootstrap_method)
                for blk in FROZEN_BLOCKS:
                    bootstrap_ci[f"{tkey}|{eng}|{scn}|block{blk}"] = \
                        bootstrap_mean_ci_ruled(
                            seq, theta=_theta_of[tkey],
                            method=config.methods.bootstrap_method,
                            block_len=blk, n_boot=n_boot)
                strata = {d: (d[:4], _regime_label(d), event_of[d])
                          for d in {**d_tp, **d_fp}}
                # DR-3 + DR-5 (Aaron 2026-08-10): the grid consumes the
                # ruled FP-allocation and K-repeat policies; theta enters
                # the repeat RNG stream.
                feasibility_grid[f"{tkey}|{eng}|{scn}"] = build_grid(
                    d_tp, d_fp, strata, p,
                    fp_allocation=config.methods.fp_allocation,
                    grid_policy=config.methods.grid_policy,
                    theta=_theta_of[tkey])

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
    out = {
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
            t: {scn: {**study["per_theta"][t]["executable"]["E2"][scn]
                      ["worst_day_report"],
                      # DR-8 RULED (linear, 2026-08-10): the status is
                      # derived from the single ruled source; sealing still
                      # fail-closes if it ever reads unresolved.
                      "estimator_status":
                          ("resolved"
                           if config.methods.worst_day_estimator is not None
                           else "unresolved_DR-M6-H")}
                for scn in study["scenarios_used"]}
            for t in study["per_theta"]},
        "sizing_outputs": {t: {"rows": study["per_theta"][t]["sizing_rows"],
                               "coverage":
                               study["per_theta"][t]["sizing_coverage"]}
                           for t in study["per_theta"]},
        "frequency": {t: study["per_theta"][t]["frequency"]
                      for t in study["per_theta"]},
        "stability_views": {t: build_stability_views(
            study["per_theta"][t], day_meta,
            vol_axis={d: _vol_label(d) for d in day_meta},
            # DR-7 (Aaron 2026-08-10): BOTH populations reported.
            stability_population=config.methods.stability_population)
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
            # A11 (contract): the NA-conservation RESTATEMENT — the same
            # itemized reasons/totals Stage D verifies, restated in the
            # sealed report so a reader can re-add them without the
            # internal envelope.
            "na_conservation": _na_conservation_block(structural),
            # IR-28c (explicit Fable delegation, 2026-08-10): the IR-7
            # Option-ii sensitivity channel enters the FORMAL report.
            # Adverse slip acts on E1 stop fills only, so the +1-tick
            # impact is LINEAR and exact: -$0.50 per stop-triggered day
            # per contract. Derived from the PRIMARY records by pure
            # arithmetic — never a substitute for the Primary columns.
            "sensitivity_adverse_plus1":
                _sensitivity_adverse_plus1_block(study),
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
    # M6.1.4 (main-1): CANONICAL EVIDENCE is captured at compute time, in
    # the one scope where the atoms (ds, bars, records, config) are all
    # live — a SECOND derivation path, not a copy of study.py aggregates.
    # split_envelope drops the key from both halves, so it can never leak
    # into the sealed payload; the renderer REQUIRES it and reconciles the
    # formal payload + actual sealed bytes against it before sealing.
    from itsf.s0 import evidence as _ev
    out["evidence"] = _ev.capture_evidence(
        ds, bars_by_date, out, config, universe=universe,
        frozen_hash_observations=frozen_hash_observations, n_boot=n_boot,
        # F-1 (Codex blocker #1): the evidence layer consumes the prepared
        # immutable snapshot, never the live config callable, post-exposure.
        day_value_snapshot=day_value_snapshot)
    return out


def _expected_governance(snapshot=None) -> dict:
    """Independently RE-derive the governance context from primary sources
    (registry bytes + guards constants) — never from the payload's own
    governance block, so the cross-check catches drift/tampering between
    compute and seal (M6.1.1 S1 wiring).

    M6.1.7 — `snapshot` is the PRE-EXPOSURE authorization snapshot carried
    by the prepared execution input. Production ALWAYS passes it (pinned by
    test); the `None` path is for non-run callers (direct renderer tests),
    which have no run and therefore no RUN_STARTED row skewing the count.

    WHY THE COUNT MUST COME FROM THE SNAPSHOT AND THE COMMIT MUST NOT.
    `registry_sequence_snapshot` means "the registry as of authorization".
    Re-deriving it at seal time returns the pre-exposure count PLUS this
    run's own RUN_STARTED row, so it is taken from the snapshot. The
    AUTHORIZED COMMIT is different in kind: it is the run's authorization
    identity and must be STABLE, so it is still re-read from live registry
    bytes and required to agree with the snapshot.

    WHAT THAT RE-READ IS AND IS NOT WORTH (M6.1.7 review L-6, correcting the
    reason first recorded here). It does NOT rescue this comparison from
    vacuity: measured, FOUR of the five keys are already the same in-process
    expression on both sides — `trial_id` (`TRIAL_ID`), `engineering_seed`
    (`ENGINEERING_SEED`), `frozen_hashes` (`dict(guards.FROZEN_HASHES)`) and,
    since M6.1.7, `registry_sequence_snapshot` (the snapshot on both sides).
    The re-read keeps exactly ONE key non-vacuous, not two.

    Its real value is the `raise` below: it is a MID-RUN RE-AUTHORIZATION
    DETECTOR, and it is the only one there is. `pre_exposure_recheck`
    structurally cannot cover this — it runs BEFORE `RUN_STARTED`, so a
    registry re-authorized after the exposure boundary is invisible to it.
    Moving the check there would strictly lose detection. Note also that
    `RUN_STARTED` is not a `RUN_AUTHORIZED` row, so this run's own append
    cannot trip it: the count moves, the commit does not.

    The non-vacuous governance comparison lives elsewhere and is unaffected
    by any of this — `output_proof.prove_governance` builds its expected
    side from the snapshot plus the frozen-hash authority cross-checked
    against a live disk re-hash, and reads its actual side off the sealed
    bytes on disk.
    """
    from itsf import guards as _g
    text = REGISTRY.read_text(encoding="utf-8")
    _row, commit, _reason = find_authorization_event(text)
    if snapshot is None:
        sequence = len(parse_registry_events(text))
    else:
        snap_commit = snapshot.get("authorized_commit")
        if snap_commit != commit:
            raise ValueError(
                "authorized commit changed between the pre-exposure "
                "authorization snapshot and seal time — refusing to seal "
                "(snapshot vs live registry disagree)")
        sequence = snapshot["event_sequence"]
    return {
        "trial_id": TRIAL_ID,
        "authorized_commit": commit,
        "engineering_seed": ENGINEERING_SEED,
        "frozen_hashes": dict(_g.FROZEN_HASHES),
        "registry_sequence_snapshot": sequence,
    }


def validate_report_contract(payload, *, expected_governance=None
                             ) -> list[str]:
    """M6.1 E3: thin alias — the authoritative validator lives in
    src/itsf/s0/report.py (validate_formal_payload). Kept so older callers
    and tests share one implementation."""
    from itsf.s0 import report as rep
    return rep.validate_formal_payload(
        payload, expected_governance=expected_governance)


class _PreparedExecutionInput:
    """M6.1.6 — the object the pre-exposure prepare seam hands to Stage C.
    Exact-type-pinned by `RealChain.compute`, so Stage C cannot be fed a
    look-alike and cannot fall back to re-resolving configuration.

    "RUN-SCOPED" IS WRAPPER-SCOPED, AND THE DIFFERENCE MATTERS (M6.1.6
    review A2-1/A2-2). Each run gets its own wrapper, and two `RealChain`
    instances never share one. But `.config` is the process-global instance
    the gateway caches (`out_cfg = cached_cfg`), so the wrapper is scoped
    per run while the config it carries is not. And the pin is a TYPE pin,
    not a PROVENANCE pin: a hand-built instance, or an
    `object.__setattr__` swap of `.config` after prepare, would not be
    detected. Neither is reachable through `S0Runner.run()` — the window
    between prepare and compute contains only runner-owned code — but the
    guarantee is "Stage C cannot re-resolve", not "Stage C's config is
    unforgeable".

    __slots__, no generated __eq__/__repr__: it is identified by
    `type(x) is _PreparedExecutionInput` and consumed by attribute read, and
    is never compared, unpacked or serialized.

    HONEST SCOPE — what this object freezes (S0 closeout, Aaron 2026-08-10).
    `config` is a `StudyConfig` (immutable scalars tuple, frozen method
    dataclasses). `day_values` is the F-1 MATERIALISED per-day value
    snapshot (`context.DayValueSnapshot`): the regime/vol-axis labels were
    computed ONCE at prepare time (pre-exposure) under the ruled DR-2
    vocabulary, and Stage C consumes only these VALUES — the config
    callables are never invoked after prepare (AST-pinned). Remaining
    honest limit: `methods.spread_cost.adverse_slippage_ticks` is a
    MappingProxyType whose backing dict contracts.py builds; for the RULED
    instance that backing dict is module-private
    (`AARON_RULED_ADVERSE_TICKS_PRIMARY`), so no run-time author holds a
    mutable reference, but a hand-built bypass config could still carry a
    live view — the gateway's canonical-form checks are the guard there.

    M6.1.7 — it also carries the PRE-EXPOSURE AUTHORIZATION SNAPSHOT.

    `snapshot` is a MappingProxyType over a PRIVATE dict copy taken at
    prepare time. Nobody else holds a reference to the backing dict, so
    unlike `.config`'s live method table this one is genuinely materialised
    — it is not the `MappingProxyType` PARTIAL noted above.

    WHY IT IS HERE AT ALL. `compute()` used to re-read `ops/TRIAL_REGISTRY.md`
    to build `governance`, and that read happens AFTER `_atomic_run_start`
    has appended this run's own `RUN_STARTED` row. `parse_registry_events`
    counts that row, so the sealed `registry_sequence_snapshot` was the
    pre-exposure count PLUS ONE. It went unnoticed because
    `_expected_governance()` re-read the registry at seal time too: both
    sides of the contract check drifted together and agreed at N+1. Same
    shape as the CRLF defect — a check and its expectation drawn from one
    moving source cannot see that source move.
    """

    __slots__ = ("config", "reason", "snapshot", "day_values",
                 "exact_l3_dates", "exact_l3_digest",
                 "assertions_bytes", "assertions_digest")

    def __init__(self, *, config, reason, snapshot, day_values=None,
                 exact_l3_dates=None, exact_l3_digest=None,
                 assertions_bytes=None, assertions_digest=None):
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "snapshot", snapshot)
        # F-1 (S0 closeout, Aaron 2026-08-10): the materialised per-day
        # regime / vol-axis VALUE snapshot (context.DayValueSnapshot).
        # Stage C consumes THIS, never the config callables.
        object.__setattr__(self, "day_values", day_values)
        # R4 B1 — the EXACT L3 authority: the sorted structurally-eligible
        # day tuple rebuilt at prepare time from the VERIFIED structural
        # atoms (universe.funnel.structurally_eligible — the same funnel
        # Stage B checked against the locked assertions), plus its digest.
        # KC1 compares the published era union against THIS, never against
        # anything derived from the payload under test.
        object.__setattr__(self, "exact_l3_dates", exact_l3_dates)
        object.__setattr__(self, "exact_l3_digest", exact_l3_digest)
        # R4 B2 — the run-scoped ASSERTIONS snapshot: the locked preflight
        # bytes read + sha-verified ONCE at prepare (pre-exposure); every
        # later boundary (pre-write screen, post-write release) consumes
        # these bytes — the path is never re-read after RUN_STARTED.
        object.__setattr__(self, "assertions_bytes", assertions_bytes)
        object.__setattr__(self, "assertions_digest", assertions_digest)

    def __setattr__(self, name, value):          # no post-prepare mutation
        raise AttributeError("_PreparedExecutionInput is immutable")


class RealChain:
    """Cached real-data chain. Universe/dataset are built at most once per
    process; Stage B reads only structural counts from them, Stage C returns
    the same cached dataset (no recompute, no drift)."""

    def __init__(self) -> None:
        self._ds = None
        self._uni = None
        self._bars = None

    def ready(self) -> tuple[bool, str]:
        """Public readiness probe — ALWAYS returns (bool, str).

        M6.1.4-ARCH (F-1): the (bool, str) contract is now TOTAL, and it is
        made total by the SAME single mechanism the config gateway uses
        (`_run_guarded`), not by a second set of guards. The artifact
        probes below are inside it too: `Path.exists()` can raise OSError
        on a pathological path, and that must be a refusal, not an escape.
        """
        cursor = _StageCursor("ready_gate", "R1_artifact_paths")
        return _run_guarded(self._ready_body, cursor,
                            lambda why: (False, why))

    def _ready_body(self, cursor):
        """Straight-line readiness pipeline. CONTAINS NO try/except."""
        cursor.at("R1_artifact_paths")
        missing = [str(p) for p in (F10_CSV, SYMBOLOGY_CSV,
                                    A1_JOB_DIR / "condition.json",
                                    A1_JOB_DIR / "manifest.json")
                   if not p.exists()]
        if missing:
            raise _Refusal(f"stage-C artifacts missing: {missing}")
        # M6.1 E1: readiness and compute share resolved_study_config —
        # ready() can never say True while compute() would refuse.
        cursor.at("R2_config_gateway")
        cfg, why = resolved_study_config()
        if cfg is None:
            raise _Refusal(f"stage-C fail-closed pre-exposure: {why}")
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

    def _governance_context(self, prepared):
        """Build the INDEPENDENT expected-side context for the governance
        checks. Its authorization facts come from the PRE-EXPOSURE snapshot
        the prepared object carries — never from `self.authorization_snapshot()`
        called again here, which after RUN_STARTED would observe a registry
        one event longer than the one the run was authorized against.

        The frozen-hash re-hash IS taken live from disk at call time: that
        fact has an independent authority (`guards.FROZEN_HASHES`) to be
        compared against, so observing it late is a feature, not drift."""
        from itsf import guards as _g
        from itsf.s0 import output_proof as _op
        return _op.SourceContext(
            authorization_snapshot=dict(prepared.snapshot),
            frozen_hash_authority=dict(_g.FROZEN_HASHES),
            frozen_hash_observations={
                p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
                for p in sorted(_g.FROZEN_HASHES)},
            engineering_seed=ENGINEERING_SEED,
            engineering_seed_provenance="DR-02 / packet §5")

    def render_report_with_governance_proof(self, result, prepared):
        """M6.1.6/M6.1.7 — production render entry point.

        Takes the prepared object EXPLICITLY (Stage E is post-exposure, and
        the run's pre-exposure authority must be handed to it rather than
        fished out of a module global or an instance attribute — stashing it
        was how the defect this milestone closes got in).

        What happens here is the pre-write screen only. The release verdict
        is `post_write_verify`, below, which reads the bytes off disk."""
        if type(prepared) is not _PreparedExecutionInput:
            raise RuntimeError("stage-E requires the prepared execution "
                               "input produced by the pre-exposure prepare "
                               "seam")
        return render_s0_report(
            result,
            expected_governance=_expected_governance(prepared.snapshot),
            governance_context=self._governance_context(prepared),
            # the VALIDATED config's rulings — drives the handoff admission
            # context AND the F-2 key-claims pre-write screen.
            methods=prepared.config.methods,
            # R4 B1/B2: run-scoped immutable authority from prepare.
            key_claims_authority=(prepared.assertions_bytes,
                                  prepared.exact_l3_dates))

    def post_write_verify(self, rdir, written, prepared):
        """M6.1.7 — THE RELEASE VERDICT, taken from the bytes on disk.

        Runs after every renderer artifact has been written and before
        Stage E completes. `written` is the runner's (name, bytes) record;
        it is deliberately NOT used as the source of truth here — this
        checker re-reads the files, because a verdict computed from the
        same in-memory values the writer used is the exact mistake M6.1.6
        made. `written` is accepted so the seam's contract is uniform and
        so a future check can compare the two independently.

        THE ASYMMETRY (see runner.py): the WIRING of this seam is proven
        pre-exposure, but the CHECK itself can only run once the bytes
        exist, i.e. after the exposure boundary. A refusal here is a
        Stage-E RUN failure with the trial already burned. That is
        unavoidable — disk bytes cannot be verified before they are disk
        bytes — and it is why nothing on the refusal path deletes anything.
        """
        from itsf.s0 import output_proof as _op
        if type(prepared) is not _PreparedExecutionInput:
            return (False, "post-write verify: not the prepared execution "
                           "input from the pre-exposure seam")
        try:
            proof = _op.prove_governance(
                self._governance_context(prepared),
                report_path=Path(rdir) / "S0_REPORT.json",
                infrastructure_files=("manifest.jsonl",
                                      "REGISTRY_AFTER_RUN_STARTED.json"))
        except _op.ProofRefused as exc:
            return (False, f"post-write governance proof refused: {exc}")
        if not proof.ok:
            return (False, "post-write governance proof failed: "
                    + "; ".join(proof.problems))
        # F-2 key-claims POST-WRITE release (Aaron 2026-08-10): re-verify
        # the payload-bound claims against the BYTES ON DISK plus the disk
        # verdict itself. KC3 is pre-write-only by design; its verdict
        # carries to disk by BYTE IDENTITY, and that custody argument is
        # made TRUE here (conformance F2.3): S0_REPORT.json is
        # self-excluded from the sealed-set manifest, so its disk bytes
        # are compared DIRECTLY against the renderer's in-memory `written`
        # record before anything else is concluded from them.
        try:
            disk_report_bytes = (Path(rdir) / "S0_REPORT.json").read_bytes()
        except Exception as exc:                          # noqa: BLE001
            return (False, "post-write key-claims: cannot read disk "
                    f"report: {type(exc).__name__}")
        written_map = dict(written) if written else {}
        mem = written_map.get("S0_REPORT.json")
        if mem is None:
            return (False, "post-write key-claims: renderer record carries "
                           "no S0_REPORT.json bytes to bind against")
        if hashlib.sha256(mem).hexdigest() != hashlib.sha256(
                disk_report_bytes).hexdigest():
            return (False, "post-write key-claims: S0_REPORT.json disk "
                           "bytes differ from the renderer's written bytes "
                           "— byte-identity custody broken")
        try:
            disk_formal = json.loads(disk_report_bytes.decode("utf-8"))
        except Exception as exc:                          # noqa: BLE001
            return (False, "post-write key-claims: cannot parse disk "
                    f"report: {type(exc).__name__}")
        # KC3 custody (Codex blocker #2c fix): the pre-write evidence
        # verdict is NOT re-synthesized here — it is read back from the
        # SEALED HANDOFF_ADMISSION.json on disk, whose bytes are bound by
        # the manifest inside the (byte-verified) disk report. A missing
        # record, a manifest digest mismatch, or a non-empty sealed hard
        # list each refuse the release.
        try:
            adm_bytes = (Path(rdir) / "HANDOFF_ADMISSION.json").read_bytes()
            declared = (disk_formal["mc_handoff_manifest"]["sealed_files"]
                        ["HANDOFF_ADMISSION.json"]["sha256"])
        except Exception as exc:                          # noqa: BLE001
            return (False, "post-write key-claims: sealed admission record "
                    f"unreadable/undeclared: {type(exc).__name__}")
        if hashlib.sha256(adm_bytes).hexdigest() != declared:
            return (False, "post-write key-claims: HANDOFF_ADMISSION.json "
                           "disk bytes do not match the manifest digest — "
                           "custody broken")
        try:
            adm = json.loads(adm_bytes.decode("utf-8"))
            sealed_ev = adm["evidence_reconciliation"]
            ev_problems = (list(sealed_ev["hard_problems"])
                           + list(sealed_ev["partial_coverage"]))
        except Exception as exc:                          # noqa: BLE001
            return (False, "post-write key-claims: sealed admission record "
                    f"malformed: {type(exc).__name__}")
        # R5.1 B2: the DR-5 staged boundary is RE-VALIDATED from the disk
        # bytes (same validator as the seal), so a boundary block that was
        # deleted or tampered between seal and verify refuses the release.
        from itsf.s0 import handoff as _ho
        dr5_problems = _ho.validate_dr5_staged_boundary(
            adm.get("dr5_staged_boundary"))
        if dr5_problems:
            return (False, "post-write dr5 staged boundary invalid on "
                    "disk: " + "; ".join(dr5_problems))
        kc = _op.verify_key_claims(
            disk_formal,
            _op.ResearchClaimsContext(
                # R4 B2: the SAME prepared bytes as pre-write — the
                # assertions path is never re-read after RUN_STARTED.
                assertions_bytes=prepared.assertions_bytes,
                exact_l3_dates=prepared.exact_l3_dates,
                # the VALIDATED config's methods — never a fresh source
                # resolution after exposure (M6.1.6 discipline).
                ruled_methods=prepared.config.methods,
                evidence_problems=ev_problems,
                disk_report={"ok": True,
                             "detail": "sealed-set byte proof passed"}),
            phase="post_write")
        if not kc.releasable_post_write:
            return (False, "post-write key-claims release failed: "
                    + "; ".join(kc.problems))
        return (True, "disk governance + sealed-set proof passed "
                f"({proof.comparisons_performed} governance, "
                f"{proof.disk_checks_performed} disk checks, "
                f"report {proof.report_sha256[:16]})")

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

    def prepare(self, snapshot):
        """M6.1.6 (S1 seam) — the PRE-EXPOSURE preparation step.

        This is the ONLY place the production config sources are read for a
        run. It runs after every Stage-B check has passed and BEFORE
        `_atomic_run_start`, so a refusal here is pre-exposure by
        construction: no RUN_STARTED, no runs directory, exposure not
        consumed (`runner.py` prepare seam, mirroring the pre-exposure
        registry recheck precedent).

        SCOPE (S0 closeout, Aaron 2026-08-10). Beyond closing the LIFECYCLE
        hole (ready() resolving and discarding a config that compute()
        re-resolved post-exposure), prepare now also delivers the F-1
        materialised plan: it binds the stable injectable resolvers to the
        ONE ruled DR-2 mapping built from the loaded universe and
        materialises the per-day value snapshot (`day_values`) that Stage C
        consumes INSTEAD of the config callables. DR-2's `vol_na` fourth
        stratum is ruled, so every eligible day gets a definite label.

        `_approved_injectables()` is now the RULED production source
        (sha256-pinned spread table -> B-i scalars; singleton resolvers);
        a failure inside it still surfaces as a Stage-B refusal.

        M6.1.7 — `snapshot` is the Stage-A authorization snapshot held by
        `make_snapshot_control`'s closure. It is passed IN rather than
        re-derived here on purpose: a second `authorization_snapshot()` call
        would be a second source of truth for the same fact, and this
        milestone exists because two sources of truth for one fact is how
        both the CRLF defect and the sequence-count defect got in. Because
        the value comes from that closure, `pre_exposure_recheck` — which
        runs later, inside `_atomic_run_start` — proves the registry is
        still byte-identical to THE VERY SNAPSHOT this object carries.
        """
        # Snapshot first: it is the cheap, purely structural half, so a
        # malformed snapshot is attributable as such instead of being
        # masked by whatever the config resolver happens to say today.
        if not isinstance(snapshot, _Mapping):
            raise RuntimeError("prepare requires the Stage-A authorization "
                               "snapshot mapping")
        snap = dict(snapshot)                     # private copy; see below
        missing = sorted({"trial_id", "authorized_commit", "event_sequence",
                          "registry_sha256"} - set(snap))
        if missing:
            raise RuntimeError("authorization snapshot is missing required "
                               "fields: " + ", ".join(missing))
        if not snap["authorized_commit"]:
            raise RuntimeError("authorization snapshot carries no authorized "
                               "commit — refusing to prepare a run")
        if not isinstance(snap["event_sequence"], int):
            raise RuntimeError("authorization snapshot event_sequence is not "
                               "an int")
        cfg, why = resolved_study_config()
        if cfg is None:
            raise RuntimeError(f"stage-C config unavailable: {why}")
        # F-1 (Aaron 2026-08-10): BIND the stable injectable resolvers to
        # the ONE ruled DR-2 mapping built from the loaded universe (still
        # pre-exposure), then MATERIALIZE the per-day value snapshot. Post-
        # exposure code consumes only the snapshot; the callables are never
        # invoked after this point (AST-pinned in compute).
        ds, uni = self._ensure()
        from itsf.s0.context import materialize_day_value_snapshot as _mat
        # BINDING is only needed when the config carries the PRODUCTION
        # resolver singletons (the real injectable source). A hermetic
        # config whose callables are already data-free synthetics is
        # materialised directly — no universe consultation, no binding.
        if (cfg.regime_of is _REGIME_RESOLVER
                or cfg.vol_axis_of is _VOL_AXIS_RESOLVER):
            from itsf.s0.dataset import (
                build_vol20_regime_mapping_from_universe as _vmap)
            mapping = _vmap(uni, cfg.methods.volatility_regime)
            _REGIME_RESOLVER.bind(mapping.label_of)
            _VOL_AXIS_RESOLVER.bind(mapping.label_of)  # shared mapping scope
        day_values = _mat(tuple(sorted(r.trade_date for r in ds.records)),
                          cfg.regime_of, cfg.vol_axis_of)
        # R4 B1 — EXACT L3 authority, rebuilt from the verified structural
        # atoms, pre-exposure, immutable. PRODUCTION: the funnel Stage B
        # checked against the locked assertions. HERMETIC (synthetic
        # universe absent): ds.records IS the structurally-eligible set —
        # the same atom family, one representation earlier. No third path.
        eligible = getattr(getattr(uni, "funnel", None),
                           "structurally_eligible", None)
        if eligible:
            exact_l3 = tuple(sorted(str(d) for d in eligible))
        elif ds is not None and getattr(ds, "records", None):
            exact_l3 = tuple(sorted(str(r.trade_date) for r in ds.records))
        else:
            raise RuntimeError(
                "prepare: no verified structural atoms available — the "
                "exact-L3 authority cannot be built (fail closed, "
                "pre-exposure)")
        exact_l3_digest = hashlib.sha256(
            "\n".join(exact_l3).encode("utf-8")).hexdigest()
        # R4 B2 — run-scoped assertions snapshot: ONE sha-pinned read,
        # pre-exposure; missing file / drifted bytes refuse here.
        assertions_bytes = _read_key_claims_assertions()
        return _PreparedExecutionInput(
            config=cfg, reason=why,
            snapshot=_MProxy(snap), day_values=day_values,
            exact_l3_dates=exact_l3, exact_l3_digest=exact_l3_digest,
            assertions_bytes=assertions_bytes,
            assertions_digest=hashlib.sha256(assertions_bytes).hexdigest())

    def compute(self, prepared):
        # M6.1.6: Stage C consumes the PREPARED object and MUST NOT reach
        # for a config source again. `resolved_study_config()`,
        # `_resolved_methods()` and `_approved_injectables()` are not called
        # anywhere below this line — pinned by an AST test.
        if type(prepared) is not _PreparedExecutionInput:
            raise RuntimeError("stage-C requires the prepared execution "
                               "input produced by the pre-exposure prepare "
                               "seam; refusing to re-resolve configuration")
        cfg = prepared.config
        ds, uni = self._ensure()
        from itsf import guards as _g
        # M6.1.7: governance comes ONLY from the pre-exposure snapshot the
        # prepared object carries. Stage C runs AFTER `_atomic_run_start`
        # appended this run's own RUN_STARTED row, so the registry re-read
        # that used to stand here reported the pre-exposure event count
        # PLUS ONE. `REGISTRY` is not read anywhere below this line — the
        # frozen-hash re-hash beneath is a different fact with a different
        # source, and is deliberately kept live.
        snap = prepared.snapshot
        gov = {
            "trial_id": TRIAL_ID,
            "authorized_commit": snap["authorized_commit"],
            "engineering_seed": ENGINEERING_SEED,
            "frozen_hashes": dict(_g.FROZEN_HASHES),
            "registry_sequence_snapshot": snap["event_sequence"],
        }
        # M6.1.4 (B0 EV-13 / L127): a FRESH byte-level re-hash of the frozen
        # files, taken at compute time — the sealed governance block is then
        # reconciled against observed digests, not against the same module
        # constant read twice (the M6.1.3 tautology).
        fh_obs = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
                  for p in sorted(_g.FROZEN_HASHES)}
        return build_full_study_result(ds, self._bars, config=cfg,
                                       governance_meta=gov, universe=uni,
                                       frozen_hash_observations=fh_obs,
                                       day_value_snapshot=prepared.day_values)


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
        # M6.1.7 review L-2: `indent=1` embeds newlines, so a text-mode
        # write makes these bytes platform-dependent. This lands in the
        # ATTEMPT directory, never the run directory, so it is outside the
        # sealed set and never had the two-digest defect — same rule, same
        # reason, no exception worth remembering.
        (attempts_dir / "AUTHORIZATION_SNAPSHOT.json").write_text(
            json.dumps(snap, indent=1, sort_keys=True),
            encoding="utf-8", newline="\n")
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
        # M6.1.7: `indent=1` puts real newlines in this document, so a
        # text-mode write would make its bytes platform-dependent inside the
        # run directory. It never enters `sealed_files`, so it never had the
        # two-digest defect — but "the run directory is byte-determined" is
        # the claim this milestone makes, and an exception to it should not
        # have to be remembered.
        (rdir / "REGISTRY_AFTER_RUN_STARTED.json").write_text(
            json.dumps({"registry_sha256_after_run_started": after,
                        "snapshot_before": state.get("snapshot", {})},
                       indent=1, sort_keys=True),
            encoding="utf-8", newline="\n")

    def prepare_for_run():
        """M6.1.7 — the pre-exposure prepare seam, bound to THIS closure's
        Stage-A snapshot.

        `chain.prepare` deliberately does not read the registry itself: the
        snapshot it embeds must be the same object `pre_exposure_recheck`
        compares against, so that the recheck's "registry unchanged since
        authorization" proof applies to the value the run actually seals.
        Two independent reads of one fact is what produced the defect."""
        snap = state.get("snapshot")
        if snap is None:
            raise RuntimeError("no Stage-A authorization snapshot in memory "
                               "— refusing to prepare a run")
        return chain.prepare(snap)

    return (g_authorization_snapshot, pre_exposure_recheck,
            post_run_started_hook, prepare_for_run)


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
        assertions_path=str(REPO / "S0_INPUT_PREFLIGHT.json"),
        # L-5 ruling: governed roots travel on the config and are validated
        # by the runner's output_roots gate (runinfra.validate_output_roots).
        runs_root=str(GOVERNED_RUNS_ROOT),
        archive_root=str(GOVERNED_ARCHIVE_ROOT))

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
     post_run_started_hook, prepare_for_run) = make_snapshot_control(
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
        # M6.1.7: the prepare seam is bound to the snapshot-control closure,
        # so the prepared object embeds THE SAME Stage-A snapshot that
        # `pre_exposure_recheck` proves the registry still matches.
        prepare_compute=prepare_for_run,               # M6.1.6/7 pre-exposure
        compute=chain.compute,
        integrity_checks=build_integrity_checks(),
        # M6.1.6/7: the renderer takes (result, prepared) and runs only the
        # PRE-WRITE screen. The release verdict is `post_write_verify`,
        # which re-reads the artifacts off disk — the renderer's strings
        # cannot answer whether the bytes that landed are the right bytes.
        render_report=chain.render_report_with_governance_proof,
        post_write_verify=chain.post_write_verify,     # M6.1.7 disk seal
        append_registry_event=registry_append,
        clock_utc=clock,
        log=guarded_log,
        pre_exposure_recheck=pre_exposure_recheck,     # Aaron §三.5
        post_run_started_hook=post_run_started_hook)   # Aaron §三.6

    out = S0Runner(deps).run()
    print(f"terminal: stage={out.terminal_stage.value} ok={out.ok} "
          f"exposure_consumed={out.exposure_consumed} "
          f"kind={out.failure_kind or 'success'} "
          f"incident={out.incident_id or 'none'} "
          f"archive={out.archive_status or 'not_attempted'}")
    # L-5 / Codex #5: an archive-side failure NEVER flips `out.ok` (the run
    # is already sealed and the registry already carries COMPLETED), so this
    # terminal line is the ONLY place a human is told about it. Print the
    # reasons loudly, and keep the exit code tied to the RUN's verdict alone.
    # Channel note (H-1 precedent, deliberate): artifact names are
    # run-invariant constants and this is the same unguarded stdout as the
    # `terminal:` line — not the guarded research logger.
    if out.archive_status and out.archive_status != "archive_ok":
        print(f"ARCHIVE FAILED ({out.archive_status}) — the sealed run "
              f"directory is intact and remains the record of evidence; the "
              f"archive copy is not:")
        for line in (out.archive_report.errors if out.archive_report is not None
                     else ("no archive report available",)):
            print(f"  - {line}")
    return 0 if out.ok else 2


if __name__ == "__main__":
    sys.exit(main())
