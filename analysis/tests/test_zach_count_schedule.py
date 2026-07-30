"""Guard the frozen Zach component-count schedule for issue #205.

These checks are cheap and offline. They assert that the staged contract still
says what it was frozen to say, and that the driver's invocation dictionary
still matches the fit runner's own argument parser. If someone changes a
default in ``run_joint_fit.py``, the contract this schedule writes would
silently stop matching what the runner reports, and every rung would fail
preflight with an unhelpful "fit configuration does not match contract". This
catches that at test time instead.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
PACKAGE = ANALYSIS / "scattering" / "studies" / "joint-refits" / "zach_count_20260729"
RUNNER = ANALYSIS / "scattering" / "studies" / "joint-refits" / "run_joint_fit.py"


@pytest.fixture(scope="module")
def schedule() -> dict:
    return json.loads((PACKAGE / "rungs.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def stager():
    if str(ANALYSIS) not in sys.path:
        sys.path.insert(0, str(ANALYSIS))
    # Loading the driver by file path byte-caches it, which would leave an
    # untracked __pycache__ in the checkout; the driver's own guard runs too
    # late to stop its own .pyc. Real use runs it as __main__, which is never
    # cached, so this is a test-harness concern only.
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "stage_zach_count", PACKAGE / "stage_zach_count.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def test_schedule_is_the_contract_the_issue_asks_for(schedule):
    assert schedule["burst"] == "zach"
    assert schedule["frozen"] is True
    assert [c["label"] for c in schedule["component_counts"]] == ["C2D3", "C2D4", "C2D5"]
    assert [c["components_C"] for c in schedule["component_counts"]] == [2, 2, 2]
    assert [c["components_D"] for c in schedule["component_counts"]] == [3, 4, 5]
    assert schedule["gain_prior_variances"] == [1, 10, 100]
    assert schedule["acceptance"]["evidence_threshold"] == 5.0


def test_rung_count_matches_the_declared_total(schedule, stager):
    expected = (
        len(schedule["component_counts"])
        * len(schedule["gain_prior_variances"])
        * len(schedule["seeds"])
    )
    assert expected == schedule["total_rungs"]
    assert len(stager.rungs()) == expected


def test_rung_labels_are_unique(stager):
    labels = [
        stager.rung_label(r["count"], r["gain_s2"], r["seed"]) for r in stager.rungs()
    ]
    assert len(set(labels)) == len(labels)


def test_only_count_variance_and_seed_vary(stager):
    """Everything else in the invocation must be identical across all rungs."""
    varying = {"components_D", "gain_s2", "seed"}
    invocations = [stager.invocation(r) for r in stager.rungs()]
    fixed_keys = set(invocations[0]) - varying
    for key in fixed_keys:
        values = {json.dumps(inv[key], sort_keys=True) for inv in invocations}
        assert len(values) == 1, f"{key} varies across rungs: {values}"


def _runner_parser_defaults() -> dict:
    """Collect the fit runner's argument defaults without executing a fit."""
    source = RUNNER.read_text(encoding="utf-8")
    start = source.index("    ap = argparse.ArgumentParser()")
    end = source.index("    a = ap.parse_args()")
    block = textwrap.dedent(source[start:end])
    namespace: dict = {"argparse": argparse, "Path": Path, "controlled": True}
    exec(block, namespace)  # noqa: S102
    return {action.dest: action.default for action in namespace["ap"]._actions}


def test_invocation_matches_the_runner_argument_defaults(stager):
    """The driver must not drift from the runner it drives."""
    defaults = _runner_parser_defaults()
    invocation = stager.invocation(stager.rungs()[0])

    # Values the driver leaves at the runner's default must actually be it.
    for key in ("mu_degree", "marginalize_gain", "marginalize_gain_gp", "force_multi"):
        assert invocation[key] == defaults[key], key
    assert invocation["alpha_bounds"] == [defaults["alpha_lo"], defaults["alpha_hi"]]
    assert invocation["beta_bounds"] is None and defaults["beta_lo"] is None

    # Multi-component fits force the effective shared-width flag off, whatever
    # the flag's own default is. The contract must record the effective value.
    assert defaults["shared_zeta"] is True
    assert invocation["shared_zeta"] is False


def test_invocation_key_set_matches_the_runner(stager):
    """A key added to the runner's invocation dictionary must be added here."""
    source = RUNNER.read_text(encoding="utf-8")
    start = source.index("    invocation = {")
    end = source.index("\n    }", start)
    runner_keys = {
        line.split('"')[1]
        for line in source[start:end].splitlines()[1:]
        if line.strip().startswith('"')
    }
    assert runner_keys == set(stager.invocation(stager.rungs()[0]))


def test_contract_file_set_matches_the_controlled_source_set(stager, tmp_path):
    from scattering.scat_analysis.controlled_run import CONTROLLED_SOURCE_NAMES

    stager.band_configs(tmp_path, Path("/nonexistent/dsa.npy"), Path("/nonexistent/chime.npy"))
    files = stager.resolved_files(tmp_path)
    assert CONTROLLED_SOURCE_NAMES <= set(files)
    for name in CONTROLLED_SOURCE_NAMES:
        assert files[name].is_file(), name


def test_freeze_contract_records_the_resolved_identity_output_argument(
    stager, tmp_path, monkeypatch
):
    """The freeze command must exactly match the command bound in its contract."""
    files = {}
    for name in (
        "chime_config",
        "dsa_config",
        "chime_input",
        "dsa_input",
        "chime_telescope_config",
        "dsa_telescope_config",
        "environment_lock",
        "controlled_entrypoint",
        "fit_driver",
        "joint_tf_prep_source",
        "burstfit_joint_source",
        "controlled_run_source",
        "model_grid_source",
        "diagnostic_source",
    ):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        files[name] = path
    monkeypatch.setattr(stager, "resolved_files", lambda _root: files)
    monkeypatch.setattr(stager, "git", lambda *_args: "revision")
    monkeypatch.setattr(
        stager,
        "controlled_environment_identity",
        lambda _root, _python, _path: {"identity_sha256": "environment"},
    )
    monkeypatch.setattr(stager, "processing_environment_identity", lambda *_args: {})

    rung = stager.rungs()[0]
    resolved = tmp_path / "resolved.json"
    freeze_receipt = tmp_path / "freeze.json"
    python = Path("/runtime/python")
    contract = stager.build_contract(
        rung,
        tmp_path,
        python,
        "0" * 64,
        resolved_output=resolved,
        receipt_output=freeze_receipt,
    )
    label = stager.rung_label(rung["count"], rung["gain_s2"], rung["seed"]).replace(":", "_")
    expected = [
        str(python.absolute()),
        *stager.runner_args(
            rung,
            tmp_path / "contracts" / f"{label}.json",
            freeze_receipt,
            resolved,
        ),
    ]
    assert contract["command"]["argv"] == expected
    assert "--resolved-identity-output" in contract["command"]["argv"]


def test_controlled_environment_identity_uses_the_child_environment(stager, tmp_path):
    identity = stager.controlled_environment_identity(
        tmp_path,
        Path(sys.executable),
        ANALYSIS / "uv.lock",
    )
    assert identity["python_runtime_options"]["flags"]["dont_write_bytecode"] == 1
    assert identity["numerical_environment"]["PYTHONPATH"] == str(ANALYSIS)


def test_subprocess_env_keeps_the_source_tree_clean(stager, tmp_path):
    """Regression: bytecode writes used to poison the tree between rungs.

    Importing from the checkout creates ``__pycache__`` directories in it. The
    controlled entrypoint refuses any dirty tree, untracked files included, so
    a single freeze pass would leave the tree dirty and every pass after it
    would fail. Reproduced before the fix: one driver-style subprocess created
    seven ``__pycache__`` directories.
    """
    env = stager.subprocess_env(tmp_path)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONPATH"] == str(stager.ANALYSIS)
    # -B would be recorded in argv, which the controlled runner cannot replay.
    assert not any(arg == "-B" for arg in stager.runner_args(
        stager.rungs()[0], Path("c.json"), Path("r.json"), None
    ))


def test_driver_disables_bytecode_before_importing_the_checkout(stager):
    """The driver's own imports must not dirty the tree either."""
    source = (PACKAGE / "stage_zach_count.py").read_text(encoding="utf-8")
    guard = source.index("sys.dont_write_bytecode = True")
    first_checkout_import = source.index("from scattering.scat_analysis.controlled_run import")
    assert guard < first_checkout_import


def test_driver_does_not_set_the_bytecode_variable_in_its_own_environment(stager):
    """Regression: doing so breaks the controlled runner's flag-replay check.

    Setting PYTHONDONTWRITEBYTECODE after startup leaves this process's
    sys.flags untouched but is inherited by children, including the reference
    interpreter controlled_python_argv spawns to confirm its flags are
    replayable. The two disagree and every controlled run dies with
    "interpreter flags or options cannot be replayed". Observed for real before
    this was reverted. The variable belongs in the subprocess environment only.
    """
    source = (PACKAGE / "stage_zach_count.py").read_text(encoding="utf-8")
    assigns = [
        line for line in source.splitlines()
        if "PYTHONDONTWRITEBYTECODE" in line and "os.environ[" in line and "=" in line
    ]
    assert assigns == [], assigns
    assert '"PYTHONDONTWRITEBYTECODE": "1"' in source  # still set for children


def test_resolution_contract_records_the_owner_selected_sampling(schedule, stager, tmp_path):
    """The accepted 65.536-us sampling is explicit in schedule and band config."""
    contract = schedule["resolution_contract"]
    assert contract["status"].startswith("RESOLVED")
    assert "65.536" in contract["owner_selection"]
    assert "adjacent-pair" in contract["decision_evidence"]

    stager.band_configs(tmp_path, Path("/nonexistent/dsa.npy"), Path("/nonexistent/chime.npy"))
    dsa_config = (tmp_path / "configs/zach_dsa_run.yaml").read_text(encoding="utf-8")
    assert "t_factor: 2" in dsa_config


def test_parallel_stagers_leave_complete_identical_band_configs(stager, tmp_path):
    """Parallel rung launchers must not expose truncated shared configurations."""
    dsa = Path("/science-inputs/dsa.npy")
    chime = Path("/science-inputs/chime.npy")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(stager.band_configs, tmp_path, dsa, chime) for _ in range(48)]
        for future in futures:
            future.result()

    config_dir = tmp_path / "configs"
    dsa_config = (config_dir / "zach_dsa_run.yaml").read_text(encoding="utf-8")
    chime_config = (config_dir / "zach_chime_run.yaml").read_text(encoding="utf-8")
    assert f"path: {json.dumps(str(dsa))}" in dsa_config
    assert f"path: {json.dumps(str(chime))}" in chime_config
    assert "t_factor: 2" in dsa_config
    assert "t_factor: 24" in chime_config
    assert list(config_dir.glob(".*.yaml.*")) == []
