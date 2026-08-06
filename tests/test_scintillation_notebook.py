"""Guards against expanded escape sequences in the scintillation walkthrough notebook.

``scripts/create_scintillation_notebook.py`` builds notebook source by
concatenating ordinary (non-raw) Python string literals, so every backslash in a
LaTeX label has to be doubled. A single backslash is silently expanded: ``$\\alpha$``
written as a non-raw ``"$\\alpha$"`` collapses to BEL followed by ``lpha``.

A label carried into generated *code* has a second expansion to survive, because
the cell source is itself Python. ``'Frequency $\\nu$ (MHz)'`` in a cell is a
non-raw literal, so at notebook run time it becomes ``Frequency $`` + newline +
``u$ (MHz)``; the sibling ``ax_fit`` labels avoid this with an ``r`` prefix.

A third class leaves no trace in the output at all: an *unrecognized* escape such
as ``\\D`` keeps its backslash and only raises ``SyntaxWarning: invalid escape
sequence``. Compiling the generator with that warning promoted to an error is the
guard for it.

Both the generator's fresh output and the committed notebook are checked. The
committed file is the *executed* artifact -- it carries cell outputs and a
kernelspec the generator does not emit -- so it is not byte-comparable to a fresh
generation, but its cell source must still be free of expanded escapes.
"""

import ast
import json
import os
import sys
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.create_scintillation_notebook import create_notebook

NOTEBOOK = Path("notebooks/scintillation_interactive_walkthrough.ipynb")

# Newline and tab are the only C0 controls that legitimately appear in cell
# source; anything else is an escape that was expanded when it should not have
# been.
ALLOWED_CONTROLS = {"\n", "\t"}


def controls(text: str, allowed: set = ALLOWED_CONTROLS) -> list:
    return [repr(character) for character in text if character < " " and character not in allowed]


class ScintillationNotebookEscapes(TestCase):
    def generated(self) -> dict:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(temporary.name)
        create_notebook()
        return json.loads((Path(temporary.name) / NOTEBOOK).read_text())

    def committed(self) -> dict:
        return json.loads((ROOT / NOTEBOOK).read_text())

    def assert_no_expanded_escapes(self, notebook: dict, label: str) -> None:
        for index, cell in enumerate(notebook["cells"]):
            found = controls("".join(cell["source"]))
            self.assertEqual(
                found, [], f"{label} cell {index} carries expanded escape sequences: {found}"
            )

    def assert_labels_survive_a_second_expansion(self, notebook: dict, label: str) -> None:
        """Every ``$...$`` label in generated code must reach matplotlib intact.

        These labels are single-line, so a newline or tab inside one is corruption
        rather than formatting -- hence the empty ``allowed`` set.
        """
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            for node in ast.walk(ast.parse("".join(cell["source"]))):
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue
                if "$" not in node.value:
                    continue
                found = controls(node.value, allowed=set())
                self.assertEqual(
                    found,
                    [],
                    f"{label} cell {index} label {node.value!r} lost characters to escape "
                    f"expansion; write it as a raw string",
                )

    def test_generated_notebook_has_no_expanded_escapes(self) -> None:
        self.assert_no_expanded_escapes(self.generated(), "generated")

    def test_generated_labels_survive_a_second_expansion(self) -> None:
        self.assert_labels_survive_a_second_expansion(self.generated(), "generated")

    def test_committed_notebook_has_no_expanded_escapes(self) -> None:
        self.assert_no_expanded_escapes(self.committed(), "committed")

    def test_committed_labels_survive_a_second_expansion(self) -> None:
        self.assert_labels_survive_a_second_expansion(self.committed(), "committed")

    def test_generator_source_has_no_invalid_escape_sequences(self) -> None:
        """An unrecognized escape survives as a literal backslash, not a control
        character, so the checks above miss it -- but Python still warns.
        """
        source = ROOT / "scripts" / "create_scintillation_notebook.py"
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            compile(source.read_text(), str(source), "exec")


if __name__ == "__main__":
    main()
