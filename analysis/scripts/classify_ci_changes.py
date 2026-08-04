#!/usr/bin/env python3

import argparse
from pathlib import PurePosixPath

REGISTRY_PATHS = {
    "RESULTS.md",
    "docs/rse/control/results-registry.toml",
    "docs/rse/control/results-registry-claim-owners.toml",
}

SCIENTIFIC_PREFIXES = (
    "analysis-configs/",
    "docs/analysis/",
    "figure_receipts/",
    "figure_review/",
    "figures/",
    "outputs/",
    "results/",
)


def is_scientific_product(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return path.startswith(SCIENTIFIC_PREFIXES) or "results" in parts


def is_quality_only(path: str) -> bool:
    if is_scientific_product(path):
        return False
    return path.endswith(".md") or path.startswith("docs/") or path in {
        ".gitignore",
        ".gitattributes",
        "LICENSE",
    }


def classify(paths: list[str]) -> str:
    if paths and all(path in REGISTRY_PATHS for path in paths):
        return "registry"
    if paths and all(is_quality_only(path) for path in paths):
        return "quality"
    return "full"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    print(classify(args.paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
