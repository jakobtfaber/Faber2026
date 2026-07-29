"""CLI: build foreground data artifacts (registry, tau catalog, attribution matrix)."""

from __future__ import annotations

import argparse
from pathlib import Path

from foregrounds.propagation.attribution_matrix import write_attribution_matrix
from foregrounds.census.census_registry import write_intervening_census_registry
from foregrounds.propagation.tau_consistency import write_tau_consistency_catalog


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build foregrounds/census/data artifacts.")
    ap.add_argument(
        "--scratch-dir",
        type=Path,
        default=None,
        help="Path to scratch/codetection (default: analysis/scratch/codetection)",
    )
    ap.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Output directory (default: foregrounds/census/data)",
    )
    args = ap.parse_args(argv)

    data_dir = args.data_dir
    registry_path = write_intervening_census_registry(
        path=(data_dir / "intervening_census_registry.csv") if data_dir else None,
        scratch_dir=args.scratch_dir,
    )
    tau_path = write_tau_consistency_catalog(
        path=(data_dir / "tau_consistency_catalog.csv") if data_dir else None,
    )
    matrix_path = write_attribution_matrix(
        path=(data_dir / "sightline_attribution_matrix.csv") if data_dir else None,
    )
    print(f"Wrote {registry_path}")
    print(f"Wrote {tau_path}")
    print(f"Wrote {matrix_path}")


if __name__ == "__main__":
    main()
