"""Resolve the Faber2026 / FLITS results library root.

Results (fit JSON, PPC, catalogs, figures, review ledgers) are inventoried
under ``~/Data/Faber2026/results-library`` (override with
``FABER2026_RESULTS_LIBRARY``). Fitting *code* stays in the git checkouts.

See ``$FABER2026_RESULTS_LIBRARY/INDEX.md`` and
``_inventory/inventory.yaml``.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_LIBRARY = Path.home() / "Data" / "Faber2026" / "results-library"


def results_library_root() -> Path:
    return Path(
        os.environ.get("FABER2026_RESULTS_LIBRARY", str(DEFAULT_LIBRARY))
    ).expanduser().resolve()


def results_slot(*parts: str) -> Path:
    """Path into the library taxonomy, e.g. ``results_slot('scattering', '2026-07-14_dm-locked')``."""
    return results_library_root().joinpath(*parts)


def require_results_library() -> Path:
    root = results_library_root()
    if not root.is_dir():
        raise FileNotFoundError(
            f"results library missing: {root}. "
            "Run scripts/build_results_library_inventory.py --link "
            "or set FABER2026_RESULTS_LIBRARY."
        )
    return root
