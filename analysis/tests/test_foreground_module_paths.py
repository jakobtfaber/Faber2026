"""The foreground package moved; live code must not import its old path.

`galaxies.foreground.*` was renamed to `foregrounds.propagation.*`. `galaxies`
survives as a namespace package holding only `host`, so an import of the old
path raises `ModuleNotFoundError` at call time rather than failing at
collection — which is how two live call sites kept the stale path.
"""

from importlib import import_module
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = "galaxies.foreground"

# Dated provenance artifacts, not live code: `.archive/` holds superseded
# trees, and `docs/rse/specs/s1-scripts/` holds one-off experiment records
# that are kept as they ran. Neither is imported by anything.
EXCLUDED = (".archive", "docs")


SELF = Path(__file__).resolve()


def live_python_sources() -> list[Path]:
    # This module names the retired path in order to search for it, so it
    # excludes itself rather than matching on its own text.
    return [
        path
        for path in sorted(ROOT.rglob("*.py"))
        if path != SELF and not any(part in EXCLUDED for part in path.relative_to(ROOT).parts)
    ]


def test_no_live_module_imports_the_retired_foreground_path() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in live_python_sources()
        if RETIRED in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_the_scan_covers_the_modules_that_carried_the_stale_imports() -> None:
    # Without this the assertion above would also pass if rglob or the
    # exclusion list stopped reaching the scintillation tree.
    scanned = {str(path.relative_to(ROOT)) for path in live_python_sources()}
    assert "scintillation/scint_analysis/pipeline.py" in scanned
    assert "scintillation/ne2025/query_ne2025_scint.py" in scanned


@pytest.mark.parametrize(
    ("module", "attribute"),
    [
        ("foregrounds.propagation.scintillation_bridge", "attach_interpretation_with_bridge"),
        ("foregrounds.propagation.sightline_budget", "galactic_dm_tau"),
    ],
)
def test_the_successor_modules_expose_what_the_call_sites_import(
    module: str, attribute: str
) -> None:
    assert hasattr(import_module(module), attribute)
