"""Guard that analysis modules win over stale duplicates in the manuscript repo.

The manuscript repository still carries its own pre-migration copies of several
analysis scripts, including ``scripts/plot_codetection_gallery.py``, which
imports the retired ``flits`` package. ``plot_codetection_triptych`` used to
prepend ``manuscript_root() / "scripts"`` to ``sys.path``, so a bare
``import plot_codetection_gallery`` resolved to that stale manuscript copy and
died with ``ModuleNotFoundError: No module named 'flits.resources'``, taking the
whole triptych test module down at collection time.

The producer now prepends ``ANALYSIS_ROOT / "scripts"`` instead. These checks
fail loudly if that regresses, rather than surfacing as an unrelated missing
dependency somewhere downstream.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT / "scripts"))

from workspace import manuscript_root  # noqa: E402


def _manuscript_root_or_none():
    """The analysis repository is testable standalone; the manuscript may be absent."""
    try:
        return manuscript_root()
    except RuntimeError:
        return None

# Modules the triptych producer imports by bare name, each of which also exists
# as a stale copy under the manuscript repository's own scripts/ directory.
SHARED_MODULE_NAMES = ("plot_codetection_gallery", "plot_codetection_triptych")


def _sys_path_inserts(source: str) -> list[str]:
    return [
        line.strip()
        for line in source.splitlines()
        if "sys.path.insert" in line and not line.strip().startswith("#")
    ]


def test_triptych_producer_prepends_analysis_scripts_not_manuscript_scripts() -> None:
    """The producer must not put the manuscript's scripts/ ahead of its own."""
    source = (ANALYSIS_ROOT / "scripts/plot_codetection_triptych.py").read_text()
    inserts = _sys_path_inserts(source)
    assert inserts, "expected the producer to manage sys.path explicitly"
    for line in inserts:
        assert "ANALYSIS_ROOT" in line, line
        # Word-boundary match: bare ROOT is manuscript_root(); ANALYSIS_ROOT is not.
        assert "manuscript_root" not in line, line
        assert not re.search(r"(?<![A-Z_])ROOT\b", line), line


@pytest.mark.parametrize("name", SHARED_MODULE_NAMES)
def test_shared_module_names_resolve_inside_analysis(name: str) -> None:
    """Resolution must land in analysis/scripts, never in the manuscript copy."""
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.origin, f"{name} did not resolve at all"
    origin = Path(spec.origin).resolve()
    assert origin.is_relative_to(ANALYSIS_ROOT / "scripts"), origin


def test_manuscript_duplicate_would_have_been_the_wrong_target() -> None:
    """Document the hazard while it exists; skip once the duplicate is retired.

    Retiring the manuscript-side copies is a separate owner-approved step. Until
    then this records that a real, importable, broken alternative is sitting on
    disk, so the guard above is protecting against something live.
    """
    root = _manuscript_root_or_none()
    if root is None:
        pytest.skip("no manuscript checkout mounted")
    duplicate = root / "scripts/plot_codetection_gallery.py"
    if not duplicate.is_file():
        pytest.skip("manuscript-side duplicate has been retired")
    assert "from flits" in duplicate.read_text(), (
        "the manuscript duplicate no longer imports the retired package; "
        "re-check whether this guard is still needed"
    )


def test_triptych_test_module_imports_in_a_clean_interpreter() -> None:
    """End-to-end: a fresh interpreter must import the module without help.

    Runs out-of-process so it cannot pass by accident on sys.modules state that
    an earlier test in this session already populated. The producer resolves the
    manuscript root at import time, so this can only run where one is mounted.
    """
    root = _manuscript_root_or_none()
    if root is None:
        pytest.skip("no manuscript checkout mounted")
    result = subprocess.run(
        [sys.executable, "-c", "import plot_codetection_triptych"],
        cwd=ANALYSIS_ROOT,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(ANALYSIS_ROOT / "scripts"),
            # manuscript_root() is required at import time; pass the resolved
            # value through rather than relying on the clone's parent layout.
            "FABER2026_ROOT": str(root),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "flits" not in result.stderr
