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


class Guard:
    def __init__(self, bundle_root, tmp_root=None, runtime_roots=None):
        self.bundle = Path(bundle_root).resolve()
        self.tmp = Path(tmp_root).resolve() if tmp_root else None
        self.runtime = tuple(runtime_roots) if runtime_roots else _runtime_roots()
        self.denials = []          # every refusal, for the run report
        self.allowed_path_ops = 0

    # -- the only judgement in the file ---------------------------------
    def _inside(self, raw) -> bool:
        try:
            text = os.fsdecode(raw)
        except (TypeError, ValueError, UnicodeDecodeError):
            return False                     # undecodable: fail closed
        stripped = text.lower().rstrip("\\/")
        if stripped in DEVNULL or stripped.rsplit("\\", 1)[-1] == "nul":
            return True
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
        if event in DENIED_EXACT or event.startswith(DENIED_PREFIXES):
            self.denials.append((event, None))
            raise BundleEscapeDenied(
                "escape class denied inside the review bundle: %s" % event)
        idx = PATH_EVENTS.get(event)
        if idx is None or len(args) <= idx:
            return
        target = args[idx]
        if not isinstance(target, (str, bytes, os.PathLike)):
            return                            # a file descriptor, already open
        if self._inside(target):
            self.allowed_path_ops += 1
            return
        self.denials.append((event, str(target)))
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


def arm(bundle_root, tmp_root=None) -> Guard:
    """Install the guard. There is no disarm: an audit hook cannot be removed,
    which is the property that makes this worth using at all."""
    guard = Guard(bundle_root, tmp_root)
    sys.addaudithook(guard)
    return guard
