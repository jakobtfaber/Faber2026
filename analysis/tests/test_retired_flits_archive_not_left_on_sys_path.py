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

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Scripts that import from `.archive/flits/`. Add to this list rather than dropping the
# guard if another one needs the archive.
ARCHIVE_IMPORTING_SCRIPTS = ["audit_fig1_residual_drift"]


def _run(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(body)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": f"{ROOT}:{ROOT / 'scripts'}", "PATH": "/usr/bin:/bin"},
    )


@pytest.mark.parametrize("module", ARCHIVE_IMPORTING_SCRIPTS)
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


@pytest.mark.parametrize("module", ARCHIVE_IMPORTING_SCRIPTS)
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
