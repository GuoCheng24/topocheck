"""Five checks for claims about topology-aware segmentation.

Each one exists because it caught a real, published-looking result that was not
real.  Run them *before* believing an improvement, not after a reviewer asks.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from .metrics import break_rate, false_merge_rate
from .units import full_structure

__all__ = [
    "random_repair_baseline",
    "decompose_errors",
    "tolerance_sweep",
    "annotation_floor",
    "prevalence_check",
]


# --------------------------------------------------------------------------- #
# 1. random repair baseline
# --------------------------------------------------------------------------- #
def _random_repair(pred, n_voxels, rng):
    """Link randomly chosen component pairs until ~``n_voxels`` are added."""
    st = full_structure(pred.ndim)
    out = pred.copy()
    added = 0
    for _ in range(500):
        if added >= n_voxels:
            break
        lab, n = ndimage.label(out, structure=st)
        if n < 2:
            break
        a, b = rng.choice(np.arange(1, n + 1), size=2, replace=False)
        pa = np.argwhere(lab == a)
        pb = np.argwhere(lab == b)
        ia = pa[rng.integers(len(pa))]
        ib = pb[rng.integers(len(pb))]
        steps = int(np.abs(ia - ib).max()) + 1
        line = np.rint(np.linspace(ia, ib, steps)).astype(int)
        out[tuple(line.T)] = True
        added += steps
    return out


def random_repair_baseline(pred, repaired, units, gt=None, n_repeats: int = 20,
                           seed: int = 0, tolerance: int = 0, min_size: int = 50) -> dict:
    """What does a *random* repair of the same size achieve?

    Connectivity metrics reward adding voxels: linking anything to anything makes
    endpoints co-connected.  A method that does not clearly beat a random repair
    of equal size has not been shown to repair anything.

    Pass ``gt`` to get the second axis.  Break rate on its own can always be
    improved by connecting more, so the comparison that means anything is
    *break at matched false-merge cost*; without ``gt`` this function can only
    report half of it.

    Parameters
    ----------
    pred, repaired : bool arrays
        Prediction before and after your repair / post-processing.
    units : list of Unit
        From :func:`topocheck.units.build_units` on the ground truth.
    gt : bool array, optional
        Ground truth, used to measure false merges alongside break rate.

    Returns
    -------
    dict
        Break rate before / for the method / for the random baseline (mean and
        std over ``n_repeats`` draws), the number of voxels added, and
        ``beats_random``.  When ``gt`` is given, also the corresponding false
        merge rates and ``beats_random_at_matched_merge``, which requires the
        method to reduce breaks further than random *without* merging more.
    """
    pred = np.asarray(pred).astype(bool)
    repaired = np.asarray(repaired).astype(bool)
    n_added = int((repaired & ~pred).sum())
    rng = np.random.default_rng(seed)
    randoms = [_random_repair(pred, n_added, rng) for _ in range(n_repeats)]
    base = break_rate(pred, units, tolerance)["break_frac"]
    method = break_rate(repaired, units, tolerance)["break_frac"]
    draws = np.asarray([break_rate(r, units, tolerance)["break_frac"] for r in randoms], float)
    out = dict(
        voxels_added=n_added,
        break_before=base,
        break_method=method,
        break_random_mean=float(draws.mean()),
        break_random_std=float(draws.std()),
        beats_random=bool(method < draws.mean()),
    )
    if gt is not None:
        m_before = false_merge_rate(pred, gt, min_size)["false_merge_rate"]
        m_method = false_merge_rate(repaired, gt, min_size)["false_merge_rate"]
        m_draws = np.asarray([false_merge_rate(r, gt, min_size)["false_merge_rate"]
                              for r in randoms], float)
        m_rand = float(np.nanmean(m_draws)) if not np.all(np.isnan(m_draws)) else float("nan")
        out.update(
            merge_before=m_before,
            merge_method=m_method,
            merge_random_mean=m_rand,
            beats_random_at_matched_merge=bool(
                method < draws.mean()
                and not (m_method > m_rand)          # NaN-safe: unknown does not pass
            ),
        )
    return out


# --------------------------------------------------------------------------- #
# 2. error decomposition -> repairable budget
# --------------------------------------------------------------------------- #
def decompose_errors(pred, units, tolerance: int = 0) -> dict:
    """Split connectivity errors into undetected structure vs fragmentation.

    ``fragment / break`` is a hard upper bound on the relative break reduction
    any repair or decoding method can achieve on this prediction.  Measure it
    before building the method.
    """
    r = break_rate(pred, units, tolerance)
    r["max_repair_gain"] = r["repairable_share"]
    return r


# --------------------------------------------------------------------------- #
# 3. tolerance sensitivity
# --------------------------------------------------------------------------- #
def tolerance_sweep(pred, units, tolerances=(0, 1, 2, 3)) -> dict:
    """Does the conclusion survive a change in how endpoints are matched?

    Requiring the exact ground-truth endpoint voxel to lie inside a predicted
    component is one convention among several.  If the error composition moves a
    lot across ``tolerances``, the metric cannot on its own carry a claim about
    *why* the errors happen.
    """
    rows = {int(t): break_rate(pred, units, int(t)) for t in tolerances}
    shares = [rows[t]["repairable_share"] for t in rows]
    breaks = [rows[t]["break_frac"] for t in rows]
    # Both movements count.  Looking only at the repairable share would call a
    # case stable when tolerance drives the break rate to zero, because the share
    # is then trivially zero as well.
    break_swing = (max(breaks) - min(breaks)) / max(max(breaks), 1e-12)
    share_swing = max(shares) - min(shares)
    return dict(
        rows=rows,
        break_range=(min(breaks), max(breaks)),
        break_relative_swing=float(break_swing),
        repairable_share_range=(min(shares), max(shares)),
        stable=bool(break_swing < 0.10 and share_swing < 0.10),
    )


# --------------------------------------------------------------------------- #
# 4. annotation floor
# --------------------------------------------------------------------------- #
def annotation_floor(gt_a, gt_b, min_size: int = 5, tolerance: int = 0) -> dict:
    """The metric evaluated between two independent annotations of the same case.

    Improvements below this level are not distinguishable from the disagreement
    between two humans, and the direction of the comparison matters: a more
    inclusive annotator scores very differently as reference than as prediction.
    """
    from .units import build_units

    ua = build_units(gt_a, min_size=min_size)
    ub = build_units(gt_b, min_size=min_size)
    return dict(
        a_as_reference=break_rate(gt_b, ua, tolerance),
        b_as_reference=break_rate(gt_a, ub, tolerance),
    )


# --------------------------------------------------------------------------- #
# 5. prevalence check
# --------------------------------------------------------------------------- #
def prevalence_check(y_true, scores, prevalence: float, recalls=(0.3, 0.5, 0.8)) -> dict:
    """Translate a balanced-sample AUC into the precision you would deploy at.

    Discriminative power measured on a 1:1 sample says nothing about usability
    when positives are rare: at a prevalence of 1e-3, an AUC of 0.97 can still
    mean a hundred false positives per true one.
    """
    y = np.asarray(y_true).astype(bool)
    s = np.asarray(scores, float)
    if y.all() or not y.any():
        raise ValueError("y_true must contain both classes")
    if not 0 < prevalence < 1:
        raise ValueError("prevalence must be in (0, 1)")
    pos = np.sort(s[y])[::-1]
    neg = np.sort(s[~y])[::-1]
    out = {}
    for r in recalls:
        k = max(1, int(np.ceil(r * len(pos))))
        thr = pos[k - 1]
        tpr = float((s[y] >= thr).mean())
        n_fp = int((s[~y] >= thr).sum())
        fpr = n_fp / len(neg)
        # A zero false-positive count in a finite sample is not a zero rate: fall
        # back to the rule-of-three upper bound so the reported precision is a
        # bound rather than a finite-sample artefact.
        fpr_bounded = fpr if n_fp > 0 else 3.0 / len(neg)
        prec = tpr * prevalence / max(tpr * prevalence + fpr_bounded * (1 - prevalence), 1e-300)
        out[float(r)] = dict(threshold=float(thr), tpr=tpr, fpr=fpr,
                             fpr_is_bound=bool(n_fp == 0),
                             deployed_precision=float(prec),
                             false_per_true=float((1 - prec) / max(prec, 1e-300)))
    return dict(prevalence=float(prevalence), operating_points=out)
