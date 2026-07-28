#!/usr/bin/env python3
"""Compatibility entry point for the analysis-owned DM residual model.

The implementation and generated CSV live in ``analysis/scripts``. Keeping this
thin entry point preserves older commands without maintaining a second physics
implementation.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_SCRIPTS = ROOT / "analysis" / "scripts"
sys.path.insert(0, str(ANALYSIS_SCRIPTS))
_namespace = runpy.run_path(str(ANALYSIS_SCRIPTS / "dm_budget_uncertainty.py"))
globals().update(
    {
        name: value
        for name, value in _namespace.items()
        if not name.startswith("__")
    }
)

if __name__ == "__main__":
    raise SystemExit(main())
