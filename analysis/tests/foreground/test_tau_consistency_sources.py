"""The migrated tau-consistency catalog must resolve inside analysis."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = (
    ROOT
    / "foregrounds"
    / "studies"
    / "census"
    / "data"
    / "tau_consistency_catalog.csv"
)


def test_joint_gate_sources_are_local_and_resolvable():
    rows = list(csv.DictReader(CATALOG.open()))
    assert len(rows) == 12
    for row in rows:
        source = row["joint_gate_source"]
        if not source or source.startswith("N/A"):
            continue
        assert not Path(source).is_absolute()
        assert "pipeline/" not in source
        assert (ROOT / source).is_file(), source
