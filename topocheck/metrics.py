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

__all__ = ["label_with_tolerance", "break_rate"]


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
