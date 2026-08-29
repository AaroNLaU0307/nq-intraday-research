"""Walk the MC-DS supplement path end to end and print what happened.

WHY THIS EXISTS. Aaron asked to see a dry run before anything irreversible
is authorized, and a report he cannot regenerate himself is a report he has
to take on trust. This is the command.

    python scripts/mc_ds_rehearsal.py

WHAT IT DOES. Assembles a gate context, runs A_PRECHECK's thirteen gates
and B_DERIVE's five, drives the C_BUILD mechanism, classifies whatever
refuses, and prints the registry row that a real run WOULD append. Twice:
once with the event flags missing, once with them supplied, so both a
producer refusal and a custody refusal are visible.

WHAT IT IS NOT.

  * NOT an execution. `assert_real_run_allowed`, the directory-creation
    authorization, the registry append and P2 all still refuse, and none of
    them is called.
  * NOT evidence that a real run would pass, and it never can be. The
    production path REFUSES a test_only authority at
    `_g_custody_authority_production` and again inside
    `build_supplement_from_authority`. That partition is exactly what makes
    a rehearsal safe to point at anything, so the C_BUILD section is driven
    with the gates NOT consulted and says so in its own output.
  * NOT a reader of anything real. Every input is generated in process: the
    day universe is made-up closes, the authority is minted through the
    TEST_ONLY entry, and the registry is a string. No Development bytes, no
    governed directory, no registry or exposure event.

WHERE THE FIXTURES LIVE, and why they are imported rather than copied.
`tests/test_mc_supplement_authority.py` builds the synthetic bundle and
`tests/test_day_strata_dryrun.py` builds the synthetic universe. Copying
either into this script would create a second mirror of something that
changes -- the failure mode this repository has produced repeatedly -- so
the script reaches into `tests/` on purpose. If that import ever breaks,
the fixture moved and this script should follow it, not re-implement it.

VERIFIED BY THE MODULE ITSELF. `day_strata_dryrun.rehearse` snapshots the
governed `supplements` subtrees before and after and refuses if either
moved, so "writes nothing" is checked here rather than promised.
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))


def main() -> int:
    import test_day_strata_dryrun as fixtures
    from itsf.mc import day_strata_dryrun as dry

    print("MC-DS SUPPLEMENT REHEARSAL")
    print("repo:", REPO)
    print()

    for label, flags in (("A. event flags missing", {}),
                         ("B. all five flags supplied", fixtures.FLAGS)):
        with tempfile.TemporaryDirectory() as scratch:
            report = fixtures._rehearse(scratch, flags=flags)
            text = dry.render(report).replace(scratch, "<scratch>")
        print("=" * 72)
        print(label)
        print("=" * 72)
        print(text)
        print()

    print("The governed subtrees were snapshotted before and after each walk")
    print("and are byte-identical. Nothing was written, appended or created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
