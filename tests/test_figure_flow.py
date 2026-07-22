"""Unit tests for scripts/figure_flow.py (no PDF regen)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import figure_flow  # noqa: E402


CATALOG = ROOT / "figures" / "catalog.yaml"


def test_catalog_loads():
    figures = figure_flow.load_catalog(CATALOG)
    assert len(figures) >= 9
    ids = {f["id"] for f in figures}
    assert "clusters_icm" in ids
    assert "sightline_budget" in ids
    assert "fig1_gallery" in ids


def test_manuscript_nodes_have_producer_and_outputs():
    figures = figure_flow.load_catalog(CATALOG)
    for fig in figures:
        if not fig.get("manuscript"):
            continue
        assert fig["producer"]["argv"], fig["id"]
        assert fig["outputs"], fig["id"]


def test_topo_sort_sightline_budget_before_clusters():
    figures = figure_flow.load_catalog(CATALOG)
    order = figure_flow.topo_sort(figures, {"clusters_icm"})
    assert order.index("sightline_budget") < order.index("clusters_icm")


def test_clone_ok_selection_excludes_fig1():
    figures = figure_flow.load_catalog(CATALOG)
    selected = figure_flow.select_ids(
        figures, ids=None, manuscript=True, clone_ok=True
    )
    assert "fig1_gallery" not in selected
    assert "toa_offset_decomposition" in selected
    assert "dm_host_posteriors" in selected
    assert "oran_qualified_scint" not in selected
    manuscript_ids = {
        f["id"] for f in figures if f.get("manuscript")
    }
    assert "oran_qualified_scint" not in manuscript_ids


def test_missing_inputs_typed_error(tmp_path: Path):
    catalog = {
        "schema_version": 1,
        "figures": [
            {
                "id": "needs_data",
                "manuscript": True,
                "clone_ok": True,
                "producer": {"argv": ["true"], "cwd": "."},
                "inputs": ["definitely/missing/input.bin"],
                "outputs": ["figures/fake.pdf"],
                "depends_on": [],
                "approval_slot": None,
            }
        ],
    }
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.dump(catalog), encoding="utf-8")
    figures = figure_flow.load_catalog(path)
    with pytest.raises(figure_flow.FigureFlowError) as exc:
        figure_flow.run_node(figures[0], root=tmp_path, dry_run=False)
    assert exc.value.code == "MISSING_INPUTS"


def test_skip_missing_on_manuscript_sweep(tmp_path: Path):
    catalog = {
        "schema_version": 1,
        "figures": [
            {
                "id": "needs_data",
                "manuscript": True,
                "clone_ok": True,
                "producer": {"argv": ["true"], "cwd": "."},
                "inputs": ["nope.bin"],
                "outputs": ["out.pdf"],
                "depends_on": [],
                "approval_slot": None,
            }
        ],
    }
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.dump(catalog), encoding="utf-8")
    figures = figure_flow.load_catalog(path)
    receipt = figure_flow.run_node(figures[0], root=tmp_path, skip_missing=True)
    assert receipt["status"] == "SKIP"
    assert receipt["code"] == "MISSING_INPUTS"


def test_dry_run_ok(tmp_path: Path):
    inp = tmp_path / "in.txt"
    inp.write_text("x", encoding="utf-8")
    catalog = {
        "schema_version": 1,
        "figures": [
            {
                "id": "ok",
                "manuscript": True,
                "clone_ok": True,
                "producer": {"argv": ["true"], "cwd": "."},
                "inputs": ["in.txt"],
                "outputs": ["out.pdf"],
                "depends_on": [],
                "approval_slot": None,
            }
        ],
    }
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.dump(catalog), encoding="utf-8")
    figures = figure_flow.load_catalog(path)
    receipt = figure_flow.run_node(figures[0], root=tmp_path, dry_run=True)
    assert receipt["status"] == "DRY_RUN"


def test_cycle_detected():
    figures = [
        {
            "id": "a",
            "producer": {"argv": ["true"]},
            "outputs": ["a"],
            "depends_on": ["b"],
        },
        {
            "id": "b",
            "producer": {"argv": ["true"]},
            "outputs": ["b"],
            "depends_on": ["a"],
        },
    ]
    with pytest.raises(figure_flow.FigureFlowError) as exc:
        figure_flow.topo_sort(figures, {"a"})
    assert exc.value.code == "CYCLE"


def test_cli_list_exits_zero():
    assert figure_flow.main(["--catalog", str(CATALOG), "list"]) == 0


def test_cli_regen_dry_run_clone_ok():
    rc = figure_flow.main(
        [
            "--catalog",
            str(CATALOG),
            "regen",
            "--manuscript",
            "--clone-ok",
            "--dry-run",
        ]
    )
    assert rc == 0


def test_dep_output_satisfies_downstream_input(tmp_path: Path, capsys):
    catalog = {
        "schema_version": 1,
        "figures": [
            {
                "id": "upstream",
                "manuscript": True,
                "clone_ok": True,
                "producer": {"argv": ["true"], "cwd": "."},
                "inputs": [],
                "outputs": ["mid.csv"],
                "depends_on": [],
                "approval_slot": None,
            },
            {
                "id": "downstream",
                "manuscript": True,
                "clone_ok": True,
                "producer": {"argv": ["true"], "cwd": "."},
                "inputs": ["mid.csv"],
                "outputs": ["out.pdf"],
                "depends_on": ["upstream"],
                "approval_slot": None,
            },
        ],
    }
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.dump(catalog), encoding="utf-8")
    rc = figure_flow.main(
        ["--catalog", str(path), "regen", "--manuscript", "--clone-ok", "--dry-run"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY_RUN   upstream" in out
    assert "DRY_RUN   downstream" in out
    assert "SKIP" not in out


def test_fig1_has_approval_slot():
    figures = figure_flow.by_id(figure_flow.load_catalog(CATALOG))
    assert figures["fig1_gallery"]["approval_slot"] == "fig1-gallery"
    hint = figure_flow.approval_hint(figures["fig1_gallery"])
    assert hint is not None
    assert "figure_review.py new-batch" in hint
    assert "fig1-gallery" in hint


def test_skill_file_exists():
    skill = ROOT / "figures" / "ax" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "figure_flow.py" in text
    assert "do not open" in text.lower() or "before opening" in text.lower()
