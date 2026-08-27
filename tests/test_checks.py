import numpy as np
import pytest
from topocheck import (build_units, decompose_errors, tolerance_sweep,
                       annotation_floor, prevalence_check, random_repair_baseline)

def scene():
    g = np.zeros((60, 80), bool); g[30, 5:75] = True; g[10:50, 40] = True
    return g, build_units(g)


def test_decompose_reports_repairable_budget():
    g, u = scene(); p = g.copy(); p[30, 20] = False; p[30, 72:] = False
    r = decompose_errors(p, u)
    assert 0 < r["max_repair_gain"] < 1
    assert abs(r["missing"] + r["fragment"] - r["break_frac"]) < 1e-12


def test_tolerance_sweep_flags_an_unstable_conclusion():
    g, u = scene(); p = g.copy(); p[30, 73:] = False     # tip-only error
    assert tolerance_sweep(p, u)["stable"] is False


def test_tolerance_sweep_calls_a_robust_case_stable():
    g, u = scene(); p = g.copy(); p[30, 20] = False      # interior gap only
    assert tolerance_sweep(p, u)["stable"] is True


def test_random_baseline_flags_a_repair_that_is_no_better_than_random():
    g, u = scene()
    p = g.copy(); p[30, 20] = False; p[30, 55] = False
    # "repair" that adds a large blob of voxels connecting nothing meaningful
    bad = p.copy(); bad[5:15, 60:70] = True
    out = random_repair_baseline(p, bad, u, n_repeats=5)
    assert out["voxels_added"] > 0
    assert out["beats_random"] is False


def test_annotation_floor_is_direction_dependent():
    a = np.zeros((40, 60), bool); a[20, 5:55] = True
    b = a.copy(); b[10, 5:55] = True                     # b annotates one more branch
    fl = annotation_floor(a, b)
    assert fl["a_as_reference"]["break_frac"] == 0.0     # b covers everything a drew
    assert fl["b_as_reference"]["break_frac"] > 0.0      # a misses b's extra branch


def test_prevalence_check_collapses_a_good_auc_at_low_prevalence():
    rng = np.random.default_rng(0)
    y = np.r_[np.ones(500), np.zeros(500)].astype(bool)
    s = np.r_[rng.normal(2, 1, 500), rng.normal(0, 1, 500)]
    hi = prevalence_check(y, s, prevalence=0.5)["operating_points"][0.8]
    lo = prevalence_check(y, s, prevalence=1e-3)["operating_points"][0.8]
    assert hi["deployed_precision"] > 0.8
    assert lo["deployed_precision"] < 0.05
    assert lo["false_per_true"] > 20


def test_prevalence_check_marks_zero_fpr_as_a_bound():
    y = np.r_[np.ones(50), np.zeros(50)].astype(bool)
    s = np.r_[np.full(50, 10.0), np.zeros(50)]           # perfect separation
    op = prevalence_check(y, s, prevalence=1e-3)["operating_points"][0.5]
    assert op["fpr_is_bound"] is True
    assert op["deployed_precision"] < 1.0                # not the artefactual 1.0


def test_prevalence_check_rejects_bad_input():
    with pytest.raises(ValueError):
        prevalence_check(np.ones(10, bool), np.arange(10), 0.1)
    with pytest.raises(ValueError):
        prevalence_check(np.r_[np.ones(5), np.zeros(5)].astype(bool), np.arange(10), 1.5)
