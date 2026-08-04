#!/usr/bin/env python3

import argparse
import sys
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manuscript_root", type=Path)
    args = parser.parse_args()
    root = args.manuscript_root.resolve()
    analysis_root = root / "analysis"
    sys.path.insert(0, str(analysis_root))

    from scripts.generate_results_coverage import generate

    registry_path = analysis_root / "docs/rse/control/results-registry.toml"
    registry = tomllib.loads(registry_path.read_text())
    discovered = tomllib.loads(generate(root, registry))
    for key in ("prose_source", "artifact_coverage"):
        if discovered.get(key, []) != registry.get(key, []):
            print(f"{key} differs from the reviewed registry", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
