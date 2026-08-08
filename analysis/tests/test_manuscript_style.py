from __future__ import annotations

import builtins
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib import font_manager

from plotting.style import bundled_computer_modern_font_paths, use_manuscript_style

ROOT = Path(__file__).resolve().parents[1]


def test_manuscript_style_applies_required_settings() -> None:
    with plt.rc_context():
        use_manuscript_style()

        assert plt.rcParams["text.usetex"] is False
        assert plt.rcParams["font.family"] == ["serif"]
        assert plt.rcParams["font.serif"] == ["cmr10"]
        assert plt.rcParams["mathtext.fontset"] == "cm"
        assert plt.rcParams["xtick.direction"] == "in"
        assert plt.rcParams["ytick.direction"] == "in"
        assert plt.rcParams["pdf.fonttype"] == 42


def test_manuscript_style_registers_bundled_computer_modern(monkeypatch) -> None:
    registered: list[Path] = []
    monkeypatch.setattr(font_manager.fontManager, "addfont", registered.append)

    with plt.rc_context():
        use_manuscript_style()

    assert any(path.name == "cmr10.ttf" for path in registered)


def test_energetics_method_receipt_binds_shared_style() -> None:
    receipt = json.loads(
        (
            ROOT
            / "energetics/studies/burst-energies/figures/"
            "energetics-measurement-method.provenance.json"
        ).read_text(encoding="utf-8")
    )
    style = ROOT / "plotting/style.py"
    assert receipt["style_source"] == "plotting/style.py"
    assert receipt["style_source_sha256"] == hashlib.sha256(style.read_bytes()).hexdigest()
    figure = ROOT / receipt["figure"][0]
    assert receipt["figure_sha256"] == hashlib.sha256(figure.read_bytes()).hexdigest()
    expected_fonts = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in bundled_computer_modern_font_paths()
    }
    assert {row["name"]: row["sha256"] for row in receipt["style_fonts"]} == expected_fonts


def test_manuscript_style_fails_when_scienceplots_is_missing(monkeypatch) -> None:
    real_import = builtins.__import__

    def import_without_scienceplots(name, *args, **kwargs):
        if name == "scienceplots":
            raise ImportError("simulated missing dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_scienceplots)

    with pytest.raises(RuntimeError, match="SciencePlots is required"):
        use_manuscript_style()


def test_legacy_radio_pipeline_style_module_is_removed() -> None:
    assert importlib.util.find_spec("radio_pipeline.plotting") is None


@pytest.mark.parametrize(
    ("script_name", "function_name"),
    [
        ("dm_budget_uncertainty.py", "_apply_manuscript_style"),
        ("plot_codetection_gallery.py", "_apply_style"),
    ],
)
def test_root_invoked_scripts_can_import_shared_style(
    script_name: str, function_name: str, tmp_path: Path
) -> None:
    script = ROOT / "scripts" / script_name
    code = (
        "import runpy, sys; "
        f"sys.path.insert(0, {str(script.parent)!r}); "
        f"ns=runpy.run_path({str(script)!r}); "
        f"ns[{function_name!r}]()"
    )
    manuscript = tmp_path / "Faber2026"
    (manuscript / "figures").mkdir(parents=True)
    (manuscript / "main.tex").write_text("")
    (manuscript / "figures" / "catalog.yaml").write_text("figures: []\n")
    env = os.environ.copy()
    env["FABER2026_ROOT"] = str(manuscript)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT.parent,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
