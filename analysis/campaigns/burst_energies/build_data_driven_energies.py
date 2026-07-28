#!/usr/bin/env python3
"""Build a fit-independent, fail-closed burst-energy artifact."""

from __future__ import annotations

import argparse
from pathlib import Path

from energetics_core import build_artifact, dump_artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fluences", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    artifact = build_artifact(repo, args.fluences.resolve())
    dump_artifact(artifact, args.output)
    print(f"wrote {args.output}: {len(artifact['results'])} calculated, "
          f"{len(artifact['dispositions'])} excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
