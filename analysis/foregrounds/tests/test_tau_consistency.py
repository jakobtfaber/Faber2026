"""Behavioral tests for the active pulse-broadening consistency workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from foregrounds.propagation import run_tau_consistency_refits as runner
from foregrounds.propagation import tau_consistency as tau

ACCEPTED_VARIANTS = {
    "freya": "C1D1",
    "isha": "C2D1",
    "johndoeii": "C2D2",
    "mahi": "C1D2",
    "oran": "C2D1",
    "phineas": "C3D3",
    "whitney": "C2D3",
}

LOCKED_TAU_1GHZ_MS = {
    "freya": 0.11826818458099604,
    "isha": 0.11631269895330733,
    "johndoeii": 0.12227405312613455,
    "mahi": 0.1964102886734679,
    "oran": 0.022006398271738652,
    "phineas": 0.06758863108810399,
    "whitney": 0.0667457077673584,
}


def _cmd_value(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def test_authoritative_inputs_resolve_inside_analysis():
    assert tau.REPO_ROOT == Path(__file__).resolve().parents[2]
    assert tau.REFIT_DIR.is_dir()
    assert tau.JULY_ADJUDICATION_CSV.is_file()
    assert tau.CITABLE_ROSTER_JSON.is_file()
    assert tau.ALLEXP_FITS_DIR.is_dir()
    assert runner.RUN_JOINT.is_file()
    for path in (
        tau.REFIT_DIR,
        tau.JULY_ADJUDICATION_CSV,
        tau.CITABLE_ROSTER_JSON,
        tau.ALLEXP_FITS_DIR,
        runner.RUN_JOINT,
    ):
        assert "analysis/analysis" not in str(path)


def test_accepted_morphology_roster_matches_adjudication():
    morphologies = tau.load_july_accepted_morphologies()
    assert {name: morphology.variant for name, morphology in morphologies.items()} == (
        ACCEPTED_VARIANTS
    )


def test_citable_roster_and_budget_fit_resolve():
    names = tau.load_citable_budget_nicknames()
    assert names == frozenset(ACCEPTED_VARIANTS)
    assert tau.load_allexp_joint_tau_for_budget("casey") is None

    for name, expected_tau in LOCKED_TAU_1GHZ_MS.items():
        path = tau.find_citable_joint_json(name)
        assert path is not None
        assert path.parent == tau.DMLOCK_FIT_DIR
        assert f"DMLOCK_{ACCEPTED_VARIANTS[name]}" in path.name
        row = tau.load_allexp_joint_tau_for_budget(name)
        assert row is not None
        assert row["tau"] == pytest.approx(expected_tau, rel=1e-12)
        assert row["quality_flag"] in {"PASS", "MARGINAL"}


@pytest.mark.parametrize("burst, variant", sorted(ACCEPTED_VARIANTS.items()))
def test_refit_command_preserves_adjudicated_contract(burst: str, variant: str):
    morphology = tau.load_july_accepted_morphologies()[burst]
    command = runner.build_alpha4_joint_cmd(burst, morphology, nlive=600, nproc=8)
    components_c, components_d = tau.parse_cxdy_variant(variant)

    assert Path(command[1]) == runner.RUN_JOINT
    assert _cmd_value(command, "--components-C") == str(components_c)
    assert _cmd_value(command, "--components-D") == str(components_d)
    assert _cmd_value(command, "--alpha-lo") == "4"
    assert _cmd_value(command, "--alpha-hi") == "4"
    assert float(_cmd_value(command, "--fixed-delta-dm-C")) == pytest.approx(
        morphology.fixed_delta_dm_C
    )
    assert float(_cmd_value(command, "--fixed-delta-dm-D")) == pytest.approx(
        morphology.fixed_delta_dm_D
    )


@pytest.mark.parametrize("burst", ["casey", "chromatica", "zach"])
def test_refit_rejects_bursts_without_accepted_morphology(
    burst: str, monkeypatch: pytest.MonkeyPatch
):
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(runner.subprocess, "run", fail_if_called)
    with pytest.raises(ValueError, match="not eligible"):
        runner.run_burst(burst)
    assert not called


def test_dry_run_lists_each_accepted_morphology(capsys: pytest.CaptureFixture[str]):
    runner.main(["--dry-run"])
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == len(ACCEPTED_VARIANTS)
    assert {line.split()[0] for line in lines} == set(ACCEPTED_VARIANTS)
