"""Admission smoke test for the kernel-only Jupyter surface.

Defined in docs/rse/ops/jupyter-surface.md, section 10. Starts a real kernel
with the same interpreter running this test (no kernelspec), round-trips two
executions, and round-trips a notebook through jupytext py:percent.

Run via `make test-notebook`, which supplies the notebook dependency group:

    uv run --group test --group notebook --frozen \
        python -m pytest tests/test_jupyter_surface.py -q

The dependencies are required, not optional: if ipykernel, jupyter_client, or
jupytext is missing, these tests fail rather than skip — unavailability is
exactly the condition the smoke test exists to detect. The imports are guarded
only so that pytest can *collect* this module in environments without the
notebook group (where the tests are deselected as slow); when the tests
actually run, a missing dependency is an immediate failure.
"""

from __future__ import annotations

import json
import queue
import sys
from pathlib import Path

import pytest

try:
    import jupytext
    from jupyter_client.kernelspec import KernelSpecManager
    from jupyter_client.manager import KernelManager

    _IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as exc:  # collection must survive; running must not
    jupytext = None  # type: ignore[assignment]
    KernelSpecManager = KernelManager = None  # type: ignore[assignment,misc]
    _IMPORT_ERROR = exc

# Not "slow": the slow lane (make test-slow) also runs without the notebook
# group and would fail these tests rather than run its own validation.
pytestmark = pytest.mark.notebook_surface


@pytest.fixture(autouse=True)
def _notebook_dependencies_required():
    if _IMPORT_ERROR is not None:
        pytest.fail(
            "notebook dependency group unavailable "
            f"({_IMPORT_ERROR}); run via make test-notebook, which supplies "
            "--group notebook. A skip is not a pass (jupyter-surface.md §10)."
        )

STARTUP_TIMEOUT_S = 60
EXECUTE_TIMEOUT_S = 60


def _execute(kc, code: str) -> str:
    """Execute code on the kernel and return the repr of its result."""
    msg_id = kc.execute(code)
    result = None
    while True:
        try:
            msg = kc.get_iopub_msg(timeout=EXECUTE_TIMEOUT_S)
        except queue.Empty:
            pytest.fail(f"kernel produced no reply within {EXECUTE_TIMEOUT_S}s for: {code!r}")
        if msg["parent_header"].get("msg_id") != msg_id:
            continue
        msg_type = msg["header"]["msg_type"]
        if msg_type == "execute_result":
            result = msg["content"]["data"]["text/plain"]
        elif msg_type == "error":
            pytest.fail("kernel error: " + "\n".join(msg["content"]["traceback"]))
        elif msg_type == "status" and msg["content"]["execution_state"] == "idle":
            return result


def test_kernel_round_trip_uses_this_interpreter(tmp_path: Path):
    # Launch the test process's own interpreter, never a user-level kernelspec
    # (a stale one may point at another environment entirely). jupyter_client's
    # provisioner resolves kernels through kernelspecs, so build an ephemeral
    # task-local spec under tmp_path — the pattern jupyter-surface.md section 2
    # prescribes — rather than the deprecated kernel_cmd override.
    spec_dir = tmp_path / "kernels" / "surface-smoke"
    spec_dir.mkdir(parents=True)
    (spec_dir / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ],
                "display_name": "surface-smoke",
                "language": "python",
            }
        )
    )
    ksm = KernelSpecManager()
    ksm.kernel_dirs = [str(tmp_path / "kernels")]
    km = KernelManager(kernel_name="surface-smoke", kernel_spec_manager=ksm)
    km.start_kernel()
    try:
        kc = km.client()
        kc.start_channels()
        try:
            kc.wait_for_ready(timeout=STARTUP_TIMEOUT_S)
            assert _execute(kc, "1 + 1") == "2"
            kernel_exe = _execute(kc, "import sys; sys.executable")
            assert kernel_exe is not None
            assert kernel_exe.strip("'\"") == sys.executable, (
                f"kernel interpreter {kernel_exe} != test interpreter {sys.executable}"
            )
        finally:
            kc.stop_channels()
    finally:
        km.shutdown_kernel(now=True)


def test_jupytext_py_percent_round_trip(tmp_path: Path):
    notebook = jupytext.reads(
        "# %%\nx = 1 + 1\n\n# %% [markdown]\n# A markdown cell.\n",
        fmt="py:percent",
    )
    assert len(notebook.cells) == 2

    ipynb_path = tmp_path / "roundtrip.ipynb"
    jupytext.write(notebook, ipynb_path)
    py_text = jupytext.writes(jupytext.read(ipynb_path), fmt="py:percent")
    recovered = jupytext.reads(py_text, fmt="py:percent")

    assert [c.cell_type for c in recovered.cells] == [
        c.cell_type for c in notebook.cells
    ]
    assert [c.source for c in recovered.cells] == [c.source for c in notebook.cells]
