#!/usr/bin/env python3
"""Print a coverage block while preserving only explicit claim ownership."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

try:
    from scripts.render_results_registry import (
        REGISTRY,
        compiled_artifacts,
        compiled_sources,
        numeric_claims,
    )
except ModuleNotFoundError:  # direct script execution
    from render_results_registry import (
        REGISTRY,
        compiled_artifacts,
        compiled_sources,
        numeric_claims,
    )


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generate(root: Path, registry: dict) -> str:
    """Preserve reviewed assignments; make every newly found item unresolved."""
    existing_claims = {}
    for source in registry.get("prose_source", []):
        for claim in source.get("claims", []):
            key = (source["source"], claim["fingerprint"], claim["occurrence"])
            existing_claims[key] = claim
    existing_artifacts = {
        path: record["result_id"]
        for record in registry.get("artifact_coverage", [])
        for path in record.get("paths", [])
    }

    tables, figures = compiled_artifacts(root)
    lines = [
        "# Numeric claims are owned individually. New claims receive the deliberate",
        "# __SELECT_OWNER__ sentinel and fail validation until reviewed.",
    ]
    for path in compiled_sources(root):
        relative = path.relative_to(root).as_posix()
        if relative in tables:
            continue
        lines.extend(
            ["", "[[prose_source]]", f"source = {quoted(relative)}", "claims = ["]
        )
        for discovered in numeric_claims(path):
            key = (relative, discovered["fingerprint"], discovered["occurrence"])
            previous = existing_claims.get(key, {})
            fields = [
                f'fingerprint = {quoted(str(discovered["fingerprint"]))}',
                f'occurrence = {discovered["occurrence"]}',
                f'line = {discovered["line"]}',
                f'text = {quoted(str(discovered["text"]))}',
            ]
            if previous.get("exclusion_reason"):
                fields.append(
                    f'exclusion_reason = {quoted(previous["exclusion_reason"])}'
                )
            else:
                owner = previous.get("owner_result_id", "__SELECT_OWNER__")
                fields.append(f"owner_result_id = {quoted(owner)}")
            lines.append("  { " + ", ".join(fields) + " },")
        lines.append("]")

    lines.extend(
        ["", "# Every compiled table and figure has exactly one registry owner."]
    )
    for artifact in sorted(tables | figures):
        owner = existing_artifacts.get(artifact, "__SELECT_OWNER__")
        lines.extend(
            [
                "",
                "[[artifact_coverage]]",
                f"result_id = {quoted(owner)}",
                f"paths = [{quoted(artifact)}]",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manuscript_root", type=Path)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()
    registry = tomllib.loads(args.registry.read_text())
    print(generate(args.manuscript_root.resolve(), registry), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
