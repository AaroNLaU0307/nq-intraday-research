# -*- coding: utf-8 -*-
"""The reviewer's OUTPUT root: resolved, bound, and outside the sealed bundle.

WHY THE OUTPUT LEFT THE BUNDLE. The review seat runs under a RESTRICTED Windows
token. Its own measurement showed the sealed-bundle path is not writable to it
even with an ordinary NTFS Modify ACE present -- so no ACL is the answer, and
the last three attempts to make a bundle-local directory writable were all
answering the wrong question. The bundle is now IMMUTABLE to review execution,
full stop, and everything the reviewer produces lives in a seat-native
directory the seat has already proved it can write.

THE RESOLUTION IS OS-NATIVE AND THE ENVIRONMENT HAS NO SAY IN IT. The base is
`<FOLDERID_LocalAppData>/Temp`, read through `SHGetKnownFolderPath`, which
resolves from the user's token and the profile registry. `tempfile.gettempdir()`
would NOT do: it consults TMPDIR, TEMP and TMP first, and with those pointed
elsewhere the output root followed -- measured, before this was fixed. Neither
would `GetTempPathW` or `GetTempPath2W`, whose documented order is TMP, TEMP,
USERPROFILE, Windows directory; being a Windows API does not make a function
environment-independent. No username is hardcoded, no absolute path is written
into the contract, and there is deliberately no fallback: a fallback to the
environment-directed path would reintroduce the channel exactly when the
OS-native route failed.

THE ROOT IS BOUND TO ONE DELIVERY. Its name carries the review id and a prefix
of the manifest digest, and it holds an `OUTPUT_BINDING.json` naming the review
id, the manifest digest, the runtime digest and the round. Two deliveries
cannot collide, and an artifact cannot be mistaken for one produced against
different bytes -- `check_binding` refuses every mismatch rather than reporting
it.

IT IS AN OUTPUT SURFACE, NOT AN INPUT ONE. Nothing here reads a sibling, lists
the temp base, or treats anything under it as review input. The execution guard
admits exactly this one directory and denies the rest of the filesystem,
temp included.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path

#: The one fixed segment, so every delivery's work lands together and nothing
#: else in the seat's temp space is touched or even looked at.
NAMESPACE = "itsf-review"

#: What every retained reviewer artifact is bound to.
BINDING_FIELDS = ("review_id", "manifest_sha256", "runtime_manifest_sha256",
                  "substantive_round")

BINDING_FILE = "OUTPUT_BINDING.json"
SCRATCH_NAME = ".scratch"

#: The reviewer's retained returns. Named here so the runner can assert they
#: are never written inside `.scratch`.
RETAINED_ARTIFACTS = ("INITIAL_FINDINGS.md", "FREEZE.json", "ATTESTATION.md")


class OutputRootRefused(RuntimeError):
    """The output root cannot be established. Always a DELIVERY FAILURE."""


#: Windows KNOWNFOLDERID values. `SHGetKnownFolderPath` resolves these from the
#: user's own token and the profile registry -- NOT from the environment.
_FOLDERID_LOCAL_APPDATA = "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}"
_FOLDERID_PROFILE = "{5E6C858F-0E22-4760-9AFE-EA3317B67173}"


class _GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16),
                ("Data3", ctypes.c_uint16), ("Data4", ctypes.c_ubyte * 8)]


def _known_folder(folder_id: str) -> Path:
    """One known folder, straight from the OS.

    `OleDLL` raises on a failed HRESULT, so a folder that cannot be resolved
    becomes an exception rather than a silently wrong path.
    """
    ole32 = ctypes.OleDLL("ole32")
    shell32 = ctypes.OleDLL("shell32")
    guid = _GUID()
    ole32.CLSIDFromString(ctypes.c_wchar_p(folder_id), ctypes.byref(guid))
    out = ctypes.c_wchar_p()
    shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None,
                                 ctypes.byref(out))
    try:
        if not out.value:
            raise OutputRootRefused(
                "SHGetKnownFolderPath returned no path for %s" % folder_id)
        return Path(out.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(out)


def seat_temp_base() -> Path:
    """The seat's own temporary workspace, resolved WITHOUT the environment.

    WHY NOT `tempfile.gettempdir()`, which is what this used to call. It
    consults TMPDIR, then TEMP, then TMP, and only then falls back. Measured:
    with those three pointed at a directory of one's choosing, the review
    output root moved there -- so the previous claim that there was no
    environment channel was simply wrong, and a containment check against "the
    resolved temp base" proves nothing when the base is what moved.

    WHY NOT `GetTempPathW` OR `GetTempPath2W` EITHER, which is the correction
    worth recording: their documented resolution order is TMP, then TEMP, then
    USERPROFILE, then the Windows directory. Being a Windows API does not make
    a function environment-independent, and for a non-SYSTEM process both of
    those are environment-directed in exactly the way this must not be.

    So the base is `<FOLDERID_LocalAppData>/Temp`. `SHGetKnownFolderPath`
    resolves from the user's token and the profile registry; TMP, TEMP and
    TMPDIR have no bearing on it. It is cross-checked against
    `FOLDERID_Profile` from the same API, so a LocalAppData that does not lie
    under the seat's own profile refuses rather than being used.

    There is NO FALLBACK. A fallback to the environment-directed path would
    reintroduce the channel precisely when the OS-native route failed, which is
    the worst moment to take the reviewer's word for where to write.
    """
    if os.name != "nt":
        raise OutputRootRefused(
            "this contract resolves its output root through a Windows-native "
            "known folder; os.name is %r, and falling back to the "
            "environment-directed temporary directory would reintroduce the "
            "redirection this exists to close" % os.name)
    try:
        local = _known_folder(_FOLDERID_LOCAL_APPDATA)
        profile = _known_folder(_FOLDERID_PROFILE)
    except OSError as exc:
        raise OutputRootRefused(
            "the OS-native local application data folder could not be "
            "resolved (%s). There is deliberately no environment fallback"
            % exc)
    local, profile = local.resolve(), profile.resolve()
    if local != profile and profile not in local.parents:
        raise OutputRootRefused(
            "the resolved local application data folder %s does not lie under "
            "the seat's own profile %s" % (local, profile))
    base = (local / "Temp").resolve()
    if not base.is_dir():
        raise OutputRootRefused(
            "the OS-native temporary base %s does not exist" % base)
    return base


def _safe_segment(text: str) -> str:
    keep = [c if (c.isalnum() or c in "-_.") else "-" for c in str(text)]
    return "".join(keep)[:64].strip("-.") or "review"


def output_root_for(review_id: str, manifest_sha256: str,
                    base: Path | None = None) -> Path:
    """`<seat-temp>/itsf-review/<REVIEW_ID>-<manifest prefix>`.

    Deterministic, so the launcher and the runner derive the same path
    independently and a mismatch is detectable rather than assumed away."""
    if not review_id or not manifest_sha256:
        raise OutputRootRefused(
            "an output root needs both a review id and a manifest digest; "
            "got %r / %r" % (review_id, manifest_sha256))
    base = seat_temp_base() if base is None else Path(base).resolve()
    child = "%s-%s" % (_safe_segment(review_id),
                       _safe_segment(manifest_sha256)[:12])
    return base / NAMESPACE / child


def _assert_outside(root: Path, forbidden: Path, what: str) -> None:
    """The output root may not be inside, nor a parent of, a sealed input."""
    try:
        forbidden = Path(forbidden).resolve()
    except OSError:
        return
    if root == forbidden or forbidden in root.parents:
        raise OutputRootRefused(
            "the review output root %s is inside %s (%s); reviewer output must "
            "never land in a sealed or governed location" % (root, forbidden, what))
    if root in forbidden.parents:
        raise OutputRootRefused(
            "the review output root %s is a PARENT of %s (%s); it would contain "
            "a sealed input" % (root, forbidden, what))


def create_output_root(bundle_root: Path, review_id: str,
                       manifest_sha256: str, *, base: Path | None = None,
                       forbidden: tuple = ()) -> Path:
    """Create a NEW output root and prove, by doing it, that it is usable.

    Refuses a pre-existing non-empty directory rather than reusing it: a stale
    root from another attempt is exactly how one delivery's artifacts get read
    as another's.
    """
    bundle_root = Path(bundle_root).resolve()
    root = output_root_for(review_id, manifest_sha256, base=base)

    # THE CONTAINMENT INVARIANT, and the one that actually does the work: the
    # root must live under the seat's own temporary base. Everything the task
    # forbids -- the bundle, the live repository, quant-data, the runtime --
    # is outside that base, so this one check covers them all, and the
    # explicit ones below are belt and braces rather than the argument.
    resolved_base = seat_temp_base() if base is None else Path(base).resolve()
    if resolved_base not in root.parents:
        raise OutputRootRefused(
            "the review output root %s does not lie under the seat's "
            "temporary base %s" % (root, resolved_base))
    _assert_outside(root, bundle_root, "the sealed bundle")
    for path in forbidden:
        _assert_outside(root, Path(path), "a governed location")

    if root.exists():
        if not root.is_dir():
            raise OutputRootRefused(
                "%s exists and is not a directory" % root)
        leftovers = sorted(p.name for p in root.iterdir())
        if leftovers:
            raise OutputRootRefused(
                "the review output root %s already exists and is NOT empty "
                "(%s). A root is never reused: remove it, or the artifacts of "
                "two runs become indistinguishable" % (root, leftovers[:5]))
    else:
        root.mkdir(parents=True)

    # Prove the capability by exercising it, not by reading an ACL.
    probe = root / ".capability_probe"
    try:
        probe.mkdir()
        one = probe / "a"
        one.write_text("probe", encoding="utf-8")
        one.replace(probe / "b")
        (probe / "b").unlink()
        probe.rmdir()
    except OSError as exc:
        raise OutputRootRefused(
            "the review output root %s is not writable: %s" % (root, exc))
    if probe.exists():
        raise OutputRootRefused("the capability probe left residue in %s" % root)
    return root


def binding_for(manifest: dict) -> dict:
    """The identity every retained artifact is bound to, read off the sealed
    manifest so it cannot drift from the bytes it describes."""
    runtime = manifest.get("review_runtime") or {}
    return {
        "review_id": manifest["review_id"],
        "manifest_sha256": manifest["__manifest_sha256__"],
        "runtime_manifest_sha256": runtime.get("runtime_manifest_sha256", ""),
        "substantive_round": manifest["substantive_round"],
    }


def write_binding(root: Path, binding: dict) -> Path:
    missing = [f for f in BINDING_FIELDS if not binding.get(f)]
    if missing:
        raise OutputRootRefused(
            "the output binding is missing %s; an artifact that cannot name "
            "the object it was produced against is not evidence" % missing)
    path = Path(root) / BINDING_FILE
    payload = {k: binding[k] for k in BINDING_FIELDS}
    payload["note"] = (
        "Everything in this directory was produced against the review object "
        "named above and against no other. The sealed bundle itself is "
        "immutable to review execution; this is the only writable surface.")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def check_binding(root: Path, expected: dict) -> dict:
    """Refuse an output root that belongs to a different review object."""
    path = Path(root) / BINDING_FILE
    if not path.exists():
        raise OutputRootRefused("%s carries no %s" % (root, BINDING_FILE))
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise OutputRootRefused("%s is unreadable: %s" % (path, exc))
    wrong = {f: (found.get(f), expected.get(f)) for f in BINDING_FIELDS
             if found.get(f) != expected.get(f)}
    if wrong:
        raise OutputRootRefused(
            "the output root %s was bound to a DIFFERENT review object: %s "
            "(found, expected). Artifacts from one delivery must never be read "
            "as another's" % (root, wrong))
    return found


def _manifest_with_digest(bundle_root: Path) -> dict:
    import hashlib
    raw = (Path(bundle_root) / "MANIFEST.json").read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    manifest["__manifest_sha256__"] = hashlib.sha256(raw).hexdigest()
    return manifest


def prepare(bundle_root: str) -> Path:
    """Launcher entry: resolve, create, prove, bind. Prints the root."""
    bundle_root = Path(bundle_root).resolve()
    manifest = _manifest_with_digest(bundle_root)
    binding = binding_for(manifest)
    forbidden = [bundle_root.parent, Path(__file__).resolve().parents[1]]
    root = create_output_root(bundle_root, binding["review_id"],
                              binding["manifest_sha256"], forbidden=forbidden)
    write_binding(root, binding)
    (root / SCRATCH_NAME).mkdir(exist_ok=True)
    return root


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--prepare":
        try:
            print(str(prepare(sys.argv[2])))
        except (OutputRootRefused, OSError, KeyError) as exc:
            sys.stderr.write("REVIEW OUTPUT ROOT REFUSED: %s\n" % exc)
            raise SystemExit(96)
    else:
        sys.stderr.write("usage: review_output.py --prepare <bundle_root>\n")
        raise SystemExit(2)
