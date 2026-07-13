"""Validate manuscript-facing association diagnostics from the pipeline report.

The pipeline owns the chance-coincidence calculation.  Manuscript generators
must consume its class-aware values directly rather than silently correcting a
stale report downstream.
"""

from __future__ import annotations

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
