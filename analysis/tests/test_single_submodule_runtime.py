from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_runtime_surfaces_do_not_require_pipeline_checkout():
    makefile = (ROOT / "Makefile").read_text()
    catalog_text = (ROOT / "figures/catalog.yaml").read_text()
    slots_text = (ROOT / "figure_review/slots.json").read_text()
    assert "pipeline" not in makefile
    assert "cwd: pipeline" not in catalog_text
    assert "--project analysis" not in catalog_text
    assert '"generator": "pipeline/' not in slots_text


def test_catalog_analysis_commands_resolve_project_from_analysis_cwd():
    catalog = yaml.safe_load((ROOT / "figures/catalog.yaml").read_text())
    for figure in catalog["figures"]:
        producer = figure.get("producer")
        if not producer or producer.get("cwd") != "analysis":
            continue
        argv = producer["argv"]
        if "--project" in argv:
            assert argv[argv.index("--project") + 1] == "."


def test_lock_resolves_the_declared_flits_commit():
    project = (ROOT / "pyproject.toml").read_text()
    lock = (ROOT / "uv.lock").read_text()
    match = re.search(r"dsa110-FLITS\.git@([0-9a-f]{40})", project)
    assert match
    assert match.group(1) in lock
