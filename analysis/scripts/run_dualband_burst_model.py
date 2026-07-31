#!/usr/bin/env python3
"""Run one permanent dual-band burst-model workflow stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from workflows.dualband_burst_model import (
    aggregate_fit_cells,
    run_event,
    run_fit_cell,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument(
        "--stage",
        choices=("observations", "fit", "fit-cell", "aggregate", "verify", "review"),
        required=True,
    )
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--cells-root", type=Path)
    parser.add_argument("--association")
    parser.add_argument("--morphology")
    arguments = parser.parse_args()
    repository_root = Path(__file__).parents[1]
    if arguments.stage == "fit-cell":
        if not arguments.cells_root or not arguments.association or not arguments.morphology:
            parser.error("fit-cell requires --cells-root, --association, and --morphology")
        result = run_fit_cell(
            event=arguments.event,
            association_id=arguments.association,
            morphology=arguments.morphology,
            repository_root=repository_root,
            cells_root=arguments.cells_root,
        )
    elif arguments.stage == "aggregate":
        if not arguments.cells_root:
            parser.error("aggregate requires --cells-root")
        result = aggregate_fit_cells(
            event=arguments.event,
            repository_root=repository_root,
            cells_root=arguments.cells_root,
            output_root=arguments.output_root,
        )
    else:
        result = run_event(
            event=arguments.event,
            stage=arguments.stage,
            repository_root=repository_root,
            output_root=arguments.output_root,
        )
    print(result)


if __name__ == "__main__":
    main()
