from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_fig1_frequency_axes import root_for_telescope  # noqa: E402


def _load_current_joint_dm_runner():
    path = ROOT / "scripts/run_joint_dm_phase.py"
    spec = importlib.util.spec_from_file_location("current_joint_dm_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frequency_audit_routes_instruments_to_distinct_roots(tmp_path: Path) -> None:
    chime = tmp_path / "chime"
    dsa = tmp_path / "dsa"
    assert root_for_telescope("chime", chime, dsa) == chime
    assert root_for_telescope("dsa", chime, dsa) == dsa
    with pytest.raises(ValueError, match="unknown telescope"):
        root_for_telescope("other", chime, dsa)


def test_current_joint_dm_runner_routes_instruments_to_distinct_roots(
    tmp_path: Path,
) -> None:
    runner = _load_current_joint_dm_runner()
    chime = tmp_path / "chime"
    dsa = tmp_path / "dsa"
    assert runner.root_for_telescope("chime", chime, dsa) == chime
    assert runner.root_for_telescope("dsa", chime, dsa) == dsa
    with pytest.raises(ValueError, match="unknown telescope"):
        runner.root_for_telescope("other", chime, dsa)


def test_figure_one_catalog_declares_both_full_resolution_roots() -> None:
    catalog = yaml.safe_load((ROOT / "figures/catalog.yaml").read_text())
    figure = next(item for item in catalog["figures"] if item["id"] == "fig1_gallery")
    inputs = set(figure["inputs"])
    assert "~/Data/Faber2026/chimefrb/CHIME_bursts" in inputs
    assert "~/Data/Faber2026/dsa110/DSA_bursts" in inputs
