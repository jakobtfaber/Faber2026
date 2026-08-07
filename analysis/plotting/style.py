"""Canonical manuscript figure style."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager


def bundled_computer_modern_font_paths() -> tuple[Path, ...]:
    """Return the exact Computer Modern font files shipped by Matplotlib."""
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    return tuple(sorted(font_dir.glob("cm*.ttf")))


def _register_bundled_computer_modern_fonts() -> None:
    """Register Matplotlib's bundled fonts even when its user cache is stale."""
    for path in bundled_computer_modern_font_paths():
        font_manager.fontManager.addfont(path)


def use_manuscript_style() -> None:
    """Apply the required SciencePlots and Computer Modern manuscript style.

    SciencePlots is a required project dependency. Missing style support is an
    error because silently changing typography makes figure builds unreliable.
    """
    try:
        import scienceplots  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "SciencePlots is required for manuscript figures; install the "
            "project environment with `uv sync --project analysis --frozen`."
        ) from exc

    _register_bundled_computer_modern_fonts()
    plt.style.use(["science", "notebook"])
    plt.rcParams.update(
        {
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["cmr10"],
            "mathtext.fontset": "cm",
            "axes.formatter.use_mathtext": True,
            "axes.unicode_minus": False,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
