"""Build a verifier's external evidence directory from an explicit spec.

QROS-CF v2 §2.8 (DEC-0006 I5; converged F03). The one mechanism that kept
a verifier seat clean in this project was an EXTERNAL directory holding
only allowlisted bytes (MC-DS-S004, 2026-09-06). This script makes that
directory mechanically, in two phases, so that what the verifier can read
before freezing its own result is decided by the spec and not by care.

    python scripts/build_verifier_dir.py --spec SPEC.json --phase pre-freeze
    python scripts/build_verifier_dir.py --spec SPEC.json --phase post-freeze
    python scripts/build_verifier_dir.py --spec SPEC.json --phase pre-freeze --dry-run

SPEC (JSON):

    {
      "run_id": "MC-DS-S004",
      "verifier_label": "strict-blind-verifier",
      "blindness": "CLAIM_BLIND" | "OUTCOME_BLIND",
      "framework_commit": "<40-hex>",          # code is exported FROM THIS COMMIT
      "out_root": "C:\\\\Users\\\\Aaron\\\\quant-data\\\\review",
      "brief": "<path to the one-page brief>",  # copied to pre_freeze/BRIEF.md
      "pre_freeze": {
        "files": [{"src": "<absolute path>", "dst": "<relative name>"}, ...],
        "code_paths": ["src/itsf/mc/supplement_contract.py", ...]
      },
      "post_freeze": {
        "files": [{"src": "<absolute path>", "dst": "<relative name>"}, ...]
      }
    }

PRE-FREEZE builds `<out_root>/<run_id>-<verifier_label>-<UTC date>/pre_freeze/`
from the pre-freeze files, the code paths exported with `git show
<framework_commit>:<path>` (the AUTHORIZED bytes, never the worktree), and
the brief. It writes `ALLOWLIST.sha256` (every file, relative path and
sha256), `SPEC.json` (the spec as used) and `README_VERIFIER.md` (the rules).
It refuses if the directory already exists.

POST-FREEZE refuses unless `pre_freeze/FREEZE_MARKER.json` exists and names
a `frozen_result` file whose sha256 matches; only then are the post-freeze
comparands copied into `post_freeze/` with their own `POST_FREEZE.sha256`.
The producer's claims physically do not exist in the directory until the
verifier's result is frozen -- which is the point.

REFUSED SOURCES, always: anything under the framework's `ops/` or `tests/`,
the registry repository, the witness directory, memory files, or another
review directory. A path in the pre-freeze AND post-freeze lists is refused
(a comparand cannot also be an input). Nothing here reads a Development
bar, resolves the registry, or writes inside the framework repository.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FORBIDDEN_FRAGMENTS = ("itsf-registry", "registry-witness", "\\.claude\\",
                       "/.claude/", "\\memory\\", "/memory/")
BLINDNESS = ("CLAIM_BLIND", "OUTCOME_BLIND")


class SpecRefused(ValueError):
    """The spec or the directory state refuses the phase. Nothing written."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(p: str) -> str:
    return str(Path(p)).replace("/", "\\").lower()


def _forbidden_source(src: Path, out_root: Path, repo: Path) -> str | None:
    s = _norm(str(src))
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment.lower() in s:
            return f"source under a forbidden location ({fragment.strip(chr(92) + '/')})"
    for sub in ("ops", "tests"):
        if s.startswith(_norm(str(repo / sub)) + "\\"):
            return f"source inside the framework's {sub}/"
    if s.startswith(_norm(str(out_root)) + "\\"):
        return "source inside another review directory"
    return None


def load_spec(path: Path) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("run_id", "verifier_label", "blindness", "framework_commit",
                "out_root", "brief", "pre_freeze", "post_freeze"):
        if key not in spec:
            raise SpecRefused(f"spec lacks {key!r}")
    if spec["blindness"] not in BLINDNESS:
        raise SpecRefused(f"blindness must be one of {BLINDNESS}")
    commit = spec["framework_commit"]
    if not (isinstance(commit, str) and len(commit) == 40
            and all(c in "0123456789abcdef" for c in commit)):
        raise SpecRefused("framework_commit must be a full 40-hex commit")
    pre = spec["pre_freeze"].get("files", [])
    post = spec["post_freeze"].get("files", [])
    for entry in pre + post:
        if not isinstance(entry, dict) or "src" not in entry or "dst" not in entry:
            raise SpecRefused("every file entry needs src and dst")
        dst = Path(entry["dst"])
        if dst.is_absolute() or ".." in dst.parts:
            raise SpecRefused(f"dst {entry['dst']!r} must be a relative path without ..")
    pre_src = {_norm(e["src"]) for e in pre}
    post_src = {_norm(e["src"]) for e in post}
    both = pre_src & post_src
    if both:
        raise SpecRefused(f"{len(both)} path(s) appear in BOTH pre-freeze and "
                          "post-freeze; a comparand cannot also be an input")
    pre_dst = [e["dst"] for e in pre]
    if len(set(pre_dst)) != len(pre_dst):
        raise SpecRefused("duplicate dst in pre_freeze")
    return spec


def target_dir(spec: dict, date: str | None = None) -> Path:
    date = date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    name = f"{spec['run_id'].lower()}-{spec['verifier_label']}-{date}"
    return Path(spec["out_root"]) / name


def _git_show(repo: Path, commit: str, rel: str) -> bytes:
    out = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        raise SpecRefused(f"git show {commit[:12]}:{rel} failed: "
                          f"{out.stderr.decode('utf-8', 'replace').strip()[:160]}")
    return out.stdout


def _write_inventory(root: Path, name: str, rel_paths: list) -> Path:
    lines = [f"{_sha256(root / rel)}  {rel}" for rel in sorted(rel_paths)]
    inv = root / name
    inv.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return inv


README = """# VERIFIER DIRECTORY -- read this first

RUN_ID={run_id}
BLINDNESS={blindness}
FRAMEWORK_COMMIT={commit}
PHASE=PRE_FREEZE (post-freeze comparands are NOT here yet)

Rules (ops/REVIEWER_CONTRACT.md §4 of the framework, restated so you need
not open the framework):

1. Work ONLY inside this directory. Before you freeze: no git, no listing
   of any repository, no search, no reads outside `pre_freeze/`. Executing
   an exported module may import its dependencies; that is execution, not
   inspection -- record it in your attestation.
2. Phase order: custody (hash what is here against ALLOWLIST.sha256) ->
   recompute -> FREEZE: write your result file, then write
   `pre_freeze/FREEZE_MARKER.json` as
   {{"frozen_result": "<relative path>", "sha256": "<its sha256>",
     "frozen_at_utc": "<ISO time>"}}
   Only then ask the dispatcher for the post-freeze phase.
3. If you read anything outside `pre_freeze/` before freezing: STOP, say
   so in your attestation, and do not continue. The dispatcher may build
   ONE fresh directory for a retry; a second exposure goes to Aaron.
4. Your attestation uses the header in BRIEF.md. You commit nothing to any
   repository; you append nothing to any ledger.
"""


def build_pre_freeze(spec: dict, *, repo: Path = REPO, date: str | None = None,
                     dry_run: bool = False) -> Path:
    out_root = Path(spec["out_root"])
    target = target_dir(spec, date)
    if target.exists():
        raise SpecRefused(f"{target} already exists; a verifier directory is "
                          "built fresh, never reused")
    brief = Path(spec["brief"])
    if not brief.is_file():
        raise SpecRefused(f"brief {brief} is not a file")
    plan = []
    for entry in spec["pre_freeze"].get("files", []):
        src = Path(entry["src"])
        why = _forbidden_source(src, out_root, repo)
        if why:
            raise SpecRefused(f"{src}: {why}")
        if not src.is_file():
            raise SpecRefused(f"pre-freeze source missing: {src}")
        plan.append(("copy", src, Path("pre_freeze") / entry["dst"]))
    for rel in spec["pre_freeze"].get("code_paths", []):
        rel = str(rel).replace("\\", "/")
        if rel.startswith(("ops/", "tests/")) or ".." in rel.split("/"):
            raise SpecRefused(f"code path {rel!r} is not exportable")
        plan.append(("export", rel, Path("pre_freeze") / "code" / rel))
    plan.append(("copy", brief, Path("pre_freeze") / "BRIEF.md"))
    if dry_run:
        for kind, src, dst in plan:
            print(f"{kind:6} {src} -> {target / dst}")
        return target

    target.mkdir(parents=True, exist_ok=False)
    (target / "pre_freeze").mkdir()
    written = []
    for kind, src, dst in plan:
        full = target / dst
        full.parent.mkdir(parents=True, exist_ok=True)
        if kind == "copy":
            shutil.copyfile(src, full)
        else:
            full.write_bytes(_git_show(repo, spec["framework_commit"], src))
        written.append(dst.as_posix())
    (target / "SPEC.json").write_text(json.dumps(spec, indent=1, sort_keys=True),
                                      encoding="utf-8", newline="\n")
    (target / "README_VERIFIER.md").write_text(
        README.format(run_id=spec["run_id"], blindness=spec["blindness"],
                      commit=spec["framework_commit"]),
        encoding="utf-8", newline="\n")
    _write_inventory(target, "ALLOWLIST.sha256", written)
    return target


def _read_marker(target: Path) -> dict:
    marker = target / "pre_freeze" / "FREEZE_MARKER.json"
    if not marker.is_file():
        raise SpecRefused("no pre_freeze/FREEZE_MARKER.json: the verifier has "
                          "not frozen a result, so no comparand may be delivered")
    data = json.loads(marker.read_text(encoding="utf-8"))
    frozen = data.get("frozen_result", "")
    want = data.get("sha256", "")
    path = target / "pre_freeze" / frozen
    if not frozen or not path.is_file():
        raise SpecRefused(f"FREEZE_MARKER names {frozen!r}, which is not a file "
                          "under pre_freeze/")
    got = _sha256(path)
    if got != want:
        raise SpecRefused(f"FREEZE_MARKER sha256 {want[:12]} != the frozen "
                          f"file's {got[:12]}; the result is not frozen")
    return data


def build_post_freeze(spec: dict, *, repo: Path = REPO, date: str | None = None,
                      dry_run: bool = False) -> Path:
    out_root = Path(spec["out_root"])
    target = target_dir(spec, date)
    if not (target / "pre_freeze").is_dir():
        raise SpecRefused(f"{target} has no pre_freeze/; run pre-freeze first")
    _read_marker(target)
    post = target / "post_freeze"
    if post.exists():
        raise SpecRefused("post_freeze/ already exists; comparands are delivered once")
    plan = []
    for entry in spec["post_freeze"].get("files", []):
        src = Path(entry["src"])
        why = _forbidden_source(src, out_root, repo)
        if why and "registry" not in why:
            raise SpecRefused(f"{src}: {why}")
        if not src.is_file():
            raise SpecRefused(f"post-freeze source missing: {src}")
        plan.append((src, Path("post_freeze") / entry["dst"]))
    if dry_run:
        for src, dst in plan:
            print(f"copy   {src} -> {target / dst}")
        return target
    post.mkdir()
    written = []
    for src, dst in plan:
        full = target / dst
        full.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, full)
        written.append(dst.as_posix())
    _write_inventory(target, "POST_FREEZE.sha256", written)
    return target


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--phase", required=True, choices=["pre-freeze", "post-freeze"])
    ap.add_argument("--date", default=None, help="UTC date for the directory name")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        spec = load_spec(Path(args.spec))
        if args.phase == "pre-freeze":
            target = build_pre_freeze(spec, date=args.date, dry_run=args.dry_run)
        else:
            target = build_post_freeze(spec, date=args.date, dry_run=args.dry_run)
    except SpecRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
