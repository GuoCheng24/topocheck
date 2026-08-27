"""Run all five checks on a synthetic case, so the output can be reproduced
without downloading anything.

The synthetic ground truth is a small vessel-like tree.  The "prediction" is that
tree with two different failures deliberately introduced: one interior gap (which
a repair could close) and one faded tip (which it could not).  A deliberately
useless "repair" is then applied, and the checks are asked whether to believe it.
"""
from __future__ import annotations

import numpy as np

import topocheck as tc


def make_tree(shape=(96, 128)) -> np.ndarray:
    gt = np.zeros(shape, bool)
    gt[48, 8:120] = True                      # trunk
    for x, dy in ((30, -1), (60, 1), (90, -1)):   # three branches
        for k in range(22):
            gt[48 + dy * k, x + k // 2] = True
    return gt


def main() -> None:
    gt = make_tree()
    units = tc.build_units(gt)

    pred = gt.copy()
    pred[48, 64] = False                      # interior gap  -> fragment
    pred[48, 112:] = False                    # faded tip     -> missing

    print(f"ground truth decomposes into {len(units)} branches\n")

    print("[1] how much of the error is repairable at all")
    d = tc.decompose_errors(pred, units)
    print(f"    break {d['break_frac']:.3f} = missing {d['missing']:.3f} "
          f"+ fragmented {d['fragment']:.3f}")
    print(f"    a repair method can remove at most {100*d['max_repair_gain']:.0f}% of the breaks\n")

    print("[2] does a proposed repair beat a random one of the same size")
    repaired = pred.copy()
    repaired[40:46, 20:26] = True             # a blob that connects nothing useful
    r = tc.random_repair_baseline(pred, repaired, units, n_repeats=10)
    print(f"    added {r['voxels_added']} voxels")
    print(f"    break: {r['break_before']:.3f} -> {r['break_method']:.3f} "
          f"(random of equal size: {r['break_random_mean']:.3f})")
    print(f"    beats random: {r['beats_random']}\n")

    print("[3] does the conclusion survive the endpoint convention")
    t = tc.tolerance_sweep(pred, units)
    for k, v in t["rows"].items():
        print(f"    tolerance {k}: break {v['break_frac']:.3f}, "
              f"repairable share {v['repairable_share']:.2f}")
    print(f"    stable across conventions: {t['stable']}\n")

    print("[4] where does a second annotator land")
    other = gt.copy()
    other[48, 100:] = False                   # a less inclusive annotator
    fl = tc.annotation_floor(gt, other)
    print(f"    first as reference : break {fl['a_as_reference']['break_frac']:.3f}")
    print(f"    second as reference: break {fl['b_as_reference']['break_frac']:.3f}\n")

    print("[5] does a balanced-sample AUC survive the real class ratio")
    rng = np.random.default_rng(0)
    y = np.r_[np.ones(400), np.zeros(400)].astype(bool)
    s = np.r_[rng.normal(2.2, 1, 400), rng.normal(0, 1, 400)]
    p = tc.prevalence_check(y, s, prevalence=1e-3)
    for rec, v in p["operating_points"].items():
        print(f"    recall {rec:.1f}: deployed precision {v['deployed_precision']:.4f} "
              f"({v['false_per_true']:.0f} false positives per true one)")


if __name__ == "__main__":
    main()
