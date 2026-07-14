import json
import os
from pathlib import Path

import pytest

from scripts.association_diagnostics import (
    class_aware_chance_probability,
    reported_chance_probability,
)
from scripts.plot_association_summary import load_rows


def test_reported_probability_validates_class_aware_provenance():
    constrained = {
        "chance_coincidence_P": 5e-9,
        "chance_coincidence_f_DM": 0.01,
        "chance_coincidence_class": "dm_position_time",
        "dm_agreement": {"consistent": True},
    }
    unconstrained = {
        "chance_coincidence_P": 4.407079754e-7,
        "chance_coincidence_f_DM": 1.0,
        "chance_coincidence_class": "position_time",
        "dm_agreement": {"consistent": None},
    }
    assert reported_chance_probability(constrained) == 5e-9
    assert reported_chance_probability(unconstrained) == pytest.approx(4.407079754e-7)


def test_reported_probability_rejects_legacy_or_misclassified_rows():
    with pytest.raises(ValueError, match="lacks class-aware provenance"):
        reported_chance_probability(
            {"chance_coincidence_P": 5e-9, "dm_agreement": {"consistent": None}}
        )


def test_recomputed_probability_preserves_pre_specified_association_class():
    inputs = {
        "rate_per_day": 1000.0,
        "omega_win_deg2": 0.7853981633974483,
        "dt_s": 1.0,
        "ddm": 5.0,
    }
    constrained = {"dm_agreement": {"consistent": True}}
    position_time = {"dm_agreement": {"consistent": None}}
    assert class_aware_chance_probability(
        constrained, dm=411.435717, inputs=inputs
    ) < 1e-8
    assert class_aware_chance_probability(
        position_time, dm=411.435717, inputs=inputs
    ) == pytest.approx(4.407079754e-7)


def test_figure_five_uses_verified_dms_without_reclassifying_associations():
    rows = load_rows()
    assert len(rows) == 12
    assert sum(row["dm_constrained"] for row in rows) == 8
    assert max(abs(row["timing_z"]) for row in rows) < 3.0
    assert max(row["pcc"] for row in rows) == pytest.approx(4.407079754e-7)
    isha = next(row for row in rows if row["name"] == "isha")
    assert isha["dm_difference"] == pytest.approx(-0.116990)
    assert isha["dm_difference_sigma"] == pytest.approx(0.09734831)
    with pytest.raises(ValueError, match="must use f_DM=1"):
        reported_chance_probability(
            {
                "chance_coincidence_P": 5e-9,
                "chance_coincidence_f_DM": 0.01,
                "chance_coincidence_class": "position_time",
                "dm_agreement": {"consistent": None},
            }
        )


def test_committed_report_has_eight_dm_filtered_and_four_position_time_rows():
    root = Path(__file__).resolve().parents[1]
    pipeline = Path(os.environ.get("FABER2026_PIPELINE_SOURCE", root / "pipeline"))
    report = json.loads(
        (pipeline / "crossmatching/association_report.json").read_text()
    )
    constrained_rows = [
        row
        for row in report["bursts"]
        if row["dm_agreement"]["consistent"] is not None
    ]
    unconstrained_rows = [
        row
        for row in report["bursts"]
        if row["dm_agreement"]["consistent"] is None
    ]
    assert len(constrained_rows) == 8
    assert len(unconstrained_rows) == 4

    provenance_fields = {"chance_coincidence_class", "chance_coincidence_f_DM"}
    if any(not provenance_fields <= row.keys() for row in report["bursts"]):
        pytest.xfail(
            "the rewritten FLITS pin does not yet contain the class-aware "
            "association lane; re-landing it remains an explicit owner decision"
        )
    constrained = [reported_chance_probability(row) for row in constrained_rows]
    unconstrained = [reported_chance_probability(row) for row in unconstrained_rows]
    assert max(constrained) < 1e-8
    assert unconstrained == pytest.approx([4.407079754e-7] * 4)
