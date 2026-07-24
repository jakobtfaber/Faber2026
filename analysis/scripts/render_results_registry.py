#!/usr/bin/env python3
"""Render the deterministic human view of the canonical results registry."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/rse/control/results-registry.toml"
CLAIM_OWNERS = ROOT / "docs/rse/control/results-registry-claim-owners.toml"
OUTPUT = ROOT / "RESULTS.md"
EXPECTED_SCHEMA_VERSION = 6
EXPECTED_REGISTRY_FIELDS: dict[str, type] = {
    "schema_version": int,
    "updated": str,
    "prose_source": list,
    "artifact_coverage": list,
    "input_exception": list,
    "result": list,
}
EXPECTED_CLAIM_OWNER_SCHEMA_VERSION = 1
EXPECTED_CLAIM_OWNER_FIELDS = {"schema_version", "source"}
EXPECTED_CLAIM_OWNER_SOURCE_FIELDS = {"path", "claims"}
CLAIM_OWNER_BASE_FIELDS = {"fingerprint", "occurrence"}
EXPECTED_PROSE_SOURCE_FIELDS = {"source", "claims"}
PROSE_CLAIM_BASE_FIELDS = {"fingerprint", "occurrence", "line", "text"}
EXPECTED_ARTIFACT_COVERAGE_FIELDS = {"result_id", "paths"}
EXPECTED_INPUT_EXCEPTION_FIELDS = {"name", "class", "path", "status", "reason"}
CANONICAL_INPUT_EXCEPTION_NAMES = (
    "remediation.casey",
    "remediation.chromatica",
    "remediation.freya",
    "remediation.hamilton",
    "remediation.isha",
    "remediation.johndoeII",
    "remediation.mahi",
    "remediation.oran",
    "remediation.phineas",
    "remediation.whitney",
    "remediation.wilhelm",
    "remediation.zach",
    "freya-package.coarse-rank1-v1",
    "freya-package.coarse-rank2-v1",
    "freya-package.rank1-v1",
)
ASSOCIATION_CARD_ARTIFACTS = {
    f"figures/association_cards/association_card_{name}.pdf"
    for name in (
        "casey",
        "chromatica",
        "freya",
        "hamilton",
        "isha",
        "johndoeii",
        "mahi",
        "oran",
        "phineas",
        "whitney",
        "wilhelm",
        "zach",
    )
}
ALLOWED_TRUST = {"trusted", "pending", "revoked"}
ALLOWED_PROVENANCE = {"complete", "pending"}
UNRESOLVED_PIN_WORDS = re.compile(
    r"\b(?:infer(?:red)?|unconfirmed|verify|unverified|not verified|placeholder|unknown|pending)\b|confirm (?:receipt|pin)",
    re.IGNORECASE,
)
EXACT_PIN = re.compile(r"^([0-9a-f]{40})$", re.IGNORECASE)
PLACEHOLDER = re.compile(
    r"(?:^|[^A-Za-z])(?:TBD|TODO|N/A)(?:$|[^A-Za-z])", re.IGNORECASE
)
NUMBER = re.compile(r"(?<![A-Za-z])[-+~]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
TEX_DEPENDENCY = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
GRAPHIC = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")
TABLE_ENVIRONMENT = re.compile(
    r"^(?:\\startlongtable\s*)?\\begin\{(?:deluxe)?table\*?\}"
)
REQUIRED_FIELDS: dict[str, type] = {
    "id": str,
    "library_slots": list,
    "section": str,
    "kind": str,
    "description": str,
    "value": str,
    "units": str,
    "producing_script": str,
    "pipeline_pin": str,
    "inputs": list,
    "external_sources": list,
    "artifact": str,
    "consumed_by": list,
    "trust": str,
    "provenance_state": str,
    "provenance_gaps": list,
    "cleared_by": str,
    "current": bool,
    "notes": str,
    "provenance_refs": list,
}
LIST_FIELDS = {
    "library_slots",
    "inputs",
    "external_sources",
    "consumed_by",
    "provenance_gaps",
}
CANONICAL_RESULT_IDS = (
    "association.sample_roster",
    "association.sample_table",
    "association.pcc_sum",
    "association.cards_figures",
    "association.dm_measurements_table",
    "association.toa_offset_figure",
    "sample.gallery_fig1",
    "mw.foreground_characterization",
    "mw.disk_halo_values",
    "census.foreground_table",
    "census.counts",
    "census.halo_grid_figure",
    "census.clusters_icm_figure",
    "budget.budget_table",
    "budget.dm_int_nonzero",
    "budget.cluster_column",
    "budget.host_dm_posteriors",
    "scattering.beta_table",
    "scattering.jointmodel_figures",
    "scattering.multiplicity_demo",
    "scint.dsa_acf_figures",
    "scint.chime_gate_table",
    "scint.twoscreen_table",
    "energies.burst_energies_table",
    "attribution.frb20230913a_intervening",
    "scint.two_band_campaign",
    "l0.casey.chime_full",
    "l0.casey.dsa",
    "l0.casey.chime_upchan",
    "l0.chromatica.chime_full",
    "l0.chromatica.dsa",
    "l0.chromatica.chime_upchan",
    "l0.freya.chime_full",
    "l0.freya.dsa",
    "l0.freya.chime_upchan",
    "l0.hamilton.chime_full",
    "l0.hamilton.dsa",
    "l0.hamilton.chime_upchan",
    "l0.isha.chime_full",
    "l0.isha.dsa",
    "l0.isha.chime_upchan",
    "l0.johndoeII.chime_full",
    "l0.johndoeII.dsa",
    "l0.johndoeII.chime_upchan",
    "l0.mahi.chime_full",
    "l0.mahi.dsa",
    "l0.mahi.chime_upchan",
    "l0.oran.chime_full",
    "l0.oran.dsa",
    "l0.oran.chime_upchan",
    "l0.phineas.chime_full",
    "l0.phineas.dsa",
    "l0.phineas.chime_upchan",
    "l0.whitney.chime_full",
    "l0.whitney.dsa",
    "l0.whitney.chime_upchan",
    "l0.wilhelm.chime_full",
    "l0.wilhelm.dsa",
    "l0.wilhelm.chime_upchan",
    "l0.zach.chime_full",
    "l0.zach.dsa",
    "l0.zach.chime_upchan",
)
PROVENANCE_REF_KEYS = {"role", "path", "repository", "commit"}
PROVENANCE_REPOSITORIES = {
    "analysis",
    "pipeline",
    "manuscript",
    "external",
    "unresolved",
}


def _cell(value: object) -> str:
    if isinstance(value, list):
        text = "; ".join(str(item) for item in value) or "—"
    else:
        text = str(value) if value not in (None, "") else "—"
    return text.replace("|", "\\|").replace("\n", " ")


def manuscript_root(explicit: Path | None = None) -> Path:
    """Return the manuscript root; standalone analysis worktrees need an override."""
    if explicit is not None:
        root = explicit.resolve()
    elif os.environ.get("FABER2026_ROOT"):
        root = Path(os.environ["FABER2026_ROOT"]).expanduser().resolve()
    else:
        root = ROOT.parent
    if not (root / "main.tex").is_file():
        raise ValueError(
            "manuscript root not found; set FABER2026_ROOT to the Faber2026 checkout"
        )
    return root


def _strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cut = len(line)
        for index, char in enumerate(line):
            if char == "%" and (index == 0 or line[index - 1] != "\\"):
                cut = index
                break
        lines.append(line[:cut])
    return "\n".join(lines)


def _fls_sources(root: Path, graph: list[Path]) -> list[Path]:
    """Use a recorder only when newer than parsed and recorder-only sources."""
    recorder = root / "main.fls"
    if not recorder.is_file() or recorder.stat().st_mtime < max(
        path.stat().st_mtime for path in graph
    ):
        return []
    found: list[Path] = []
    for line in recorder.read_text(errors="replace").splitlines():
        if not line.startswith("INPUT ") or not line[6:].endswith(".tex"):
            continue
        path = Path(line[6:])
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if (
            path.is_file()
            and (path == root or root in path.parents)
            and path not in found
        ):
            found.append(path)
    if found and recorder.stat().st_mtime < max(path.stat().st_mtime for path in found):
        return []
    return found


def has_exact_result_schema(row: dict) -> bool:
    """Whether a result row has exactly the canonical top-level keys."""
    return set(row) == set(REQUIRED_FIELDS)


def validate_claim_owner_ledger(
    reviewed: dict, known_result_ids: set[str]
) -> tuple[list[str], dict[tuple[str, str, int], tuple[str | None, str | None]]]:
    """Validate the independent claim ledger before building its lookup."""
    errors: list[str] = []
    assignments: dict[tuple[str, str, int], tuple[str | None, str | None]] = {}
    if set(reviewed) != EXPECTED_CLAIM_OWNER_FIELDS:
        errors.append("claim-owner ledger has incorrect top-level fields")
    if (
        type(reviewed.get("schema_version")) is not int
        or reviewed.get("schema_version") != EXPECTED_CLAIM_OWNER_SCHEMA_VERSION
    ):
        errors.append("claim-owner ledger has unsupported schema_version")
    sources = reviewed.get("source", [])
    if not isinstance(sources, list):
        return errors + ["claim-owner ledger source must be a list"], assignments

    source_paths: list[str] = []
    for source_index, source in enumerate(sources):
        label = f"claim-owner source {source_index}"
        if not isinstance(source, dict):
            errors.append(f"{label} must be a table")
            continue
        if set(source) != EXPECTED_CLAIM_OWNER_SOURCE_FIELDS:
            errors.append(f"{label} has incorrect fields")
        path = source.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"{label} path must be a non-empty string")
            path = f"<invalid-source-{source_index}>"
        else:
            source_paths.append(path)
        claims = source.get("claims", [])
        if not isinstance(claims, list):
            errors.append(f"{path}: claims must be a list")
            continue
        for claim_index, claim in enumerate(claims):
            claim_label = f"{path}: claim {claim_index}"
            if not isinstance(claim, dict):
                errors.append(f"{claim_label} must be a table")
                continue
            selectors = {"owner_result_id", "exclusion_reason"} & set(claim)
            expected_fields = CLAIM_OWNER_BASE_FIELDS | selectors
            if len(selectors) != 1 or set(claim) != expected_fields:
                errors.append(f"{claim_label} has incorrect fields")
            fingerprint = claim.get("fingerprint")
            occurrence = claim.get("occurrence")
            if not isinstance(fingerprint, str) or not re.fullmatch(
                r"[0-9a-f]{16}", fingerprint
            ):
                errors.append(f"{claim_label} fingerprint must be 16 lowercase hex")
                continue
            if type(occurrence) is not int or occurrence < 1:
                errors.append(f"{claim_label} occurrence must be a positive integer")
                continue
            owner = claim.get("owner_result_id")
            exclusion = claim.get("exclusion_reason")
            if owner is not None and (
                not isinstance(owner, str) or owner not in known_result_ids
            ):
                errors.append(f"{claim_label} has unknown owner {owner}")
            if exclusion is not None and (
                not isinstance(exclusion, str) or not exclusion.strip()
            ):
                errors.append(f"{claim_label} exclusion must be a non-empty string")
            key = (path, fingerprint, occurrence)
            if key in assignments:
                errors.append(
                    f"claim-owner ledger has duplicate claim: {path}:{fingerprint}:{occurrence}"
                )
            else:
                assignments[key] = (owner, exclusion)

    duplicates = sorted(
        path for path, count in Counter(source_paths).items() if count > 1
    )
    if duplicates:
        errors.append(f"claim-owner ledger has duplicate sources: {duplicates}")
    return errors, assignments


def has_canonical_result_inventory(rows: list[dict]) -> bool:
    """Whether rows exactly match the reviewed 62-row roster and order."""
    return tuple(row.get("id") for row in rows) == CANONICAL_RESULT_IDS


def has_canonical_input_exception_inventory(rows: list[dict]) -> bool:
    """Whether exceptions exactly match the reviewed 15-record roster."""
    return tuple(row.get("name") for row in rows) == CANONICAL_INPUT_EXCEPTION_NAMES


def compiled_sources(root: Path) -> list[Path]:
    """Resolve the active TeX graph, augmented by a fresh .fls recorder."""
    found: list[Path] = []

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in found:
            return
        if not path.is_file() or root not in path.parents and path != root:
            raise ValueError(f"compiled TeX input is missing or outside root: {path}")
        found.append(path)
        for name in TEX_DEPENDENCY.findall(_strip_comments(path.read_text())):
            root_child = root / name
            local_child = path.parent / name
            if not root_child.suffix:
                root_child = root_child.with_suffix(".tex")
                local_child = local_child.with_suffix(".tex")
            child = root_child if root_child.exists() else local_child
            visit(child)

    visit(root / "main.tex")
    for path in _fls_sources(root, found):
        visit(path)
    return found


def numeric_claims(path: Path) -> list[dict[str, object]]:
    """Identify number-bearing lines with stable duplicate ordinals."""
    claims: list[dict[str, object]] = []
    seen: Counter[str] = Counter()
    text = _strip_comments(path.read_text())
    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized = " ".join(line.split())
        normalized = re.sub(
            r"\\(?:cite\w*|ref|eqref|label|url)\{[^}]*\}", "", normalized
        )
        if NUMBER.search(normalized):
            fingerprint = hashlib.sha256(normalized.encode()).hexdigest()[:16]
            seen[fingerprint] += 1
            claims.append(
                {
                    "fingerprint": fingerprint,
                    "occurrence": seen[fingerprint],
                    "line": line_number,
                    "text": normalized,
                }
            )
    return claims


def prose_fingerprints(path: Path) -> list[str]:
    """Compatibility view used by external tooling."""
    return [str(claim["fingerprint"]) for claim in numeric_claims(path)]


def compiled_artifacts(root: Path) -> tuple[set[str], set[str]]:
    """Return compiled generated-table and figure paths."""
    sources = compiled_sources(root)
    source_rel = {path.relative_to(root).as_posix() for path in sources}
    tables = {
        path.relative_to(root).as_posix()
        for path in sources
        if TABLE_ENVIRONMENT.match(_strip_comments(path.read_text()).lstrip())
    }
    figures: set[str] = set()
    for source in sources:
        text = _strip_comments(source.read_text())
        for name in GRAPHIC.findall(text):
            if "#" in name:
                macro = re.search(r"\\newcommand\{\\(\w+)\}\[1\]", text)
                if not macro:
                    raise ValueError(f"unresolved graphics macro in {source}: {name}")
                calls = re.findall(rf"\\{macro.group(1)}\{{([^}}]+)\}}", text)
                figures.update(
                    f"figures/{name.replace('#1', value)}" for value in calls
                )
            else:
                figures.add(name if name.startswith("figures/") else f"figures/{name}")
    return tables, figures


def validate_registry(registry: dict, root: Path) -> list[str]:
    """Return fail-closed registry and manuscript-coverage errors."""
    errors: list[str] = []
    if set(registry) != set(EXPECTED_REGISTRY_FIELDS):
        errors.append("registry has incorrect top-level fields")
    for field, expected_type in EXPECTED_REGISTRY_FIELDS.items():
        if field not in registry:
            errors.append(f"registry missing top-level field {field}")
        elif type(registry[field]) is not expected_type:
            errors.append(
                f"registry top-level field {field} must be {expected_type.__name__}"
            )
    if registry.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append(f"registry schema_version must be {EXPECTED_SCHEMA_VERSION}")

    input_exceptions = registry.get("input_exception", [])
    if isinstance(input_exceptions, list):
        if not all(isinstance(item, dict) for item in input_exceptions):
            errors.append("input_exception entries must be tables")
            input_exceptions = []
        if not has_canonical_input_exception_inventory(input_exceptions):
            errors.append("input exceptions differ from the canonical 15-record roster")
        for index, item in enumerate(input_exceptions):
            label = item.get("name", f"input_exception {index}")
            if set(item) != EXPECTED_INPUT_EXCEPTION_FIELDS:
                errors.append(f"{label}: input exception has incorrect fields")
            for field in EXPECTED_INPUT_EXCEPTION_FIELDS:
                if (
                    not isinstance(item.get(field), str)
                    or not item.get(field, "").strip()
                ):
                    errors.append(
                        f"{label}: input exception {field} must be a non-empty string"
                    )
            expected_class = (
                "remediation_packet"
                if str(item.get("name", "")).startswith("remediation.")
                else "freya_package_manifest"
            )
            if item.get("class") != expected_class:
                errors.append(f"{label}: input exception class is incorrect")
            if item.get("status") != "incomplete_lineage":
                errors.append(
                    f"{label}: input exception status must be incomplete_lineage"
                )
    rows = registry.get("result", [])
    if not isinstance(rows, list):
        return ["result must be a list"]
    if not all(isinstance(row, dict) for row in rows):
        return ["every result row must be a table"]
    ids = [row.get("id") for row in rows if isinstance(row.get("id"), str)]
    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate result ids: {duplicates}")
    known = set(ids)
    if not has_canonical_result_inventory(rows):
        errors.append("result inventory differs from the canonical 62-row roster")

    rows_by_id = {row["id"]: row for row in rows if isinstance(row.get("id"), str)}
    cards = rows_by_id.get("association.cards_figures", {})
    toa = rows_by_id.get("association.toa_offset_figure", {})
    if (
        cards.get("description")
        != "Twelve per-burst association cards (fig:assoc-cards-grid)"
    ):
        errors.append("association cards description exceeds its twelve-card scope")
    if cards.get("consumed_by") != ["sections/appendix.tex"]:
        errors.append("association cards consumers exceed its appendix-only scope")
    cards_consumers = cards.get("consumed_by", [])
    toa_consumers = toa.get("consumed_by", [])
    if isinstance(cards_consumers, list) and isinstance(toa_consumers, list):
        overlap = sorted(set(cards_consumers) & set(toa_consumers))
        if overlap:
            errors.append(
                f"association cards and pending TOA figure consumers overlap: {overlap}"
            )
    if toa.get("trust") != "pending":
        errors.append("TOA offset figure must remain pending explicit authority")
    for row in rows:
        if row.get("id") == "association.toa_offset_figure":
            continue
        scoped_text = f"{row.get('description', '')} {row.get('artifact', '')}"
        if (
            "toa-offset-decomposition" in scoped_text
            or "toa_offset_decomposition" in scoped_text
        ):
            errors.append(
                f"{row.get('id')}: TOA decomposition scope belongs only to the pending TOA row"
            )

    repository_roots = {
        "analysis": ROOT,
        "pipeline": root / "pipeline",
        "manuscript": root,
    }

    def exists(declared: str) -> bool:
        return any((base / declared).exists() for base in (ROOT, root))

    for row in rows:
        raw_id = row.get("id")
        row_id = raw_id if isinstance(raw_id, str) else "<invalid-id>"
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in row:
                errors.append(f"{row_id}: missing required field {field}")
            elif type(row[field]) is not expected_type:
                errors.append(f"{row_id}: {field} must be {expected_type.__name__}")
        unknown_fields = sorted(set(row) - set(REQUIRED_FIELDS))
        if unknown_fields:
            errors.append(f"{row_id}: unknown fields: {', '.join(unknown_fields)}")
        for field in LIST_FIELDS:
            if (
                field in row
                and isinstance(row[field], list)
                and not all(isinstance(item, str) for item in row[field])
            ):
                errors.append(f"{row_id}: {field} entries must be strings")
        for field in REQUIRED_FIELDS:
            value = row.get(field)
            values = value if isinstance(value, list) else [value]
            if any(
                isinstance(item, str) and PLACEHOLDER.search(item) for item in values
            ):
                errors.append(f"{row_id}: {field} contains a placeholder token")
        trust_state = row.get("trust")
        if not isinstance(trust_state, str) or trust_state not in ALLOWED_TRUST:
            errors.append(f"{row_id}: invalid trust state")
        state = row.get("provenance_state")
        if not isinstance(state, str) or state not in ALLOWED_PROVENANCE:
            errors.append(f"{row_id}: invalid or absent provenance_state")
            continue
        gaps = row.get("provenance_gaps", [])
        if state == "pending" and not gaps:
            errors.append(f"{row_id}: pending provenance lacks explicit gaps")
        if state == "complete":
            if gaps:
                errors.append(f"{row_id}: complete provenance has open gaps")
            for field in ("producing_script", "pipeline_pin", "inputs", "artifact"):
                if not row.get(field):
                    errors.append(f"{row_id}: complete provenance lacks {field}")
            joined = " ".join(
                str(row.get(field, ""))
                for field in ("producing_script", "pipeline_pin", "inputs", "artifact")
            )
            if UNRESOLVED_PIN_WORDS.search(joined):
                errors.append(
                    f"{row_id}: complete provenance contains unresolved wording"
                )
            pin_match = EXACT_PIN.fullmatch(str(row.get("pipeline_pin", "")))
            if not pin_match:
                errors.append(
                    f"{row_id}: complete provenance lacks an exact commit pin"
                )
            for producer in str(row.get("producing_script", "")).split(" + "):
                if producer and not exists(producer):
                    errors.append(
                        f"{row_id}: producing path does not exist: {producer}"
                    )
            declared_inputs = row.get("inputs", [])
            if isinstance(declared_inputs, list):
                for input_path in declared_inputs:
                    if not exists(str(input_path)):
                        errors.append(
                            f"{row_id}: input path does not exist: {input_path}"
                        )
            for artifact in str(row.get("artifact", "")).split(" + "):
                artifact_path = artifact.split()[0] if artifact else ""
                if artifact_path and not exists(artifact_path):
                    errors.append(
                        f"{row_id}: artifact path does not exist: {artifact_path}"
                    )
        declared_pin = str(row.get("pipeline_pin", ""))
        if declared_pin:
            pin_match = EXACT_PIN.fullmatch(declared_pin)
            if not pin_match:
                errors.append(f"{row_id}: pipeline_pin has invalid format")
            elif not (root / "pipeline" / ".git").exists():
                errors.append(
                    f"{row_id}: pipeline repository is unavailable for pin verification"
                )
            else:
                verified = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(root / "pipeline"),
                        "cat-file",
                        "-e",
                        f"{pin_match.group(1)}^{{commit}}",
                    ],
                    capture_output=True,
                    check=False,
                )
                if verified.returncode:
                    errors.append(
                        f"{row_id}: pipeline pin does not exist: {pin_match.group(1)}"
                    )

        expected_refs: list[tuple[str, str]] = []
        producer = row.get("producing_script")
        if isinstance(producer, str) and producer:
            expected_refs.extend(
                ("producer", part.strip()) for part in producer.split(" + ")
            )
        inputs = row.get("inputs")
        if isinstance(inputs, list):
            expected_refs.extend(("input", str(path)) for path in inputs)
        artifact = row.get("artifact")
        if isinstance(artifact, str) and artifact:
            expected_refs.extend(
                ("artifact", part.strip()) for part in artifact.split(" + ")
            )

        refs = row.get("provenance_refs", [])
        if isinstance(refs, list):
            if not all(isinstance(ref, dict) for ref in refs):
                errors.append(f"{row_id}: provenance_refs entries must be tables")
                refs = []
            declared_refs: list[tuple[str, str]] = []
            for ref in refs:
                if set(ref) != PROVENANCE_REF_KEYS:
                    errors.append(f"{row_id}: provenance ref has incorrect keys")
                    continue
                role = ref.get("role")
                path = ref.get("path")
                repository = ref.get("repository")
                commit = ref.get("commit")
                if role not in {"producer", "input", "artifact"}:
                    errors.append(f"{row_id}: invalid provenance role {role}")
                if not isinstance(path, str) or not path:
                    errors.append(f"{row_id}: provenance ref path must be non-empty")
                    continue
                declared_refs.append((role, path))
                if repository not in PROVENANCE_REPOSITORIES:
                    errors.append(
                        f"{row_id}: invalid provenance repository {repository}"
                    )
                    continue
                if not isinstance(commit, str):
                    errors.append(f"{row_id}: provenance commit must be a string")
                    continue
                if path.startswith("pipeline/") and repository != "pipeline":
                    errors.append(f"{row_id}: {path} must declare repository pipeline")
                if (
                    path.startswith(("scripts/", "dm-joint-phase-v2/"))
                    and role != "artifact"
                    and repository != "analysis"
                ):
                    errors.append(f"{row_id}: {path} must declare repository analysis")
                artifact_path = path.split()[0]
                if (
                    role == "artifact"
                    and (
                        artifact_path.startswith("figures/")
                        or artifact_path.endswith(".tex")
                    )
                    and repository != "manuscript"
                ):
                    errors.append(
                        f"{row_id}: {path} must declare repository manuscript"
                    )
                if repository in {"external", "unresolved"}:
                    if commit:
                        errors.append(
                            f"{row_id}: {repository} ref cannot declare a Git commit"
                        )
                    if state == "complete":
                        errors.append(
                            f"{row_id}: complete provenance cannot use {repository} refs"
                        )
                    continue
                if commit and not re.fullmatch(r"[0-9a-f]{40}", commit):
                    errors.append(f"{row_id}: provenance commit must be full 40-hex")
                    continue
                if state == "complete" and not commit:
                    errors.append(
                        f"{row_id}: complete provenance ref lacks commit: {path}"
                    )
                    continue
                if commit:
                    repo_root = repository_roots[repository]
                    verified = subprocess.run(
                        [
                            "git",
                            "-C",
                            str(repo_root),
                            "cat-file",
                            "-e",
                            f"{commit}^{{commit}}",
                        ],
                        capture_output=True,
                        check=False,
                    )
                    if verified.returncode:
                        errors.append(
                            f"{row_id}: provenance commit does not exist in {repository}: {commit}"
                        )
                    else:
                        repository_path = path.split()[0]
                        if repository == "pipeline" and repository_path.startswith(
                            "pipeline/"
                        ):
                            repository_path = repository_path.removeprefix("pipeline/")
                        path_verified = subprocess.run(
                            [
                                "git",
                                "-C",
                                str(repo_root),
                                "cat-file",
                                "-e",
                                f"{commit}:{repository_path}",
                            ],
                            capture_output=True,
                            check=False,
                        )
                        if path_verified.returncode:
                            errors.append(
                                f"{row_id}: provenance path does not exist at declared "
                                f"{repository} commit: {path}"
                            )
            if Counter(declared_refs) != Counter(expected_refs):
                errors.append(
                    f"{row_id}: provenance_refs do not cover every producer/input/artifact"
                )

    prose_rows = registry.get("prose_source", [])
    if not isinstance(prose_rows, list) or not all(
        isinstance(item, dict) and isinstance(item.get("source"), str)
        for item in prose_rows
    ):
        errors.append("prose_source must contain tables with string source fields")
        prose_rows = []
    prose_source_paths = [item["source"] for item in prose_rows]
    for item in prose_rows:
        source = item["source"]
        if set(item) != EXPECTED_PROSE_SOURCE_FIELDS:
            errors.append(f"{source}: prose_source has incorrect fields")
    duplicate_prose_sources = sorted(
        path for path, count in Counter(prose_source_paths).items() if count > 1
    )
    if duplicate_prose_sources:
        errors.append(
            f"duplicate registry prose_source blocks: {duplicate_prose_sources}"
        )
    prose_sources = {}
    for item in prose_rows:
        prose_sources.setdefault(item["source"], item)
    compiled = compiled_sources(root)
    table_paths, figure_paths = compiled_artifacts(root)
    prose_paths = [
        path
        for path in compiled
        if path.relative_to(root).as_posix() not in table_paths
    ]
    expected_sources = {path.relative_to(root).as_posix() for path in prose_paths}
    if set(prose_sources) != expected_sources:
        errors.append(
            "prose coverage source mismatch: "
            f"missing={sorted(expected_sources - set(prose_sources))}; "
            f"extra={sorted(set(prose_sources) - expected_sources)}"
        )
    for relative in sorted(expected_sources & set(prose_sources)):
        record = prose_sources[relative]
        actual = {
            (claim["fingerprint"], claim["occurrence"])
            for claim in numeric_claims(root / relative)
        }
        actual_text = {
            (claim["fingerprint"], claim["occurrence"]): claim["text"]
            for claim in numeric_claims(root / relative)
        }
        actual_lines = {
            (claim["fingerprint"], claim["occurrence"]): claim["line"]
            for claim in numeric_claims(root / relative)
        }
        declared_claims = record.get("claims", [])
        if not isinstance(declared_claims, list) or not all(
            isinstance(claim, dict) for claim in declared_claims
        ):
            errors.append(f"{relative}: claims must be a list of tables")
            declared_claims = []
        declared = {
            (claim.get("fingerprint"), claim.get("occurrence"))
            for claim in declared_claims
            if isinstance(claim.get("fingerprint"), str)
            and type(claim.get("occurrence")) is int
        }
        if declared != actual or len(declared) != len(declared_claims):
            errors.append(f"{relative}: per-claim numeric coverage is stale")
        for claim in declared_claims:
            fingerprint = claim.get("fingerprint")
            occurrence = claim.get("occurrence")
            claim_key = (
                (fingerprint, occurrence)
                if isinstance(fingerprint, str) and type(occurrence) is int
                else (None, None)
            )
            selectors = {"owner_result_id", "exclusion_reason"} & set(claim)
            expected_fields = PROSE_CLAIM_BASE_FIELDS | selectors
            if len(selectors) != 1 or set(claim) != expected_fields:
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    "prose claim has incorrect fields"
                )
            if not isinstance(fingerprint, str) or not re.fullmatch(
                r"[0-9a-f]{16}", fingerprint
            ):
                errors.append(
                    f"{relative}: prose claim fingerprint must be 16 lowercase hex"
                )
            if type(occurrence) is not int or occurrence < 1:
                errors.append(
                    f"{relative}: prose claim occurrence must be a positive integer"
                )
            if type(claim.get("line")) is not int or claim.get("line", 0) < 1:
                errors.append(
                    f"{relative}: prose claim line must be a positive integer"
                )
            if (
                not isinstance(claim.get("text"), str)
                or not claim.get("text", "").strip()
            ):
                errors.append(
                    f"{relative}: prose claim text must be a non-empty string"
                )
            if claim.get("text") != actual_text.get(claim_key):
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    "claim text is stale"
                )
            expected_line = actual_lines.get(claim_key)
            if claim.get("line") != expected_line:
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    "claim line is stale"
                )
            owner = claim.get("owner_result_id")
            exclusion = claim.get("exclusion_reason")
            if bool(owner) == bool(exclusion):
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    "claim needs exactly one owner or exclusion"
                )
            elif (not isinstance(owner, str) or owner not in known) and not exclusion:
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    f"unknown owner {owner}"
                )
            if owner == "__SELECT_OWNER__" or (
                isinstance(exclusion, str) and PLACEHOLDER.search(exclusion)
            ):
                errors.append(
                    f"{relative}:{claim.get('fingerprint')}:{claim.get('occurrence')}: "
                    "claim ownership is unresolved"
                )

    reviewed = tomllib.loads(CLAIM_OWNERS.read_text())
    ledger_errors, reviewed_assignments = validate_claim_owner_ledger(reviewed, known)
    errors.extend(ledger_errors)
    declared_assignments = {}
    for source in prose_rows:
        for claim in source.get("claims", []):
            fingerprint = claim.get("fingerprint")
            occurrence = claim.get("occurrence")
            if not isinstance(fingerprint, str) or type(occurrence) is not int:
                continue
            key = (source["source"], fingerprint, occurrence)
            declared_assignments[key] = (
                claim.get("owner_result_id"),
                claim.get("exclusion_reason"),
            )
    if declared_assignments != reviewed_assignments:
        errors.append("claim ownership differs from independent semantic review")

    artifact_records = registry.get("artifact_coverage", [])
    artifacts = defaultdict(list)
    for record in artifact_records:
        if not isinstance(record, dict):
            errors.append("artifact coverage entries must be tables")
            continue
        if set(record) != EXPECTED_ARTIFACT_COVERAGE_FIELDS:
            errors.append("artifact coverage entry has incorrect fields")
        paths = record.get("paths", [])
        if (
            not isinstance(paths, list)
            or not paths
            or not all(isinstance(path, str) and bool(path.strip()) for path in paths)
        ):
            errors.append("artifact coverage paths must be a non-empty list of strings")
            continue
        for path in paths:
            artifacts[path].append(record.get("result_id", ""))
        result_id = record.get("result_id")
        if not isinstance(result_id, str) or result_id not in known:
            errors.append(
                f"artifact coverage has unknown result id: {record.get('result_id')}"
            )
    expected_artifacts = table_paths | figure_paths
    if set(artifacts) != expected_artifacts:
        errors.append(
            "artifact coverage mismatch: "
            f"missing={sorted(expected_artifacts - set(artifacts))}; "
            f"extra={sorted(set(artifacts) - expected_artifacts)}"
        )
    for path in sorted(expected_artifacts):
        if len(artifacts[path]) != 1:
            errors.append(
                f"{path}: expected exactly one registry owner, found {len(artifacts[path])}"
            )
    cards_artifacts = {
        path
        for path, owners in artifacts.items()
        if "association.cards_figures" in owners
    }
    if cards_artifacts != ASSOCIATION_CARD_ARTIFACTS:
        errors.append("association cards must own exactly the twelve card artifacts")
    toa_artifacts = {
        path
        for path, owners in artifacts.items()
        if "association.toa_offset_figure" in owners
    }
    if toa_artifacts != {"figures/toa_offset_decomposition.pdf"}:
        errors.append("pending TOA row must solely own the TOA decomposition artifact")
    return errors


def render(registry: dict) -> str:
    rows = registry["result"]
    manuscript = [row for row in rows if row["section"] != "§0"]
    certificates = [row for row in rows if row["section"] == "§0"]
    trust = Counter(row["trust"] for row in manuscript)
    provenance = Counter(row["provenance_state"] for row in manuscript)
    certificate_trust = Counter(row["trust"] for row in certificates)
    certificate_provenance = Counter(row["provenance_state"] for row in certificates)
    claim_count = sum(
        len(source.get("claims", [])) for source in registry.get("prose_source", [])
    )

    lines = [
        "<!-- Generated by scripts/render_results_registry.py; do not edit. -->",
        "# Results registry",
        "",
        f"Registry schema: `{registry['schema_version']}`. Updated: `{registry['updated']}`.",
        "Scientific trust and provenance completeness are separate: a complete",
        "inventory record does not promote a scientific claim.",
        "",
        "## Summary",
        "",
        f"- Manuscript-facing rows: {len(manuscript)}",
        f"- Scientific trust: {trust['trusted']} trusted; {trust['pending']} pending; {trust['revoked']} revoked",
        f"- Provenance metadata: {provenance['complete']} complete; {provenance['pending']} pending",
        f"- Input certificates: {len(certificates)} ({certificate_trust['trusted']} trusted; {certificate_trust['pending']} pending; {certificate_trust['revoked']} revoked)",
        f"- Input-certificate provenance: {certificate_provenance['complete']} complete; {certificate_provenance['pending']} pending",
        f"- Numeric prose coverage: {claim_count} individually owned or excluded claims across {len(registry.get('prose_source', []))} compiled source files",
        f"- Explicit input-lineage exceptions: {len(registry['input_exception'])}",
        "",
        "## Manuscript-facing inventory",
        "",
        "| ID | Section | Result | Current | Trust | Provenance | Producer | Pin | Artifact | Open provenance gaps |",
        "|---|---|---|:---:|---|---|---|---|---|---|",
    ]
    for row in manuscript:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    f"`{row['id']}`",
                    row["section"],
                    row["description"],
                    "yes" if row["current"] else "no",
                    row["trust"],
                    row["provenance_state"],
                    row["producing_script"],
                    row["pipeline_pin"],
                    row["artifact"],
                    row.get("provenance_gaps", []),
                )
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Input certificates",
            "",
            "| ID | Product | Frequency order | Trust | Provenance | Artifact | Open provenance gaps |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in certificates:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    f"`{row['id']}`",
                    row["description"],
                    row["value"],
                    row["trust"],
                    row["provenance_state"],
                    row["artifact"],
                    row.get("provenance_gaps", []),
                )
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Input-lineage exceptions",
            "",
            "| Name | Class | Status | Path | Reason |",
            "|---|---|---|---|---|",
        ]
    )
    for row in registry["input_exception"]:
        lines.append(
            "| "
            + " | ".join(
                _cell(row[key]) for key in ("name", "class", "status", "path", "reason")
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--manuscript-root", type=Path)
    args = parser.parse_args()
    content = render(tomllib.loads(REGISTRY.read_text()))
    if args.validate:
        errors = validate_registry(
            tomllib.loads(REGISTRY.read_text()), manuscript_root(args.manuscript_root)
        )
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0
    if args.stdout:
        sys.stdout.write(content)
        return 0
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != content:
            print(f"stale generated file: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0
    OUTPUT.write_text(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
