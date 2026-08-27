"""The synthetic demonstration must keep demonstrating the thing it claims.

If a change makes the random strategy stop winning on break rate, either the
package is broken or the argument in the README has changed; both need to be
noticed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))


@pytest.mark.parametrize("cuts", [20])
def test_random_wins_on_break_and_loses_on_merges(cuts):
    import why_random_wins as w

    res = w.main(seeds=range(2), cut_levels=(cuts,))[cuts]
    order = sorted(("random", "nearest", "oracle"),
                   key=lambda k: -res[k]["break_reduction"])
    assert order[0] == "random", (
        "the demonstration no longer shows a random repair topping the break "
        f"rate ranking: {[(k, round(res[k]['break_reduction'], 1)) for k in order]}"
    )
    assert res["random"]["false_merge"] > res["oracle"]["false_merge"], (
        "random repair should fuse more than the oracle; if it does not, the "
        "merge metric is not measuring what the argument needs"
    )
    assert res["none"]["break_reduction"] == 0.0


def test_quickstart_runs():
    import quickstart
    quickstart.main()
