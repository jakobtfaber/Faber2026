"""The walkthrough notebook's cell 1 must reach the scintillation package.

``scintillation.scint_analysis`` lives at ``analysis/scintillation/``. Cell 1
used to put only the manuscript repository root on ``sys.path``, and the
2026-08 monorepo consolidation left no ``scintillation`` package there, so
every import in the cell raised ``ModuleNotFoundError`` before the notebook
did any work. It also read the root off ``Path.cwd()``, which under Jupyter is
wherever the notebook was opened from -- ``notebooks/`` for anyone who opens
this file directly -- so the guard exercises both working directories.

The path block is executed rather than pattern-matched, so this tracks what
the cell actually resolves instead of how it happens to spell it. Cell 1 also
imports numpy, matplotlib and the scintillation package itself; those are
stripped before the exec, because the manuscript suite runs under the bare
interpreter, which has none of them.
"""

import ast
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.create_scintillation_notebook import create_notebook

NOTEBOOK = Path("notebooks/scintillation_interactive_walkthrough.ipynb")

# Top-level packages cell 1 imports that the bare interpreter cannot supply.
# `scintillation` is the very thing the path block exists to make importable,
# so it goes too -- resolving it is what the assertion below checks for.
UNAVAILABLE = {"numpy", "matplotlib", "scintillation"}


def _is_unavailable_import(node: ast.stmt) -> bool:
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] in UNAVAILABLE for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return (node.module or "").split(".")[0] in UNAVAILABLE
    return False


def path_block(source: str) -> str:
    """Cell source reduced to the statements that resolve `sys.path`.

    Everything from the first `scintillation` import onward is dropped -- that
    import is the cell's payload, not part of resolving the path to it. The
    `try: import ipywidgets` block survives: it already guards itself with
    `except ImportError`, so it is harmless under the bare interpreter.
    """
    body = ast.parse(source).body
    payload = [
        index
        for index, node in enumerate(body)
        if isinstance(node, ast.ImportFrom)
        and (node.module or "").split(".")[0] == "scintillation"
    ]
    head = body[: payload[0]] if payload else body
    kept = [node for node in head if not _is_unavailable_import(node)]
    return ast.unparse(ast.Module(body=kept, type_ignores=[]))


def added_paths(source: str, cwd: Path) -> list:
    """Run cell 1's path block from `cwd`; return what it put on `sys.path`."""
    before = list(sys.path)
    origin = Path.cwd()
    try:
        os.chdir(cwd)
        # Running the cell is the point here; the source is this repository's
        # own committed notebook, not external input.
        exec(  # noqa: S102
            compile(path_block(source), "<cell-1>", "exec"), {"__name__": "__main__"}
        )
        return [entry for entry in sys.path if entry not in before]
    finally:
        os.chdir(origin)
        sys.path[:] = before


class NotebookImportPath(TestCase):
    def generated(self) -> dict:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(temporary.name)
        create_notebook()
        return json.loads((Path(temporary.name) / NOTEBOOK).read_text())

    def committed(self) -> dict:
        return json.loads((ROOT / NOTEBOOK).read_text())

    def first_code_cell(self, notebook: dict) -> str:
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                return "".join(cell["source"])
        self.fail("the notebook has no code cell")

    def assert_reaches_the_package(self, notebook: dict, label: str) -> None:
        source = self.first_code_cell(notebook)
        for cwd in (ROOT, ROOT / "notebooks"):
            added = added_paths(source, cwd)
            self.assertTrue(
                any((Path(entry) / "scintillation").is_dir() for entry in added),
                f"{label} cell 1, run from {cwd}, put {added} on sys.path; none "
                f"of those holds the scintillation package, so every import in "
                f"the cell raises ModuleNotFoundError",
            )

    def test_generated_cell_reaches_the_package(self) -> None:
        self.assert_reaches_the_package(self.generated(), "generated")

    def test_committed_cell_reaches_the_package(self) -> None:
        self.assert_reaches_the_package(self.committed(), "committed")

    def test_the_guard_would_notice_an_unresolvable_path(self) -> None:
        """Without this, a path block that adds nothing would pass vacuously."""
        stub = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "import sys\n",
                        "from pathlib import Path\n",
                        "sys.path.insert(0, str(Path.cwd().resolve()))\n",
                    ],
                }
            ]
        }
        with self.assertRaises(AssertionError):
            self.assert_reaches_the_package(stub, "stub")


if __name__ == "__main__":
    main()
