#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path

GITHUB_URL = re.compile(r"https://github\.com/[^}\s]+")
ANALYSIS_PATH = re.compile(r"\\texttt\{(analysis/[^}]+)\}")
ALLOWED_GITHUB_URL = "https://github.com/jakobtfaber/Faber2026"


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    sources = [root / "main.tex", *sorted((root / "sections").glob("*.tex"))]
    text = "\n".join(path.read_text() for path in sources if path.is_file())
    urls = GITHUB_URL.findall(text)
    if urls != [ALLOWED_GITHUB_URL]:
        errors.append(
            f"manuscript GitHub URLs must be exactly [{ALLOWED_GITHUB_URL}]; got {urls}"
        )
    for rendered in ANALYSIS_PATH.findall(text):
        relative = rendered.replace(r"\_", "_")
        if not (root / relative.rstrip("/")).exists():
            errors.append(f"manuscript analysis path does not exist: {rendered}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
