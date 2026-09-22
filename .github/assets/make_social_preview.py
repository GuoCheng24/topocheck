"""Generate the GitHub social-preview card (1200x630). Reproducible: python3 make_social_preview.py

The previous card put its message in a block of 14 pt monospace. A social card is unfurled at about
360 px wide in Slack, where that is grey noise, so the message is in the headline now and the
terminal panel is texture beside it. Layout shared across this account via bin/lightcard.py.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from lightcard import draw  # noqa: E402

out = draw(
    out=str(pathlib.Path(__file__).parent / "social-preview.png"),
    accent="#1f6feb", badge="T", headline_size=40,
    kicker="PYTHON PACKAGE  ·  pip install topocheck",
    headline="A random repair beat every learned one",
    subline="so the harness says what is repairable",
    body=["On TopCoW a random fragment", "assignment cut the break rate by", "25.9 percent, ahead of every learned", "repair we built."],
    panel=[("$ python examples/quickstart.py", "dim"),
           ("[1] how much of the error is repairable", "ink"),
           ("    at most 50% of the breaks", "warn"),
           ("[2] does the repair beat a random one", "ink"),
           ("    beats random: False", "red")],
    footer="github.com/GuoCheng24/topocheck",
)
print(f"written {pathlib.Path(out).name} 1200x630")
