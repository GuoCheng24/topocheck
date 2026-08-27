"""Regenerate the README figure from the measured values.

Every number below is quoted from the experiments described in the README and is
reproduced verbatim here so the figure can be audited against them.  Sources:

(a) TopCoW, 50 held-out volumes, strict endpoint criterion.
(b) HRF (45 fundus images) and TopCoW, plain U-Net baseline, threshold 0.5.
(c) same two datasets, endpoint tolerance swept over 0-3 voxels.
(d) STARE, 20 fundus images with two expert annotators
the model is a U-Net
    cross-validated on the same 20 images against annotator "ah".
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "Liberation Sans",
    "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
})
# Okabe-Ito, colour-vision-safe
BLUE, ORANGE, GREEN, GREY, RED = "#0072B2", "#E69F00", "#009E73", "#999999", "#D55E00"

# (a) break reduction vs false-merge cost, TopCoW test50, strict criterion
A_LABELS = ["shuffled-label\ncontrol", "cheapest-partner\nrule", "learned pairwise\nselector",
            "random\nassignment", "connect all to\nlargest component"]
A_GAIN = [0.00, 16.47, 20.58, 25.87, 27.36]          # % break reduction
A_MERGE = [1.0, 17.0, 10.0, 18.0, 20.0]              # false-merge rate, x baseline
A_ISRAND = [False, False, False, True, False]

# (b) error composition at the strict criterion
B_SETS = ["HRF\n(2-D retina)", "TopCoW\n(3-D brain)"]
B_BREAK = [0.517, 0.146]
B_FRAG_SHARE = [0.033, 0.277]

# (c) undetected share vs endpoint tolerance
C_TOL = [0, 1, 2, 3]
C_HRF = [96.7, 93.8, 94.6, 95.1]
C_COW = [72.3, 63.3, 48.2, 41.6]

# (d) STARE: human-human disagreement band and where a model lands
D_HUMAN = (0.204, 0.564)     # ah as reference / vk as reference
D_MODEL, D_HUMAN_SAME_EVAL = 0.214, 0.206   # field-of-view masked, same evaluation


def main(out: str = "docs/hero.png") -> str:
    fig, ax = plt.subplots(2, 2, figsize=(9.0, 6.4))
    fig.subplots_adjust(left=0.09, right=0.975, top=0.93, bottom=0.08, hspace=0.55, wspace=0.30)

    # ---- (a) horizontal bars: the random baseline is not far behind ----------
    a = ax[0, 0]
    y = np.arange(len(A_LABELS))
    cols = [RED if r else (GREY if g == 0 else BLUE) for r, g in zip(A_ISRAND, A_GAIN)]
    a.barh(y, A_GAIN, color=cols, height=0.62)
    a.set_yticks(y)
    a.set_yticklabels(A_LABELS)
    a.invert_yaxis()
    a.set_xlabel("break rate reduction (%)")
    a.set_xlim(0, 37)
    for yi, (g, m) in enumerate(zip(A_GAIN, A_MERGE)):
        a.text(g + 0.7, yi, f"{g:.1f}%" + ("" if m <= 1.0 else f"   false merges {m:.0f}x"),
               va="center", fontsize=8)
    a.set_title("a   a random repair is competitive on the metric",
                loc="left", fontsize=9.5, fontweight="bold", pad=8)

    # ---- (b) stacked composition: how much is even repairable ---------------
    b = ax[0, 1]
    x = np.arange(len(B_SETS))
    frag = [br * fs for br, fs in zip(B_BREAK, B_FRAG_SHARE)]
    miss = [br - f for br, f in zip(B_BREAK, frag)]
    b.bar(x, miss, color=GREY, width=0.5, label="undetected structure (unrepairable)")
    b.bar(x, frag, bottom=miss, color=GREEN, width=0.5, label="fragmented (repairable)")
    b.set_xticks(x)
    b.set_xticklabels(B_SETS)
    b.set_ylabel("break rate")
    b.set_ylim(0, 0.68)
    b.set_xlim(-0.62, 2.05)
    for xi, (br, fs) in enumerate(zip(B_BREAK, B_FRAG_SHARE)):
        b.annotate(f"repairable\nat most {100*fs:.1f}%", xy=(xi + 0.27, br), xytext=(xi + 0.33, br + 0.075),
                   fontsize=8, color=GREEN, ha="left", va="bottom",
                   arrowprops=dict(arrowstyle="-", color=GREEN, lw=0.8))
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1,
             frameon=False, handlelength=1.2)
    b.set_title("b   the ceiling on any repair method",
                loc="left", fontsize=9.5, fontweight="bold", pad=8)

    # ---- (c) lines: does the conclusion survive the conventions -------------
    c = ax[1, 0]
    c.plot(C_TOL, C_HRF, "-o", color=BLUE, lw=1.6, ms=4.5, label="HRF (2-D)")
    c.plot(C_TOL, C_COW, "-s", color=ORANGE, lw=1.6, ms=4.5, label="TopCoW (3-D)")
    c.set_xticks(C_TOL)
    c.set_xlabel("endpoint tolerance (voxels)")
    c.set_ylabel("share of breaks that are\nundetected structure (%)")
    c.set_ylim(30, 105)
    c.annotate("same measurement,\nopposite story", xy=(2, 48.2), xytext=(1.15, 66),
               fontsize=8, color=ORANGE,
               arrowprops=dict(arrowstyle="->", color=ORANGE, lw=0.9))
    c.legend(loc="lower left", frameon=False, handlelength=1.6)
    c.set_title("c   one convention, a different conclusion",
                loc="left", fontsize=9.5, fontweight="bold", pad=8)

    # ---- (d) band + point: is the gain inside human disagreement ------------
    d = ax[1, 1]
    lo, hi = D_HUMAN
    d.axvspan(lo, hi, color=GREY, alpha=0.28, lw=0)
    d.plot([lo, hi], [1, 1], color=GREY, lw=2.2, solid_capstyle="butt")
    d.plot([lo], [1], "o", color=GREY, ms=7)
    d.plot([hi], [1], "o", color=GREY, ms=7)
    d.text(lo, 1.16, "annotator ah\nas reference (0.204)", ha="left", fontsize=8, color=GREY)
    d.text(hi, 1.16, "annotator vk\nas reference (0.564)", ha="right", fontsize=8, color=GREY)
    # lower row: the two numbers that are directly comparable (same evaluation)
    d.plot([D_HUMAN_SAME_EVAL], [0.45], "o", color=GREY, ms=7)
    d.plot([D_MODEL], [0.45], "D", color=BLUE, ms=7.5)
    d.annotate(f"second human {D_HUMAN_SAME_EVAL:.3f}", xy=(D_HUMAN_SAME_EVAL, 0.45),
               xytext=(0.30, 0.22), fontsize=8, color=GREY, ha="left", va="center",
               arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8))
    d.annotate(f"U-Net {D_MODEL:.3f}", xy=(D_MODEL, 0.45), xytext=(0.30, 0.70),
               fontsize=8, color=BLUE, ha="left", va="center",
               arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8))
    d.text(0.487, 0.46, "0.008 apart", fontsize=8, color="#444444", ha="left", va="center")
    d.set_xlim(0.135, 0.66)
    d.set_ylim(0.02, 1.52)
    d.set_yticks([])
    d.spines["left"].set_visible(False)
    d.set_xlabel("break rate on STARE")
    d.set_title("d   the model lands inside human disagreement",
                loc="left", fontsize=9.5, fontweight="bold", pad=8)

    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    print("wrote", main())
