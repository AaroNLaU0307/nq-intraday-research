"""The governed `supplements` subtrees, and what may be asserted of them.

UNTIL 2026-08-29 five tests asserted `not subtree.exists()`. That was the
ruling's CONDITION -- "两个根下的 `supplements\\` 子树在授权执行前继续保持
不存在" -- and it held because directory creation had never been authorized.

On 2026-08-29 Aaron authorized it verbatim, the main agent created both
directories manually, and the pre/post exact-set snapshots went into
`ops/DIRECTORY_CREATION_GRANTS.md` §4 row 1. The condition's premise is
gone: it was "before the authorization is executed", and it has been.

THE PROPERTY THOSE TESTS PROTECTED IS NOT GONE, and it is not the same as
the assertion they used. What matters is that NO CODE PATH -- not the
runner, not the gates, not a test battery -- creates or writes into those
directories. `not exists()` was a proxy for that, and it was a proxy that
STOPS WORKING the moment the directories legitimately exist: after that it
would pass while a test quietly wrote files into them.

So the replacement is strictly stronger, not weaker:

    they exist  (tied to the recorded grant, not to nothing)
    they are EMPTY
    and nothing a test touched changed their contents

`emptiness` catches what `absence` could not: a write into an existing
directory.
"""

from pathlib import Path

GOVERNED_SUBTREES = (
    Path(r"C:\Users\Aaron\quant-data\itsf-runs") / "supplements",
    Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive") / "supplements",
)

#: Where the creation is recorded. Existence without this row would mean
#: something created them outside any authorization.
GRANT_RECORD = "ops/DIRECTORY_CREATION_GRANTS.md"
GRANT_MARK = "**USED（用掉即失效）**"


def contents(subtree: Path) -> tuple:
    """The exact set under a governed subtree: relative posix paths.

    A subtree that does not exist reports `None`, which is DIFFERENT from
    an empty one -- "I could not look" must never read as "nothing is
    there"."""
    if not subtree.exists():
        return None
    return tuple(sorted(p.relative_to(subtree).as_posix()
                        for p in subtree.rglob("*")))


def snapshot() -> dict:
    return {str(s): contents(s) for s in GOVERNED_SUBTREES}


def assert_governed_subtrees_untouched(before: dict, what: str) -> None:
    """Nothing `what` did created, removed, or wrote into either subtree."""
    after = snapshot()
    assert before == after, (
        "%s changed a governed supplements subtree.\n  before=%s\n  after =%s\n"
        "Directory creation is a separate authorization and the one that was "
        "granted (2026-08-29) is bound to an event and already USED."
        % (what, before, after))


def assert_governed_subtrees_are_empty(repo_root: Path) -> None:
    """They exist because of a recorded grant, and hold nothing.

    Both halves matter. Existence WITHOUT the grant row would mean
    something created them unauthorized; a non-empty subtree would mean
    something wrote into them, which no authorization has ever covered."""
    record = (repo_root / GRANT_RECORD).read_text(encoding="utf-8")
    assert GRANT_MARK in record, (
        "the governed subtrees exist but %s records no used grant -- so "
        "something created them outside any authorization" % GRANT_RECORD)
    for subtree in GOVERNED_SUBTREES:
        held = contents(subtree)
        assert held is not None, (
            "%s is gone. It was created under the 2026-08-29 grant and its "
            "removal is not something any code path may do." % subtree)
        assert held == (), (
            "%s holds %s. The grant covered CREATING the empty parent and "
            "nothing else; writing into it needs the execution authorization, "
            "which has not been given." % (subtree, list(held)))
