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
    assert aggregate["needs"] == "dualband-fit-cell"
    assert "--stage aggregate" in "\n".join(_run_commands(aggregate))
    for job in (matrix, aggregate):
        assert job["permissions"] == {"contents": "read"}
        for step in job["steps"]:
            if isinstance(step, dict) and "uses" in step:
                assert "@" in step["uses"]
                assert len(step["uses"].rsplit("@", 1)[1].split()[0]) == 40
