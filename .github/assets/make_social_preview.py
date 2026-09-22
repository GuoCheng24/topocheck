"""Generate the GitHub social-preview card (1200x630). Reproducible: python3 make_social_preview.py

The evidence on this card is the strategy table from docs/EVIDENCE.md, which is the finding:
a random assignment reduces the break rate more than the learned selector does.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cardkit import SANS, card  # noqa: E402

# docs/EVIDENCE.md, TopCoW, 50 held-out volumes, strict endpoint criterion
STRATEGIES = [
    ("random assignment", 25.9, True),
    ("learned selector", 20.6, False),
]


def chart(ax, accent):
    """Two bars, because at 360 px five of them are five grey smudges.

    The finding is one comparison: the random assignment reduces the break rate more than
    the learned selector does. The other three strategies are in docs/EVIDENCE.md.
    """
    x0, span, top, step = 5.55, 3.35, 2.95, 1.32
    for i, (name, value, hero) in enumerate(STRATEGIES):
        y = top - i * step
        ax.barh(y, span * value / 27.4, height=0.66, left=x0,
                color=accent if hero else "#c7c3bc", zorder=3)
        ax.text(x0 - 0.22, y, name, fontsize=34,
                fontweight="bold" if hero else "normal",
                color="#17181a" if hero else "#55585c",
                family=SANS, ha="right", va="center")
        ax.text(x0 + span * value / 27.4 + 0.18, y, f"{value:.1f}%",
                fontsize=40, fontweight="bold",
                color="#17181a" if hero else "#55585c", family=SANS, va="center")


out = card(
    out=str(pathlib.Path(__file__).parent / "social-preview.png"),
    accent="#1f6feb", badge="T",
    kicker="PYTHON PACKAGE  ·  pip install topocheck",
    headline="Random repair beat every learned one",
    evidence="break rate reduction, TopCoW, 50 held-out volumes",
    chart=chart,
    footer="github.com/GuoCheng24/topocheck",
    headline_size=41,
)
print(f"written {pathlib.Path(out).name} 1200x630")
