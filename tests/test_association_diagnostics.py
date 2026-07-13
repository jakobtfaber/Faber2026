import json
import math
from pathlib import Path

import pytest

from scripts.association_diagnostics import (
    class_aware_chance_probability,
    position_time_chance_probability,
)


INPUTS = {
    "rate_per_day": 1000.0,
    "omega_win_deg2": math.pi * 0.5**2,
    "dt_s": 1.0,
}


def test_position_time_probability_omits_dm_suppression():
    assert position_time_chance_probability(INPUTS) == pytest.approx(4.407079754e-7)


def test_class_aware_probability_uses_report_value_only_when_dm_is_constrained():
    constrained = {
        "chance_coincidence_P": 5e-9,
        "dm_agreement": {"consistent": True},
    }
    unconstrained = {
        "chance_coincidence_P": 5e-9,
        "dm_agreement": {"consistent": None},
    }
    assert class_aware_chance_probability(constrained, INPUTS) == 5e-9
    assert class_aware_chance_probability(unconstrained, INPUTS) == pytest.approx(4.407079754e-7)


def test_committed_report_has_eight_dm_filtered_and_four_position_time_rows():
    root = Path(__file__).resolve().parents[1]
    report = json.loads(
        (root / "pipeline/crossmatching/association_report.json").read_text()
    )
    values = [
        class_aware_chance_probability(row, report["inputs"])
        for row in report["bursts"]
    ]
    unconstrained = [
        value
        for row, value in zip(report["bursts"], values, strict=True)
        if row["dm_agreement"]["consistent"] is None
    ]
    constrained = [
        value
        for row, value in zip(report["bursts"], values, strict=True)
        if row["dm_agreement"]["consistent"] is not None
    ]
    assert len(constrained) == 8
    assert len(unconstrained) == 4
    assert max(constrained) < 1e-8
    assert unconstrained == pytest.approx([4.407079754e-7] * 4)
