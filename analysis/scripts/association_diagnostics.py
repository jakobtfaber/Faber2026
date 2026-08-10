"""Validate manuscript-facing association diagnostics from the pipeline report.

The pipeline owns the chance-coincidence calculation.  Manuscript generators
must consume its class-aware values directly rather than silently correcting a
stale report downstream.
"""

from __future__ import annotations

import math


def class_aware_chance_probability(
    burst: dict,
    *,
    dm: float,
    inputs: dict,
) -> float:
    """Recompute Pcc at the new DM without changing the pre-specified class."""
    mu = (
        float(inputs["rate_per_day"])
        / (4.0 * math.pi)
        / 86400.0
        * (float(inputs["omega_win_deg2"]) / (180.0 / math.pi) ** 2)
        * (2.0 * float(inputs["dt_s"]))
    )
    if burst["dm_agreement"]["consistent"] is not None:
        dm_median, dm_sigma_ln = 500.0, 0.7
        z = (math.log(dm) - math.log(dm_median)) / dm_sigma_ln
        density = math.exp(-0.5 * z * z) / (
            dm * dm_sigma_ln * math.sqrt(2.0 * math.pi)
        )
        mu *= min(1.0, density * 2.0 * float(inputs["ddm"]))
    return -math.expm1(-mu)


def reported_chance_probability(burst: dict) -> float:
    """Return source Pcc after checking its class and applied DM factor."""
    required = {
        "chance_coincidence_P",
        "chance_coincidence_f_DM",
        "chance_coincidence_class",
    }
    missing = sorted(required - burst.keys())
    if missing:
        raise ValueError(
            "association report lacks class-aware provenance fields: " + ", ".join(missing)
        )

    dm_constrained = burst["dm_agreement"]["consistent"] is not None
    expected_class = "dm_position_time" if dm_constrained else "position_time"
    if burst["chance_coincidence_class"] != expected_class:
        raise ValueError(
            f"association class mismatch: expected {expected_class}, "
            f"got {burst['chance_coincidence_class']}"
        )
    if not dm_constrained and float(burst["chance_coincidence_f_DM"]) != 1.0:
        raise ValueError("position-and-time-only association must use f_DM=1")
    return float(burst["chance_coincidence_P"])
