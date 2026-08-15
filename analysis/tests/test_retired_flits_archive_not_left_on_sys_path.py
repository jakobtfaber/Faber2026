"""Importing an analysis script must not leave the retired FLITS archive on sys.path.

`workflows/dualband_burst_model.py::_environment_preflight` refuses to run when any
`sys.path` entry names flits, so a module-level `sys.path.insert` that is never undone
does not just linger — it fails every dualband workflow that runs later in the same
interpreter, with a message ("FLITS runtime contamination detected") that points at the
environment rather than at the import that caused it.

Each check runs in a fresh subprocess so the result does not depend on what an earlier
test in the session already imported.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workspace import manuscript_root  # noqa: E402

# Scripts guarded against re-acquiring the retired `.archive/flits/` tree at import
# time. Add to this list when another script grows an archive import; do not drop it.
GUARDED_SCRIPTS = ["audit_fig1_residual_drift"]


def _manuscript_root_or_none() -> Path | None:
    """The analysis repository is testable standalone; the manuscript may be absent."""
    try:
        return manuscript_root()
    except RuntimeError:
        return None


MANUSCRIPT_ROOT = _manuscript_root_or_none()

# Every guarded script resolves the manuscript root at import time, so none of them can
# be imported at all where no manuscript is mounted. Skip rather than fail there: the
# absence is a supported layout, not a regression of the invariant under test.
pytestmark = pytest.mark.skipif(
    MANUSCRIPT_ROOT is None, reason="no manuscript checkout mounted"
)


def _run(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(body)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": f"{ROOT}:{ROOT / 'scripts'}",
            # The module under test resolves both of these at import time —
            # `manuscript_root()` for its ROOT, `Path.home()` for the two data-root
            # defaults. Pass the resolved values through rather than relying on the
            # clone's parent layout or on the passwd database.
            "FABER2026_ROOT": str(MANUSCRIPT_ROOT),
            **({"HOME": os.environ["HOME"]} if "HOME" in os.environ else {}),
        },
    )


@pytest.mark.parametrize("module", GUARDED_SCRIPTS)
def test_import_does_not_leave_a_flits_entry_on_sys_path(module: str) -> None:
    result = _run(
        f"""
        import sys
        import {module}  # noqa: F401
        leaked = [p for p in sys.path if "flits" in p.lower()]
        print("LEAKED:" + repr(leaked))
        """
    )

    assert result.returncode == 0, result.stderr
    assert "LEAKED:[]" in result.stdout, result.stdout


@pytest.mark.parametrize("module", GUARDED_SCRIPTS)
def test_dualband_preflight_does_not_report_contamination_after_the_import(
    module: str,
) -> None:
    """The user-visible consequence, asserted on the contamination check alone.

    `_environment_preflight` has other preconditions — a clean checkout, no editable
    installs from outside the tree — that a unit test should not have to satisfy, so
    this asserts only that the flits branch is not the one that fires.
    """
    result = _run(
        f"""
        from pathlib import Path
        import {module}  # noqa: F401
        from workflows.dualband_burst_model import _environment_preflight
        try:
            _environment_preflight(Path.cwd())
        except Exception as error:  # a later precondition, not our concern here
            print("PREFLIGHT-RAISED:" + str(error))
        else:
            print("PREFLIGHT-RAISED:")
        """
    )

    assert result.returncode == 0, result.stderr
    assert "FLITS runtime contamination detected" not in result.stdout, result.stdout
