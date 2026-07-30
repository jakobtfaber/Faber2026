from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_joint_fit_event_config import (  # noqa: E402
    CANONICAL_OUTPUT_ROOT,
    CANONICAL_TRIGGER_PATH,
    STATION_CLOCK_SIGMA_S,
    migrate_config,
)
from one_event_workflow import STAGES, event_binding_sha256, validate_config  # noqa: E402
from run_one_event_absolute_dm_workflow import make_plan  # noqa: E402


@pytest.mark.parametrize(
    ("event", "source_icrs", "epoch_mjd_utc"),
    [
        ("oran", "21h12m10.760s +72d49m38.20s", "59705.59701292354"),
        ("isha", "04h45m38.64s +70d18m26.6s", "59896.386510976576"),
    ],
)
def test_migration_preserves_reviewed_inputs_and_builds_disabled_plan(
    event: str,
    source_icrs: str,
    epoch_mjd_utc: str,
) -> None:
    source_path = (
        ROOT / "analysis-configs" / "absolute-dm" / "phase-b" / event
        / "workflow-config.json"
    )
    source = json.loads(source_path.read_text())
    preserved = {
        "input_sha256": deepcopy(source["input_sha256"]),
        "chime": deepcopy(source["chime"]),
        "dsa": deepcopy(source["dsa"]),
        "geometry": deepcopy(source["geometry"]),
        "review": deepcopy(source["review"]),
    }

    migrated = migrate_config(
        source,
        source_icrs=source_icrs,
        epoch_mjd_utc=epoch_mjd_utc,
    )

    for key, value in preserved.items():
        assert migrated[key] == value
    for key, value in source["paths"].items():
        if key not in {"trigger_recovery", "output_root"}:
            assert migrated["paths"][key] == value

    assert migrated["paths"]["trigger_recovery"] == str(CANONICAL_TRIGGER_PATH)
    assert migrated["paths"]["output_root"] == str(CANONICAL_OUTPUT_ROOT / event)
    assert migrated["identity"]["input_basenames"]["trigger_recovery"] == (
        "trigger_mjd_microsecond_recovery.json"
    )
    assert migrated["identity"]["output_root_basename"] == event
    assert migrated["workflow"]["stages"] == list(STAGES)
    assert migrated["workflow"]["regression_fixture"] is False
    assert migrated["workflow"]["execution_authorized"] is False
    assert migrated["joint_fit"]["status"] == "blocked_pending_reviewed_inputs"
    assert migrated["joint_fit"]["execution_authorized"] is False
    assert migrated["joint_fit"]["geometry"]["source_icrs"] == source_icrs
    assert migrated["joint_fit"]["geometry"]["epoch_mjd_utc"] == epoch_mjd_utc
    assert migrated["joint_fit"]["geometry"]["clock_sigma_s"] == {
        "chime": STATION_CLOCK_SIGMA_S,
        "dsa": STATION_CLOCK_SIGMA_S,
    }
    assert migrated["event_binding_sha256"] == event_binding_sha256(migrated)
    schema = json.loads(
        (ROOT / "analysis-configs" / "absolute-dm" / "schema.json").read_text()
    )
    jsonschema.validate(migrated, schema)
    validate_config(migrated)

    plan = make_plan(
        migrated,
        config_path=ROOT / "analysis-configs" / "absolute-dm" / f"{event}.json",
        repo_root=ROOT,
        from_stage=STAGES[0],
        through_stage=STAGES[-1],
    )
    assert [row["stage"] for row in plan["stages"]] == list(STAGES)
    assert not (CANONICAL_OUTPUT_ROOT / event).exists()


def test_migration_rejects_missing_geometry_identity() -> None:
    source = json.loads(
        (
            ROOT
            / "analysis-configs"
            / "absolute-dm"
            / "phase-b"
            / "oran"
            / "workflow-config.json"
        ).read_text()
    )
    with pytest.raises(ValueError, match="source_icrs"):
        migrate_config(source, source_icrs=" ", epoch_mjd_utc="59705.59701292354")
