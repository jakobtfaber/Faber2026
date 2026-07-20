#!/usr/bin/env python3
"""Promote curated analysis artifacts into a fail-closed ``latest`` roster.

The YAML specification is tracked in git. Result bytes live under the external
Faber2026 results library. A changed per-item slot is moved to timestamped
history before its replacement is installed. Unchanged promotions are no-ops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LIBRARY = Path.home() / "Data" / "Faber2026" / "results-library"
SCHEMA = "faber2026-latest-analysis/v1"
PRESENT = "artifact-present"
MISSING = "not-yet-promoted"


class PromotionError(RuntimeError):
    """Raised before publication when a promotion invariant is violated."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def _archive_stamp(as_of: str) -> str:
    try:
        parsed = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PromotionError(f"invalid --as-of timestamp: {as_of}") from exc
    return parsed.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_spec(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise PromotionError(f"spec must use schema {SCHEMA}")
    for key in ("analysis", "domain", "expected_bursts", "source_commit", "bursts"):
        if key not in raw:
            raise PromotionError(f"spec missing {key!r}")
    bursts = raw["bursts"]
    if not isinstance(bursts, list) or len(bursts) != int(raw["expected_bursts"]):
        raise PromotionError("burst count does not match expected_bursts")
    seen: set[str] = set()
    for index, entry in enumerate(bursts):
        if not isinstance(entry, dict):
            raise PromotionError(f"bursts[{index}] must be a mapping")
        for key in (
            "nick",
            "tns",
            "promotion_status",
            "fit_quality_status",
            "figure_review_status",
            "adoption_status",
        ):
            if key not in entry:
                raise PromotionError(f"bursts[{index}] missing {key!r}")
        nick = str(entry["nick"])
        if nick in seen:
            raise PromotionError(f"duplicate burst: {nick}")
        seen.add(nick)
        status = entry["promotion_status"]
        if status not in (PRESENT, MISSING):
            raise PromotionError(f"{nick}: unknown promotion_status {status!r}")
        artifacts = entry.get("artifacts")
        if status == PRESENT:
            if not isinstance(artifacts, dict) or set(artifacts) != {
                "fit_json",
                "jointmodel_npz",
            }:
                raise PromotionError(
                    f"{nick}: artifact-present requires fit_json and jointmodel_npz"
                )
        elif artifacts:
            raise PromotionError(f"{nick}: not-yet-promoted cannot name artifacts")
    return raw


def _prepare_records(spec: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for source_entry in spec["bursts"]:
        entry = dict(source_entry)
        artifacts_spec = entry.pop("artifacts", None)
        record: dict[str, Any] = {
            "schema": SCHEMA,
            "analysis": spec["analysis"],
            "domain": spec["domain"],
            "source_commit": spec["source_commit"],
            **entry,
        }
        copies: list[dict[str, Any]] = []
        artifact_records: dict[str, Any] = {}
        if entry["promotion_status"] == PRESENT:
            destinations = {"fit_json": "fit.json", "jointmodel_npz": "jointmodel.npz"}
            for kind, destination in destinations.items():
                relative = Path(str(artifacts_spec[kind]))
                source = root / relative
                if not source.is_file():
                    raise PromotionError(f"{entry['nick']}: missing source {relative}")
                if kind == "fit_json":
                    try:
                        json.loads(source.read_text())
                    except (OSError, json.JSONDecodeError) as exc:
                        raise PromotionError(
                            f"{entry['nick']}: invalid fit JSON {relative}"
                        ) from exc
                digest = _sha256(source)
                copies.append({"source": source, "destination": destination})
                artifact_records[kind] = {
                    "source_path": relative.as_posix(),
                    "latest_name": destination,
                    "sha256": digest,
                    "bytes": source.stat().st_size,
                }
        record["artifacts"] = artifact_records
        record["content_fingerprint"] = hashlib.sha256(_json_bytes(record)).hexdigest()
        prepared.append({"record": record, "copies": copies})
    return prepared


def _status_markdown(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['tns']} ({record['nick']})",
        "",
        f"- Promotion: `{record['promotion_status']}`",
        f"- Fit quality: `{record['fit_quality_status']}`",
        f"- Figure review: `{record['figure_review_status']}`",
        f"- Adoption: `{record['adoption_status']}`",
    ]
    if record.get("components"):
        lines.append(f"- Components: `{record['components']}`")
    if record.get("reason"):
        lines.append(f"- Reason: {record['reason']}")
    lines.extend(
        [
            "",
            "> `latest` records recency only. It does not imply PASS or manuscript acceptance.",
            "",
        ]
    )
    return "\n".join(lines)


def _root_readme(spec: dict[str, Any]) -> str:
    return f"""# Latest {spec["analysis"]} artifacts

This directory is the current promoted roster for `{spec["domain"]}/{spec["analysis"]}`.
Every expected burst has a directory, including bursts with no promoted fit.

`latest` means **newest promoted artifact**, not scientific acceptance. Read each
burst's `record.json` or `STATUS.md` for fit-quality, figure-review, and owner-
adoption state. A numeric result is not a PASS unless the authoritative fit-
quality contract and full diagnostic-figure review gate are both satisfied.

When a burst is replaced, its complete prior slot moves to `../historical/<UTC>/`.
Raw posterior samples, experiment ladders, and unpromoted diagnostics stay outside
this directory.
"""


def promote(
    spec_path: Path,
    root: Path,
    library: Path,
    *,
    as_of: str,
) -> dict[str, int]:
    """Publish one specification after validating every source and collision."""

    spec_path = spec_path.resolve()
    root = root.resolve()
    library = library.expanduser().resolve()
    spec = _load_spec(spec_path)
    prepared = _prepare_records(spec, root)
    analysis_root = library / str(spec["domain"]) / str(spec["analysis"])
    latest = analysis_root / "latest"
    history = analysis_root / "historical"
    stamp = _archive_stamp(as_of)

    actions: list[tuple[dict[str, Any], Path, bool, Path | None]] = []
    for item in prepared:
        record = item["record"]
        current = latest / record["nick"]
        unchanged = False
        if current.is_dir():
            try:
                existing = json.loads((current / "record.json").read_text())
                unchanged = (
                    existing.get("content_fingerprint") == record["content_fingerprint"]
                )
            except (FileNotFoundError, json.JSONDecodeError):
                unchanged = False
        archive = (
            None
            if unchanged or not current.exists()
            else history / stamp / record["nick"]
        )
        if archive is not None and archive.exists():
            raise PromotionError(f"archive collision: {archive}")
        actions.append((item, current, unchanged, archive))

    latest.mkdir(parents=True, exist_ok=True)
    installed = unchanged_count = archived = 0
    final_records: list[dict[str, Any]] = []
    for item, current, unchanged, archive in actions:
        if unchanged:
            unchanged_count += 1
            final_records.append(json.loads((current / "record.json").read_text()))
            continue
        record = {**item["record"], "promoted_at": as_of}
        stage = latest / f".staging-{record['nick']}-{uuid.uuid4().hex}"
        stage.mkdir()
        try:
            for copy in item["copies"]:
                shutil.copy2(copy["source"], stage / copy["destination"])
            _write_json(stage / "record.json", record)
            (stage / "STATUS.md").write_text(_status_markdown(record))
            if archive is not None:
                archive.parent.mkdir(parents=True, exist_ok=True)
                os.replace(current, archive)
                archived += 1
            os.replace(stage, current)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
        installed += 1
        final_records.append(record)

    summary = {
        "artifact_present": sum(
            r["promotion_status"] == PRESENT for r in final_records
        ),
        "not_yet_promoted": sum(
            r["promotion_status"] == MISSING for r in final_records
        ),
    }
    manifest = {
        "schema": SCHEMA,
        "analysis": spec["analysis"],
        "domain": spec["domain"],
        "generated_at": as_of,
        "source_commit": spec["source_commit"],
        "spec_path": spec_path.relative_to(root).as_posix(),
        "policy": spec.get("policy", {}),
        "summary": summary,
        "bursts": final_records,
    }
    _write_json(latest / "manifest.json", manifest)
    (latest / "README.md").write_text(_root_readme(spec))
    return {"installed": installed, "unchanged": unchanged_count, "archived": archived}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument(
        "--as-of",
        default=datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        help="UTC ISO-8601 promotion timestamp",
    )
    args = parser.parse_args()
    result = promote(args.spec, args.root, args.library, as_of=args.as_of)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
