#!/usr/bin/env python3
"""Run one permanent dual-band burst-model workflow stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from workflows.dualband_burst_model import run_event


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument(
        "--stage",
        choices=("observations", "fit", "verify", "review"),
        required=True,
    )
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    result = run_event(
        event=arguments.event,
        stage=arguments.stage,
        repository_root=Path(__file__).parents[1],
        output_root=arguments.output_root,
    )
    print(result)


if __name__ == "__main__":
    main()
