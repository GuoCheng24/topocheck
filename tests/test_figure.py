"""The README figure has to be readable at the width GitHub renders it.

Font size on the page follows  px = pt * displayed_width / (fig_width_in * 72),
which is independent of dpi: raising dpi does not make text readable, only a
wider figure or a larger point size does.  Upscaling a small render is equally
useless.  These bounds are pinned so a future edit cannot quietly break them.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "docs" / "hero.png"
SCRIPT = ROOT / "examples" / "make_hero_figure.py"
GITHUB_README_WIDTH_PX = 880          # what GitHub renders a full-width image at


def test_figure_exists_and_is_referenced():
    assert FIG.is_file(), "docs/hero.png is missing"
    assert "docs/hero.png" in (ROOT / "README.md").read_text()


def test_figure_is_not_upscaled_or_oversized():
    Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")
    w, _ = Image.open(FIG).size
    ratio = GITHUB_README_WIDTH_PX / w
    assert 0.40 <= ratio <= 1.00, (
        f"displayed/native = {ratio:.2f}; below 0.40 the text is downsampled away, "
        f"above 1.00 the image is upscaled"
    )


def test_font_size_survives_the_render_width():
    src = SCRIPT.read_text()
    fig_w = float(re.search(r"figsize=\(([\d.]+)", src).group(1))
    pt = float(re.search(r'"font\.size": ([\d.]+)', src).group(1))
    px = pt * GITHUB_README_WIDTH_PX / (fig_w * 72)
    assert px >= 9.0, f"body text renders at {px:.1f} px on the README; keep it >= 9"


def test_figure_script_is_self_contained():
    src = SCRIPT.read_text()
    assert "matplotlib.use(\"Agg\")" in src, "must render headless"
    for token in ("/public/", "chengguo", "results/"):
        assert token not in src, f"figure script must not reference private paths ({token})"
