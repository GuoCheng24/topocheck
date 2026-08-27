"""The README must not drift away from the code or from its own sources.

`check_claims.py` is the real check; this makes it part of the test run so a
local `pytest` catches drift too, not only CI.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# check_claims.py runs the test suite to measure coverage.  Without this guard
# the two would call each other until the machine gives up; it happened once.
pytestmark = pytest.mark.skipif(
    os.environ.get("TOPOCHECK_IN_CLAIMS") == "1",
    reason="invoked from check_claims.py, which is the thing this test runs",
)


def test_readme_claims_hold():
    r = subprocess.run([sys.executable, "check_claims.py"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_unclaimed_numbers_in_the_readme():
    sys.path.insert(0, str(ROOT))
    import check_claims
    loose = check_claims.uncovered_numbers()
    assert not loose, (
        f"these numbers appear in the README with nothing checking them: {loose}. "
        "Add a CLAIMS entry, or list the number in EXEMPT with a reason."
    )
