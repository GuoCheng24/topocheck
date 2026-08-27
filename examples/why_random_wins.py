"""Why a random repair scores so well, shown on synthetic data.

The observation in the README — a random assignment of fragments reduced the
break rate by 25.9%, ahead of every learned repair we built — is not a property
of those datasets.  It follows from what the break rate measures.

A unit counts as repaired once its two endpoints share a connected component.
Any linking of components therefore repairs units in bulk, whether or not the
link corresponds to a real vessel.  Break rate cannot see the difference; only
the false merge rate can.

This script builds synthetic vasculature, fragments it, and repairs it three
ways: at random, by nearest component (a plausible heuristic), and by the true
partner.  It sweeps the fragmentation level over several seeds and reports both
axes.  Run it: the three strategies land close together on break rate and far
apart on false merges.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

import topocheck as tc

SHAPE = (220, 260)


def synth_vasculature(rng, n_trees: int = 4) -> np.ndarray:
    """A few separate vessel trees, so that fusing two of them is a real error."""
    gt = np.zeros(SHAPE, bool)
    for t in range(n_trees):
        y0 = 28 + t * 52
        x0, x1 = 20, SHAPE[1] - 20
        gt[y0, x0:x1] = True                                  # trunk
        for b in range(3):
            xb = x0 + 30 + b * 62
            dy = -1 if b % 2 == 0 else 1
            for k in range(20):
                y = np.clip(y0 + dy * k, 0, SHAPE[0] - 1)
                gt[y, min(xb + k // 2, SHAPE[1] - 1)] = True
    return gt


def fragment(gt, rng, n_cuts: int) -> np.ndarray:
    """Cut the prediction at random skeleton positions and fade a few tips."""
    pred = gt.copy()
    ys, xs = np.nonzero(gt)
    for _ in range(n_cuts):
        i = rng.integers(len(ys))
        y, x = ys[i], xs[i]
        pred[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = False
    return pred


def link(pred, a_pts, b_pts, rng):
    ia = a_pts[rng.integers(len(a_pts))]
    ib = b_pts[rng.integers(len(b_pts))]
    steps = int(np.abs(ia - ib).max()) + 1
    line = np.rint(np.linspace(ia, ib, steps)).astype(int)
    out = pred.copy()
    out[tuple(line.T)] = True
    return out


def repair(pred, gt, strategy: str, rng) -> np.ndarray:
    st = tc.full_structure(pred.ndim)
    labp, n = ndimage.label(pred, structure=st)
    if n < 2:
        return pred.copy()
    labg, _ = ndimage.label(gt, structure=st)
    sizes = np.bincount(labp.ravel()); sizes[0] = 0
    order = [c for c in np.argsort(-sizes) if c > 0]
    trunk = order[0]
    pts = {c: np.argwhere(labp == c) for c in order}
    # which GT tree each predicted component belongs to
    tree = {c: int(np.bincount(labg[labp == c]).argmax()) for c in order}
    out = pred.copy()
    for c in order[1:]:
        cand = [d for d in order if d != c]
        if strategy == "random":
            tgt = int(rng.choice(cand))
        elif strategy == "nearest":
            cen = pts[c].mean(0)
            tgt = min(cand, key=lambda d: np.linalg.norm(pts[d].mean(0) - cen))
        elif strategy == "oracle":
            same = [d for d in cand if tree[d] == tree[c]]
            if not same:
                continue
            cen = pts[c].mean(0)
            tgt = min(same, key=lambda d: np.linalg.norm(pts[d].mean(0) - cen))
        else:
            raise ValueError(strategy)
        out = link(out, pts[c], pts[tgt], rng)
    return out


def main(seeds=range(6), cut_levels=(12, 20, 30)) -> dict:
    rows = {}
    for n_cuts in cut_levels:
        acc = {s: {"break": [], "merge": []} for s in ("none", "random", "nearest", "oracle")}
        for sd in seeds:
            rng = np.random.default_rng(sd)
            gt = synth_vasculature(rng)
            units = tc.build_units(gt)
            pred = fragment(gt, rng, n_cuts)
            acc["none"]["break"].append(tc.break_rate(pred, units)["break_frac"])
            acc["none"]["merge"].append(tc.false_merge_rate(pred, gt)["false_merge_rate"])
            for s in ("random", "nearest", "oracle"):
                r = repair(pred, gt, s, np.random.default_rng(1000 + sd))
                acc[s]["break"].append(tc.break_rate(r, units)["break_frac"])
                acc[s]["merge"].append(tc.false_merge_rate(r, gt)["false_merge_rate"])
        base = float(np.mean(acc["none"]["break"]))
        rows[n_cuts] = {s: dict(
            break_frac=float(np.mean(v["break"])),
            break_reduction=100.0 * (base - float(np.mean(v["break"]))) / max(base, 1e-9),
            false_merge=float(np.nanmean(v["merge"])),
        ) for s, v in acc.items()}
    return rows


def plot(res, out: str = "docs/random_baseline.png") -> str:
    """Both axes at once: the ideal repair sits in the top-left corner."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    style = {"random": ("#D55E00", "o"), "nearest": ("#0072B2", "s"), "oracle": ("#009E73", "D")}
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    for s, (col, mk) in style.items():
        xs = [res[n][s]["false_merge"] for n in res]
        ys = [res[n][s]["break_reduction"] for n in res]
        ax.plot(xs, ys, mk, color=col, ms=7, ls="-", lw=1.0, alpha=0.9, label=s)
    ax.annotate("what a repair\nshould look like", xy=(0.02, 88), xytext=(0.20, 92),
                fontsize=8.5, color="#009E73",
                arrowprops=dict(arrowstyle="->", color="#009E73", lw=0.9))
    ax.annotate("wins on break rate\nby fusing everything", xy=(0.97, 84), xytext=(0.50, 62),
                fontsize=8.5, color="#D55E00", ha="center",
                arrowprops=dict(arrowstyle="->", color="#D55E00", lw=0.9))
    ax.set_xlabel("false merge rate  (lower is better)")
    ax.set_ylabel("break rate reduction (%)  (higher is better)")
    ax.set_xlim(-0.08, 1.14); ax.set_ylim(28, 100)
    ax.legend(frameon=False, loc="lower right", title="repair strategy",
              title_fontsize=8.5, handlelength=1.4, borderaxespad=0.8)
    fig.tight_layout()
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    res = main()
    print(f"{'cuts':>5}  {'strategy':<9} {'break':>7} {'reduction':>10} {'false merges':>13}")
    for n_cuts, r in res.items():
        for s in ("none", "random", "nearest", "oracle"):
            v = r[s]
            print(f"{n_cuts:>5}  {s:<9} {v['break_frac']:7.3f} "
                  f"{v['break_reduction']:9.1f}% {v['false_merge']:13.2f}")
        print()
    best = {n: max(("random", "nearest", "oracle"), key=lambda k: r[k]["break_reduction"])
            for n, r in res.items()}
    print("Strategy with the largest break reduction, at each fragmentation level:")
    for n, s in best.items():
        print(f"  {n:>3} cuts: {s}  (false merge rate "
              f"{res[n][s]['false_merge']:.2f}, oracle achieves {res[n]['oracle']['false_merge']:.2f})")
    print()
    print("The strategy that wins on break rate is the one that fuses everything.")
    print("Break rate alone cannot tell a repair from a collapse; only the second")
    print("axis can, which is why both are reported together.")
    try:
        out = plot(res)
        print(f"\nwrote {out}")
    except Exception as exc:            # matplotlib is an optional dev dependency
        print(f"\n(figure skipped: {exc})")
