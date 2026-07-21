#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_gate(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def gate_failures(gate: dict) -> list[str]:
    failures: list[str] = []
    if gate.get("status") != "passed":
        failures.append(f"status={gate.get('status')!r}")
    for defect in gate.get("defects", []):
        if defect.get("status") != "passed":
            failures.append(f"defect {defect.get('id', '<missing-id>')} is {defect.get('status')!r}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed gate for the expanded foreground catalog validation."
    )
    parser.add_argument(
        "--gate",
        type=Path,
        default=Path("docs/rse/specs/validation-expanded-foreground-catalog.json"),
    )
    args = parser.parse_args(argv)

    failures = gate_failures(load_gate(args.gate))
    if failures:
        print("expanded foreground catalog gate failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
