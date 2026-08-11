"""`REPRODUCE.md` must not document `figure_flow` under a bare interpreter.

`figure_flow.py` loads `figures/catalog.yaml` through `_load_yaml`, which
imports PyYAML before the run does anything else. On a host whose system
interpreter lacks it — a fresh CI runner, a plain clone — a documented
`python3 scripts/figure_flow.py …` exits `ERROR MISSING_DEP` instead of
regenerating, so the recipe a reader copies out of `REPRODUCE.md` cannot
work. Every invocation there has to name the project environment.

The manuscript-side guard added in #356 for `figures/ax/SKILL.md` keys on the
literal `python3 analysis/scripts/figure_flow.py`; `REPRODUCE.md` writes
its paths relative to `analysis/`, so this assertion matches either spelling.
"""

from __future__ import annotations

import re
from pathlib import Path

REPRODUCE = Path(__file__).parents[1] / "REPRODUCE.md"

# `python3 scripts/figure_flow.py`, `python analysis/scripts/figure_flow.py`,
# and any other directory prefix in front of the same script.
INVOCATION = re.compile(r"\bpython3?\s+(?:\S*/)?figure_flow\.py")


def test_reproduce_runs_figure_flow_in_the_project_environment() -> None:
    offenders = [
        f"line {number}: {line.strip()}"
        for number, line in enumerate(REPRODUCE.read_text().splitlines(), start=1)
        if INVOCATION.search(line) and "uv run" not in line
    ]
    assert not offenders, (
        "REPRODUCE.md documents figure_flow under a bare interpreter, which exits "
        "ERROR MISSING_DEP before reading the catalog:\n" + "\n".join(offenders)
    )
