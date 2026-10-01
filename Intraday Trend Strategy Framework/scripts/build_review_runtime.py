# -*- coding: utf-8 -*-
"""Materialise a PORTABLE review runtime beside the sealed bundles.

WHY. `CODE_REVIEW_BUNDLE_CONTRACT v1` bound the execution environment by
VERSION and PACKAGE SET and left the interpreter as a RUNTIME dependency the
reviewer was expected to resolve. That is enough to identify Aaron's local
interpreter and not enough to run anywhere else: two seats failed on it, the
second even on the exact host-local path, because the only invocable route to
that interpreter is a Windows App Execution Alias.

WHAT THIS DOES, and what it deliberately does not. It copies the interpreter
that was ALREADY mechanically shown to satisfy the bound identity, plus the 49
pinned distributions, into one relocatable tree with a per-file digest
manifest. Nothing is downloaded, nothing is installed, no version moves, no pin
is dropped -- so the identity is not weakened, it is made portable. It is NOT
an environment manager and NOT a sandbox: the execution boundary stays
`code_review_bundle_guard.py`, unchanged.

THE RUNTIME IS INFRASTRUCTURE, NOT EVIDENCE. It carries no project code, no
authority, no test and no probe. `ops/REVIEWER_CONTRACT.md` section 4.2 already
classes executing a dependency as EXECUTION rather than inspection.
"""
import hashlib
import io
import json
import shutil
import sys
import sysconfig
import time
from importlib import metadata as md
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

OUT = Path(sys.argv[1])                      # .../bundles/N14-RUNTIME-001
LOCK = Path(sys.argv[2])                     # the sealed bundle's lockfile
RUNTIME_ID = OUT.name

INSTALL = Path(sysconfig.get_paths()["stdlib"]).parent


def refuse(why):
    raise SystemExit("RUNTIME BUILD REFUSED: " + why)


if OUT.exists():
    refuse("%s already exists; a runtime is never overwritten" % OUT)

# ---- the pinned set, read from the SEALED bundle's lockfile ---------------
want = {}
for line in LOCK.read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "==" in line:
        name, _, ver = line.partition("==")
        want[name.strip()] = ver.strip()
if not want:
    refuse("the lockfile yielded no pins")

# ---- 1. the interpreter --------------------------------------------------
t0 = time.time()
PY_DST = OUT / "python"


def _ignore(dirpath, names):
    """MSIX packaging metadata is package plumbing, not runtime; the install's
    own `site-packages` is replaced by the pinned set; `__pycache__` is
    regenerable and embeds build-host paths."""
    drop = []
    for n in names:
        low = n.lower()
        if low.startswith("appx") or low in ("_resources", "site-packages",
                                             "__pycache__"):
            drop.append(n)
    return drop


shutil.copytree(INSTALL, PY_DST, ignore=_ignore)
EXE = PY_DST / "python.exe"
if not EXE.exists():
    refuse("the copied interpreter has no python.exe")
print("interpreter: %d files in %.1fs" % (
    sum(1 for p in PY_DST.rglob("*") if p.is_file()), time.time() - t0))

# ---- 2. the 49 pinned distributions, file-exact --------------------------
t0 = time.time()
# INSIDE the interpreter tree on purpose. Anywhere else needs PYTHONPATH or a
# `._pth`, and PYTHONPATH is on the project's own HOSTILE_ENV_VARS list
# (execution_identity.py:89) -- a launcher that sets it would be handing the
# reviewer an environment the project's own gate calls hostile. Here the
# standard `site` discovery finds them with NO environment variable at all.
SP_DST = OUT / "python" / "Lib" / "site-packages"
SP_DST.mkdir(parents=True)
escaped, copied, skipped_cache = [], 0, 0
for name, ver in sorted(want.items()):
    try:
        dist = md.distribution(name)
    except Exception:                                         # noqa: BLE001
        refuse("pinned distribution not installed: %s==%s" % (name, ver))
    if dist.version != ver:
        refuse("pinned %s==%s but %s is installed -- the runtime may not "
               "change a pin" % (name, ver, dist.version))
    base = Path(str(dist.locate_file("")))
    for rel in dist.files or ():
        src = Path(str(dist.locate_file(rel)))
        try:
            inside = src.resolve().is_relative_to(base.resolve())
        except (OSError, ValueError):
            inside = False
        if not inside:
            escaped.append(str(rel))
            continue
        relp = src.resolve().relative_to(base.resolve())
        if "__pycache__" in relp.parts:
            skipped_cache += 1
            continue
        dst = SP_DST / relp
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            copied += 1
        except OSError as exc:
            refuse("could not copy %s: %s" % (relp, exc))
# ---- 2b. NO STARTUP INJECTION -------------------------------------------
# A `.pth` file in site-packages is EXECUTED by `site` at every interpreter
# start. `execution_identity.py` already treats that as a surface to control
# (EXPECTED_EXECUTABLE_PTH pins the two the host carries, by digest). A review
# runtime should have NO startup side effects at all: the one `.pth` in the
# pinned set exists to wire system TLS certificates, the review makes no
# network call, and the guard denies the whole network family anyway. Measured:
# left in place it prints `pip_system_certs: ERROR: truststore not available`
# on every start, because it needs a package the lockfile does not pin -- so
# keeping it would ALSO mean shipping unpinned material.
omitted_startup = []
for pth in sorted(SP_DST.glob("*.pth")):
    omitted_startup.append({
        "file": pth.name,
        "sha256": hashlib.sha256(pth.read_bytes()).hexdigest(),
        "reason": ("a `.pth` is executed by `site` at every interpreter start. "
                   "This one bootstraps system TLS certificates, which no part "
                   "of an outcome-blind code review needs and which the "
                   "execution guard denies outright. Its owning distribution "
                   "is still present at its pinned version, so LOCKFILE_GATE "
                   "is unaffected; only the startup injection is removed."),
    })
    pth.unlink()
left = sorted(p.name for p in SP_DST.rglob("*.pth"))
if left:
    refuse("a .pth file survives in the runtime: %s -- startup injection must "
           "be explicit" % left)
print("startup injection: %d .pth removed (%s)"
      % (len(omitted_startup), ", ".join(o["file"] for o in omitted_startup) or "none"))

print("packages: %d dists, %d files copied, %d __pycache__ skipped, "
      "%d outside site-packages skipped, %.1fs"
      % (len(want), copied, skipped_cache, len(escaped), time.time() - t0))
if escaped:
    print("  outside entries (console scripts etc., not runtime imports): %s"
          % escaped[:5])

# ---- 3. the runtime's own verifier, which runs ON the runtime ------------
VERIFY = '''# -*- coding: utf-8 -*-
"""Recompute this runtime's identity. Run BY this runtime, on itself.

It answers three questions and nothing else: are these the bytes the manifest
declares, is this interpreter the declared version, and is every pinned package
present at exactly the pinned version. It reads only inside the runtime tree.
"""
import hashlib
import json
import sys
from importlib import metadata as md
from pathlib import Path

ROOT = Path(__file__).resolve().parent
man = json.loads((ROOT / "RUNTIME_MANIFEST.json").read_text(encoding="utf-8"))

bad_bytes = []
for rel, row in sorted(man["files"].items()):
    p = ROOT / rel
    try:
        data = p.read_bytes()
    except OSError as exc:
        bad_bytes.append("%s: unreadable (%s)" % (rel, exc))
        continue
    if len(data) != row["byte_count"]:
        bad_bytes.append("%s: %d bytes, expected %d"
                         % (rel, len(data), row["byte_count"]))
    elif hashlib.sha256(data).hexdigest() != row["sha256"]:
        bad_bytes.append("%s: digest mismatch" % rel)
present = {p.relative_to(ROOT).as_posix()
           for p in ROOT.rglob("*") if p.is_file()
           and p.name not in ("RUNTIME_MANIFEST.json",)
           and "__pycache__" not in p.parts}
undeclared = sorted(present - set(man["files"]))

ident = man["identity"]
running = ".".join(str(x) for x in sys.version_info[:3])
problems = list(bad_bytes)
if running != ident["python_version"]:
    problems.append("interpreter is %s, manifest declares %s"
                    % (running, ident["python_version"]))
if sys.platform != ident["platform"]:
    problems.append("platform is %s, manifest declares %s"
                    % (sys.platform, ident["platform"]))
for name, ver in sorted(ident["packages"].items()):
    try:
        got = md.version(name)
    except Exception:                                         # noqa: BLE001
        got = None
    if got != ver:
        problems.append("%s is %r, pinned %s" % (name, got, ver))
if undeclared:
    problems.append("%d file(s) in the runtime are not in its manifest: %s"
                    % (len(undeclared), undeclared[:5]))

print("RUNTIME_ID          = %s" % ident["runtime_id"])
print("PYTHON_VERSION      = %s" % running)
print("EXECUTABLE          = %s" % sys.executable)
print("FILES_VERIFIED      = %d" % len(man["files"]))
print("PINNED_PACKAGES     = %d" % len(ident["packages"]))
if problems:
    print("RUNTIME_VERIFY      = FAIL")
    for p in problems[:20]:
        print("   " + p)
    sys.exit(1)
print("RUNTIME_VERIFY      = OK")
'''
(OUT / "verify_runtime.py").write_bytes(
    VERIFY.replace("\r\n", "\n").encode("utf-8"))

# ---- 4. the manifest ----------------------------------------------------
t0 = time.time()
files = {}
for p in sorted(OUT.rglob("*")):
    if not p.is_file() or p.name == "RUNTIME_MANIFEST.json":
        continue
    if "__pycache__" in p.parts:
        continue
    data = p.read_bytes()
    files[p.relative_to(OUT).as_posix()] = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_count": len(data),
    }
identity = {
    "runtime_id": RUNTIME_ID,
    "python_version": ".".join(str(x) for x in sys.version_info[:3]),
    "python_version_major_minor": "%d.%d" % sys.version_info[:2],
    "platform": sys.platform,
    "packages": want,
    "source_interpreter": str(INSTALL),
    "source_note": ("copied from the interpreter that was mechanically shown to "
                    "satisfy the sealed bundle's bound environment identity "
                    "(DEC-CRB-ENV-2/3). Nothing was downloaded or installed, and "
                    "no pin was changed, so the identity is unchanged -- only "
                    "its reachability is."),
    "omitted_startup_files": omitted_startup,
    "startup_injection": "NONE -- no .pth remains in site-packages",
    "materialised_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
manifest = {
    "runtime_manifest_version": "REVIEW_RUNTIME v1",
    "identity": identity,
    "file_count": len(files),
    "byte_total": sum(r["byte_count"] for r in files.values()),
    "files": files,
    "self_hash": "NOT SELF-HASHED BY CONSTRUCTION -- "
                 "RUNTIME_MANIFEST_SHA256 is recorded in the bundle",
}
blob = (json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True)
        .replace("\r\n", "\n") + "\n").encode("utf-8")
(OUT / "RUNTIME_MANIFEST.json").write_bytes(blob)
digest = hashlib.sha256(blob).hexdigest()
print("manifest: %d files, %.1f MB, hashed in %.1fs"
      % (len(files), manifest["byte_total"] / 1e6, time.time() - t0))
print()
print("RUNTIME_ID              = %s" % RUNTIME_ID)
print("RUNTIME_MANIFEST_SHA256 = %s" % digest)
