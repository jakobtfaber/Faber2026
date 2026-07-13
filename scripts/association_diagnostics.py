"""Shared manuscript-facing association diagnostic calculations.

The pipeline association report applies the DM-window factor to every row.  For
bursts without an independently constrained CHIME DM, the manuscript instead
defines a position-and-time-only chance probability (``f_DM = 1``).  Keep that
class-aware correction in one place for the sample table and summary figure.
"""

from __future__ import annotations

import math

FULL_SKY_SR = 4.0 * math.pi
SECONDS_PER_DAY = 86400.0
DEG2_PER_SR = (180.0 / math.pi) ** 2


def position_time_chance_probability(inputs: dict) -> float:
    """Poisson probability for the report's sky/time window with no DM cut."""
    mu = (
        float(inputs["rate_per_day"])
        / FULL_SKY_SR
        / SECONDS_PER_DAY
        * (float(inputs["omega_win_deg2"]) / DEG2_PER_SR)
        * (2.0 * float(inputs["dt_s"]))
    )
    return -math.expm1(-mu)


def class_aware_chance_probability(burst: dict, inputs: dict) -> float:
    """Return DM-filtered Pcc when DM is constrained, otherwise position+time Pcc."""
    if burst["dm_agreement"]["consistent"] is None:
        return position_time_chance_probability(inputs)
    return float(burst["chance_coincidence_P"])
