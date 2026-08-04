from scripts.classify_ci_changes import classify


def test_registry_lane_requires_only_registry_surfaces() -> None:
    assert classify(["RESULTS.md"]) == "registry"
    assert (
        classify(
            [
                "RESULTS.md",
                "docs/rse/control/results-registry.toml",
                "docs/rse/control/results-registry-claim-owners.toml",
            ]
        )
        == "registry"
    )


def test_ordinary_documentation_uses_quality_lane() -> None:
    assert classify(["README.md", "docs/rse/ops/knowledge-base.md"]) == "quality"


def test_scientific_products_fail_closed_to_full_lane() -> None:
    assert classify(["docs/analysis/dm-review.md"]) == "full"
    assert classify(["dispersion/results/joint-phase/README.md"]) == "full"
    assert classify(["foregrounds/results/table.csv"]) == "full"
    assert classify(["figures/catalog.yaml"]) == "full"


def test_code_dependencies_workflows_and_mixed_changes_use_full_lane() -> None:
    assert classify(["faber2026/burst_models/fit.py"]) == "full"
    assert classify(["pyproject.toml", "uv.lock"]) == "full"
    assert classify([".github/workflows/analysis-ci.yml"]) == "full"
    assert classify(["README.md", "scripts/run_dualband_burst_model.py"]) == "full"
    assert classify([]) == "full"
