"""Generate the GitHub social-preview card (1280x640). Reproducible: python3 make_social_preview.py"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

W, H = 12.8, 6.4
fig = plt.figure(figsize=(W, H), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
ax.add_patch(plt.Rectangle((0, 0), W, H, color="#0d1117"))
SANS, MONO = "Liberation Sans", "Liberation Mono"
ax.text(0.75, 5.55, "topocheck", fontsize=34, fontweight="bold", color="#e6edf3", family=SANS)
ax.text(0.75, 4.92, "Sanity checks for topology-aware segmentation claims.", fontsize=17, color="#8b949e", family=SANS)
ax.add_patch(FancyBboxPatch((0.72, 1.28), 11.36, 3.05, boxstyle="round,pad=0.12", fc="#161b22", ec="#30363d", lw=1.5))
ax.text(0.95, 4.02, "$ python examples/quickstart.py", fontsize=13.5, color="#7d8590", family=MONO)
rows = [
    ("[1] how much of the error is repairable at all", "#e6edf3"),
    ("    break 0.286 = missing 0.143 + fragmented 0.143  -> at most 50% repairable", "#58a6ff"),
    ("[2] does the proposed repair beat a random one of the same size", "#e6edf3"),
    ("    break 0.286 -> 0.286   random of equal size: 0.143   beats random: False", "#f85149"),
]
y = 3.55
for txt, c in rows:
    ax.text(0.95, y, txt, fontsize=14, color=c, family=MONO); y -= 0.5
ax.text(0.95, y - 0.02, "random-repair baseline | repairable-error ceiling | tolerance sensitivity | inter-annotator floor",
        fontsize=12, color="#7d8590", family=MONO)
ax.text(0.75, 0.62, "On TopCoW a random fragment assignment cut the break rate by 25.9% - ahead of every learned repair we built.",
        fontsize=12.5, color="#8b949e", family=SANS)
fig.savefig(pathlib.Path(__file__).parent / "social-preview.png"); print("written social-preview.png 1280x640")
