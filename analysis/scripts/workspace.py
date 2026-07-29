"""Resolve the analysis repository and its mounted manuscript repository."""

from __future__ import annotations

import os
from pathlib import Path

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]


def manuscript_root() -> Path:
    """Return the Faber2026 manuscript root or fail with an actionable error."""
    configured = os.environ.get("FABER2026_ROOT")
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(ANALYSIS_ROOT.parent)
    for candidate in candidates:
        resolved = candidate.resolve()
        if (
            (resolved / "main.tex").is_file()
            and (ANALYSIS_ROOT / "figures" / "catalog.yaml").is_file()
        ):
            return resolved
    raise RuntimeError(
        "Faber2026 manuscript checkout not found; mount this repository as "
        "Faber2026/analysis or set FABER2026_ROOT=/path/to/Faber2026"
    )
