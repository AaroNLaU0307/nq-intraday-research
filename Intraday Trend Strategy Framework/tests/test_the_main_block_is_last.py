"""`if __name__ == "__main__"` must be the last thing in a test file.

WRITTEN AFTER MAKING THE SAME MISTAKE THREE TIMES IN ONE EVENING. A fresh
Sol review caught the first instance as a LOW finding: classes appended
after the `__main__` block still run under pytest's discovery, but a direct
`python tests/foo.py` executes only the classes defined ABOVE it — and
reports OK.

    direct run   Ran 5 tests ... OK      <- half the file never ran
    pytest       10 passed

I fixed that one, then did it twice more the same night, because the cause
is a habit: appending with `cat >>` puts new classes after whatever is
already at the end of the file.

A mistake made three times is not a mistake, it is a missing guard. The
repository does not run tests by direct invocation, so nothing was ever
broken — but "OK" from a run that executed half the file is the kind of
green that teaches you the wrong thing.
"""

import ast
import io
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent


class TestNoClassIsStrandedAfterTheMainBlock(unittest.TestCase):

    def _files(self):
        files = sorted(p for p in TESTS.glob("*.py")
                       if p.name != Path(__file__).name)
        self.assertGreater(len(files), 50,
                           "the glob found %d test files, too few to be real"
                           % len(files))
        return files

    def test_every_main_block_is_the_last_statement(self):
        offenders = []
        for path in self._files():
            source = io.open(path, encoding="utf-8").read()
            tree = ast.parse(source)
            main_at = None
            for node in tree.body:
                if (isinstance(node, ast.If)
                        and isinstance(node.test, ast.Compare)
                        and getattr(node.test.left, "id", "") == "__name__"):
                    main_at = node.lineno
            if main_at is None:
                continue
            stranded = [n.name for n in tree.body
                        if isinstance(n, (ast.ClassDef, ast.FunctionDef))
                        and n.lineno > main_at]
            if stranded:
                offenders.append("%s: %s" % (path.name, stranded))
        self.assertEqual(
            [], offenders,
            "these files define tests AFTER their `__main__` block, so a "
            "direct `python tests/<file>.py` runs only part of the file and "
            "reports OK:\n  " + "\n  ".join(offenders))

    def test_the_scan_sees_files_that_have_a_main_block(self):
        """A sweep that finds no `__main__` block anywhere would report
        clean while checking nothing."""
        with_main = 0
        for path in self._files():
            tree = ast.parse(io.open(path, encoding="utf-8").read())
            for node in tree.body:
                if (isinstance(node, ast.If)
                        and isinstance(node.test, ast.Compare)
                        and getattr(node.test.left, "id", "") == "__name__"):
                    with_main += 1
                    break
        self.assertGreater(with_main, 10,
                           "only %d test files carry a `__main__` block; "
                           "the check is nearly vacuous" % with_main)


if __name__ == "__main__":
    unittest.main()
