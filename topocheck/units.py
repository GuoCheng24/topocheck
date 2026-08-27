"""Branch (unit) decomposition of a ground-truth mask, and connectivity readout.

A *unit* is a maximal branch of the GT skeleton: junctions are removed, and each
surviving connected piece with exactly two endpoints becomes one unit.  Topology
of a prediction is then read out per unit: a unit is *broken* when its two
endpoints do not end up in the same connected component of the prediction.

Works for 2-D and 3-D.  Connectivity is full (8- / 26-neighbourhood) throughout,
which is the convention that avoids the well-known foreground/background
connectivity paradox for thin structures.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize

__all__ = ["Unit", "build_units", "full_structure"]


class Unit:
    """One GT branch: its skeleton voxels and its two endpoints."""

    __slots__ = ("coords", "ends")

    def __init__(self, coords: np.ndarray, ends: tuple):
        self.coords = coords
        self.ends = ends

    def __len__(self) -> int:
        return len(self.coords)

    def __repr__(self) -> str:  # pragma: no cover - repr only
        return f"Unit(n={len(self.coords)}, ends={self.ends})"


def full_structure(ndim: int) -> np.ndarray:
    """8-connectivity in 2-D, 26-connectivity in 3-D."""
    return np.ones((3,) * ndim, dtype=bool)


def _neighbour_count(skel: np.ndarray) -> np.ndarray:
    st = full_structure(skel.ndim).astype(np.uint8)
    return ndimage.convolve(skel.astype(np.uint8), st, mode="constant") - skel


def build_units(gt: np.ndarray, min_size: int = 5) -> list[Unit]:
    """Decompose ``gt`` into branch units.

    Parameters
    ----------
    gt : bool array, 2-D or 3-D
        Ground-truth foreground mask.
    min_size : int
        Discard branches shorter than this many skeleton voxels.  Very short
        branches are dominated by skeletonisation artefacts.

    Returns
    -------
    list of :class:`Unit`
    """
    gt = np.asarray(gt).astype(bool)
    if gt.ndim not in (2, 3):
        raise ValueError(f"gt must be 2-D or 3-D, got {gt.ndim}-D")
    skel = skeletonize(gt)
    if not skel.any():
        return []
    deg = _neighbour_count(skel)
    branches = skel & (deg <= 2)          # drop junctions (degree >= 3)
    lab, n = ndimage.label(branches, structure=full_structure(gt.ndim))
    units: list[Unit] = []
    if n == 0:
        return units
    objs = ndimage.find_objects(lab)
    bdeg = _neighbour_count(branches)
    for i in range(1, n + 1):
        sl = objs[i - 1]
        if sl is None:
            continue
        m = lab[sl] == i
        if m.sum() < min_size:
            continue
        ends_local = np.argwhere(m & (bdeg[sl] == 1))
        if len(ends_local) != 2:          # keep only clean open branches
            continue
        off = np.array([s.start for s in sl])
        coords = np.argwhere(m) + off
        e = [tuple(int(v) for v in (p + off)) for p in ends_local]
        units.append(Unit(coords, (e[0], e[1])))
    return units
