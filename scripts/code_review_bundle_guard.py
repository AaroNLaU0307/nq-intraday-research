# -*- coding: utf-8 -*-
"""Execution guard for a sealed code-review bundle.

THE OWNER RESERVATION THIS IMPLEMENTS. The sealed-bundle execution boundary
must fail closed against escape to prohibited external sources: filesystem
reads/listings outside the bundle, symlink/junction escape, subprocess or
shell escape, outbound network, and any reach into quant-data, real datasets,
the live repository, other review directories or outcome-bearing surfaces.

WHY A FILE-OPEN HOOK ALONE WOULD NOT DO, which the Owner said explicitly. A
hook on `open` leaves `os.listdir`, `os.scandir`, `subprocess`, `socket` and
`ctypes` wide open. This one denies whole EVENT FAMILIES by prefix, so a family
member added by a future CPython release is denied by default rather than
missed -- fail closed is the direction the reservation names.

THE THREE DESIGN POINTS THAT DO THE WORK:

1.  Paths are compared AFTER `Path.resolve()`, which follows symlinks and NTFS
    junctions. A link planted inside the bundle resolves to its real target and
    is therefore judged by where it actually points, not by where it sits. That
    is what closes link escape at read time; the builder additionally refuses to
    cut a bundle containing any link.

2.  `subprocess.*`, `socket.*` and `ctypes.*` are denied WHOLESALE, by prefix.
    Review execution needs none of them. The Owner said DENY is preferred where
    nothing requires them, and nothing here does.

3.  Two narrow allowances, each argued rather than assumed:
      - the interpreter and its libraries, because without them no Python runs;
      - the Windows null device, which is a SINK. Nothing about the project can
        be read through it, and pytest's capture machinery opens it.
    A per-run temp directory is allowed only if the caller passes one.

WHAT THIS DOES NOT CLAIM. It is not a sandbox and does not defend against
adversarial native code executed in-process -- the same boundary the project
already ratified for the L6 runtime (R18: in-process adversarial code is out of
scope). It defends against an honest reviewer's accidental escape and against a
test or module reaching outside the sealed surface, which is the actual threat
the review transport has hit four times.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

#: Whole families denied by prefix, so a new member is denied by default.
DENIED_PREFIXES = ("subprocess.", "socket.", "ctypes.", "os.exec", "os.spawn",
                   "os.posix_spawn", "urllib.", "ftplib.", "smtplib.",
                   "http.client.", "webbrowser.")
#: Exact events with no useful prefix.
DENIED_EXACT = frozenset({"os.system", "os.startfile", "os.fork", "os.forkpty",
                          "pty.spawn", "shutil.rmtree"})
#: event -> index of the path argument.
PATH_EVENTS = {"open": 0, "os.listdir": 0, "os.scandir": 0, "os.mkdir": 0,
               "os.rmdir": 0, "os.remove": 0, "os.rename": 0, "os.replace": 0,
               "os.symlink": 0, "os.link": 0, "os.truncate": 0,
               "os.chmod": 0, "os.chown": 0, "shutil.copyfile": 0,
               "shutil.copymode": 0, "shutil.copystat": 0, "shutil.move": 0}


class BundleEscapeDenied(PermissionError):
    """Raised in-process the moment an escape is attempted."""


def _guard_file() -> str:
    return sys._getframe().f_code.co_filename


#: This module's own code location, taken from a code object rather than from
#: `__file__`, which is an ordinary rebindable attribute.
_GUARD_FILE = _guard_file()


#: The NATIVE RESOLUTION events: resolving a shared library, and resolving a
#: symbol inside one. Everything else in the `ctypes.*` family stays denied
#: outright -- these two are the only ones a runtime can be initialised
#: without, and the only ones this policy can validate a target for.
NATIVE_RESOLUTION_EVENTS = frozenset({"ctypes.dlopen", "ctypes.dlsym"})

#: Code provenance, decided by WHERE CODE WAS LOADED FROM. A name a module
#: gives itself is not provenance: `__name__`, `__file__` and a fabricated
#: `co_filename` are all writable by the code being classified.
RUNTIME = "RUNTIME"
RUNNER = "RUNNER"
REVIEWED = "REVIEWED"
UNREGISTERED = "UNREGISTERED"


def _import_machinery_files() -> frozenset:
    """The frozen bootstrap's own pseudo-filenames, read off the real code
    objects rather than written down.

    These frames sit between a wrapped loader and the module it is executing,
    so a provenance rule that did not account for them would reject every
    initialisation. They are the interpreter's own import machinery: RUNTIME by
    construction, and obtained here from the machinery itself so that a
    renamed or refrozen bootstrap is picked up rather than missed.
    """
    import importlib._bootstrap as b
    import importlib._bootstrap_external as be
    names = set()
    # Deliberately NOT `SourceFileLoader.exec_module`: this module wraps that
    # one, so after installation its code object reports THIS file and the
    # machinery set would both lose `_bootstrap_external` and gain the guard.
    # Everything below is left alone by the wrapper.
    for obj in (b._call_with_frames_removed, b._load, b._find_and_load,
                be.cache_from_source, be.FileFinder.find_spec,
                be.PathFinder.find_spec, be.SourceLoader.get_code):
        try:
            names.add(obj.__code__.co_filename)
        except AttributeError:
            continue
    return frozenset(n for n in names if n and n != _GUARD_FILE)


def _system_library_dirs() -> tuple:
    """The protected system locations a native library may be resolved from.

    Read from the registry rather than from `SystemRoot` in the environment,
    for the same reason the review workspace stopped reading TMP: a variable a
    caller can set is not an authority. `winreg` reaches HKLM through the
    user's own token; nothing here is spelled out as an absolute path.
    """
    try:
        import winreg
    except ImportError:
        return ()
    try:
        with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            root, _ = winreg.QueryValueEx(key, "SystemRoot")
    except OSError:
        return ()
    dirs = []
    for name in ("System32", "SysWOW64"):
        try:
            path = Path(root, name).resolve()
        except OSError:
            continue
        if path.is_dir():
            dirs.append(path)
    return tuple(dirs)


class _Lifecycle:
    """One module initialisation extent, on one thread."""

    __slots__ = ("ident", "module", "origin", "eligible", "frame")

    def __init__(self, ident, module, origin, eligible, frame):
        self.ident = ident
        self.module = module
        self.origin = origin
        self.eligible = eligible
        self.frame = frame


class RuntimeInitPolicy:
    """FIRST NORMAL RUNTIME INITIALIZATION, and nothing wider than that.

    THE PROBLEM THIS SOLVES, exactly. Denying the whole `ctypes.*` family
    refused `ctypes.WinDLL('user32')` while the pinned runtime was initialising
    itself -- pandas' import chain asks dateutil for a timezone, and on Windows
    dateutil reads the registry backend, which loads `user32` to resolve
    localized display names. `BundleEscapeDenied` is a `PermissionError` is an
    `OSError` is a `WindowsError`, and dateutil catches exactly that, so the
    refusal was swallowed and a different timezone backend was substituted in
    silence. The review then executed against objects an ordinary run would not
    have produced, and every test still passed.

    THE RULE. A native resolution is permitted only while a pinned RUNTIME
    module is running its FIRST normal initialisation on this thread, only when
    every Python frame between the event and that initialisation is itself
    runtime code, and only when the library resolves into the runtime tree or a
    protected system location. Outside that, the family denial is unchanged.

    WHY "ATTEMPTED" AND NOT "COMPLETED". A module key is marked the moment its
    first eligible extent BEGINS, so the extent that ends by raising has still
    spent the module's one chance. A completion-keyed set would hand a second
    eligible extent to exactly the module whose first attempt failed, which is
    the one case where a second attempt is most likely to be someone else's
    idea.

    WHAT IT DOES NOT CLAIM. `co_filename` is writable by code that constructs
    its own code objects, so in-process adversarial code can forge RUNTIME
    provenance. That is the boundary the project already ratified (L6 R18: in
    -process adversarial code is out of scope) and this does not move it. What
    this does defend against is the accident it was built for: a refusal that
    changes execution semantics and is then swallowed.
    """

    def __init__(self, runtime_roots=(), runner_roots=(), reviewed_roots=()):
        import threading
        self.runtime_roots = tuple(Path(p).resolve() for p in runtime_roots)
        self.runner_roots = tuple(Path(p).resolve() for p in runner_roots)
        self.reviewed_roots = tuple(Path(p).resolve() for p in reviewed_roots)
        self.machinery = _import_machinery_files()
        self.system_dirs = _system_library_dirs()
        self._attempted = set()              # module keys, process-wide
        self._attempt_lock = threading.Lock()
        self._local = threading.local()      # a new thread inherits nothing
        self._seq = 0
        self._seq_lock = threading.Lock()
        self._provenance_cache = {}
        self.events = []                     # permitted native resolutions
        self.installed = False

    # -- provenance ----------------------------------------------------
    def _under(self, path: Path, roots) -> bool:
        return any(path == r or r in path.parents for r in roots)

    def provenance(self, filename) -> str:
        """Classify ONE code location. Cached: it is asked per frame."""
        if not filename:
            return UNREGISTERED
        hit = self._provenance_cache.get(filename)
        if hit is not None:
            return hit
        if filename in self.machinery:
            result = RUNTIME
        elif filename.startswith("<"):
            # `<string>`, `<stdin>`, `<frozen ...>` that is not the machinery:
            # generated or unregistered code, which never acquires provenance.
            result = UNREGISTERED
        else:
            try:
                real = Path(filename).resolve()
            except (OSError, ValueError, RuntimeError):
                return UNREGISTERED          # uncached: it may be transient
            if self._under(real, self.reviewed_roots):
                result = REVIEWED            # checked first: it nests inside
            elif self._under(real, self.runner_roots):
                result = RUNNER
            elif self._under(real, self.runtime_roots):
                result = RUNTIME
            else:
                result = UNREGISTERED
        self._provenance_cache[filename] = result
        return result

    # -- the lifecycle -------------------------------------------------
    def _stack(self) -> list:
        stack = getattr(self._local, "stack", None)
        if stack is None:
            stack = []
            self._local.stack = stack
        return stack

    def begin(self, module, frame):
        """Called around a loader executing an as-yet-uninitialised module.

        EVERY wrapped execution pushes an extent, not only the eligible ones,
        so that nesting is faithful and the innermost extent is really the
        innermost. A reviewed module imported inside a runtime initialisation
        pushes an INELIGIBLE extent and therefore masks the runtime one, which
        is the conservative direction.
        """
        spec = getattr(module, "__spec__", None)
        name = getattr(spec, "name", None) or getattr(module, "__name__", None)
        origin = getattr(spec, "origin", None)
        eligible = False
        if name and origin and self.provenance(origin) == RUNTIME:
            with self._attempt_lock:
                if name not in self._attempted:
                    self._attempted.add(name)
                    eligible = True
        with self._seq_lock:
            self._seq += 1
            ident = "L%d" % self._seq
        extent = _Lifecycle(ident, name, origin, eligible, frame)
        self._stack().append(extent)
        return extent

    def end(self, extent) -> None:
        """Ends on RETURN and on RAISE alike -- the caller uses `finally`."""
        stack = self._stack()
        while stack:
            top = stack.pop()
            if top is extent:
                return

    def active(self):
        stack = self._stack()
        return stack[-1] if stack else None

    def attempted(self, name) -> bool:
        with self._attempt_lock:
            return name in self._attempted

    # -- the judgement -------------------------------------------------
    def _frames_are_runtime(self, extent, frame=None) -> tuple:
        """Walk from the event to the extent. Every frame in between must be
        runtime code or the import machinery, and the extent's own frame must
        actually be on this stack -- which is what proves the event happened
        inside that initialisation rather than merely while it was open.

        The walk starts at the frame that RAISED the event. When the caller
        does not say which that is, the guard's own frames are stepped over
        first: an audit hook runs on top of the stack it is judging, so
        starting where this function stands would classify the guard itself.
        """
        if frame is None:
            frame = sys._getframe(1)
            while frame is not None and frame is not extent.frame                     and frame.f_code.co_filename == _GUARD_FILE:
                frame = frame.f_back
        seen = []
        for _ in range(200):
            if frame is None:
                return False, seen, "the extent's frame is not on this stack"
            if frame is extent.frame:
                return True, seen, None
            filename = frame.f_code.co_filename
            kind = self.provenance(filename)
            if kind != RUNTIME:
                return False, seen, "%s code ran inside the initialisation: %s" % (
                    kind, filename)
            seen.append(filename)
            frame = frame.f_back
        return False, seen, "the stack is deeper than this policy will walk"

    def _resolve_target(self, raw):
        """A library name -> the file it names, or None.

        Only three shapes are accepted: a path, a name that exists in the
        runtime tree, and a name that exists in a protected system directory.
        Anything that cannot be resolved that way is not approved, so the
        failure direction is refusal.
        """
        if not isinstance(raw, str) or not raw:
            return None
        if "/" in raw or "\\" in raw or (len(raw) > 1 and raw[1] == ":"):
            try:
                candidate = Path(raw).resolve()
            except (OSError, ValueError, RuntimeError):
                return None
            return candidate if candidate.is_file() else None
        for base in self.system_dirs + self.runtime_roots:
            for name in (raw, raw + ".dll"):
                try:
                    candidate = base / name
                    if candidate.is_file():
                        return candidate.resolve()
                except (OSError, ValueError):
                    continue
        return None

    def _approved_target(self, path) -> bool:
        return bool(path) and (self._under(path, self.system_dirs)
                               or self._under(path, self.runtime_roots))

    def judge(self, event, args, frame=None) -> tuple:
        """PERMIT or not, plus the record that has to be written either way.

        `frame` is the frame that raised the event. The audit hook knows it
        exactly and passes it; anything else lets the walk find it.
        """
        raw = None
        if args:
            first = args[0]
            raw = first if isinstance(first, str) else getattr(
                first, "_name", None)
        record = {"event": event, "target_name": raw}
        extent = self.active()
        if extent is None:
            record["refused"] = "no runtime initialisation is active"
            return False, record
        record["lifecycle"] = extent.ident
        record["initializing_module"] = extent.module
        record["initializing_origin"] = extent.origin
        if not extent.eligible:
            record["refused"] = (
                "the innermost active initialisation is not a first normal "
                "RUNTIME initialisation")
            return False, record
        ok, seen, why = self._frames_are_runtime(extent, frame)
        if not ok:
            record["refused"] = why
            return False, record
        record["executing_provenance"] = RUNTIME
        record["frames_checked"] = len(seen)
        target = self._resolve_target(raw)
        if not self._approved_target(target):
            record["refused"] = (
                "%r does not resolve into the runtime tree or a protected "
                "system location" % (raw,))
            return False, record
        record["target"] = str(target)
        record["permitted"] = True
        return True, record

    # -- installation --------------------------------------------------
    def deactivate(self) -> None:
        """Stop being the active policy. The loader wrappers stay in place and
        become pass-throughs, because unwrapping them mid-process would race
        with any import already running through one."""
        global _ACTIVE_POLICY
        if _ACTIVE_POLICY is self:
            _ACTIVE_POLICY = None
        self.installed = False

    def install(self) -> int:
        """Wrap the eligible runtime loaders' `exec_module`.

        WHY THE LOADER CLASSES AND NOT A META-PATH PROXY. Replacing
        `spec.loader` with a wrapper object changes what `isinstance` says
        about every loaded module's loader, and third-party import code does
        ask. Wrapping the three file-loader CLASSES leaves every object
        identity intact and is what "an eligible runtime loader" names: these
        are the loaders that execute a file from a location on disk. The
        runtime TREE is untouched -- this is an in-process wrapper, and the
        delivery still re-hashes all 12002 runtime files afterwards.
        """
        global _ACTIVE_POLICY
        import importlib.machinery as machinery
        classes = (machinery.SourceFileLoader, machinery.SourcelessFileLoader,
                   machinery.ExtensionFileLoader)
        wrapped = 0
        for cls in classes:
            original = cls.exec_module
            if getattr(original, "_itsf_lifecycle", False):
                continue
            cls.exec_module = _make_exec_module(original)
            wrapped += 1
        _ACTIVE_POLICY = self
        self.installed = True
        return wrapped


#: The one policy the loader wrappers consult. A module-level pointer rather
#: than a closure, so the wrapper is installed once and a policy can stop being
#: the active one without leaving a half-unwrapped import machinery behind.
_ACTIVE_POLICY = None


def _make_exec_module(original):
    def exec_module(self, module):
        policy = _ACTIVE_POLICY
        if policy is None:
            return original(self, module)
        extent = policy.begin(module, sys._getframe())
        try:
            return original(self, module)
        finally:
            policy.end(extent)
    exec_module._itsf_lifecycle = True
    return exec_module


def admission_exit_code(guard, code) -> tuple:
    """The admission rule, in one place so it can be tested.

    A refusal no sealed negative control prescribed, or a prescribed one that
    never happened, fails the run -- REGARDLESS of what the test session
    reported. That last clause is the whole point: a library can catch a
    refusal, substitute a fallback and let every test pass, which is exactly
    what happened before this existed.
    """
    reconciled = guard.reconcile()
    if reconciled["unexpected_denials"] or             reconciled["missing_prescribed_denials"]:
        return (code or 98), reconciled
    return code, reconciled


def _devnull_names() -> frozenset:
    n = {"nul", "nul:", os.devnull.lower()}
    n |= {"\\\\.\\" + x for x in ("nul",)}
    n |= {"\\\\?\\" + x for x in ("nul",)}
    return frozenset(n)


DEVNULL = _devnull_names()


def _runtime_roots() -> tuple:
    roots = set()
    candidates = {sys.prefix, sys.base_prefix, os.path.dirname(os.__file__)}
    candidates |= {p for p in sys.path if p}
    for c in candidates:
        try:
            p = Path(c)
            if p.exists():
                roots.add(p.resolve())
        except OSError:
            continue
    return tuple(roots)


#: Events that MUTATE the filesystem. Inside the bundle these are permitted
#: ONLY under the reviewer-writable surface -- the sealed payload is READ-ONLY
#: to review execution. ADDED 2026-09-11: until now the guard judged only
#: WHERE an operation pointed, so a write anywhere inside the bundle root was
#: allowed, the sealed payload included. The reviewer never had permission to
#: create the old scratch directory at the bundle root, which is what made that
#: latitude visible.
MUTATING_EVENTS = frozenset({
    "os.mkdir", "os.rmdir", "os.remove", "os.rename", "os.replace",
    "os.truncate", "os.symlink", "os.link", "os.chmod", "os.chown",
    "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.move"})

#: `open` is a mutation only when the mode says so. args = (path, mode, flags).
_WRITE_MODES = ("w", "a", "x", "+")


def _is_mutation(event, args) -> bool:
    if event in MUTATING_EVENTS:
        return True
    if event != "open":
        return False
    mode = args[1] if len(args) > 1 else None
    if not isinstance(mode, str):
        return False                     # os.open flags: judged by the caller
    return any(m in mode for m in _WRITE_MODES)


#: Events that only ENUMERATE. A listing-only admission permits exactly these
#: under the admitted roots; `open` is deliberately absent, so names may be
#: read and contents may not.
LISTING_EVENTS = frozenset({"os.listdir", "os.scandir", "os.stat"})


#: The Windows extended-length prefixes, which `Path.resolve()` leaves in
#: place. FOUND 2026-09-11 in a sealed run: pytest took its tmp-directory lock
#: through `\\?\C:\...`, and a path INSIDE the bundle therefore failed to
#: compare inside and was denied. That failure was fail-closed -- an ESCAPE
#: spelled the same way is still denied, because after stripping it resolves
#: outside -- but a boundary that refuses legitimate work is a defect even
#: when it errs safe, and a reviewer hitting it would read it as a transport
#: failure. Stripping also makes the `..` case STRICTER, not looser: under the
#: prefix Windows treats `..` as a literal directory name, and normalising it
#: can only move the resolved path further out, where it is denied.
_EXTENDED = ("\\\\?\\UNC\\", "\\\\?\\", "\\\\.\\")


def _strip_extended_prefix(text: str) -> str:
    for prefix in _EXTENDED:
        if text.upper().startswith(prefix.upper()):
            rest = text[len(prefix):]
            if prefix.endswith("UNC\\"):
                return "\\\\" + rest
            # A drive-qualified remainder is a path; anything else (`NUL`,
            # `PhysicalDrive0`) is a DEVICE NAME and must not be treated as
            # one, so it is left exactly as it came in.
            if len(rest) >= 2 and rest[1] == ":":
                return rest
            return text
    return text


class Expectation:
    """A denial a sealed negative control PRESCRIBES, declared before it is
    caused.

    The guarded surface contains controls that MUST be refused -- a write
    outside the bundle, a native resolution outside a runtime initialisation --
    and a reviewer reading a flat denial list cannot tell those from an
    accident. So the control declares what it is about to cause, the guard
    matches refusals against the declarations, and anything unmatched is
    UNEXPECTED. A declaration nothing matches is just as much a failure: it
    means the control stopped controlling.
    """

    __slots__ = ("event", "contains", "prescribed_by", "why", "matched")

    def __init__(self, event, contains, prescribed_by, why):
        self.event = event
        self.contains = (contains or "").lower()
        self.prescribed_by = prescribed_by
        self.why = why
        self.matched = 0

    def matches(self, event, target) -> bool:
        if event != self.event:
            return False
        if not self.contains:
            return True
        return self.contains in str(target or "").lower()

    def as_dict(self) -> dict:
        return {"event": self.event, "target_contains": self.contains,
                "prescribed_by": self.prescribed_by, "why": self.why,
                "matched": self.matched}


class Guard:
    def __init__(self, bundle_root, tmp_root=None, runtime_roots=None,
                 listing_only_roots=(), writable_root=None, policy=None):
        self.bundle = Path(bundle_root).resolve()
        self.tmp = Path(tmp_root).resolve() if tmp_root else None
        # The ONE writable surface inside the bundle. `return/` is where the
        # review contract already sends INITIAL_FINDINGS, FREEZE and
        # ATTESTATION, and it is the only place the review seat has been
        # observed to be able to write. Everything else in the bundle is
        # sealed input and stays read-only while the review runs.
        self.writable = (Path(writable_root).resolve()
                         if writable_root else None)
        self.runtime = tuple(runtime_roots) if runtime_roots else _runtime_roots()
        # BOUNDED ADMISSION (Aaron, 2026-09-10, on DEC-CRB-HOLD-1 / B-34):
        # directory-NAME enumeration only, under exactly these roots, for the
        # N14 profile alone. File contents under them stay denied -- which is
        # the whole difference between the admission granted and a data read.
        self.listing_only = tuple(Path(p).resolve() for p in listing_only_roots
                                  if Path(p).exists())
        self.denials = []          # every refusal, for the run report
        self.denial_records = []   # the same refusals, with their attribution
        self.expectations = []     # what the sealed negative controls declare
        self.policy = policy       # runtime-initialization provenance, or None
        self.allowed_path_ops = 0
        self.admitted_listings = 0
        self._judging = False      # re-entrancy: judging touches the fs

    # -- prescribed denials --------------------------------------------
    def expect(self, event, contains=None, prescribed_by=None, why=None):
        """Declare a denial a negative control is about to cause."""
        expectation = Expectation(event, contains, prescribed_by, why)
        self.expectations.append(expectation)
        return expectation

    def _attribute(self, event, target) -> Expectation:
        for expectation in self.expectations:
            if expectation.matches(event, target):
                expectation.matched += 1
                return expectation
        return None

    def _refuse(self, event, target, detail=None):
        """One place where a refusal is recorded, so nothing is refused
        without also being attributed."""
        expectation = self._attribute(event, target)
        self.denials.append((event, None if target is None else str(target)))
        record = {"event": event,
                  "target": None if target is None else str(target),
                  "prescribed_by": expectation.prescribed_by if expectation
                  else None}
        if detail:
            record["detail"] = detail
        self.denial_records.append(record)
        return record

    def reconcile(self) -> dict:
        """EXPECTED / UNEXPECTED / MISSING, derived from the declarations.

        A run with an unexpected refusal has not established what it looks like
        it established: the refusal may have been swallowed by a library and
        the session may still have reported success.
        """
        expected = [r for r in self.denial_records if r["prescribed_by"]]
        unexpected = [r for r in self.denial_records if not r["prescribed_by"]]
        missing = [e.as_dict() for e in self.expectations if not e.matched]
        return {"expected_denials": expected, "unexpected_denials": unexpected,
                "missing_prescribed_denials": missing,
                "prescribed": [e.as_dict() for e in self.expectations],
                "runtime_initialization_events":
                    list(self.policy.events) if self.policy else []}

    def _write_admitted(self, real: Path) -> bool:
        """A mutation is admitted under the reviewer surface, under a caller-
        supplied scratch root, or -- unchanged from before -- anywhere the
        interpreter itself lives. The last one is not new latitude: it is the
        same runtime allowance reads already have, and B-39 tracks tightening
        it separately."""
        for root in (self.writable, self.tmp):
            if root is not None and (real == root or root in real.parents):
                return True
        return any(real == r or r in real.parents for r in self.runtime)

    def _listing_admitted(self, real: Path) -> bool:
        return any(real == r or r in real.parents for r in self.listing_only)

    # -- the only judgement in the file ---------------------------------
    def _inside(self, raw) -> bool:
        try:
            text = os.fsdecode(raw)
        except (TypeError, ValueError, UnicodeDecodeError):
            return False                     # undecodable: fail closed
        stripped = text.lower().rstrip("\\/")
        if stripped in DEVNULL or stripped.rsplit("\\", 1)[-1] == "nul":
            return True
        text = _strip_extended_prefix(text)
        try:
            # resolve() follows symlinks and junctions: a link inside the
            # bundle is judged by its TARGET, which is what closes link escape.
            real = Path(text).resolve()
        except (OSError, ValueError, RuntimeError):
            return False                     # unresolvable: fail closed
        if real == self.bundle or self.bundle in real.parents:
            return True
        if self.tmp and (real == self.tmp or self.tmp in real.parents):
            return True
        return any(real == r or r in real.parents for r in self.runtime)

    def __call__(self, event, args):
        # NATIVE RESOLUTION, judged before the family denial it belongs to.
        # The family stays denied; what this carves out is one narrow extent --
        # a pinned runtime module running its first normal initialisation, with
        # only runtime code on the stack and a library that resolves into the
        # runtime tree or a protected system location. Outside that extent the
        # answer below is unchanged.
        if event in NATIVE_RESOLUTION_EVENTS and self.policy is not None \
                and not self._judging:
            self._judging = True
            try:
                permitted, record = self.policy.judge(
                    event, args, sys._getframe(1))
            finally:
                self._judging = False
            if permitted:
                self.policy.events.append(record)
                return
            self._refuse(event, record.get("target_name"),
                         detail=record.get("refused"))
            raise BundleEscapeDenied(
                "native resolution denied outside a first normal runtime "
                "initialisation: %s -> %r (%s)"
                % (event, record.get("target_name"), record.get("refused")))
        if event in DENIED_EXACT or event.startswith(DENIED_PREFIXES):
            self._refuse(event, None)
            raise BundleEscapeDenied(
                "escape class denied inside the review bundle: %s" % event)
        idx = PATH_EVENTS.get(event)
        if idx is None or len(args) <= idx:
            return
        target = args[idx]
        if not isinstance(target, (str, bytes, os.PathLike)):
            return                            # a file descriptor, already open
        if self._inside(target):
            if _is_mutation(event, args) and self.writable is not None:
                try:
                    real = Path(_strip_extended_prefix(
                        os.fsdecode(target))).resolve()
                except Exception:                             # noqa: BLE001
                    real = None
                devnull = str(target).lower().rstrip(chr(92) + "/") in DEVNULL
                if real is not None and not devnull \
                        and not self._write_admitted(real):
                    self._refuse(event, target)
                    raise BundleEscapeDenied(
                        "the sealed payload is read-only to review execution: "
                        "%s -> %r. Reviewer output and ephemeral scratch belong "
                        "under return/." % (event, target))
            self.allowed_path_ops += 1
            return
        if event in LISTING_EVENTS:
            try:
                real = Path(os.fsdecode(target)).resolve()
            except Exception:
                real = None
            if real is not None and self._listing_admitted(real):
                # names only, under the admitted roots, and nothing else
                self.admitted_listings += 1
                return
        self._refuse(event, target)
        raise BundleEscapeDenied(
            "filesystem escape denied inside the review bundle: %s -> %r"
            % (event, target))


def block_colorama() -> None:
    """pytest imports colorama on Windows and colorama binds kernel32 through
    ctypes. Rather than carve a native-code hole in the ctypes denial to allow
    coloured output, make colorama unimportable -- pytest already handles that
    ImportError. The denial stays total; the output loses colour."""
    class _Blocked:
        def find_spec(self, name, path=None, target=None):
            if name == "colorama" or name.startswith("colorama."):
                raise ImportError("colorama is unavailable inside the bundle")
            return None
    sys.meta_path.insert(0, _Blocked())


#: The armed guard, so a review probe can ASSERT on what the boundary actually
#: refused rather than take its existence on trust. Read-only by convention;
#: an audit hook cannot be removed once installed, so this exposes evidence,
#: not control.
ACTIVE = None


def arm(bundle_root, tmp_root=None, listing_only_roots=(),
        writable_root=None, reviewed_roots=()) -> Guard:
    """Install the guard. There is no disarm: an audit hook cannot be removed,
    which is the property that makes this worth using at all.

    The loader wrapping happens HERE, before anything else is imported, which
    is what makes the runtime's own first initialisations visible. Nothing is
    pre-imported to arrange it: the entry point keeps its normal lazy order and
    the policy simply watches it happen.
    """
    global ACTIVE
    bundle_root = Path(bundle_root).resolve()
    policy = RuntimeInitPolicy(
        runtime_roots=_runtime_roots(),
        runner_roots=(bundle_root,),
        reviewed_roots=tuple(reviewed_roots) or (bundle_root / "tree",))
    policy.install()
    guard = Guard(bundle_root, tmp_root, listing_only_roots=listing_only_roots,
                  writable_root=writable_root, policy=policy)
    sys.addaudithook(guard)
    ACTIVE = guard
    return guard
