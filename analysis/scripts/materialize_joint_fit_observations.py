#!/usr/bin/env python3
"""Materialize one reviewed native-order fitting grid."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    repo_root = str(Path(__file__).resolve().parents[1])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from radio_pipeline.fitting import materialize_fit_resolution

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-observation", type=Path, required=True)
    parser.add_argument("--frequency-bin-factor", type=int, required=True)
    parser.add_argument("--time-bin-factor", type=int, required=True)
    parser.add_argument("--minimum-valid-fraction", type=float, required=True)
    parser.add_argument(
        "--frequency-contiguity-tolerance-mhz",
        type=float,
        default=1.0e-9,
    )
    parser.add_argument("--output-observation", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.output_receipt.suffix.lower() != ".json":
        raise ValueError("fit-resolution receipt must use the .json extension")
    receipt = materialize_fit_resolution(
        args.source_observation,
        args.output_observation,
        frequency_bin_factor=args.frequency_bin_factor,
        time_bin_factor=args.time_bin_factor,
        minimum_valid_fraction=args.minimum_valid_fraction,
        frequency_contiguity_tolerance_mhz=args.frequency_contiguity_tolerance_mhz,
    )
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_receipt.write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    )
    print(json.dumps({"status": receipt["status"], "instrument": receipt["instrument"]}))


if __name__ == "__main__":
    main()
