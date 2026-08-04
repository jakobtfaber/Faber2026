import subprocess
import sys
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "analysis-ci.yml"
DUALBAND_MODULE = "tests/test_permanent_dualband_workflow.py"
INVENTORY_MODULE = "tests/test_checkout_inventory.py"
MARKERS = (
    "not slow and not network and not external_data and "
    "not historical_replay and not integration"
)


def _run_commands(job: dict[str, object]) -> list[str]:
    return [
        step["run"]
        for step in job["steps"]
        if isinstance(step, dict) and "run" in step
    ]


def _collect(*extra: str) -> set[str]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "--standalone-analysis",
            "-m",
            MARKERS,
            *extra,
        ],
        cwd=WORKFLOW.parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line
        for line in completed.stdout.splitlines()
        if "::" in line and not line.startswith(" ")
    }


def test_analysis_ci_partitions_the_original_suite_exactly_once() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    jobs = workflow["jobs"]
    general = jobs["analysis-tests"]
    dualband = jobs["dualband-workflow-tests"]
    inventory = jobs["checkout-inventory-tests"]
    all_commands = "\n".join(
        command for job in jobs.values() for command in _run_commands(job)
    )
    assert all_commands.count("bash tests/test_journal_append.sh") == 1
    for job in (general, dualband, inventory):
        assert job["timeout-minutes"] == 15
        command = "\n".join(_run_commands(job))
        assert "uv run --group test --frozen python -m pytest -q" in command
        assert "--standalone-analysis" in command
        assert f'-m "{MARKERS}"' in command
    general_command = "\n".join(_run_commands(general))
    assert f"--ignore={DUALBAND_MODULE}" in general_command
    assert f"--ignore={INVENTORY_MODULE}" in general_command
    assert dualband["needs"] == ["changes", "dualband-aggregate"]
    test_step = next(
        step for step in dualband["steps"] if DUALBAND_MODULE in step.get("run", "")
    )
    assert test_step["env"]["FABER2026_DUALBAND_PUBLISHED_FIXTURE"] == (
        "${{ runner.temp }}/dualband-published"
    )
    downloads = [
        step
        for step in dualband["steps"]
        if step.get("uses", "").startswith("actions/download-artifact@")
    ]
    assert len(downloads) == 1
    assert downloads[0]["with"] == {
        "name": "dualband-aggregate-${{ github.sha }}",
        "path": "${{ runner.temp }}/dualband-published",
    }


def test_analysis_ci_pytest_partitions_are_complete_and_disjoint() -> None:
    original = _collect()
    general = _collect(
        f"--ignore={DUALBAND_MODULE}",
        f"--ignore={INVENTORY_MODULE}",
    )
    dualband = _collect(DUALBAND_MODULE)
    inventory = _collect(INVENTORY_MODULE)
    assert not general & dualband
    assert not general & inventory
    assert not dualband & inventory
    assert general | dualband | inventory == original


def test_analysis_ci_declares_fixed_four_cell_serial_matrix() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    jobs = workflow["jobs"]
    matrix = jobs["dualband-fit-cell"]
    assert matrix["strategy"]["fail-fast"] is False
    assert matrix["timeout-minutes"] == 15
    assert matrix["strategy"]["matrix"]["include"] == [
        {"association": "one-to-one", "morphology": "gaussian"},
        {"association": "one-to-one", "morphology": "emg"},
        {"association": "wrong-chime-component", "morphology": "gaussian"},
        {"association": "wrong-chime-component", "morphology": "emg"},
    ]
    matrix_commands = "\n".join(_run_commands(matrix))
    assert "--stage fit-cell" in matrix_commands
    assert "worker_processes" not in matrix_commands
    aggregate = jobs["dualband-aggregate"]
    assert aggregate["needs"] == ["changes", "dualband-fit-cell"]
    assert "--stage aggregate" in "\n".join(_run_commands(aggregate))
    for job in (matrix, aggregate):
        assert job["permissions"] == {"contents": "read"}
        for step in job["steps"]:
            if isinstance(step, dict) and "uses" in step:
                assert "@" in step["uses"]
                assert len(step["uses"].rsplit("@", 1)[1].split()[0]) == 40


def test_registry_only_changes_use_the_fast_lane() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    jobs = workflow["jobs"]
    route = "\n".join(_run_commands(jobs["changes"]))
    assert "results-registry.toml" in route
    assert "results-registry-claim-owners.toml" in route
    assert "registry-only=$registry_only" in route
    assert jobs["registry-validation"]["if"] == (
        "needs.changes.outputs.registry-only == 'true'"
    )
    for name in (
        "analysis-tests",
        "dualband-workflow-tests",
        "checkout-inventory-tests",
        "dualband-fit-cell",
        "dualband-aggregate",
        "analysis-quality",
    ):
        assert jobs[name]["if"] == "needs.changes.outputs.full-suite == 'true'"


def test_analysis_ci_exposes_one_stable_required_check() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    required = workflow["jobs"]["required"]
    assert required["name"] == "analysis-ci"
    assert required["if"] == "always()"
    command = "\n".join(_run_commands(required))
    assert 'if [ "$FULL_SUITE" = true ]' in command
    assert 'test "$REGISTRY_VALIDATION" = success' in command
    assert 'test "$DUALBAND_FIT" = success' in command
