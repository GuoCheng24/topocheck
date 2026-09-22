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
    ("connect all to largest", 27.4, False),
    ("random assignment", 25.9, True),
    ("learned selector", 20.6, False),
    ("cheapest partner", 16.5, False),
    ("shuffled control", 0.0, False),
]


def chart(ax, accent):
    """All five strategies from docs/EVIDENCE.md.

    Two were shown first, because five at 22 pt are five grey smudges at the width a Slack
    unfurl gives a card. The fix was the type size, not the row count: the ladder - a
    shuffled control at zero, then two rules, then the learned selector, and a random
    assignment above all of them - is the finding, and three of its rungs were missing.
    """
    x0, span, top, step = 5.45, 3.35, 3.44, 0.62
    for i, (name, value, hero) in enumerate(STRATEGIES):
        y = top - i * step
        ax.barh(y, max(span * value / 27.4, 0.035), height=0.38, left=x0,
                color=accent if hero else "#c7c3bc", zorder=3)
        ax.text(x0 - 0.24, y, name, fontsize=34,
                fontweight="bold" if hero else "normal",
                color="#17181a" if hero else "#55585c",
                family=SANS, ha="right", va="center")
        ax.text(x0 + span * value / 27.4 + 0.20, y, f"{value:.1f}%",
                fontsize=34, fontweight="bold" if hero else "normal",
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
