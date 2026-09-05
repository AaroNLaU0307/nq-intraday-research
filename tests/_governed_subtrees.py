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

AND ON 2026-09-05 THE SAME THING HAPPENED AGAIN, one level up. Aaron
authorized the run directory for the first real N09, the run executed, and
`itsf-runs/supplements/MC-DS-S001_<UTC>/DAY_STRATA_SUPPLEMENT.json` is now
legitimately on disk in both trees. So EMPTINESS has stopped working for
exactly the reason ABSENCE did: it was a proxy for "no test wrote here",
and the proxy is now false for a reason that has nothing to do with tests.

The property has never changed, and it is what is asserted now:

    they exist  (tied to the recorded grant, not to nothing)
    and NOTHING A TEST DID changed their contents

That is a before/after comparison, which is the only form that keeps
working no matter what an authorized run legitimately puts there. It is
also strictly narrower than "an authorization exists, so anything goes": a
test that writes into a subtree still fails, and so does one that deletes
from it.
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


def assert_governed_subtrees_exist_under_the_grant(repo_root: Path) -> None:
    """They exist, and a USED grant row records why.

    RENAMED AND NARROWED 2026-09-05. This used to also assert they were
    EMPTY. The first authorized N09 run wrote a sealed supplement into both
    trees, so emptiness became false for a reason that says nothing about
    tests -- the same way `not exists()` became false in August.

    What survives is the half that never depended on a snapshot: existence
    WITHOUT the grant row would mean something created them outside any
    authorization. "Nothing a test wrote" is now
    `assert_governed_subtrees_untouched`, which compares before to after and
    therefore cannot rot."""
    record = (repo_root / GRANT_RECORD).read_text(encoding="utf-8")
    assert GRANT_MARK in record, (
        "the governed subtrees exist but %s records no used grant -- so "
        "something created them outside any authorization" % GRANT_RECORD)
    for subtree in GOVERNED_SUBTREES:
        assert contents(subtree) is not None, (
            "%s is gone. It was created under the 2026-08-29 grant and its "
            "removal is not something any code path may do." % subtree)
