import numpy as np
from topocheck import build_units, break_rate, label_with_tolerance

def line():
    g = np.zeros((40, 60), bool); g[20, 5:55] = True
    return g, build_units(g)


def test_perfect_prediction_has_no_breaks():
    g, u = line()
    assert break_rate(g, u)["break_frac"] == 0.0


def test_interior_gap_is_fragment_not_missing():
    g, u = line(); p = g.copy(); p[20, 30] = False
    r = break_rate(p, u)
    assert r["fragment"] == 1.0 and r["missing"] == 0.0
    assert r["repairable_share"] == 1.0


def test_missing_tip_is_missing_not_fragment():
    g, u = line(); p = g.copy(); p[20, 50:] = False
    r = break_rate(p, u)
    assert r["missing"] == 1.0 and r["fragment"] == 0.0
    assert r["repairable_share"] == 0.0          # nothing a repair could fix


def test_tolerance_recovers_a_tip_only_when_close_enough():
    g, u = line(); p = g.copy(); p[20, 53:] = False      # endpoint 2 px away
    assert break_rate(p, u, tolerance=1)["break_frac"] == 1.0
    assert break_rate(p, u, tolerance=2)["break_frac"] == 0.0


def test_empty_prediction_is_all_missing():
    g, u = line()
    r = break_rate(np.zeros_like(g), u)
    assert r["missing"] == 1.0 and r["break_frac"] == 1.0


def test_no_units_returns_nan_not_zero():
    r = break_rate(np.zeros((5, 5), bool), [])
    assert r["n_units"] == 0 and np.isnan(r["break_frac"])


def test_label_with_tolerance_keeps_component_identity():
    g = np.zeros((20, 20), bool); g[5, 2:8] = True; g[5, 12:18] = True
    lab = label_with_tolerance(g, tolerance=1)
    assert lab[5, 1] == lab[5, 2] and lab[5, 2] != lab[5, 12]
