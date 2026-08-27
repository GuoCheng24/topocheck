"""Per-unit connectivity readout, with the two knobs that decide what it means.

``break_rate`` reports not just *how many* units are broken but *why*:

``missing``
    at least one endpoint is not inside any predicted component — the structure
    was never detected, so no amount of post-hoc repair can fix it;
``fragment``
    both endpoints are detected but land in different components — this is the
    part a repair method could in principle fix.

The split matters because ``fragment / break`` is a hard upper bound on what any
repair or decoding method can achieve.  Reporting only ``break`` hides it.

``tolerance`` relaxes the requirement that the exact GT endpoint voxel lie inside
a predicted component to "within ``tolerance`` voxels of one".  For thin
structures whose tips fade out this is not a cosmetic choice: see
:func:`topocheck.checks.tolerance_sweep`.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from .units import full_structure

__all__ = ["label_with_tolerance", "break_rate", "false_merge_rate"]


def label_with_tolerance(pred: np.ndarray, tolerance: int = 0) -> np.ndarray:
    """Component labels of ``pred``, optionally reachable from ``tolerance`` away.

    Voxels within ``tolerance`` of the prediction inherit the label of their
    nearest predicted voxel; everything else stays 0.
    """
    pred = np.asarray(pred).astype(bool)
    st = full_structure(pred.ndim)
    lab, _ = ndimage.label(pred, structure=st)
    if tolerance <= 0:
        return lab
    grown = pred.copy()
    for _ in range(int(tolerance)):
        grown = ndimage.binary_dilation(grown, structure=st)
    if not pred.any():
        return np.zeros_like(lab)
    idx = ndimage.distance_transform_edt(~pred, return_distances=False, return_indices=True)
    return np.where(grown, lab[tuple(idx)], 0)


def break_rate(pred: np.ndarray, units, tolerance: int = 0) -> dict:
    """Fraction of units whose endpoints are not co-connected in ``pred``.

    Returns a dict with ``break``, ``missing``, ``fragment`` (all fractions of
    ``n_units``), ``repairable_share`` = ``fragment / break``, and ``n_units``.
    """
    if len(units) == 0:
        return dict(break_frac=float("nan"), missing=float("nan"), fragment=float("nan"),
                    repairable_share=float("nan"), n_units=0)
    lab = label_with_tolerance(pred, tolerance)
    miss = frag = 0
    for u in units:
        a, b = lab[u.ends[0]], lab[u.ends[1]]
        if a == 0 or b == 0:
            miss += 1
        elif a != b:
            frag += 1
    n = len(units)
    brk = miss + frag
    return dict(
        break_frac=brk / n,
        missing=miss / n,
        fragment=frag / n,
        repairable_share=(frag / brk) if brk else 0.0,
        n_units=n,
    )


def false_merge_rate(pred: np.ndarray, gt: np.ndarray, min_size: int = 50) -> dict:
    """Fraction of ground-truth component pairs that the prediction fuses.

    This is the other half of the picture.  Break rate alone can always be
    improved by connecting more, so it says nothing on its own; what separates a
    repair from a random one is what it costs here.

    Ground-truth components smaller than ``min_size`` are ignored: they are
    dominated by annotation speckle and would swamp the statistic.

    Returns ``{"false_merge_rate", "n_pairs", "n_merged", "n_components"}``.
    ``false_merge_rate`` is NaN when the ground truth has fewer than two
    components above ``min_size``, i.e. when there is nothing that could be
    wrongly fused.
    """
    pred = np.asarray(pred).astype(bool)
    gt = np.asarray(gt).astype(bool)
    if pred.shape != gt.shape:
        raise ValueError(f"pred {pred.shape} and gt {gt.shape} must have the same shape")
    st = full_structure(gt.ndim)
    labg, ng = ndimage.label(gt, structure=st)
    sizes = np.bincount(labg.ravel())
    big = [i for i in range(1, ng + 1) if sizes[i] >= min_size]
    labp, _ = ndimage.label(pred, structure=st)
    if len(big) < 2:
        return dict(false_merge_rate=float("nan"), n_pairs=0, n_merged=0,
                    n_components=len(big))
    # which predicted component each GT component mostly falls into
    rep = {}
    for c in big:
        overlap = labp[(labg == c) & pred]
        rep[c] = int(np.bincount(overlap).argmax()) if overlap.size else 0
    merged = pairs = 0
    for i in range(len(big)):
        for j in range(i + 1, len(big)):
            a, b = rep[big[i]], rep[big[j]]
            if a and b:
                pairs += 1
                merged += int(a == b)
    return dict(false_merge_rate=(merged / pairs) if pairs else float("nan"),
                n_pairs=pairs, n_merged=merged, n_components=len(big))
