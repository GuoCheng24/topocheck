import numpy as np
import pytest
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


def test_false_merge_rate_is_zero_when_nothing_is_fused():
    from topocheck import false_merge_rate
    gt = np.zeros((60, 80), bool); gt[20, 5:75] = True; gt[40, 5:75] = True
    r = false_merge_rate(gt, gt, min_size=20)
    assert r["false_merge_rate"] == 0.0 and r["n_components"] == 2


def test_false_merge_rate_catches_a_fused_pair():
    from topocheck import false_merge_rate
    gt = np.zeros((60, 80), bool); gt[20, 5:75] = True; gt[40, 5:75] = True
    fused = gt.copy(); fused[20:41, 40] = True
    assert false_merge_rate(fused, gt, min_size=20)["false_merge_rate"] == 1.0


def test_false_merge_rate_is_nan_when_nothing_could_be_fused():
    from topocheck import false_merge_rate
    gt = np.zeros((60, 80), bool); gt[20, 5:75] = True
    r = false_merge_rate(gt, gt, min_size=20)
    assert np.isnan(r["false_merge_rate"]) and r["n_pairs"] == 0


def test_false_merge_rate_ignores_annotation_speckle():
    from topocheck import false_merge_rate
    gt = np.zeros((60, 80), bool); gt[20, 5:75] = True; gt[40, 5:75] = True
    gt[5, 5] = True                                  # one-pixel speck
    assert false_merge_rate(gt, gt, min_size=20)["n_components"] == 2


def test_false_merge_rate_rejects_shape_mismatch():
    from topocheck import false_merge_rate
    with pytest.raises(ValueError):
        false_merge_rate(np.zeros((4, 4), bool), np.zeros((5, 5), bool))
