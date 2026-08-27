import numpy as np
import pytest

from topocheck import build_units, full_structure


def test_single_line_is_one_unit():
    g = np.zeros((40, 60), bool)
    g[20, 5:55] = True
    u = build_units(g)
    assert len(u) == 1
    assert set(u[0].ends) == {(20, 5), (20, 54)}


def test_cross_splits_into_four_branches():
    g = np.zeros((40, 40), bool)
    g[20, 5:35] = True
    g[10:30, 20] = True
    assert len(build_units(g)) == 4


def test_short_branches_dropped_by_min_size():
    # Two disconnected open branches, one long and one 3 px long.
    g = np.zeros((30, 40), bool)
    g[10, 5:25] = True
    g[20, 5:8] = True
    assert len(build_units(g, min_size=5)) == 1
    assert len(build_units(g, min_size=2)) == 2


def test_junction_removal_clears_the_whole_junction_neighbourhood():
    # Under full connectivity the pixels flanking a junction are themselves of
    # degree >= 3, so a short stub attached to a line leaves no open branch of
    # its own: the line is split in two and the stub disappears.  Pinned here
    # because it decides what "a branch" means everywhere else in the package.
    g = np.zeros((30, 30), bool)
    g[15, 5:25] = True
    g[13:15, 12] = True
    u = build_units(g, min_size=1)
    assert len(u) == 2
    assert all(e[0] == 15 for unit in u for e in unit.ends)


def test_empty_mask_returns_no_units():
    assert build_units(np.zeros((10, 10), bool)) == []


def test_works_in_3d():
    g = np.zeros((20, 20, 20), bool)
    g[10, 10, 3:17] = True
    u = build_units(g)
    assert len(u) == 1 and len(u[0].ends[0]) == 3


def test_rejects_4d():
    with pytest.raises(ValueError):
        build_units(np.zeros((4, 4, 4, 4), bool))


def test_full_structure_is_full_connectivity():
    assert full_structure(2).sum() == 9
    assert full_structure(3).sum() == 27


def test_unit_reports_its_length_and_repr():
    g = np.zeros((30, 40), bool)
    g[10, 5:25] = True
    u = build_units(g)[0]
    assert len(u) == len(u.coords)
    assert "Unit(" in repr(u)
