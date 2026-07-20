from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from scripts.build_results_library_inventory import ExternalPathSpec
from scripts.promote_analysis_latest import PromotionError, promote


def _write_spec(root: Path, *, missing: bool = False) -> Path:
    (root / "artifacts").mkdir()
    (root / "artifacts/a.json").write_text('{"value": 1}\n')
    (root / "artifacts/a.npz").write_bytes(b"model-v1")
    spec = {
        "schema": "faber2026-latest-analysis/v1",
        "analysis": "demo",
        "domain": "scattering",
        "expected_bursts": 2,
        "source_commit": "abc123",
        "policy": {"latest_means": "newest promoted artifact"},
        "bursts": [
            {
                "nick": "a",
                "tns": "FRB A",
                "promotion_status": "artifact-present",
                "fit_quality_status": "candidate",
                "figure_review_status": "pending",
                "adoption_status": "owner-pending",
                "artifacts": {
                    "fit_json": "artifacts/missing.json"
                    if missing
                    else "artifacts/a.json",
                    "jointmodel_npz": "artifacts/a.npz",
                },
            },
            {
                "nick": "b",
                "tns": "FRB B",
                "promotion_status": "not-yet-promoted",
                "fit_quality_status": "unavailable",
                "figure_review_status": "unavailable",
                "adoption_status": "not-applicable",
                "reason": "no promoted fit",
            },
        ],
    }
    path = root / "spec.yaml"
    path.write_text(yaml.safe_dump(spec, sort_keys=False))
    return path


def test_initial_promotion_and_idempotence(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    library = tmp_path / "library"
    root.mkdir()
    spec = _write_spec(root)

    first = promote(spec, root, library, as_of="2026-07-20T12:00:00Z")
    second = promote(spec, root, library, as_of="2026-07-20T12:01:00Z")

    latest = library / "scattering/demo/latest"
    assert first == {"installed": 2, "unchanged": 0, "archived": 0}
    assert second == {"installed": 0, "unchanged": 2, "archived": 0}
    assert (latest / "a/fit.json").read_text() == '{"value": 1}\n'
    assert (latest / "a/jointmodel.npz").read_bytes() == b"model-v1"
    assert not (latest / "b/fit.json").exists()
    manifest = json.loads((latest / "manifest.json").read_text())
    assert [row["nick"] for row in manifest["bursts"]] == ["a", "b"]
    assert manifest["summary"] == {"artifact_present": 1, "not_yet_promoted": 1}
    assert not (library / "scattering/demo/historical").exists()


def test_changed_content_archives_previous_slot(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    library = tmp_path / "library"
    root.mkdir()
    spec = _write_spec(root)
    promote(spec, root, library, as_of="2026-07-20T12:00:00Z")
    (root / "artifacts/a.npz").write_bytes(b"model-v2")

    result = promote(spec, root, library, as_of="2026-07-21T09:30:00Z")

    archived = library / "scattering/demo/historical/20260721T093000Z/a"
    assert result == {"installed": 1, "unchanged": 1, "archived": 1}
    assert (archived / "jointmodel.npz").read_bytes() == b"model-v1"
    assert (
        library / "scattering/demo/latest/a/jointmodel.npz"
    ).read_bytes() == b"model-v2"


def test_missing_source_aborts_before_mutation(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    library = tmp_path / "library"
    root.mkdir()
    spec = _write_spec(root, missing=True)

    with pytest.raises(PromotionError, match="missing source"):
        promote(spec, root, library, as_of="2026-07-20T12:00:00Z")

    assert not library.exists()


def test_duplicate_burst_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    library = tmp_path / "library"
    root.mkdir()
    spec = _write_spec(root)
    payload = yaml.safe_load(spec.read_text())
    payload["bursts"][1]["nick"] = "a"
    spec.write_text(yaml.safe_dump(payload, sort_keys=False))

    with pytest.raises(PromotionError, match="duplicate burst"):
        promote(spec, root, library, as_of="2026-07-20T12:00:00Z")

    assert not library.exists()


def test_external_path_suffix_respects_library_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FABER2026_RESULTS_LIBRARY", str(tmp_path))
    spec = ExternalPathSpec(
        env="FABER2026_RESULTS_LIBRARY",
        default="~/Data/Faber2026/results-library",
        suffix="scattering/jointmodel",
    )

    assert spec.resolve() == tmp_path / "scattering/jointmodel"
